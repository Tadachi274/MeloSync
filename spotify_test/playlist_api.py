# playlist_api.py
import os
import sys
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
print(f"DEBUG: Attempting to load .env file from: {dotenv_path}")
load_dotenv(dotenv_path=dotenv_path)
# --- 后续的其他 import ---
from fastapi import FastAPI, Depends, Header, HTTPException, Query
from jose import jwt, JWTError
import psycopg2
from cryptography.fernet import Fernet
from datetime import datetime, timezone
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import get_max_playlist
# backend_serverディレクトリをパスに追加
backend_server_path = os.path.join(os.path.dirname(__file__), '..', 'backend_server')
sys.path.insert(0, backend_server_path)
# generate_final_playlistから関数をインポート
from generate_final_playlist import recommend_playlist
app = FastAPI()
# --- Env ---
JWT_SECRET_KEY    = os.getenv("JWT_SECRET_KEY")
ALGORITHM         = "HS256"
raw_FERNET_KEY = os.getenv("FERNET_KEY")
print("DEBUG FERNET_KEY", raw_FERNET_KEY)
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


# --- プレイリスト作成／更新処理（リファクタリング版） ---
def create_or_update_playlist(
    sp: spotipy.Spotify,
    source_playlist_id: str,
    new_playlist_name: str,
    user_start_mood: str = None,
    user_target_mood: str = None,
    min_score: float = 40.0
) -> str:
    """
    指定された条件に基づいてSpotifyプレイリストを作成または更新します。
    気分移行が指定された場合、generate_final_playlistから推薦を取得して歌单を生成します。
    """
    me = sp.me()["id"]

    # --- ステップ1: 新しいプレイリストを作成、または同名の既存プレイリストを探す ---
    target_playlist_id = None
    for pl in sp.current_user_playlists()["items"]:
        if pl["name"] == new_playlist_name:
            target_playlist_id = pl["id"]
            print(f"既存のプレイリスト '{new_playlist_name}' (ID: {target_playlist_id}) を更新します。")
            break
    else:
        # 見つからなければ新しく作成
        new_playlist = sp.user_playlist_create(me, new_playlist_name, public=True)
        target_playlist_id = new_playlist["id"]
        print(f"新しいプレイリスト '{new_playlist_name}' (ID: {target_playlist_id}) を作成しました。")


    uris_to_add = []
    # --- ステップ2: 推薦ロジックを呼び出し、曲のIDリストを取得 ---
    # 気分移行が指定されている場合、generate_final_playlistを呼び出す
    if user_start_mood and user_target_mood:
        print("情報: generate_final_playlist から推薦リストを生成中...")
        playlist_url = f"https://open.spotify.com/playlist/{source_playlist_id}"
        
        # ★★★ ここが核心部分です ★★★
        # generate_final_playlist.py の recommend_playlist を呼び出し、ランキングリストを取得します。
        # recommended_playlist の形式: [(track_id, score), (track_id, score), ...]
        recommended_playlist = recommend_playlist(
            playlist_url=playlist_url,
            user_start_mood_name=user_start_mood,
            user_target_mood_name=user_target_mood
        )
        
        if recommended_playlist:
            # ランキングリストから track_id を抽出し、Spotify APIが要求するURI形式に変換します。
            # ▼▼▼ 新增的打印排名代码 ▼▼▼
            print("\n" + "="*60)
            print(f"「{user_start_mood}」から「{user_target_mood}」への推薦ランキング (上位20曲)")
            print("="*60)
            # 为了避免终端被刷屏，只显示排名前20的歌曲
            for i, (track_id, score) in enumerate(recommended_playlist[:50]):
                print(f"{i+1:2d}. Track ID: {track_id:<25} | Score: {score:6.2f}")
            print("="*60 + "\n")
            # ▲▲▲ 打印代码结束 ▲▲▲
            # ▼▼▼ 変更点 2: 変数名を probability から score に変更し、min_score でフィルタリング ▼▼▼
            for track_id, score in recommended_playlist:
                if score >= min_score:
                    uris_to_add.append(f"spotify:track:{track_id}")
            
            # ▼▼▼ 変更点 3: ログメッセージを score ベースに更新 ▼▼▼
            print(f"情報: 移行スコアが {min_score} 以上の楽曲 {len(uris_to_add)} 曲を処理対象にします。")
        else:
            print("警告: 推薦リストの生成に失敗しました。プレイリストは空のままです。")
            pass

    else:
        # (フォールバック処理) 気分移行が指定されない場合、元コードのpopularityフィルターを適用
        print("情報: 気分移行が指定されていないため、popularity > 50 の曲をフィルタリングします。")
        results = sp.playlist_items(source_playlist_id)
        source_uris = [item["track"]["uri"] for item in results["items"] if item.get("track")]
        while results["next"]:
            results = sp.next(results)
            source_uris += [item["track"]["uri"] for item in results["items"] if item.get("track")]

        for uri in source_uris:
            track = sp.track(uri)
            if track.get("popularity", 0) > 50:
                uris_to_add.append(uri)

    # --- ステップ3: 抽出した曲をプレイリストに追加 ---
    if uris_to_add:
        # プレイリストの中身を完全に置き換える場合はこちらが効率的です。
        # まずは100件ずつ追加します（APIの制限のため）
        for i in range(0, len(uris_to_add), 100):
            sp.playlist_add_items(target_playlist_id, uris_to_add[i:i+100])

        print(f"情報: {len(uris_to_add)} 曲をプレイリスト '{new_playlist_name}' に追加しました。")

    else:
        print("情報: 追加する曲がありませんでした。")

    return target_playlist_id


# --- API エンドポイント ---
@app.post("/api/spotify/create-playlist")
async def spotify_create_playlist(
    user_id: str = Depends(get_current_user)
):
    info = get_max_playlist.get_max_playlist_information()
    source_playlist_id = info.get("id") or ""
    if not source_playlist_id:
        raise HTTPException(500, "ソースプレイリストIDが取得できませんでした")
    
    new_playlist_name= f"Filtered Playlist - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    # 1. DB からトークン取得 ＆ 復号
    access_token, refresh_token, expires_at = fetch_user_tokens(user_id)
    # 2. Spotipy インスタンス
    sp = get_spotify(access_token, refresh_token, expires_at)
    # 3. プレイリスト作成
    new_id = create_or_update_playlist(sp, source_playlist_id, new_playlist_name)
    return {"playlist_url": f"https://open.spotify.com/playlist/{new_id}"}


# --- 気分移行推薦エンドポイント ---
@app.post("/api/spotify/mood-transition-playlist")
async def create_mood_transition_playlist(
    #user_start_mood: str = Query(..., description="現在の気分: 'Angry/Frustrated', 'Happy/Excited', 'Relax/Chill', 'Tired/Sad'"),
    #user_target_mood: str = Query(..., description="目標の気分: 'Angry/Frustrated', 'Happy/Excited', 'Relax/Chill', 'Tired/Sad'"),
    # ▼▼▼ 変更点 4: APIパラメータを min_score に変更し、説明と範囲を更新 ▼▼▼
    #min_score: float = Query(40.0, ge=0, le=100, description="最小移行スコア（0-100）"),
    user_id: str = Depends(get_current_user)
):
    user_start_mood= 'Tired/Sad'  # デフォルト値
    user_target_mood= 'Happy/Excited'  # デフォルト値
    min_score=45.0
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
    # ▼▼▼ 変更点 5: create_or_update_playlist に min_score を渡す ▼▼▼
    new_id = create_or_update_playlist(
        sp, source_playlist_id, new_playlist_name,
        user_start_mood, user_target_mood, min_score
    )
    
    # ▼▼▼ 変更点 6: レスポンスの内容を min_score に更新 ▼▼▼
    return {
        "playlist_url": f"https://open.spotify.com/playlist/{new_id}",
        "mood_transition": f"{user_start_mood} → {user_target_mood}",
        "min_score": min_score
    }
