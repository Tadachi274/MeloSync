import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, log_loss
from sklearn.impute import SimpleImputer
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
import xgboost as xgb
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
import joblib
from sklearn.linear_model import LogisticRegression
import lightgbm as lgb

# 各CSVファイルのパス
dataset_files = {
    'Happy/Excited': 'data/music_data_happy_normalized_encoded.csv',
    'Angry/Frustrated': 'data/music_data_angry_normalized_encoded.csv',
    'Tired/Sad': 'data/music_data_tired_normalized_encoded.csv',
    'Relax/Chill': 'data/music_data_relax_normalized_encoded.csv'
}

# --- ★ 1. 初期化 ---
results_summary = []
all_feature_importances = [] # 全モデルの重要度を保存するリスト

# --- ★ 2. ループ処理で各CSVファイルに対してモデルを構築 ---
for emotion, file_path in dataset_files.items():
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
    
    
    
    # 最初の7列と不要な列を除外
    df = df.iloc[:, 7:]
    df = df.drop(columns=['mode_0.0', 'mode_1.0'])
    df = df.drop(columns=['genre_nan', 'genre_acoustic', 'genre_alt-rock', 'genre_alternative', 'genre_anime', 'genre_dance', 'genre_edm', 'genre_electro', 'genre_electronic', 'genre_garage', 'genre_grunge', 'genre_hip-hop', 'genre_indie', 'genre_indie pop', 'genre_j-dance', 'genre_j-idol', 'genre_j-pop', 'genre_j-rock', 'genre_k-pop', 'genre_mandopop', 'genre_metal', 'genre_pop', 'genre_punk', 'genre_punk-rock', 'genre_r&b', 'genre_reggae', 'genre_rock', 'genre_rockabilly', 'genre_singer-songwriter', 'genre_soul', 'genre_techno', 'genre_trance', 'genre_trip-hop', 'genre_turkish'])
    if 'ジャンル' in df.columns:
        df = df.drop(columns=['ジャンル'])
    print(df.columns)

    # 特徴量と正解ラベルの分割
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]

    # データクリーニング
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
    
    # モデルの学習
    # ロジスティック回帰
    model = LogisticRegression(multi_class='multinomial', solver='lbfgs', random_state=42, max_iter=1000)
    
    # ランダムフォレスト
    # model = RandomForestClassifier(random_state=42)
    
    # LightGBM
    # model = lgb.LGBMClassifier(random_state=42)
    
    # XGBoost
    # le = LabelEncoder()
    # # yの文字列ラベルを数値（0, 1, 2, 3）に変換
    # y_encoded = le.fit_transform(y)
    # # 変換後のy_encodedを使ってデータを分割
    # X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
    # model = xgb.XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='mlogloss')
    
    # SVM
    # model = SVC(probability=True, random_state=42)

    model.fit(X_train, y_train)
    
    # # --- 特徴量の重要度をリストに保存 --- ランダムフォレストの場合のみこれが動かせる。
    # importances = model.feature_importances_
    # feature_importance_df = pd.DataFrame({
    #     'Feature': X.columns,
    #     'Importance': importances
    # })
    # all_feature_importances.append(feature_importance_df)

    # ... (モデルの評価や保存処理は変更なし) ...
    # --- モデルの保存 ---
    model_filename = f"model/model_{emotion.replace('/', '-')}.joblib"
    joblib.dump(model, model_filename)
    print(f"モデルを '{model_filename}' に保存しました。")
    
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    loss = log_loss(y_test, y_pred_proba, labels=model.classes_)
    results_summary.append({'model': model_name, 'accuracy': accuracy, 'loss': loss})
    print(f"{model_name}モデルの評価完了 - 正解率: {accuracy:.4f}")


# --- ★ 3. 全ての処理完了後、結果をまとめて表示 ---
print("\n=================================================")
print("全モデルの評価結果まとめ")
print("=================================================")
if results_summary:
    for result in results_summary:
        print(f"モデル: {result['model']:<10} | 正解率: {result['accuracy']:.4f} | 損失: {result['loss']:.4f}")
    average_accuracy = np.mean([result['accuracy'] for result in results_summary])
    print("-------------------------------------------------")
    print(f"平均正解率: {average_accuracy:.4f}")

# --- ★ 4. 全モデルの重要度を合算してランキングを作成 ★---　ランダムフォレストの場合これが動かせる。
# print("\n=================================================")
# print("総合的な特徴量の重要度ランキング（4モデル平均）")
# print("=================================================")
# if not all_feature_importances:
#     print("特徴量の重要度データがありません。")
# else:
#     # 全モデルの重要度データを1つのDataFrameに結合
#     combined_importances_df = pd.concat(all_feature_importances)

#     # 特徴量ごとに重要度の平均を計算
#     # ascending=Trueで重要度が低い順（必要ない順）にソート
#     average_importance = combined_importances_df.groupby('Feature')['Importance'].mean().sort_values(ascending=True)

#     print("【総合的に見て必要ない可能性が高い特徴量ランキング】")
#     print(average_importance.head(15)) # ワースト15位を表示

#     # グラフ描画用に降順でソート
#     average_importance_desc = average_importance.sort_values(ascending=False)

#     # 総合的な重要度をグラフで可視化
#     plt.figure(figsize=(12, 10))
#     plt.barh(average_importance_desc.index, average_importance_desc.values)
#     plt.xlabel('平均重要度 (Average Importance)')
#     plt.ylabel('特徴量 (Feature)')
#     plt.title('総合的な特徴量の重要度（4モデル平均）')
#     plt.gca().invert_yaxis()
#     plt.tight_layout()

#     # グラフをファイルとして保存
#     os.makedirs('feature_importance_graphs', exist_ok=True)
#     graph_filename = "data/analysis/importance_ALL_MODELS_combined.png"
#     plt.savefig(graph_filename)
#     print(f"\n総合的な特徴量の重要度グラフを '{graph_filename}' に保存しました。")
#     plt.show()