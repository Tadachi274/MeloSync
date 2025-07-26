# generate_final_playlist.py (最終修正版、このファイルのみを編集)

import pandas as pd
import joblib
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from typing import List, Tuple, Optional

# --- 重要なステップ：プログラムの最初に.envファイルを読み込む ---
load_dotenv()

# --- 分離したモジュールから必要な機能を取得 ---
from spotify_utils import get_playlist_tracks
from recommend import recommend_songs_for_target
from pre_process_normalize import process_tracks_directly
# score_normalizer.pyからのインポートは不要になりました

# --- ここから正規化関数を直接定義 ---
def normalize_scores(
    recommendations: List[Tuple[str, float]]
) -> List[Tuple[str, float]]:
    """
    移行確率のリストを0から100のスケールの移行スコアに正規化する関数。

    Args:
        recommendations (List[Tuple[str, float]]): (track_id, probability) のタプルのリスト。

    Returns:
        List[Tuple[str, float]]: (track_id, score) のタプルのリスト。スコアは0から100の範囲。
    """
    # 確率が空、または1曲しかない場合は、正規化せずにそのまま返すか、固定スコアを返す
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
# --- ここまで正規化関数の定義 ---


def recommend_playlist(
    playlist_url: str,
    user_start_mood_name: str,
    user_target_mood_name: str,
    top_k: int = 10000
) -> Optional[List[Tuple[str, float]]]:
    """
    プレイリストから推薦楽曲を生成する関数
    
    Args:
        playlist_url: SpotifyプレイリストのURL
        user_start_mood_name: 現在の気分
        user_target_mood_name: 目標の気分
        top_k: 推薦する楽曲の最大数
        
    Returns:
        List[Tuple[str, float]]: トラックIDと移行スコアのペアのリスト
    """
    if 'ここに分析したいSpotifyプレイリストのURLをペースト' in playlist_url or 'googleusercontent.com' in playlist_url:
        print("エラー: 有効なSpotifyプレイリストのURLを指定してください。")
        return None

    try:
        print("情報: Spotifyアクセストークンを取得中...")
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not client_id or not client_secret:
            print("エラー: .envファイルまたは環境変数からSPOTIPY_CLIENT_IDとSPOTIPY_CLIENT_SECRETを読み込めませんでした。")
            return None
            
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        access_token = auth_manager.get_access_token(as_dict=False)
        print("情報: トークンの取得に成功しました。")

        playlist_id = playlist_url.split('/')[-1].split('?')[0]
        print(f"情報: プレイリスト '{playlist_id}' からトラックを取得中...")
        
        playlist_items = get_playlist_tracks(playlist_id, access_token)
        track_ids = [item['track']['id'] for item in playlist_items if item.get('track') and item['track'].get('id')]
        
        if not track_ids:
            print(f"エラー: プレイリスト {playlist_url} からトラックを取得できませんでした。")
            return None
        print(f"情報: {len(track_ids)} 曲のトラックを正常に取得しました。")
            
        print("情報: SoundStatから特徴を取得し、pre_process_normalize.pyの方法で前処理を行っています...")
        processed_df = process_tracks_directly(track_ids)

        if processed_df.empty:
            print("エラー: 楽曲の特徴を処理できませんでした。")
            return None

        playlist_track_ids = processed_df['id'].values
        X_playlist = processed_df.drop(columns=['id', 'name', 'artists'])
        
        model_filename = f"model/model_{user_start_mood_name.replace('/', '-')}.joblib"
        print(f"情報: モデル '{model_filename}' を読み込み中...")
        model = joblib.load(model_filename)
        
        mood_map = {'Angry/Frustrated': 0, 'Happy/Excited': 1, 'Relax/Chill': 2, 'Tired/Sad': 3}
        target_mood_code = mood_map[user_target_mood_name]
        
        print("情報: 推薦リストを生成中...")
        recommended_playlist_with_probs = recommend_songs_for_target(
            model=model, X=X_playlist, track_ids=playlist_track_ids,
            target_mood_code=target_mood_code, top_k=top_k
        )
        
        print("情報: 移行確率を0-100の移行スコアに正規化しています...")
        final_scored_playlist = normalize_scores(recommended_playlist_with_probs)
        
        return final_scored_playlist

    except FileNotFoundError as e:
        print(f"\nモデルファイルが見つかりません: {e}")
        print("モデルトレーニングスクリプトを実行し、生成された.joblibファイルがこのスクリプトと同じディレクトリにあることを確認してください。")
        return None
    except Exception as e:
        print(f"\nプログラム実行中にエラーが発生しました: {e}")
        return None

# --- ユーザー設定 ---
PLAYLIST_URL = 'https://open.spotify.com/playlist/6rEdUNfBu6BiWgp0PNXIO4?si=1611984fbf574d02'
user_start_mood_name = 'Relax/Chill'
user_target_mood_name ='Relax/Chill'

# --- メイン実行関数 ---
def main():
    recommended_playlist = recommend_playlist(
        playlist_url=PLAYLIST_URL,
        user_start_mood_name=user_start_mood_name,
        user_target_mood_name=user_target_mood_name
    )
    
    if recommended_playlist:
        print("\n" + "="*50)
        print(f"「{user_start_mood_name}」から「{user_target_mood_name}」への推薦リスト")
        print("="*50)
        for i, (track_id, score) in enumerate(recommended_playlist):
            print(f"{i+1:2d}. トラックID: {track_id:<25} | 移行スコア: {score:3.0f}")
    else:
        print("推薦できる楽曲が見つかりませんでした。")

if __name__ == "__main__":
    main()
