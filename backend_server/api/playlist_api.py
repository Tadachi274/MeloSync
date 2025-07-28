from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple, Optional
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import joblib
import psycopg2
from cryptography.fernet import Fernet
from datetime import datetime, timezone

# データベース設定
DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = 5433
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
FERNET_KEY  = os.getenv("FERNET_KEY")


# 環境変数を読み込み（親ディレクトリの.envファイルを読み込む）
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# FastAPIアプリケーションを作成
app = FastAPI(title="MeloSync Playlist Generator API", version="1.0.0")

# リクエストモデル
class AllPlaylistsRequest(BaseModel):
    user_id: str  # ユーザーID
    playlist_ids: List[str]  # 複数のプレイリストIDを受け取る

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
    playlist_ids: List[str]
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
                        target_mood_code=target_mood_code, top_k=10000
                    )
                    
                    final_scored_playlist = normalize_scores(recommended_playlist_with_probs)
                    # 只保留score大于45的歌曲
                    filtered_playlist = [(track_id, score) for track_id, score in final_scored_playlist if score > 45]
                    
                    # プレイリストデータを整形
                    playlist_data = []
                    for i, (track_id, score) in enumerate(filtered_playlist):
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



def fetch_user_tokens(user_id: str):
    """ユーザーのSpotifyトークンを取得し、必要に応じてリフレッシュする"""
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
    
    # トークンの有効期限をチェック
    if expires_at and expires_at < datetime.now(timezone.utc):
        # トークンが期限切れの場合、リフレッシュする
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
        
        from spotipy.oauth2 import SpotifyOAuth
        sp_oauth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="playlist-modify-public playlist-modify-private"
        )
        
        # リフレッシュトークンを使用して新しいアクセストークンを取得
        token_info = sp_oauth.refresh_access_token(refresh_token)
        if not token_info:
            raise HTTPException(401, "Failed to refresh access token")
        
        # 新しいトークンをデータベースに保存
        new_access_token = token_info['access_token']
        new_refresh_token = token_info.get('refresh_token', refresh_token)
        new_expires_at = datetime.fromtimestamp(token_info['expires_at'], tz=timezone.utc)
        
        # トークンを暗号化して保存
        enc_new_access = f.encrypt(new_access_token.encode()).decode()
        enc_new_refresh = f.encrypt(new_refresh_token.encode()).decode()
        
        with psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE spotify_tokens 
                       SET access_token = %s, refresh_token = %s, expires_at = %s
                     WHERE user_id = %s
                """, (enc_new_access, enc_new_refresh, new_expires_at, user_id))
                conn.commit()
        
        return new_access_token, new_refresh_token, new_expires_at
    
    return access_token, refresh_token, expires_at

def create_user_spotify_playlist(
    user_id: str,
    recommended_playlist: List[Tuple[str, float]],
    user_start_mood_name: str,
    user_target_mood_name: str,
    max_tracks: int = 20
) -> Optional[str]:
    """
    ユーザーのSpotifyアカウントにプレイリストを作成または更新する関数
    
    Args:
        user_id: ユーザーID
        recommended_playlist: 推薦された楽曲のリスト（トラックIDとスコアのタプル）
        user_start_mood_name: 現在の気分
        user_target_mood_name: 目標の気分
        max_tracks: プレイリストに追加する最大楽曲数
        
    Returns:
        str: 作成または更新されたプレイリストのURL、失敗時はNone
    """
    try:
        # ユーザーのトークンを取得
        access_token, _, _ = fetch_user_tokens(user_id)
        
        # Spotifyクライアントを作成
        sp = spotipy.Spotify(auth=access_token)
        
        # 現在のユーザー情報を取得
        user_info = sp.current_user()
        user_id_spotify = user_info['id']
        print(f"情報: ユーザー '{user_info['display_name']}' として認証されました。")
        
        # 感情名のマッピング
        mood_mapping = {
            'Angry/Frustrated': 'ANGRY',
            'Happy/Excited': 'HAPPY',
            'Relax/Chill': 'RELAX',
            'Tired/Sad': 'SAD'
        }
        
        # プレイリスト名を生成
        start_mood_short = mood_mapping.get(user_start_mood_name, user_start_mood_name)
        target_mood_short = mood_mapping.get(user_target_mood_name, user_target_mood_name)
        playlist_name = f"{start_mood_short}-to-{target_mood_short}"
        playlist_description = f"MeloSync generated playlist: Transition from {user_start_mood_name} to {user_target_mood_name}"
        
        # 既存のプレイリストを検索
        existing_playlist = None
        offset = 0
        limit = 50
        
        while True:
            playlists = sp.current_user_playlists(limit=limit, offset=offset)
            if not playlists['items']:
                break
                
            for playlist in playlists['items']:
                if playlist['name'] == playlist_name:
                    existing_playlist = playlist
                    break
            
            if existing_playlist:
                break
                
            offset += limit
            if offset >= playlists['total']:
                break
        
        playlist_id = None
        playlist_url = None
        
        if existing_playlist:
            # 既存のプレイリストを更新
            playlist_id = existing_playlist['id']
            playlist_url = existing_playlist['external_urls']['spotify']
            print(f"情報: 既存のプレイリスト '{playlist_name}' を更新中...")
            
            # 既存の楽曲をすべて削除
            current_tracks = sp.playlist_tracks(playlist_id, fields='items(track(id))')
            if current_tracks['items']:
                track_ids_to_remove = [item['track']['id'] for item in current_tracks['items'] if item['track']]
                if track_ids_to_remove:
                    sp.playlist_remove_all_occurrences_of_items(playlist_id, track_ids_to_remove)
                    print(f"情報: 既存の {len(track_ids_to_remove)} 曲を削除しました。")
        else:
            # 新しいプレイリストを作成
            print(f"情報: 新しいプレイリスト '{playlist_name}' を作成中...")
            playlist = sp.user_playlist_create(
                user=user_id_spotify,
                name=playlist_name,
                description=playlist_description,
                public=True
            )
            playlist_id = playlist['id']
            playlist_url = playlist['external_urls']['spotify']
        
        # 推薦された楽曲をプレイリストに追加
        track_ids = [track_id for track_id, _ in recommended_playlist[:max_tracks]]
        
        if track_ids:
            print(f"情報: {len(track_ids)} 曲をプレイリストに追加中...")
            
            # 楽曲をプレイリストに追加
            sp.playlist_add_items(playlist_id, track_ids)
            
            action = "更新" if existing_playlist else "作成"
            print(f"✅ プレイリストが正常に{action}されました！")
            print(f"   プレイリスト名: {playlist_name}")
            print(f"   楽曲数: {len(track_ids)}")
            print(f"   プレイリストURL: {playlist_url}")
            
            return playlist_url
        else:
            print("エラー: 追加する楽曲がありません。")
            return None
            
    except Exception as e:
        print(f"エラー: プレイリスト作成/更新中にエラーが発生しました: {e}")
        return None

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
            playlist_ids=request.playlist_ids
        )
        
        # 成功したプレイリスト数をカウント
        successful_count = 0
        total_count = 0
        for current_mood in all_playlists:
            for target_mood in all_playlists[current_mood]:
                total_count += 1
                if all_playlists[current_mood][target_mood]["success"]:
                    successful_count += 1

        # Spotifyプレイリスト作成の処理（デフォルトでtrue、max_tracks=20）
        spotify_playlist_urls = None
        try:
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
                        
                        # ユーザーのSpotifyプレイリストを作成
                        playlist_url = create_user_spotify_playlist(
                            user_id=request.user_id,
                            recommended_playlist=recommended_playlist,
                            user_start_mood_name=current_mood,
                            user_target_mood_name=target_mood,
                            max_tracks=20  # デフォルト値
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
