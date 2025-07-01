# -*- coding: utf-8 -*-
import pandas as pd
from spotify_api import fetch_audio_features
from feature_engineering import standardize_features, one_hot_encode
from label_processing import build_transition_matrix
from model import build_model
from recommend import recommend_songs

# === 1. 元データの読み込み ===
df = pd.read_csv('data/melosync_music_data.csv')

# === 2. Spotifyからオーディオ特徴量を取得 ===
CLIENT_ID = 'あなたのclient_id'
CLIENT_SECRET = 'あなたのclient_secret'
audio_features_df = fetch_audio_features(df, CLIENT_ID, CLIENT_SECRET, url_col='spotify_url')

# === 3. 特徴量のマージと前処理 ===
# モデルで使用する特徴量を選択
selected_features = ['id', 'danceability', 'energy', 'key', 'loudness', 'mode',
                     'speechiness', 'acousticness', 'instrumentalness', 'liveness',
                     'valence', 'tempo', 'duration_ms']
audio_features_df = audio_features_df[selected_features]
audio_features_df = audio_features_df.rename(columns={'id': 'track_id'}) # IDの列名を統一
# 元データとオーディオ特徴量をマージ
df_merged = pd.merge(df, audio_features_df, on='track_id', how='left')
df_merged.dropna(subset=selected_features[1:], inplace=True) # 特徴量が欠損している曲は削除

# === 4. ラベルデータ（4x4の遷移確率行列）の作成 ===
mood_map = {'Angry': 0, 'Happy': 1, 'Relaxed': 2, 'Sad': 3}
final_labels_df = build_transition_matrix(df_merged, mood_map)
# 特徴量とラベルデータを結合して最終的なデータセットを作成
df_final = pd.merge(audio_features_df, final_labels_df, on='track_id', how='inner')
df_final.fillna(0, inplace=True) # 欠損値を0で埋める

# === 5. 特徴量エンジニアリング ===
# 数値特徴量とカテゴリカル特徴量を定義
feature_cols_numeric = [col for col in selected_features if col not in ['id', 'track_id', 'key', 'mode']]
# 数値特徴量を標準化
df_final, scaler = standardize_features(df_final, feature_cols_numeric)
# カテゴリカル特徴量をワンホットエンコーディング
df_final = one_hot_encode(df_final, ['key', 'mode'])
# モデルの入力(X)と出力(Y)の列を定義
feature_cols = [col for col in df_final.columns if col not in ['track_id'] and not col.startswith('start_')]
output_cols = [col for col in df_final.columns if col.startswith('start_')]

# === 6. データセットの分割 ===
from sklearn.model_selection import train_test_split
X = df_final[feature_cols] # 説明変数（曲の特徴量）
Y = df_final[output_cols] # 目的変数（4x4の遷移確率）
# 訓練データとテストデータに8:2で分割
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

# === 7. モデルの構築と学習 ===
# モデルを構築
model = build_model(X_train.shape[1])
num_start_moods = 4
num_end_moods = 4
# Kerasの多出力モデルの入力形式に合わせて、Yを4つの出力層に対応するリストに分割
Y_train_split = [Y_train[[f'start_{i}_end_{j}' for j in range(num_end_moods)]].values for i in range(num_start_moods)]
Y_test_split = [Y_test[[f'start_{i}_end_{j}' for j in range(num_end_moods)]].values for i in range(num_start_moods)]
# モデルの学習を実行
model.fit(X_train, Y_train_split, epochs=50, batch_size=32, validation_data=(X_test, Y_test_split), verbose=1)

# === 8. 推薦の実行例 ===
# テストデータを使って推薦を試す
track_ids_test = X_test.index.map(lambda i: df_final.loc[i, 'track_id']) # テストデータのtrack_idを取得
start_mood_code = 0  # 例：ユーザーの現在の感情が「怒り(Angry)」
target_mood_code = 1 # 例：ユーザーの目標感情が「幸せ(Happy)」
# 推薦リストを取得
recommend_list = recommend_songs(model, X_test, track_ids_test, start_mood_code, target_mood_code, top_k=10)
print("推薦結果：", recommend_list)