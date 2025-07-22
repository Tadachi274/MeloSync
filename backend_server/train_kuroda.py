import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from sklearn.impute import SimpleImputer
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier
import lightgbm as lgb

# 各CSVファイルのパス
dataset_files = [
    'data/music_data_happy_normalized_encoded.csv', 
    'data/music_data_angry_normalized_encoded.csv', 
    'data/music_data_tired_normalized_encoded.csv', 
    'data/music_data_relax_normalized_encoded.csv'
]

# --- ★ 1. モデルの評価結果を保存するリストを初期化 ---
results_summary = []

# --- ループ処理で各CSVファイルに対してモデルを構築 ---
for file_path in dataset_files:
    print(f"=================================================")
    print(f"処理中のファイル: {file_path}")
    print(f"=================================================")
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません。次のファイルに進みます。\n")
        continue
    
    # モデル名を抽出
    base_name = os.path.basename(file_path)
    model_name = base_name.replace('music_data_', '').replace('_normalized_encoded.csv', '')
    
    # # 各々の担当データのみで予測
    # name_list = ["Chen", "大林", "黒田", "渡邊", "忠地", "Yifan"]
    # df = df[df["担当者"] == "Yifan"]
    # print(len(df))
    
    missing_counts = df.isnull().sum()
    print("各列の欠損値の数:")
    print(missing_counts[missing_counts > 0])  # 欠損がある列だけ表示
    print("\n")
    print(df.head())
    
    # 最初の7列を除外
    df = df.iloc[:, 7:]
    # modeを除外
    df = df.drop(columns=['mode_0.0', 'mode_1.0'])
    
    # ジャンルを除外
    df = df.drop(columns=['ジャンル'])

    # 特徴量と正解ラベルの分割
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]

    # データクリーニング（型変換）
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    if y.isnull().any():
        y.fillna(y.mode()[0], inplace=True)

    # 訓練データとテストデータに分割
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # 欠損値の補完
    imputer = SimpleImputer(strategy='median')
    X_train = imputer.fit_transform(X_train)
    X_test = imputer.transform(X_test)
    
    print("データ準備完了（欠損値処理済み）")
    
    # モデルの学習
    # ロジスティック回帰
    # model = LogisticRegression(multi_class='multinomial', solver='lbfgs', random_state=42, max_iter=1000)
    
    # ランダムフォレスト
    model = RandomForestClassifier(random_state=42)
    
    # LightGBM
    # model = lgb.LGBMClassifier(random_state=42)
    
    model.fit(X_train, y_train)
    
    print("モデルの学習が完了しました。")
    # 学習済みモデルを 'my_model.joblib' という名前で保存
    joblib.dump(model, f'model/my_model_{model_name}.joblib') 

    print(f"学習済みモデルを model/my_model_{model_name}.joblib として保存しました。")
    
    # モデルの評価
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    loss = log_loss(y_test, y_pred_proba, labels=model.classes_)
    

    # --- ★ 2. 評価結果をリストに追加 ---
    results_summary.append({
        'model': model_name,
        'accuracy': accuracy,
        'loss': loss
    })
    
    # 予測結果の保存
    output_filename = f"data/prediction/prediction_results_{model_name}.csv"
    results_df = pd.DataFrame(y_pred_proba, columns=model.classes_)
    results_df['True Label'] = y_test.values
    results_df['Predicted Label'] = y_pred
    results_df.to_csv(output_filename, index=False)
    print(f"予測結果を '{output_filename}' に保存しました。\n")



# --- ★ 3. 全ての処理完了後、結果をまとめて表示 ---
print("=================================================")
print("全モデルの評価結果まとめ")
print("=================================================")

if not results_summary:
    print("処理されたモデルがありませんでした。")
else:
    for result in results_summary:
        print(f"モデル: {result['model']:<10} | 正解率: {result['accuracy']:.4f} | 損失: {result['loss']:.4f}")

    # --- ★ 4. 平均正解率を計算して表示 ---
    all_accuracies = [result['accuracy'] for result in results_summary]
    average_accuracy = np.mean(all_accuracies)
    
    print("-------------------------------------------------")
    print(f"平均正解率: {average_accuracy:.4f}")
    print("=================================================")