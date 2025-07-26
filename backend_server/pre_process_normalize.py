import pandas as pd
import numpy as np
import requests
import os
import time
from urllib.parse import urlparse
import json
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder 
from sklearn.compose import ColumnTransformer 
import joblib 

def get_soundstat_track_info(spotify_track_id: str):
    """
    Soundstat APIを使用して、指定されたSpotifyトラックIDの楽曲情報を取得します。

    Args:
        spotify_track_id (str): SpotifyのトラックID。

    Returns:
        dict: APIから返された楽曲情報の辞書。エラーの場合はNoneを返します。
    """
    # 環境変数からAPIキーを取得
    api_key = os.getenv("SOUNDSTAT_API_KEY")
    if not api_key:
        print("エラー: 環境変数 'SOUNDSTAT_API_KEY' が設定されていません。")
        return None

    # Soundstat APIのエンドポイント
    api_url = f"https://soundstat.info/api/v1/track/{spotify_track_id}"
    
    # リクエストヘッダーにAPIキーを設定
    headers = {
        "X-API-Key": api_key
    }
    
    # クエリパラメータにトラックIDを設定
    params = {
        "id": spotify_track_id
    }

    print(f"'{spotify_track_id}' の情報を取得中...")

    try:
        # response = requests.get(api_url, headers=headers, params=params)
        response = requests.get(api_url, headers=headers)
        
        # リクエストが成功したかチェック
        response.raise_for_status()  # 200番台以外のステータスコードの場合に例外を発生させる

        # JSONレスポンスを辞書に変換して返す
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTPエラーが発生しました: {http_err}")
        print(f"レスポンス内容: {response.text}")
    except requests.exceptions.RequestException as req_err:
        print(f"リクエストエラーが発生しました: {req_err}")
    
    return None

# # --- 以下、実行例 ---
# if __name__ == "__main__":
#     # 情報を取得したいSpotifyのトラックIDを指定
#     # 例: 嵐 - 「HAPPINESS」
#     track_id_to_analyze = "0Ns63lt28epRgED3Tnhmth" 

#     # 関数を呼び出して楽曲情報を取得
#     track_info = get_soundstat_track_info(track_id_to_analyze)

#     # 結果を出力
#     if track_info:
#         print("\n✅ 楽曲情報の取得に成功しました。")
#         # 結果をきれいにフォーマットして表示
#         print(json.dumps(track_info, indent=2, ensure_ascii=False))
    

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


def preprocess_music_data(input_csv, output_csv):
    # データ読み込み
    df = pd.read_csv(input_csv)

    # 欠損値除去
    df = df.dropna()

    # 文字列カラムのトリム
    str_cols = df.select_dtypes(include='object').columns
    for col in str_cols:
        df[col] = df[col].str.strip()

    # 一旦、全カラムを残す
    features_list = []
    fail_list = []
    for idx, row in df.iterrows():
        url = row['URL']
        track_id = extract_track_id_from_url(url)
        if not track_id:
            features_list.append({})
            continue
        track_info = get_soundstat_track_info(track_id)
        print(track_info)
        
        if track_info is None:
            features_list.append({})
            print(f"track_id: {track_id} の情報が取得できませんでした。")
            continue
        
        try:
            # 必要なSpotify特徴量のみ抽出
            features = {
                'id': track_info['id'],
                'name': track_info['name'],
                'artists': track_info['artists'],
                'genre': track_info['genre'],
                'popularity': track_info['popularity'],
                'duration_ms': track_info['duration_ms'],

                # Audio features
                'tempo': track_info['features']['tempo'],
                'key': track_info['features']['key'],
                'mode': track_info['features']['mode'],
                'key_confidence': track_info['features']['key_confidence'],
                'energy': track_info['features']['energy'],
                'danceability': track_info['features']['danceability'],
                'valence': track_info['features']['valence'],
                'instrumentalness': track_info['features']['instrumentalness'],
                'acousticness': track_info['features']['acousticness'],
                'loudness': track_info['features']['loudness'],

                # Segments info
                'segments_count': track_info['features']['segments']['count'],
                'segments_avg_duration': track_info['features']['segments']['average_duration'],

                # Beats info
                'beats_count': track_info['features']['beats']['count'],
                'beats_regularity': track_info['features']['beats']['regularity'],
            }
            features_list.append(features)
            time.sleep(0.1)  # API制限対策
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            fail_list.append({track_id})
            continue
        
    features_df = pd.DataFrame(features_list)
    df = pd.concat([df.reset_index(drop=True), features_df], axis=1)

    # 保存先ディレクトリがなければ作成
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    # CSVとして保存
    df.to_csv(output_csv, index=False)
    print(f"前処理済みデータを {output_csv} に保存しました。行数: {len(df)}")
    print(f"失敗したトラックID: {fail_list}")
    print(f"失敗したトラックの数: {len(fail_list)}")

def normalize_and_encode_data(input_csv, output_csv_normalized):
    """
    指定されたCSVファイルの数値データを0-1に正規化し、カテゴリ特徴量をOne-Hotエンコードします。
    """
    df = pd.read_csv(input_csv)

    # 数値データとカテゴリデータの識別
    # 'key' と 'mode' は数値ですが、カテゴリとして扱うことが多いです。
    # 必要に応じてこのリストを調整してください。
    numerical_features = [
        'popularity', 'duration_ms', 'tempo', 'key_confidence', 'energy',
        'danceability', 'valence', 'instrumentalness', 'acousticness',
        'loudness', 'segments_count', 'segments_avg_duration',
        'beats_count', 'beats_regularity'
    ]
    # 'key' は音階（0-11）であり、数値ですが、カテゴリとして扱う方が適切です。
    # 'mode' は長調/短調（0または1）であり、カテゴリとして扱います。
    categorical_features = ['genre', 'key'] 

    # DataFrameに実際に存在する列のみを対象とする
    numerical_features = [col for col in numerical_features if col in df.columns]
    categorical_features = [col for col in categorical_features if col in df.columns]

    # Min-Max Scaling
    if numerical_features:
        scaler = MinMaxScaler()
        df[numerical_features] = scaler.fit_transform(df[numerical_features])
        print(f"数値特徴量を0-1に正規化しました: {numerical_features}")
    else:
        print("0-1正規化する数値特徴量が見つかりませんでした。")

    
    if categorical_features:
        encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
        encoded_features = encoder.fit_transform(df[categorical_features])
        # 新しいOne-Hotエンコードされた列名を取得
        encoded_df = pd.DataFrame(encoded_features, columns=encoder.get_feature_names_out(categorical_features))
        
        # 元のカテゴリ特徴量列を削除し、エンコードされた特徴量を結合
        df = pd.concat([df.drop(columns=categorical_features), encoded_df], axis=1)
        print(f"カテゴリ特徴量をOne-Hotエンコードしました: {categorical_features}")
    else:
        print("One-Hotエンコードするカテゴリ特徴量が見つかりませんでした。")

    # 処理後のデータを保存
    os.makedirs(os.path.dirname(output_csv_normalized), exist_ok=True)
    df.to_csv(output_csv_normalized, index=False)
    print(f"正規化およびエンコードされたデータを {output_csv_normalized} に保存しました。")

def normalize_and_encode_dataframe(df):
    """
    DataFrameの数値データを0-1に正規化し、カテゴリ特徴量をOne-Hotエンコードします。
    CSVを介さずに直接DataFrameを処理します。
    """
    if df.empty:
        print("入力DataFrameが空です。")
        return df

    # 数値データとカテゴリデータの識別
    numerical_features = [
        'popularity', 'duration_ms', 'tempo', 'key_confidence', 'energy',
        'danceability', 'valence', 'instrumentalness', 'acousticness',
        'loudness', 'segments_count', 'segments_avg_duration',
        'beats_count', 'beats_regularity'
    ]
    categorical_features = ['key']  # modeとgenreを除外

    # DataFrameに実際に存在する列のみを対象とする
    numerical_features = [col for col in numerical_features if col in df.columns]
    categorical_features = [col for col in categorical_features if col in df.columns]

    # Min-Max Scaling
    if numerical_features:
        scaler = MinMaxScaler()
        df[numerical_features] = scaler.fit_transform(df[numerical_features])
        print(f"数値特徴量を0-1に正規化しました: {numerical_features}")
    else:
        print("0-1正規化する数値特徴量が見つかりませんでした。")

    # One-Hot Encoding
    if categorical_features:
        encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
        encoded_features = encoder.fit_transform(df[categorical_features])
        # 新しいOne-Hotエンコードされた列名を取得
        encoded_df = pd.DataFrame(encoded_features, columns=encoder.get_feature_names_out(categorical_features))
        
        # key列を0.0〜11.0で固定（プレイリストに含まれるkeyに関係なく12個の列を生成）
        if 'key' in categorical_features:
            # 全てのkey列（key_0.0〜key_11.0）を生成
            all_key_columns = [f'key_{i}.0' for i in range(12)]
            
            # 現在のDataFrameに存在するkey列を取得
            existing_key_columns = [col for col in encoded_df.columns if col.startswith('key_')]
            
            # 存在しないkey列を0で埋めて追加
            for key_col in all_key_columns:
                if key_col not in existing_key_columns:
                    encoded_df[key_col] = 0
            
            # 列の順序を統一（key_0.0〜key_11.0の順）
            key_columns_ordered = [f'key_{i}.0' for i in range(12)]
            other_columns = [col for col in encoded_df.columns if not col.startswith('key_')]
            encoded_df = encoded_df[key_columns_ordered + other_columns]
        
        # 元のカテゴリ特徴量列を削除し、エンコードされた特徴量を結合
        df = pd.concat([df.drop(columns=categorical_features), encoded_df], axis=1)
        print(f"カテゴリ特徴量をOne-Hotエンコードしました: {categorical_features}")
    else:
        print("One-Hotエンコードするカテゴリ特徴量が見つかりませんでした。")
    print(df.columns)
    return df

def process_tracks_directly(track_ids: list) -> pd.DataFrame:
    """
    トラックIDのリストを受け取り、SoundStat APIから特徴量を取得し、
    pre_process_normalize.pyと同じ前処理を行ってDataFrameを返します。
    CSVを介さずに直接処理します。
    """
    if not track_ids:
        return pd.DataFrame()

    features_list = []
    fail_list = []
    
    for idx, track_id in enumerate(track_ids):
        print(f"処理中: {idx+1}/{len(track_ids)} - {track_id}")
        
        track_info = get_soundstat_track_info(track_id)
        
        if track_info is None:
            fail_list.append(track_id)
            print(f"track_id: {track_id} の情報が取得できませんでした。")
            continue
        
        try:
            # pre_process_normalize.pyと同じ特徴量抽出（modeとgenreを除外）
            features = {
                'id': track_info['id'],
                'name': track_info['name'],
                'artists': track_info['artists'],
                'popularity': track_info['popularity'],
                'duration_ms': track_info['duration_ms'],

                # Audio features（modeを除外）
                'tempo': track_info['features']['tempo'],
                'key': track_info['features']['key'],
                'key_confidence': track_info['features']['key_confidence'],
                'energy': track_info['features']['energy'],
                'danceability': track_info['features']['danceability'],
                'valence': track_info['features']['valence'],
                'instrumentalness': track_info['features']['instrumentalness'],
                'acousticness': track_info['features']['acousticness'],
                'loudness': track_info['features']['loudness'],

                # Segments info
                'segments_count': track_info['features']['segments']['count'],
                'segments_avg_duration': track_info['features']['segments']['average_duration'],

                # Beats info
                'beats_count': track_info['features']['beats']['count'],
                'beats_regularity': track_info['features']['beats']['regularity'],
            }
            features_list.append(features)
            time.sleep(0.1)  # API制限対策
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            fail_list.append(track_id)
            continue
    
    if not features_list:
        print("有効な特徴量を取得できませんでした。")
        return pd.DataFrame()
    
    # DataFrameに変換
    df = pd.DataFrame(features_list)
    
    # 欠損値除去
    df = df.dropna()
    
    if df.empty:
        print("欠損値除去後、有効なデータが残りませんでした。")
        return pd.DataFrame()
    
    # 正規化とエンコード
    df = normalize_and_encode_dataframe(df)
    
    print(f"前処理完了: {len(df)} 曲の特徴量を処理しました。")
    print(f"失敗したトラックID: {fail_list}")
    print(f"失敗したトラックの数: {len(fail_list)}")
    
    return df

if __name__ == "__main__":
    # preprocess_music_data(
    #     input_csv="data/melosync_music_data.csv",
    #     output_csv="data/processed_music_data.csv"
    # )
    
    # csvファイルのヘッダー並び替えたい
    # 担当者,アーティスト,曲名（optional）,URL,Happy/Excited,Angry/Frustrated,Tired/Sad,Relax/Chill,ジャンル,id,name,artists,genre,popularity,duration_ms,tempo,key,mode,key_confidence,energy,danceability,valence,instrumentalness,acousticness,loudness,segments_count,segments_avg_duration,beats_count,beats_regularity
    # →担当者,アーティスト,曲名（optional）,URL,id,name,artists,genre,popularity,duration_ms,tempo,key,mode,key_confidence,energy,danceability,valence,instrumentalness,acousticness,loudness,segments_count,segments_avg_duration,beats_count,beats_regularity,Happy/Excited,Angry/Frustrated,Tired/Sad,Relax/Chill,ジャンル
    
    # ヘッダー並び替え
    df = pd.read_csv("data/processed_music_data.csv")
    df = df[['担当者', 'アーティスト', '曲名（optional）', 'URL', 'id', 'name', 'artists', 'genre', 'popularity', 'duration_ms', 'tempo', 'key', 'mode', 'key_confidence', 'energy', 'danceability', 'valence', 'instrumentalness', 'acousticness', 'loudness', 'segments_count', 'segments_avg_duration', 'beats_count', 'beats_regularity', 'Happy/Excited', 'Angry/Frustrated', 'Tired/Sad', 'Relax/Chill', 'ジャンル']]
    df.to_csv("data/processed_music_data.csv", index=False)

    
    print("\n--- データ正規化とOne-Hotエンコードを開始します ---")
    normalize_and_encode_data(
        input_csv="data/processed_music_data.csv",
        output_csv_normalized="data/music_data_normalized_encoded.csv" 
    )
    print("--- データ正規化とOne-Hotエンコードが完了しました ---")
    
    
    if os.path.exists("data/music_data_normalized_encoded.csv"):
        df_encoded = pd.read_csv("data/music_data_normalized_encoded.csv")

        emotion_columns = ['Happy/Excited', 'Angry/Frustrated', 'Tired/Sad', 'Relax/Chill']
        
       
        all_feature_columns = [col for col in df_encoded.columns if col not in emotion_columns]

      
        df_encoded[all_feature_columns + ['Happy/Excited']].to_csv("data/music_data_happy_normalized_encoded.csv", index=False)
        print("data/music_data_happy.csv を保存しました。")

        df_encoded[all_feature_columns + ['Angry/Frustrated']].to_csv("data/music_data_angry_normalized_encoded.csv", index=False)
        print("data/music_data_angry.csv を保存しました。")

        df_encoded[all_feature_columns + ['Tired/Sad']].to_csv("data/music_data_tired_normalized_encoded.csv", index=False)
        print("data/music_data_tired.csv を保存しました。")

        df_encoded[all_feature_columns + ['Relax/Chill']].to_csv("data/music_data_relax_normalized_encoded.csv", index=False)
        print("data/music_data_relax.csv を保存しました。")
    else:
        print("data/music_data_normalized_encoded.csv が見つかりません。正規化とエンコードのステップが完了していることを確認してください。")
