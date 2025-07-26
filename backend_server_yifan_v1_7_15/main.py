import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import lightgbm as lgb
import joblib
# 修正したモジュールをインポート
from spotify_api import fetch_audio_features
from feature_engineering import standardize_features, one_hot_encode
from recommend import recommend_songs_for_target

# --- 4. 推薦の実行例 ---
print("\nステップ 4/5: 推薦の実行例...")

# this params will be input from user.
# ユーザーの現在の感情が 'Angry'（怒り）で、目標が 'Happy'（幸せ）であると仮定
user_start_mood_name = 'Angry/Frustrated'
user_target_mood_name = 'Happy/Excited'


target_mood_code = mood_map[user_target_mood_name]

# 3.1 対応するモデルを選択
model_to_use = trained_models.get(user_start_mood_name)

if model_to_use:
    # 3.2 推薦に使用する全楽曲データを準備（同様の特徴量エンジニアリングが必要）
    all_songs_featured = audio_features_df_selected.copy()
    scaler_to_use = all_scalers[user_start_mood_name] # 対応するモデルの訓練時に使用したscalerを利用
    
    numeric_cols = [col for col in selected_feature_cols if col not in ['key', 'mode']]
    all_songs_featured[numeric_cols] = scaler_to_use.transform(all_songs_featured[numeric_cols])
    all_songs_featured = one_hot_encode(all_songs_featured, ['key', 'mode'])
    
    # 訓練時と列の順序が一致するように保証
    training_cols = X_train.columns # 最後に訓練されたモデルの列順を基準とする
    all_songs_X = all_songs_featured.drop(columns=['track_id']).reindex(columns=training_cols, fill_value=0)

    # 3.3 推薦を生成
    recommend_list = recommend_songs_for_target(
        model_to_use, 
        all_songs_X, 
        all_songs_featured['track_id'].values, 
        target_mood_code, 
        top_k=10
    )
    print(f"\n'{user_start_mood_name}' から '{user_target_mood_name}' へのTop 10推薦楽曲:")
    print(recommend_list)
else:
    print(f"'{user_start_mood_name}' のための訓練済みモデルが見つかりませんでした。")

print("\nステップ 5/5: 全ての処理が完了しました。")
