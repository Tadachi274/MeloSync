import pandas as pd
import numpy as np
import requests
import time
import json
from urllib.parse import urlparse, parse_qs
import os
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

class SpotifyFeatureExtractor:
    def __init__(self, client_id: str, client_secret: str):
        """
        Spotify APIを使用して曲の特徴量を取得するクラス
        
        Args:
            client_id: Spotify APIのクライアントID
            client_secret: Spotify APIのクライアントシークレット
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://api.spotify.com/v1"
        
    def get_access_token(self) -> str:
        """Spotify APIのアクセストークンを取得"""
        auth_url = "https://accounts.spotify.com/api/token"
        
        auth_response = requests.post(auth_url, {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        })
        
        if auth_response.status_code == 200:
            auth_response_data = auth_response.json()
            self.access_token = auth_response_data['access_token']
            return self.access_token
        else:
            raise Exception(f"認証エラー: {auth_response.status_code}")
    
    def extract_track_id_from_url(self, url: str) -> Optional[str]:
        """Spotify URLからトラックIDを抽出"""
        try:
            parsed_url = urlparse(url)
            if 'track' in parsed_url.path:
                # URLパスからトラックIDを抽出
                path_parts = parsed_url.path.split('/')
                track_index = path_parts.index('track')
                if track_index + 1 < len(path_parts):
                    track_id = path_parts[track_index + 1]
                    # クエリパラメータを除去
                    if '?' in track_id:
                        track_id = track_id.split('?')[0]
                    return track_id
            return None
        except Exception as e:
            print(f"URL解析エラー: {url}, エラー: {e}")
            return None
    
    def get_track_info(self, track_id: str) -> Optional[Dict]:
        """トラックの基本情報を取得"""
        if not self.access_token:
            self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        url = f"{self.base_url}/tracks/{track_id}"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"トラック情報取得エラー: {response.status_code}")
                return None
        except Exception as e:
            print(f"トラック情報取得エラー: {e}")
            return None
    
    def get_audio_features(self, track_id: str) -> Optional[Dict]:
        """トラックの音声特徴量を取得"""
        if not self.access_token:
            self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        url = f"{self.base_url}/audio-features/{track_id}"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"音声特徴量取得エラー: {response.status_code}")
                return None
        except Exception as e:
            print(f"音声特徴量取得エラー: {e}")
            return None
    
    def get_audio_analysis(self, track_id: str) -> Optional[Dict]:
        """トラックの詳細音声分析を取得"""
        if not self.access_token:
            self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        url = f"{self.base_url}/audio-analysis/{track_id}"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"音声分析取得エラー: {response.status_code}")
                return None
        except Exception as e:
            print(f"音声分析取得エラー: {e}")
            return None
    
    def extract_all_features(self, track_id: str) -> Optional[Dict]:
        """トラックの全ての特徴量を取得"""
        print(f"トラックID {track_id} の特徴量を取得中...")
        
        # 基本情報を取得
        track_info = self.get_track_info(track_id)
        if not track_info:
            return None
        
        # 音声特徴量を取得
        audio_features = self.get_audio_features(track_id)
        if not audio_features:
            return None
        
        # 音声分析を取得
        audio_analysis = self.get_audio_analysis(track_id)
        
        # 特徴量を統合
        features = {
            # 基本情報
            'track_name': track_info.get('name', ''),
            'artist_name': track_info.get('artists', [{}])[0].get('name', ''),
            'album_name': track_info.get('album', {}).get('name', ''),
            'popularity': track_info.get('popularity', 0),
            'duration_ms': track_info.get('duration_ms', 0),
            'explicit': int(track_info.get('explicit', False)),
            
            # 音声特徴量
            'danceability': audio_features.get('danceability', 0),
            'energy': audio_features.get('energy', 0),
            'key': audio_features.get('key', 0),
            'loudness': audio_features.get('loudness', 0),
            'mode': audio_features.get('mode', 0),
            'speechiness': audio_features.get('speechiness', 0),
            'acousticness': audio_features.get('acousticness', 0),
            'instrumentalness': audio_features.get('instrumentalness', 0),
            'liveness': audio_features.get('liveness', 0),
            'valence': audio_features.get('valence', 0),
            'tempo': audio_features.get('tempo', 0),
            'time_signature': audio_features.get('time_signature', 0),
            
            # 音声分析から追加特徴量
            'num_segments': len(audio_analysis.get('segments', [])) if audio_analysis else 0,
            'num_sections': len(audio_analysis.get('sections', [])) if audio_analysis else 0,
        }
        
        # 音声分析から統計量を計算
        if audio_analysis and 'segments' in audio_analysis:
            segments = audio_analysis['segments']
            if segments:
                # セグメントの統計量
                pitches = [seg.get('pitches', [0]*12) for seg in segments]
                timbres = [seg.get('timbre', [0]*12) for seg in segments]
                
                if pitches:
                    # ピッチの統計量
                    pitch_means = np.mean(pitches, axis=0)
                    pitch_stds = np.std(pitches, axis=0)
                    features.update({
                        f'pitch_mean_{i}': pitch_means[i] for i in range(12)
                    })
                    features.update({
                        f'pitch_std_{i}': pitch_stds[i] for i in range(12)
                    })
                
                if timbres:
                    # ティムブレの統計量
                    timbre_means = np.mean(timbres, axis=0)
                    timbre_stds = np.std(timbres, axis=0)
                    features.update({
                        f'timbre_mean_{i}': timbre_means[i] for i in range(12)
                    })
                    features.update({
                        f'timbre_std_{i}': timbre_stds[i] for i in range(12)
                    })
        
        return features
    
    def process_csv_data(self, csv_file: str, output_file: str = None) -> pd.DataFrame:
        """CSVファイルのデータを処理してSpotify特徴量を追加"""
        print("CSVファイルを読み込み中...")
        df = pd.read_csv(csv_file)
        
        # 結果を格納するリスト
        all_features = []
        failed_tracks = []
        
        for index, row in df.iterrows():
            url = row['URL']
            track_id = self.extract_track_id_from_url(url)
            
            if track_id:
                features = self.extract_all_features(track_id)
                if features:
                    # 元のデータと結合
                    combined_data = {**row.to_dict(), **features}
                    all_features.append(combined_data)
                    print(f"成功: {row['アーティスト']} - {row['曲名（optional）']}")
                else:
                    failed_tracks.append({
                        'index': index,
                        'artist': row['アーティスト'],
                        'song': row['曲名（optional）'],
                        'url': url
                    })
                    print(f"失敗: {row['アーティスト']} - {row['曲名（optional）']}")
            else:
                failed_tracks.append({
                    'index': index,
                    'artist': row['アーティスト'],
                    'song': row['曲名（optional）'],
                    'url': url
                })
                print(f"URL解析失敗: {row['アーティスト']} - {row['曲名（optional）']}")
            
            # API制限を避けるため少し待機
            time.sleep(0.1)
        
        # 結果をDataFrameに変換
        result_df = pd.DataFrame(all_features)
        
        # 失敗したトラックの情報を保存
        if failed_tracks:
            failed_df = pd.DataFrame(failed_tracks)
            failed_df.to_csv('failed_tracks.csv', index=False)
            print(f"\n失敗したトラック数: {len(failed_tracks)}")
            print("詳細は failed_tracks.csv を確認してください")
        
        # 結果を保存
        if output_file:
            result_df.to_csv(output_file, index=False)
            print(f"\n結果を {output_file} に保存しました")
        
        print(f"\n成功したトラック数: {len(result_df)}")
        return result_df
    
    def get_feature_descriptions(self) -> Dict[str, str]:
        """Spotify特徴量の説明を取得"""
        return {
            'danceability': 'ダンス性（0-1）: 曲がダンスに適しているかどうか',
            'energy': 'エネルギー（0-1）: 曲の強度と活動性',
            'key': '調（0-11）: 曲の調性（C=0, C#=1, ..., B=11）',
            'loudness': '音量（dB）: 曲の全体的な音量',
            'mode': '調性（0-1）: 0=短調, 1=長調',
            'speechiness': '話声性（0-1）: 話声の存在度',
            'acousticness': 'アコースティック性（0-1）: アコースティック楽器の使用度',
            'instrumentalness': '器楽性（0-1）: 歌詞の有無',
            'liveness': 'ライブ性（0-1）: ライブ録音の可能性',
            'valence': '明るさ（0-1）: 曲のポジティブな感情',
            'tempo': 'テンポ（BPM）: 曲の速度',
            'time_signature': '拍子記号: 拍子の数',
            'popularity': '人気度（0-100）: Spotifyでの人気度',
            'duration_ms': '長さ（ミリ秒）: 曲の長さ',
            'explicit': '露骨な内容（0-1）: 露骨な歌詞の有無'
        }

def main():
    """メイン実行関数"""
    # Spotify API認証情報を環境変数から取得
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("エラー: Spotify API認証情報が設定されていません")
        print("以下の環境変数を設定してください:")
        print("export SPOTIFY_CLIENT_ID='your_client_id'")
        print("export SPOTIFY_CLIENT_SECRET='your_client_secret'")
        return
    
    # 特徴量抽出器を初期化
    extractor = SpotifyFeatureExtractor(client_id, client_secret)
    
    # CSVファイルを処理
    result_df = extractor.process_csv_data(
        'melosync_music_data.csv',
        'melosync_music_data_with_spotify_features.csv'
    )
    
    # 特徴量の説明を表示
    print("\n=== Spotify特徴量の説明 ===")
    descriptions = extractor.get_feature_descriptions()
    for feature, description in descriptions.items():
        if feature in result_df.columns:
            print(f"{feature}: {description}")
    
    # 基本統計を表示
    print(f"\n=== 基本統計 ===")
    print(f"データ形状: {result_df.shape}")
    print(f"Spotify特徴量の数: {len([col for col in result_df.columns if col in descriptions])}")

if __name__ == "__main__":
    main() 