# evaluate_models_jp.py

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# --- 1. モデルとデータのマッピングを定義 ---
mood_map = {
    'Angry/Frustrated': ('data/music_data_angry_normalized_encoded.csv', 'Angry/Frustrated'),
    'Happy/Excited': ('data/music_data_happy_normalized_encoded.csv', 'Happy/Excited'),
    'Relax/Chill': ('data/music_data_relax_normalized_encoded.csv', 'Relax/Chill'),
    'Tired/Sad': ('data/music_data_tired_normalized_encoded.csv', 'Tired/Sad')
}

print("--- テストセットで各モデルの評価を開始します ---")

# --- 2. 各モデルをループで読み込み、評価を実行 ---
for mood_name, (csv_path, label_column) in mood_map.items():
    print(f"\n--- モデルの評価中: {mood_name} ---")
    
    # モデルをロード
    model_filename = f"model_{mood_name.replace('/', '-')}.joblib"
    model = joblib.load(model_filename)

    # データをロード
    df = pd.read_csv(csv_path)
    df.dropna(subset=[label_column], inplace=True)

    # 特徴量とラベルを定義
    non_feature_cols = ['担当者', 'アーティスト', '曲名（optional）', 'URL', 'id', 'name', 'artists', 'genre', 'ジャンル', label_column]
    cols_to_drop = [col for col in non_feature_cols if col in df.columns]
    X = df.drop(columns=cols_to_drop)
    Y = df[label_column]

    # 訓練時と完全に同じパラメータでデータを分割し、同一の「テスト問題」を取得する
    _, X_test, _, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42, stratify=Y)
    
    # テストデータで予測を実行
    Y_pred = model.predict(X_test)
    
    # 評価指標を計算して表示
    accuracy = accuracy_score(Y_test, Y_pred)
    print(f"\n✅ 正解率 (Accuracy): {accuracy:.2%}")
    
    print("\n📊 分類レポート (Classification Report):")
    print(classification_report(Y_test, Y_pred))

    print("\n🤔 混同行列 (Confusion Matrix):")
    print(confusion_matrix(Y_test, Y_pred))

print("\n--- 全てのモデルの評価が完了しました！ ---")