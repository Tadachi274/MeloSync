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
DB_PORT     = 5433
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


print("DEBUG JWT_SECRET_KEY", JWT_SECRET_KEY)
print("DEBUG FERNET_KEY", raw_FERNET_KEY)
print("DEBUG SPOTIFY_CLIENT_ID    =", SPOTIFY_CLIENT_ID)

# --- JWT から user_id を取り出す Dependency ---
def get_current_user(authorization: str = Header(..., alias="Authorization")) -> str:
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


# --- 新しい関数：感情プレイリストのトラックを取得 ---
def get_emotion_playlist_tracks(
    sp: spotipy.Spotify,
    playlist_name: str
):
    # 既存プレイリスト検索
    target_id = None
    for pl in sp.current_user_playlists()["items"]:
        if pl["name"] == playlist_name:
            target_id = pl["id"]
            break

    if not target_id:
        raise HTTPException(status_code=404, detail="Playlist not found")

    # プレイリストのトラックを全部取得
    tracks = []
    results = sp.playlist_items(target_id)
    tracks += results["items"]
    while results["next"]:
        results = sp.next(results)
        tracks += results["items"]

    # トラック情報を抽出
    track_info_list = []
    for item in tracks:
        track = item["track"]
        track_id = track["id"]
        image_uri = track["album"]["images"][0]["url"] if track["album"]["images"] else None
        artist_name = track["artists"][0]["name"] if track["artists"] else None
        track_name = track["name"]

        track_info_list.append({
            "track_id": track_id,
            "image_uri": image_uri,
            "artist_name": artist_name,
            "track_name": track_name
        })

    return track_info_list

# --- 修正された関数：指定された複数のプレイリストIDのトラックを取得 ---
def get_specific_playlist_tracks(
    sp: spotipy.Spotify,
    playlist_ids: list
):
    track_info_list = []
    for playlist_id in playlist_ids:
        # プレイリストのトラックを全部取得
        tracks = []
        results = sp.playlist_items(playlist_id)
        tracks += results["items"]
        while results["next"]:
            results = sp.next(results)
            tracks += results["items"]

        # トラック情報を抽出
        for item in tracks:
            track = item["track"]
            track_id = track["id"]
            image_uri = track["album"]["images"][0]["url"] if track["album"]["images"] else None
            artist_name = track["artists"][0]["name"] if track["artists"] else None
            track_name = track["name"]

            track_info_list.append({
                "track_id": track_id,
                "image_uri": image_uri,
                "artist_name": artist_name,
                "track_name": track_name
            })

    return track_info_list

# --- API エンドポイント ---

#感情を元にプレイリストのトラックを取得
@app.post("/api/spotify/emotion-playlist-tracks")
async def emotion_playlist_tracks(
    user_id: str = Depends(get_current_user),
    before_emotion: str = Query(...),
    after_emotion: str = Query(...),
    chosen_playlist: list[str] = Query(...)
):

    # 2. DBからトークンを取得
    access_token, refresh_token, expires_at = fetch_user_tokens(user_id)

    # 3. Spotipyクライアントを初期化
    sp = get_spotify(access_token, refresh_token, expires_at)

    # 4. プレイリスト名を生成
    emotion_playlist_name = f"{before_emotion}-to-{after_emotion}"

    # 5. プレイリストのトラックを取得
    try:
        emotion_tracks = get_emotion_playlist_tracks(sp, emotion_playlist_name)
        specific_tracks = get_specific_playlist_tracks(sp, chosen_playlist)
        print(f"DEBUG emotion_tracks: {emotion_tracks}")
        print(f"DEBUG specific_tracks: {specific_tracks}")
        # フィルタリング: emotion_tracks に含まれる曲のみを返す
        filtered_tracks = [
            track for track in specific_tracks
            if any(emotion_track["track_id"] == track["track_id"] for emotion_track in emotion_tracks)
        ]
        return filtered_tracks
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# ユーザーのプレイリスト一覧を取得
@app.post("/api/playlists")
async def user_playlists(
    user_id: str = Depends(get_current_user)
):
    # 1. DBからトークンを取得
    access_token, refresh_token, expires_at = fetch_user_tokens(user_id)

    # 2. Spotipyクライアントを初期化
    sp = get_spotify(access_token, refresh_token, expires_at)

    # 3. ユーザーのプレイリスト一覧を取得
    try:
        playlists = sp.current_user_playlists()["items"]
        playlist_info_list = [
            {
                "playlist_id": pl["id"],
                "name": pl["name"],
                "description": pl.get("description"),
                "image_uri": pl["images"][0]["url"] if pl["images"] else None
            }
            for pl in playlists
        ]
        return playlist_info_list
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
