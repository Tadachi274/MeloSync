from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple, Optional
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import joblib

# 環境変数を読み込み
load_dotenv()

# FastAPIアプリケーションを作成
app = FastAPI(title="MeloSync Playlist Generator API", version="1.0.0")

# リクエストモデル
class PlaylistRequest(BaseModel):
    playlist_url: str
    current_mood: str
    target_mood: str
    top_k: int = 10000

# レスポンスモデル
class PlaylistResponse(BaseModel):
    success: bool
    message: str
    playlist: Optional[List[dict]] = None
    error: Optional[str] = None

# 利用可能な感情のリスト
AVAILABLE_MOODS = ['Angry/Frustrated', 'Happy/Excited', 'Relax/Chill', 'Tired/Sad']

# generate_final_playlist.pyから必要な関数をインポート
from spotify_utils import get_playlist_tracks
from recommend import recommend_songs_for_target
from pre_process_normalize import process_tracks_directly

def normalize_scores(
    recommendations: List[Tuple[str, float]]
) -> List[Tuple[str, float]]:
    """
    移行確率のリストを0から100のスケールの移行スコアに正規化する関数。
    """
    if not recommendations or len(recommendations) < 2:
        if recommendations:
            track_id, _ = recommendations[0]
            return [(track_id, 50.0)]
        return []

    probabilities = [prob for _, prob in recommendations]
    min_prob = min(probabilities)
    max_prob = max(probabilities)
    
    if min_prob == max_prob:
        return [(track_id, 50.0) for track_id, _ in recommendations]

    normalized_list = []
    for track_id, prob in recommendations:
        score = ((prob - min_prob) / (max_prob - min_prob)) * 100
        normalized_list.append((track_id, score))
        
    normalized_list.sort(key=lambda item: item[1], reverse=True)
    return normalized_list

def recommend_playlist(
    playlist_url: str,
    user_start_mood_name: str,
    user_target_mood_name: str,
    top_k: int = 10000
) -> Optional[List[Tuple[str, float]]]:
    """
    プレイリストから推薦楽曲を生成する関数
    """
    if 'ここに分析したいSpotifyプレイリストのURLをペースト' in playlist_url or 'googleusercontent.com' in playlist_url:
        raise ValueError("有効なSpotifyプレイリストのURLを指定してください。")

    try:
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError("SPOTIFY_CLIENT_IDとSPOTIFY_CLIENT_SECRETが設定されていません。")
            
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        access_token = auth_manager.get_access_token(as_dict=False)

        playlist_id = playlist_url.split('/')[-1].split('?')[0]
        playlist_items = get_playlist_tracks(playlist_id, access_token)
        track_ids = [item['track']['id'] for item in playlist_items if item.get('track') and item['track'].get('id')]
        
        if not track_ids:
            raise ValueError(f"プレイリスト {playlist_url} からトラックを取得できませんでした。")
            
        processed_df = process_tracks_directly(track_ids)

        if processed_df.empty:
            raise ValueError("楽曲の特徴を処理できませんでした。")

        playlist_track_ids = processed_df['id'].values
        X_playlist = processed_df.drop(columns=['id', 'name', 'artists'])
        
        model_filename = f"model/model_{user_start_mood_name.replace('/', '-')}.joblib"
        model = joblib.load(model_filename)
        
        mood_map = {'Angry/Frustrated': 0, 'Happy/Excited': 1, 'Relax/Chill': 2, 'Tired/Sad': 3}
        target_mood_code = mood_map[user_target_mood_name]
        
        recommended_playlist_with_probs = recommend_songs_for_target(
            model=model, X=X_playlist, track_ids=playlist_track_ids,
            target_mood_code=target_mood_code, top_k=top_k
        )
        
        final_scored_playlist = normalize_scores(recommended_playlist_with_probs)
        
        return final_scored_playlist

    except FileNotFoundError as e:
        raise ValueError(f"モデルファイルが見つかりません: {e}")
    except Exception as e:
        raise ValueError(f"プレイリスト生成中にエラーが発生しました: {e}")

@app.get("/")
async def root():
    """APIのルートエンドポイント"""
    return {
        "message": "MeloSync Playlist Generator API",
        "version": "1.0.0",
        "available_moods": AVAILABLE_MOODS
    }

@app.get("/moods")
async def get_available_moods():
    """利用可能な感情のリストを取得"""
    return {
        "success": True,
        "available_moods": AVAILABLE_MOODS
    }

@app.post("/generate-playlist", response_model=PlaylistResponse)
async def generate_playlist(request: PlaylistRequest):
    """
    ユーザーの現在の感情と目標感情に基づいてプレイリストを生成するエンドポイント
    """
    try:
        # 入力値の検証
        if request.current_mood not in AVAILABLE_MOODS:
            raise HTTPException(
                status_code=400, 
                detail=f"無効な現在の感情です。利用可能な感情: {AVAILABLE_MOODS}"
            )
        
        if request.target_mood not in AVAILABLE_MOODS:
            raise HTTPException(
                status_code=400, 
                detail=f"無効な目標感情です。利用可能な感情: {AVAILABLE_MOODS}"
            )
        
        if not request.playlist_url or 'spotify.com/playlist/' not in request.playlist_url:
            raise HTTPException(
                status_code=400, 
                detail="有効なSpotifyプレイリストURLを指定してください"
            )

        # プレイリスト生成
        recommended_playlist = recommend_playlist(
            playlist_url=request.playlist_url,
            user_start_mood_name=request.current_mood,
            user_target_mood_name=request.target_mood,
            top_k=request.top_k
        )
        
        if not recommended_playlist:
            return PlaylistResponse(
                success=False,
                message="推薦できる楽曲が見つかりませんでした。",
                error="No recommendations found"
            )

        # レスポンス用のプレイリストデータを作成
        playlist_data = []
        for i, (track_id, score) in enumerate(recommended_playlist):
            playlist_data.append({
                "rank": i + 1,
                "track_id": track_id,
                "transition_score": round(score, 2)
            })

        return PlaylistResponse(
            success=True,
            message=f"「{request.current_mood}」から「{request.target_mood}」への推薦プレイリストを生成しました。",
            playlist=playlist_data
        )

    except HTTPException:
        raise
    except ValueError as e:
        return PlaylistResponse(
            success=False,
            message="プレイリスト生成に失敗しました。",
            error=str(e)
        )
    except Exception as e:
        return PlaylistResponse(
            success=False,
            message="予期しないエラーが発生しました。",
            error=str(e)
        )

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "message": "MeloSync API is running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)