# generate_final_playlist.py (最終修正版、このファイルのみを編集)

import pandas as pd
import joblib
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

# --- 重要なステップ：プログラムの最初に.envファイルを読み込む ---
load_dotenv()

# --- 分離したモジュールから必要な機能を取得 ---
from spotify_utils import get_playlist_tracks
from recommend import recommend_songs_for_target
from feature_processor import process_tracks

# --- ユーザー設定 ---
# ここにあなたのSpotifyプレイリストのURLを入力してください
PLAYLIST_URL = 'https://open.spotify.com/playlist/53hcnFSWtcg7otg3rnVHkK?si=FwUmyRPoT5uqbfPZJ8f-Rg' 
user_start_mood_name = 'Tired/Sad'
user_target_mood_name ='Happy/Excited'

# --- メイン実行関数 ---
def main():
    if 'ここに分析したいSpotifyプレイリストのURLをペースト' in PLAYLIST_URL or 'googleusercontent.com' in PLAYLIST_URL:
        print("エラー: スクリプトを編集して、PLAYLIST_URLを実際のSpotifyプレイリストのURLに更新してください。")
        return

    try:
        # 1. 【追加】ここで認証トークンを取得
        print("情報: Spotifyアクセストークンを取得中...")
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not client_id or not client_secret:
            print("エラー: .envファイルまたは環境変数からSPOTIPY_CLIENT_IDとSPOTIPY_CLIENT_SECRETを読み込めませんでした。")
            return
            
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        access_token = auth_manager.get_access_token(as_dict=False)
        print("情報: トークンの取得に成功しました。")

        # 2. プレイリストのトラックIDを取得
        playlist_id = PLAYLIST_URL.split('/')[-1].split('?')[0]
        print(f"情報: プレイリスト '{playlist_id}' からトラックを取得中...")
        
        # 【修正】取得したaccess_tokenを2番目の引数として渡す
        playlist_items = get_playlist_tracks(playlist_id, access_token)
        
        track_ids = [item['track']['id'] for item in playlist_items if item.get('track') and item['track'].get('id')]
        
        if not track_ids:
            print(f"エラー: プレイリスト {PLAYLIST_URL} からトラックを取得できませんでした。")
            return
        print(f"情報: {len(track_ids)} 曲のトラックを正常に取得しました。")
            
        # 3. 中央プロセッサを呼び出してすべての特徴を取得・処理
        print("情報: SoundStatから特徴を取得し、前処理を行っています...")
        processed_df = process_tracks(track_ids)

        if processed_df.empty:
            print("エラー: 楽曲の特徴を処理できませんでした。")
            return

        playlist_track_ids = processed_df['id'].values
        X_playlist = processed_df.drop(columns=['id'])
        
        # 4. モデルを読み込んで推薦を生成
        model_filename = f"model_{user_start_mood_name.replace('/', '-')}.joblib"
        print(f"情報: モデル '{model_filename}' を読み込み中...")
        model = joblib.load(model_filename)
        
        mood_map = {'Angry/Frustrated': 0, 'Happy/Excited': 1, 'Relax/Chill': 2, 'Tired/Sad': 3}
        target_mood_code = mood_map[user_target_mood_name]
        
        print("情報: 推薦リストを生成中...")
        recommended_playlist = recommend_songs_for_target(
            model=model, X=X_playlist, track_ids=playlist_track_ids,
            target_mood_code=target_mood_code, top_k=100
        )
        print(X_playlist)
        
        # 5. 結果を表示
        print("\n" + "="*50)
        print(f"「{user_start_mood_name}」から「{user_target_mood_name}」への推薦リスト")
        print("="*50)
        if recommended_playlist:
            for i, (track_id, probability) in enumerate(recommended_playlist):
                print(f"{i+1:2d}. トラックID: {track_id:<25} | 移行確率: {probability:.2%}")
        else:
            print("推薦できる楽曲が見つかりませんでした。")

    except FileNotFoundError as e:
        print(f"\nモデルファイルが見つかりません: {e}")
        print("モデルトレーニングスクリプトを実行し、生成された.joblibファイルがこのスクリプトと同じディレクトリにあることを確認してください。")
    except Exception as e:
        print(f"\nプログラム実行中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main()