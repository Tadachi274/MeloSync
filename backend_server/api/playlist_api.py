from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple, Optional
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import joblib

# 環境変数を読み込み（親ディレクトリの.envファイルを読み込む）
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# FastAPIアプリケーションを作成
app = FastAPI(title="MeloSync Playlist Generator API", version="1.0.0")

# リクエストモデル
class AllPlaylistsRequest(BaseModel):
    playlist_ids: List[str]  # 複数のプレイリストIDを受け取る
    top_k: int = 10000
    create_spotify_playlists: bool = False
    max_tracks: int = 20

# レスポンスモデル
class AllPlaylistsResponse(BaseModel):
    success: bool
    message: str
    playlists: Optional[dict] = None
    spotify_playlist_urls: Optional[dict] = None
    error: Optional[str] = None

# 利用可能な感情のリスト
AVAILABLE_MOODS = ['Angry/Frustrated', 'Happy/Excited', 'Relax/Chill', 'Tired/Sad']

# generate_final_playlist.pyから必要な関数をインポート
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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



def generate_all_playlists_from_multiple_sources(
    playlist_ids: List[str],
    top_k: int = 10000
) -> dict:
    """
    複数のプレイリストIDから楽曲を統合して、4つの感情状態の組み合わせで16個のプレイリストを生成する関数
    """
    # プレイリストIDの検証
    for playlist_id in playlist_ids:
        if not playlist_id or len(playlist_id) < 10:  # SpotifyプレイリストIDは通常22文字
            raise ValueError(f"無効なプレイリストIDが含まれています: {playlist_id}")

    try:
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError("SPOTIFY_CLIENT_IDとSPOTIFY_CLIENT_SECRETが設定されていません。")
            
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        access_token = auth_manager.get_access_token(as_dict=False)

        # 全てのプレイリストから楽曲を収集
        all_track_ids = []
        
        print(f"情報: {len(playlist_ids)}個のプレイリストから楽曲を収集中...")
        
        for i, playlist_id in enumerate(playlist_ids):
            try:
                print(f"情報: プレイリスト {i+1}/{len(playlist_ids)} '{playlist_id}' からトラックを取得中...")
                
                playlist_items = get_playlist_tracks(playlist_id, access_token)
                track_ids = [item['track']['id'] for item in playlist_items if item.get('track') and item['track'].get('id')]
                
                if track_ids:
                    all_track_ids.extend(track_ids)
                    print(f"情報: {len(track_ids)} 曲を取得しました。")
                else:
                    print(f"警告: プレイリスト {playlist_id} からトラックを取得できませんでした。")
                    
            except Exception as e:
                print(f"警告: プレイリスト {playlist_id} の処理中にエラーが発生しました: {e}")
                continue
        
        if not all_track_ids:
            raise ValueError("どのプレイリストからも楽曲を取得できませんでした。")
        
        # 重複を除去
        unique_track_ids = list(set(all_track_ids))
        print(f"情報: 合計 {len(unique_track_ids)} 曲のユニークな楽曲を収集しました。")
        
        # 楽曲の特徴を処理
        print("情報: 楽曲の特徴を処理中...")
        processed_df = process_tracks_directly(unique_track_ids)

        if processed_df.empty:
            raise ValueError("楽曲の特徴を処理できませんでした。")

        playlist_track_ids = processed_df['id'].values
        X_playlist = processed_df.drop(columns=['id', 'name', 'artists'])
        
        all_playlists = {}
        
        # 4つの感情状態の組み合わせで16個のプレイリストを生成
        print("情報: 16個のプレイリストを生成中...")
        for current_mood in AVAILABLE_MOODS:
            all_playlists[current_mood] = {}
            
            for target_mood in AVAILABLE_MOODS:
                try:
                    model_filename = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"model/model_{current_mood.replace('/', '-')}.joblib")
                    model = joblib.load(model_filename)
                    
                    mood_map = {'Angry/Frustrated': 0, 'Happy/Excited': 1, 'Relax/Chill': 2, 'Tired/Sad': 3}
                    target_mood_code = mood_map[target_mood]
                    
                    recommended_playlist_with_probs = recommend_songs_for_target(
                        model=model, X=X_playlist, track_ids=playlist_track_ids,
                        target_mood_code=target_mood_code, top_k=top_k
                    )
                    
                    final_scored_playlist = normalize_scores(recommended_playlist_with_probs)
                    
                    # プレイリストデータを整形
                    playlist_data = []
                    for i, (track_id, score) in enumerate(final_scored_playlist):
                        playlist_data.append({
                            "rank": i + 1,
                            "track_id": track_id,
                            "transition_score": round(score, 2)
                        })
                    
                    all_playlists[current_mood][target_mood] = {
                        "success": True,
                        "playlist": playlist_data,
                        "count": len(playlist_data)
                    }
                    
                except Exception as e:
                    all_playlists[current_mood][target_mood] = {
                        "success": False,
                        "error": str(e),
                        "playlist": [],
                        "count": 0
                    }
        
        return all_playlists

    except Exception as e:
        raise ValueError(f"全プレイリスト生成中にエラーが発生しました: {e}")



@app.get("/")
async def root():
    """APIのルートエンドポイント"""
    return {
        "message": "MeloSync Playlist Generator API",
        "version": "1.0.0",
        "available_moods": AVAILABLE_MOODS,
        "endpoints": {
            "health": "GET /health",
            "generate_all_playlists": "POST /generate-all-playlists"
        }
    }

@app.post("/generate-all-playlists", response_model=AllPlaylistsResponse)
async def generate_all_playlists_endpoint(request: AllPlaylistsRequest):
    """
    複数のプレイリストIDから楽曲を統合して、4つの感情状態の組み合わせで16個のプレイリストを一括生成するエンドポイント
    """
    try:
        # 入力値の検証
        if not request.playlist_ids or len(request.playlist_ids) == 0:
            raise HTTPException(
                status_code=400, 
                detail="プレイリストIDのリストを指定してください"
            )
        
        # 各プレイリストIDの検証
        for playlist_id in request.playlist_ids:
            if not playlist_id or len(playlist_id) < 10:
                raise HTTPException(
                    status_code=400, 
                    detail=f"無効なプレイリストIDが含まれています: {playlist_id}"
                )

        # 全プレイリスト生成
        all_playlists = generate_all_playlists_from_multiple_sources(
            playlist_ids=request.playlist_ids,
            top_k=request.top_k
        )
        
        # 成功したプレイリスト数をカウント
        successful_count = 0
        total_count = 0
        for current_mood in all_playlists:
            for target_mood in all_playlists[current_mood]:
                total_count += 1
                if all_playlists[current_mood][target_mood]["success"]:
                    successful_count += 1

        # Spotifyプレイリスト作成の処理
        spotify_playlist_urls = None
        if request.create_spotify_playlists:
            try:
                # プレイリスト作成関数をインポート（相対インポート）
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                
                # generate_final_playlistから関数をインポート
                from generate_final_playlist import create_spotify_playlist
                
                spotify_playlist_urls = {}
                
                # 各感情の組み合わせでプレイリストを作成
                for current_mood in all_playlists:
                    spotify_playlist_urls[current_mood] = {}
                    
                    for target_mood in all_playlists[current_mood]:
                        if all_playlists[current_mood][target_mood]["success"]:
                            # 推薦楽曲のリストを(track_id, score)の形式に変換
                            recommended_playlist = []
                            for track in all_playlists[current_mood][target_mood]["playlist"]:
                                recommended_playlist.append((track["track_id"], track["transition_score"]))
                            
                            # Spotifyプレイリストを作成
                            playlist_url = create_spotify_playlist(
                                recommended_playlist=recommended_playlist,
                                user_start_mood_name=current_mood,
                                user_target_mood_name=target_mood,
                                max_tracks=request.max_tracks
                            )
                            
                            spotify_playlist_urls[current_mood][target_mood] = playlist_url
                        else:
                            spotify_playlist_urls[current_mood][target_mood] = None
                            
            except Exception as e:
                print(f"Spotifyプレイリスト作成エラー: {e}")
                spotify_playlist_urls = None

        return AllPlaylistsResponse(
            success=True,
            message=f"{len(request.playlist_ids)}個のプレイリストから楽曲を統合して16個のプレイリストを生成しました。成功: {successful_count}/{total_count}",
            playlists=all_playlists,
            spotify_playlist_urls=spotify_playlist_urls
        )

    except HTTPException:
        raise
    except ValueError as e:
        return AllPlaylistsResponse(
            success=False,
            message="全プレイリスト生成に失敗しました。",
            error=str(e)
        )
    except Exception as e:
        return AllPlaylistsResponse(
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