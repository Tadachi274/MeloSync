# predict the probability of mood transition from start_mood to end_mood
# input: start_mood, end_mood
# output: probability of mood transition for each mood

# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import lightgbm as lgb
import joblib
# 修正したモジュールをインポート
from spotify_api import fetch_audio_features
from feature_engineering import standardize_features, one_hot_encode
from recommend import recommend_songs_for_target

# --- 1. データ読み込みとフォーマット変換 ---
print("ステップ 1/5: ワイド形式のデータを読み込み、ロング形式へ変換...")
df_wide = pd.read_csv('data/melosync_music_data.csv')
# df_wide = pd.read_csv('data/processed_music_data.csv')

# 感情の列名を指定
mood_columns = ['Angry/Frustrated', 'Happy/Excited', 'Relax/Chill', 'Tired/Sad']

# pd.melt()でワイド形式からロング形式へ変換
df_long = pd.melt(df_wide,
                  id_vars=['spotify_url'],
                  value_vars=mood_columns,
                  var_name='start_mood',
                  value_name='end_mood')

# 変換によって生じたNaN（空白）の行を削除
df_long.dropna(subset=['end_mood'], inplace=True)

# 変換後のdf_longを元のdf_rawとして使用
df_raw = df_long

# --- 2. Spotifyからオーディオ特徴量を取得 ---
print("ステップ 2/5: Spotifyの特徴量を取得...")
# 以降の処理は、変換後のデータを使用
audio_features_df = fetch_audio_features(df_raw, CLIENT_ID, CLIENT_SECRET, url_col='spotify_url')
# 元のユーザー遷移データと楽曲の特徴量をマージ
selected_feature_cols = [
    'danceability', 'energy', 'loudness', 'speechiness', 'acousticness',
    'instrumentalness', 'liveness', 'valence', 'tempo', 'key', 'mode'
]

audio_features_df_selected = audio_features_df[selected_feature_cols + ['track_id']]

df_merged = pd.merge(df_raw, audio_features_df_selected, on='track_id', how='inner')
df_merged.dropna(subset=selected_feature_cols, inplace=True)

mood_map = {'Angry/Frustrated': 0, 'Happy/Excited': 1, 'Relax/Chill': 2, 'Tired/Sad': 3}
df_merged['start_mood_encoded'] = df_merged['start_mood'].map(mood_map)
df_merged['end_mood_encoded'] = df_merged['end_mood'].map(mood_map)

# --- 3. 各開始感情に対し、独立したモデルを訓練 ---
print("\nステップ 3/5: 4つの感情それぞれに対し、モデルの訓練を開始...")
trained_models = {}
all_scalers = {}

for mood_name, start_mood_code in mood_map.items():
    print(f"\n--- 開始感情: {mood_name} (コード: {start_mood_code}) の処理中 ---")

    # 3.1. 現在の「開始感情」に対応するデータをdf_mergedから直接抽出します。
    model_data_df = df_merged[df_merged['start_mood_encoded'] == start_mood_code].copy()
    
    # 抽出したデータが空の場合、この感情の訓練をスキップします。
    if model_data_df.empty:
        print(f"感情 {mood_name} には十分な遷移データがないため、スキップします。")
        continue

    # 3.2. 抽出したデータに対して特徴量エンジニアリング（One-Hotエンコーディングのみ）を適用します。
    #    LightGBMを使用するため、標準化のステップは省略されています。
    model_data_df = one_hot_encode(model_data_df, ['key', 'mode'])
    

    # 3.4 データセットの分割
    feature_cols = [col for col in model_data_df.columns if col not in ['track_id', 'target_mood']]
    X = model_data_df[feature_cols]
    Y = model_data_df['target_mood']
    
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42, stratify=Y)

    # 3.5 モデルの構築と訓練
    print(f"{mood_name} LightGBM モデルの訓練準備...")
    # 初始化 LightGBM 分類器
    lgbm = lgb.LGBMClassifier(objective='multiclass', num_class=len(mood_map), random_state=42)
    
    lgbm.fit(X_train, Y_train,
             eval_set=[(X_test, Y_test)],
             eval_metric='multi_logloss')
             
    print(f"{mood_name} モデルの訓練が完了しました。")

    # 2.6 モデルの保存と格納
    model_path = f"model_{mood_name.replace('/', '-')}.joblib"
    joblib.dump(lgbm, model_path) 
    trained_models[mood_name] = lgbm
    print(f"モデルを {model_path} に保存しました。")
