# playlist_api.py
import os
from fastapi import FastAPI, Depends, Header, HTTPException, Query
from jose import jwt, JWTError
import psycopg2
from cryptography.fernet import Fernet
from datetime import datetime, timezone
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import get_max_playlist
import sys
import os

# backend_serverディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend_server'))

# generate_final_playlistから関数をインポート
from generate_final_playlist import recommend_playlist

load_dotenv()  # .envから環境変数をロード

app = FastAPI()

# --- Env ---
JWT_SECRET_KEY    = os.getenv("JWT_SECRET_KEY")
ALGORITHM         = "HS256"
raw_FERNET_KEY = os.getenv("FERNET_KEY")
FERNET_KEY        = os.getenv("FERNET_KEY").encode('utf-8')

SPOTIFY_CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI  = os.getenv("SPOTIFY_REDIRECT_URI")
SCOPE = "playlist-modify-public playlist-read-private"

DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = int(os.getenv("DB_PORT", 5432))
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

print("DEBUG_SPOTIFY_REDIRECT_URI", SPOTIFY_REDIRECT_URI)


# --- JWT から user_id を取り出す Dependency ---
def get_current_user(authorization: str = Header(...)) -> str:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "Authorization header malformed")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(401, "user_id claim missing")
        return user_id
    except JWTError as e:
        raise HTTPException(401, f"Token validation failed: {e}")


# --- DB からそのユーザーのトークンを取得＆復号 ---
def fetch_user_tokens(user_id: str):
    with psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT access_token, refresh_token, expires_at
                  FROM spotify_tokens
                 WHERE user_id = %s
            """, (user_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Tokens not found for user")
            enc_access, enc_refresh, expires_at = row

    f = Fernet(FERNET_KEY)
    access_token  = f.decrypt(enc_access.encode()).decode("utf-8")
    refresh_token = f.decrypt(enc_refresh.encode()).decode("utf-8")
    return access_token, refresh_token, expires_at


# --- Spotipy クライアント取得（必要ならリフレッシュも） ---
def get_spotify(access_token: str, refresh_token: str, expires_at: int):
    now_ts = int(datetime.now(timezone.utc).timestamp())
    if now_ts >= expires_at:
        oauth = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=SCOPE
        )
        fresh = oauth.refresh_access_token(refresh_token)
        access_token  = fresh["access_token"]
        refresh_token = fresh.get("refresh_token", refresh_token)
        expires_at    = now_ts + fresh["expires_in"]
        # （オプション）DBに新しいトークンを保存する処理をここで呼び出す

    return spotipy.Spotify(auth=access_token)


# --- プレイリスト作成／更新処理（移行確率フィルタリング対応） ---
def create_or_update_playlist(
    sp: spotipy.Spotify,
    source_playlist_id: str,
    new_playlist_name: str,
    user_start_mood: str = None,
    user_target_mood: str = None,
    min_probability: float = 0.4
) -> str:
    me = sp.me()["id"]
    # 既存プレイリスト検索
    for pl in sp.current_user_playlists()["items"]:
        if pl["name"] == new_playlist_name:
            target_id = pl["id"]
            break
    else:
        target_id = sp.user_playlist_create(me, new_playlist_name, public=True)["id"]

    # 元プレイリストのトラックを全部取得
    uris = []
    results = sp.playlist_items(source_playlist_id)
    uris += [item["track"]["uri"] for item in results["items"]]
    while results["next"]:
        results = sp.next(results)
        uris += [item["track"]["uri"] for item in results["items"]]

    # 気分移行推薦が指定されている場合は、移行確率でフィルタリング
    if user_start_mood and user_target_mood:
        # プレイリストURLを作成
        playlist_url = f"https://open.spotify.com/playlist/{source_playlist_id}"
        
        # 推薦楽曲を取得
        recommended_playlist = recommend_playlist(
            playlist_url=playlist_url,
            user_start_mood_name=user_start_mood,
            user_target_mood_name=user_target_mood
        )
        
        if recommended_playlist:
            # 移行確率が閾値以上の楽曲のみをフィルタリング
            filtered_uris = []
            for track_id, probability in recommended_playlist:
                if probability >= min_probability:
                    # track_idをURIに変換
                    track_uri = f"spotify:track:{track_id}"
                    if track_uri in uris:  # 元プレイリストに存在する場合のみ
                        filtered_uris.append(track_uri)
            
            print(f"移行確率{min_probability:.1%}以上の楽曲: {len(filtered_uris)}曲")
            uris = filtered_uris
        else:
            print("推薦楽曲の取得に失敗しました。popularityフィルタリングを使用します。")
            # 推薦に失敗した場合は従来のpopularityフィルタリングを使用
            filtered = []
            for uri in uris:
                track = sp.track(uri)
                if track.get("popularity", 0) > 50:
                    filtered.append(uri)
            uris = filtered
    else:
        # 従来のpopularityフィルタリング
        filtered = []
        for uri in uris:
            track = sp.track(uri)
            if track.get("popularity", 0) > 50:
                filtered.append(uri)
        uris = filtered

    # 既存プレイリストの中身を取得して重複を除外
    existing = []
    res2 = sp.playlist_items(target_id)
    existing += [i["track"]["uri"] for i in res2["items"]]
    while res2["next"]:
        res2 = sp.next(res2)
        existing += [i["track"]["uri"] for i in res2["items"]]

    to_add = [u for u in uris if u not in existing]
    # 100件ずつ追加
    for i in range(0, len(to_add), 100):
        sp.playlist_add_items(target_id, to_add[i:i+100])

    return target_id

# --- 気分移行推薦エンドポイント ---
@app.post("/api/spotify/mood-transition-playlist")
async def create_mood_transition_playlist(
    user_start_mood: str = Query(..., description="現在の気分: 'Angry/Frustrated', 'Happy/Excited', 'Relax/Chill', 'Tired/Sad'"),
    user_target_mood: str = Query(..., description="目標の気分: 'Angry/Frustrated', 'Happy/Excited', 'Relax/Chill', 'Tired/Sad'"),
    min_probability: float = Query(0.4, description="最小移行確率（0.0-1.0）"),
    user_id: str = Depends(get_current_user)
):
    info = get_max_playlist.get_max_playlist_information()
    source_playlist_id = info.get("id") or ""
    if not source_playlist_id:
        raise HTTPException(500, "ソースプレイリストIDが取得できませんでした")
    
    new_playlist_name = f"Mood Transition: {user_start_mood} → {user_target_mood} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 1. DB からトークン取得 ＆ 復号
    access_token, refresh_token, expires_at = fetch_user_tokens(user_id)
    # 2. Spotipy インスタンス
    sp = get_spotify(access_token, refresh_token, expires_at)
    # 3. 気分移行プレイリスト作成
    new_id = create_or_update_playlist(
        sp, source_playlist_id, new_playlist_name,
        user_start_mood, user_target_mood, min_probability
    )
    
    return {
        "playlist_url": f"https://open.spotify.com/playlist/{new_id}",
        "mood_transition": f"{user_start_mood} → {user_target_mood}",
        "min_probability": min_probability
    }
