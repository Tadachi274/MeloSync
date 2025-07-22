import pandas as pd
import numpy as np
import requests
import os
import time
from urllib.parse import urlparse

# Spotify API認証
def get_spotify_access_token():
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    if not client_id or not client_secret:
        raise Exception('Spotify API認証情報が設定されていません')
    auth_url = "https://accounts.spotify.com/api/token"
    auth_response = requests.post(auth_url, {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })
    if auth_response.status_code == 200:
        return auth_response.json()['access_token']
    else:
        raise Exception(f"Spotify認証エラー: {auth_response.status_code}")

def extract_track_id_from_url(url):
    try:
        parsed_url = urlparse(url)
        if 'track' in parsed_url.path:
            path_parts = parsed_url.path.split('/')
            track_index = path_parts.index('track')
            if track_index + 1 < len(path_parts):
                track_id = path_parts[track_index + 1]
                if '?' in track_id:
                    track_id = track_id.split('?')[0]
                return track_id
        return None
    except Exception:
        return None

def get_audio_features(track_id, access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f'https://api.spotify.com/v1/audio-features/{track_id}'
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    return None

def get_track_info(track_id, access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f'https://api.spotify.com/v1/tracks/{track_id}'
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    return None

def preprocess_music_data(input_csv, output_csv):
    # データ読み込み
    df = pd.read_csv(input_csv)

    # 欠損値除去
    df = df.dropna()

    # 文字列カラムのトリム
    str_cols = df.select_dtypes(include='object').columns
    for col in str_cols:
        df[col] = df[col].str.strip()

    # 必要なカラムのみ抽出（例：全カラムを残す場合はこのまま）
    # columns_to_keep = ['担当者', 'アーティスト', '曲名（optional）', 'URL', 'Happy/Excited', 'Angry/Frustrated', 'Tired/Sad', 'Relax/Chill', 'ジャンル']
    # df = df[columns_to_keep]

    access_token = get_spotify_access_token()
    features_list = []
    for idx, row in df.iterrows():
        url = row['URL']
        track_id = extract_track_id_from_url(url)
        if not track_id:
            features_list.append({})
            continue
        audio_features = get_audio_features(track_id, access_token)
        print(audio_features)
        track_info = get_track_info(track_id, access_token)
        print(track_info)
        if audio_features is None or track_info is None:
            features_list.append({})
            continue
        # 必要なSpotify特徴量のみ抽出
        features = {
            'danceability': audio_features.get('danceability'),
            'energy': audio_features.get('energy'),
            'valence': audio_features.get('valence'),
            'tempo': audio_features.get('tempo'),
            'loudness': audio_features.get('loudness'),
            'acousticness': audio_features.get('acousticness'),
            'instrumentalness': audio_features.get('instrumentalness'),
            'liveness': audio_features.get('liveness'),
            'speechiness': audio_features.get('speechiness'),
            'mode': audio_features.get('mode'),
            'key': audio_features.get('key'),
            'time_signature': audio_features.get('time_signature'),
            'popularity': track_info.get('popularity'),
            'duration_ms': track_info.get('duration_ms'),
            'explicit': int(track_info.get('explicit', False)),
        }
        features_list.append(features)
        time.sleep(0.1)  # API制限対策
    features_df = pd.DataFrame(features_list)
    df = pd.concat([df.reset_index(drop=True), features_df], axis=1)

    # 保存先ディレクトリがなければ作成
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    # CSVとして保存
    df.to_csv(output_csv, index=False)
    print(f"前処理済みデータを {output_csv} に保存しました。行数: {len(df)}")

if __name__ == "__main__":
    preprocess_music_data(
        input_csv="data/melosync_music_data.csv",
        output_csv="data/processed_music_data.csv"
    )