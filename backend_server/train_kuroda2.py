import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
import lightgbm as lgb

# --- 1. 基本設定 ---

# 各感情とCSVファイルのパスをマッピングした辞書
dataset_files = {
    'Happy/Excited': 'data/music_data_happy_normalized_encoded.csv',
    'Angry/Frustrated': 'data/music_data_angry_normalized_encoded.csv',
    'Tired/Sad': 'data/music_data_tired_normalized_encoded.csv',
    'Relax/Chill': 'data/music_data_relax_normalized_encoded.csv'
}

# --- ★ 1. モデルの評価結果を保存するリストを初期化 ---
results_summary = []


# # 処理対象の担当者リスト
# name_list_jp = ["Chen", "大林", "黒田", "渡邊", "忠地", "Yifan"]
# name_list_en = ["chen", "obayashi", "kuroda", "watanabe", "tadachi", "yifan"]

# # 全担当者の評価結果を保存するリストを初期化
# overall_results_summary = []

# # --- 2. 担当者ごとにループ処理 ---
# for name_jp, name_en in zip(name_list_jp, name_list_en):
#     print(f"=================================================")
#     print(f"処理中の担当者: {name_jp}")
#     print(f"=================================================")

# --- 2.1. データ読み込みと結合 ---
all_data_frames = []
for emotion, file_path in dataset_files.items():
    # モデル名を抽出
    base_name = os.path.basename(file_path)
    model_name = base_name.replace('music_data_', '').replace('_normalized_encoded.csv', '')
    df = pd.read_csv(file_path)
    df = df.iloc[:, 7:]
    df = df.drop(columns=['mode_0.0', 'mode_1.0'])
    df = df.drop(columns=['ジャンル'])
    
    # --- 2.2. Valence-Arousal ラベルの作成 ---
    # Valence: 1 (快: Happy, Relax), 0 (不快: Angry, Tired)
    df['Valence'] = df[emotion].apply(
        lambda x: 1 if x in ['Happy/Excited', 'Relax/Chill'] else 0
    )
    
    # Arousal: 1 (覚醒: Happy, Angry), 0 (鎮静: Tired, Relax)
    df['Arousal'] = df[emotion].apply(
        lambda x: 1 if x in ['Happy/Excited', 'Angry/Frustrated'] else 0
    )

    # --- 2.3. 特徴量と正解ラベルの分割 ---
    # 特徴量X: 最初の7列と、モデルで使用しないラベル関連の列を除外
    X = df.drop(columns=df.columns[[-1, -2, -3]], axis=1)
    print(df.head())
    # 目的変数y
    y_valence = df['Valence']
    y_arousal = df['Arousal']
    y_emotion_true = df[emotion] # 最終評価用の真の感情ラベル

    # --- 2.4. データの前処理と分割 ---
    X_train, X_test, y_valence_train, y_valence_test, y_arousal_train, y_arousal_test, _, y_emotion_true_test = train_test_split(X, y_valence, y_arousal, y_emotion_true, test_size=0.2, random_state=42, stratify=y_emotion_true)


    # 欠損値の補完 (中央値で補完)
    imputer = SimpleImputer(strategy='median')
    X_train = imputer.fit_transform(X_train)
    X_test = imputer.transform(X_test)
    
    print(f"データ準備完了: トレインデータ {X_train.shape[0]}件, テストデータ {X_test.shape[0]}件")

    # --- 2.5. 2つのモデルの学習 ---
    
    # モデルを選択 (ロジスティック回帰、ランダムフォレスト、LightGBMから1つ選んでください)
    # model_valence = LogisticRegression(random_state=42, max_iter=1000)
    # model_arousal = LogisticRegression(random_state=42, max_iter=1000)
    
    model_valence = RandomForestClassifier(random_state=42)
    model_arousal = RandomForestClassifier(random_state=42)
    
    # model_valence = lgb.LGBMClassifier(random_state=42)
    # model_arousal = lgb.LGBMClassifier(random_state=42)

    # Valenceモデルの学習
    model_valence.fit(X_train, y_valence_train)
    print("Valenceモデルの学習が完了しました。")

    # Arousalモデルの学習
    model_arousal.fit(X_train, y_arousal_train)
    print("Arousalモデルの学習が完了しました。")

    # 学習済みモデルの保存
    os.makedirs('model', exist_ok=True) # 保存用ディレクトリ作成
    joblib.dump(model_valence, f'model/model_{model_name}_valence.joblib')
    joblib.dump(model_arousal, f'model/model_{model_name}_arousal.joblib')
    
    # --- 2.6. 予測と結果の統合 ---
    pred_valence = model_valence.predict(X_test)
    pred_arousal = model_arousal.predict(X_test)

    # ValenceとArousalの予測結果から最終的な感情を再構成
    final_emotion_pred = []
    for v, a in zip(pred_valence, pred_arousal):
        if v == 1 and a == 1:
            final_emotion_pred.append('Happy/Excited')
        elif v == 1 and a == 0:
            final_emotion_pred.append('Relax/Chill')
        elif v == 0 and a == 1:
            final_emotion_pred.append('Angry/Frustrated')
        else: # v == 0 and a == 0
            final_emotion_pred.append('Tired/Sad')
    
    # --- 2.7. 評価 ---
    accuracy = accuracy_score(y_emotion_true_test, final_emotion_pred)

    # --- ★ 2. 評価結果をリストに追加 ---
    results_summary.append({
        'model': model_name,
        'accuracy': accuracy
    })
    
    print(f"モデル: {model_name} | 正解率: {accuracy:.4f}")



# --- ★ 3. 全ての処理完了後、結果をまとめて表示 ---
print("=================================================")
print("全モデルの評価結果まとめ")
print("=================================================")

if not results_summary:
    print("処理されたモデルがありませんでした。")
else:
    for result in results_summary:
        print(f"モデル: {result['model']:<10} | 正解率: {result['accuracy']:.4f}")

    # --- ★ 4. 平均正解率を計算して表示 ---
    all_accuracies = [result['accuracy'] for result in results_summary]
    average_accuracy = np.mean(all_accuracies)
    
    print("-------------------------------------------------")
    print(f"平均正解率: {average_accuracy:.4f}")
    print("=================================================")