# feature_processor.py

import pandas as pd
import requests
import os
import time
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 缓存文件路径 ---
CACHE_FILE_PATH = "data/soundstat_cache.csv"

def get_soundstat_track_info(spotify_track_id: str):
    """
    Soundstat APIを使用して、指定されたSpotifyトラックIDの楽曲情報を取得します。
    """
    api_key = os.getenv("SOUNDSTAT_API_KEY")
    if not api_key:
        api_key = "WUr-dT_zOy0oYVEJsrAuFEXxYpYbB9hCFidSsoRUdWk"
    
    api_url = f"https://soundstat.info/api/v1/track/{spotify_track_id}"
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as req_err:
        print(f"リクエストエラー: {req_err}, track_id: {spotify_track_id}")
    return None

def process_tracks(track_ids: list) -> pd.DataFrame:
    """
    トラックIDのリストを受け取り、APIから特徴量を取得し、
    モデル入力用に完全に処理されたデータフレームを返します。
    （キャッシュと10件ずつの並行処理を実装）
    """
    if not track_ids:
        return pd.DataFrame()

    # --- ステップ1: キャッシュの読み込みと、取得が必要なIDの特定 ---
    cached_df = pd.DataFrame()
    if os.path.exists(CACHE_FILE_PATH):
        try:
            cached_df = pd.read_csv(CACHE_FILE_PATH)
        except pd.errors.EmptyDataError:
            print(f"警告: キャッシュファイル {CACHE_FILE_PATH} は空です。")
            cached_df = pd.DataFrame()

    cached_ids = []
    if not cached_df.empty and 'id' in cached_df.columns:
        cached_ids = cached_df['id'].tolist()
    
    ids_to_fetch = list(set(track_ids) - set(cached_ids))

    # --- ステップ2: 【変更点】IDリストを10個ずつのチャンクに分割し、順次処理 ---
    newly_fetched_features = []
    if ids_to_fetch:
        print(f"INFO: キャッシュに {len(set(track_ids) & set(cached_ids))} 曲見つかりました。APIから {len(ids_to_fetch)} 曲を10曲ずつのバッチで取得します。")
        
        chunk_size = 10
        id_chunks = [ids_to_fetch[i:i + chunk_size] for i in range(0, len(ids_to_fetch), chunk_size)]
        
        for i, chunk in enumerate(id_chunks):
            print(f"--- チャンク {i+1}/{len(id_chunks)} ({len(chunk)}曲) の処理を開始... ---")
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_track_id = {executor.submit(get_soundstat_track_info, track_id): track_id for track_id in chunk}
                for future in as_completed(future_to_track_id):
                    try:
                        track_info = future.result()
                        if track_info:
                            newly_fetched_features.append(track_info)
                    except Exception as exc:
                        print(f'ERROR: {future_to_track_id[future]} の取得中に例外が発生しました: {exc}')
            # 各チャンクの間に短い待機時間を設けることで、APIサーバーへの負荷を軽減
            time.sleep(1) 
    else:
        print("INFO: 全ての曲がキャッシュにありました。APIリクエストは不要です。")

    # --- ステップ3: キャッシュと新しく取得したデータを結合し、更新 ---
    if newly_fetched_features:
        newly_fetched_df = pd.DataFrame(newly_fetched_features)
        all_raw_features_df = pd.concat([cached_df, newly_fetched_df], ignore_index=True).drop_duplicates(subset=['id'], keep='last')
        os.makedirs(os.path.dirname(CACHE_FILE_PATH), exist_ok=True)
        all_raw_features_df.to_csv(CACHE_FILE_PATH, index=False)
        print(f"INFO: キャッシュファイルを更新しました: {CACHE_FILE_PATH}")
    else:
        all_raw_features_df = cached_df

    df_raw = all_raw_features_df[all_raw_features_df['id'].isin(track_ids)]

    if df_raw.empty:
        print("有効な特徴量を取得できませんでした。")
        return pd.DataFrame()

    # --- ステップ4: 特徴量の選択と処理（変更なし） ---
    df_processed = pd.DataFrame()
    df_processed['id'] = df_raw['id']
    
    if 'features' in df_raw.columns:
        audio_features_df = pd.json_normalize(df_raw['features'].apply(lambda x: x if isinstance(x, dict) else {}))
    else:
        audio_features_df = pd.DataFrame()

    numerical_features_master_list = [
        'danceability', 'energy', 'loudness', 'speechiness', 'acousticness',
        'instrumentalness', 'liveness', 'valence', 'tempo'
    ]
    categorical_features_master_list = ['key', 'mode']
    
    for col in numerical_features_master_list + categorical_features_master_list:
        if col in audio_features_df.columns:
            df_processed[col] = audio_features_df[col].values

    df_processed.dropna(inplace=True)
    if df_processed.empty:
        print("必要な特徴量を含む有効なデータがありません。")
        return pd.DataFrame()

    existing_numerical_features = [col for col in numerical_features_master_list if col in df_processed.columns]
    existing_categorical_features = [col for col in categorical_features_master_list if col in df_processed.columns]
    
    if existing_numerical_features:
        scaler = MinMaxScaler()
        df_processed[existing_numerical_features] = scaler.fit_transform(df_processed[existing_numerical_features])

    if existing_categorical_features:
        encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False, dtype=int)
        encoded_cols = encoder.fit_transform(df_processed[existing_categorical_features])
        encoded_df = pd.DataFrame(encoded_cols, columns=encoder.get_feature_names_out(existing_categorical_features), index=df_processed.index)
        df_final = df_processed.drop(columns=existing_categorical_features).join(encoded_df)
    else:
        df_final = df_processed

    final_feature_columns = [
        'danceability', 'energy', 'loudness', 'speechiness', 'acousticness',
        'instrumentalness', 'liveness', 'valence', 'tempo',
        'key_0', 'key_1', 'key_2', 'key_3', 'key_4', 'key_5', 'key_6',
        'key_7', 'key_8', 'key_9', 'key_10', 'key_11', 'mode_0', 'mode_1'
    ]
    
    final_df_with_id = df_final.reindex(columns=['id'] + final_feature_columns, fill_value=0)
    
    print("特徴量処理が完了しました。")
    return final_df_with_id