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
import post_playlist_and_tracks as Post_pt
from fastapi.responses import JSONResponse
import playlist_api as pa

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

# --- API エンドポイント ---
from pydantic import BaseModel
from typing import List

class EmotionRequest(BaseModel):
    before_emotion: str
    after_emotion: str
    chosen_playlists: List[str]


#プレイリスト名の除外リスト
EXCLUDED_PLAYLISTS = {
    "HAPPY-to-HAPPY", "HAPPY-to-RELAX", "HAPPY-to-ANGRY", "HAPPY-to-SAD",
    "RELAX-to-HAPPY", "RELAX-to-RELAX", "RELAX-to-ANGRY", "RELAX-to-SAD",
    "ANGRY-to-HAPPY", "ANGRY-to-RELAX", "ANGRY-to-ANGRY", "ANGRY-to-SAD",
    "SAD-to-HAPPY", "SAD-to-RELAX", "SAD-to-ANGRY", "SAD-to-SAD"
}


#感情を元にプレイリストのトラックを取得
@app.post("/api/playlist/emotion")
async def emotion_playlist_tracks(
    user_id: str = Depends(Post_pt.get_current_user),
    before_emotion: str = Query(...),
    after_emotion: str = Query(...),
    chosen_playlist: list[str] = Query(...)
):
    print(f"DEBUG before_emotion: {before_emotion}, after_emotion: {after_emotion}, chosen_playlist: {chosen_playlist}")

    # 2. DBからトークンを取得
    access_token, refresh_token, expires_at = Post_pt.fetch_user_tokens(user_id)

    # 3. Spotipyクライアントを初期化
    sp = Post_pt.get_spotify(access_token, refresh_token, expires_at)

    # 4. プレイリスト名を生成
    emotion_playlist_name = f"{before_emotion}-to-{after_emotion}"

    # 5. プレイリストのトラックを取得
    try:
        emotion_tracks = Post_pt.get_emotion_playlist_tracks(sp, emotion_playlist_name)
        specific_tracks = Post_pt.get_specific_playlist_tracks(sp, chosen_playlist)
        #print(f"DEBUG emotion_tracks: {emotion_tracks[:50]}")
        # フィルタリング: emotion_tracks に含まれる曲のみを返す
        filtered_tracks = [
            track for track in specific_tracks
            if any(emotion_track["track_id"] == track["track_id"] for emotion_track in emotion_tracks)
        ]
        print(f"DEBUG filtered_tracks: {filtered_tracks[:50]}")
        return JSONResponse(content={"data": filtered_tracks})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# ユーザーのプレイリスト一覧を取得
@app.post("/api/playlists")
async def user_playlists(
    user_id: str = Depends(Post_pt.get_current_user)
):
    # 1. DBからトークンを取得
    access_token, refresh_token, expires_at = Post_pt.fetch_user_tokens(user_id)

    # 2. Spotipyクライアントを初期化
    sp = Post_pt.get_spotify(access_token, refresh_token, expires_at)

    # 3. ユーザーのプレイリスト一覧を取得
    try:
        playlists = sp.current_user_playlists()["items"]
        playlist_info_list = [
            {
                "playlist_id": pl["id"],
                "playlist_name": pl["name"],
                "image_url": pl["images"][0]["url"] if pl["images"] else None
            }
            for pl in playlists
            if pl["name"] not in EXCLUDED_PLAYLISTS  # Exclude specific playlists
        ]
        print(f"DEBUG playlist_info_list: {playlist_info_list}")
        return JSONResponse(content={"data": playlist_info_list})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/classify")
async def create_mood_transition_playlist(
    #user_start_mood: str = Query(..., description="現在の気分: 'Angry/Frustrated', 'Happy/Excited', 'Relax/Chill', 'Tired/Sad'"),
    #user_target_mood: str = Query(..., description="目標の気分: 'Angry/Frustrated', 'Happy/Excited', 'Relax/Chill', 'Tired/Sad'"),
    # ▼▼▼ 変更点 4: APIパラメータを min_score に変更し、説明と範囲を更新 ▼▼▼
    #min_score: float = Query(40.0, ge=0, le=100, description="最小移行スコア（0-100）"),
    user_id: str = Depends(pa.get_current_user)
    
):
    user_start_mood= 'Tired/Sad'  # デフォルト値
    user_target_mood= 'Happy/Excited'  # デフォルト値
    min_score=45.0
    info = pa.get_max_playlist.get_max_playlist_information()
    source_playlist_id = info.get("id") or ""
    if not source_playlist_id:
        raise HTTPException(500, "ソースプレイリストIDが取得できませんでした")
    
    new_playlist_name = f"Mood Transition: {user_start_mood} → {user_target_mood} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 1. DB からトークン取得 ＆ 復号
    access_token, refresh_token, expires_at = pa.fetch_user_tokens(user_id)
    # 2. Spotipy インスタンス
    sp = pa.get_spotify(access_token, refresh_token, expires_at)
    # 3. 気分移行プレイリスト作成
    # ▼▼▼ 変更点 5: create_or_update_playlist に min_score を渡す ▼▼▼
    new_id = pa.create_or_update_playlist(
        sp, source_playlist_id, new_playlist_name,
        user_start_mood, user_target_mood, min_score
    )
    
    # ▼▼▼ 変更点 6: レスポンスの内容を min_score に更新 ▼▼▼
    return {
        "playlist_url": f"https://open.spotify.com/playlist/{new_id}",
        "mood_transition": f"{user_start_mood} → {user_target_mood}",
        "min_score": min_score
    }
