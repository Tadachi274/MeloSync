import pandas as pd
import numpy as np
import requests
import os
import time
from urllib.parse import urlparse
import json

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

if __name__ == "__main__":
    preprocess_music_data(
        input_csv="data/melosync_music_data.csv",
        output_csv="data/processed_music_data2.csv"
    )