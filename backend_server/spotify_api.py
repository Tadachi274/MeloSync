# -*- coding: utf-8 -*-
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import time
import re

# SpotifyのURLまたはURIからトラックIDを抽出する関数
def extract_spotify_id(url_or_uri):
    # 入力が空でないことを確認
    if pd.isna(url_or_uri):
        return None
    # URL形式 (https://open.spotify.com/track/...) からIDを抽出
    match_url = re.search(r'track/([a-zA-Z0-9]+)(?:\?si=.*)?$', url_or_uri)
    if match_url:
        return match_url.group(1)
    # URI形式 (spotify:track:...) からIDを抽出
    match_uri = re.search(r'spotify:track:([a-zA-Z0-9]+)', url_or_uri)
    if match_uri:
        return match_uri.group(1)
    return None

# Spotify APIを叩いて、複数のトラックのオーディオ特徴量を取得する関数
def fetch_audio_features(df, client_id, client_secret, url_col='spotify_url'):
    # Spotify APIへの接続を確立
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
    
    # URLの列からトラックIDを抽出し、新しい列として追加
    df['track_id'] = df[url_col].apply(extract_spotify_id)
    df = df.dropna(subset=['track_id']) # トラックIDが取得できなかった行を削除
    
    # 重複を除いたユニークなトラックIDのリストを作成
    unique_track_ids = df['track_id'].unique().tolist()
    
    all_audio_features = []
    batch_size = 100 # APIへのリクエストを100件ずつのバッチ処理で行う
    
    # トラックIDのリストをバッチに分けてループ処理
    for i in range(0, len(unique_track_ids), batch_size):
        batch_ids = unique_track_ids[i:i + batch_size]
        try:
            # APIを叩いてオーディオ特徴量を取得
            features = sp.audio_features(batch_ids)
            all_audio_features.extend([f for f in features if f is not None])
            print(f"処理済みバッチ {i // batch_size + 1}/{(len(unique_track_ids) + batch_size - 1) // batch_size}")
            time.sleep(0.1) # APIへの負荷を軽減するために少し待機
        except Exception as e:
            # エラーが発生した場合はメッセージを表示して処理を続行
            print(f"バッチ {i // batch_size + 1} でエラーが発生しました: {e}")
            time.sleep(5) # エラー時は長めに待機
            
    # 取得した特徴量をpandasのDataFrameに変換
    audio_features_df = pd.DataFrame(all_audio_features)
    return audio_features_df