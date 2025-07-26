import pandas as pd
from sklearn.model_selection import train_test_split
import lightgbm as lgb
import joblib

# --- 1. モデルとデータのマッピングを定義 ---
# 構造: '開始感情名': ('対応するCSVファイルのパス', 'そのファイル内のターゲット感情のラベル列名')
# ここでのラベル列名は、予測したいターゲット感情を指します
mood_map = {
    'Angry/Frustrated': ('data/music_data_angry_normalized_encoded.csv', 'Angry/Frustrated'),
    'Happy/Excited': ('data/music_data_happy_normalized_encoded.csv', 'Happy/Excited'),
    'Relax/Chill': ('data/music_data_relax_normalized_encoded.csv', 'Relax/Chill'),
    'Tired/Sad': ('data/music_data_tired_normalized_encoded.csv', 'Tired/Sad')
}

trained_models = {}

print("--- 4つの感情それぞれに対し、モデルの訓練を開始します ---")

# --- 2. 各CSVファイルをループで読み込み、モデルを訓練 ---
for mood_name, (csv_path, label_column) in mood_map.items():
    print(f"\n--- 開始感情: {mood_name} の処理中 ---")
    
    try:
        # 2.1 対応するデータを読み込む
        df = pd.read_csv(csv_path)
        # NaNを含む行を削除し、データの品質を保証する
        df.dropna(subset=[label_column], inplace=True)
        print(f"データ読み込み成功: {csv_path}, データ数: {len(df)}")

        if df.empty:
            print("データが空のため、この感情の処理をスキップします。")
            continue
            
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません {csv_path}。この感情の処理をスキップします。")
        continue

    # 2.2 特徴量(X)とラベル(Y)を定義
    # 特徴量 = 全ての列 - ラベル列 - 特徴量ではない可能性のある列（例: URL, id, nameなど）
    non_feature_cols = ['担当者', 'アーティスト', '曲名（optional）', 'URL', 'id', 'name', 'artists', 'genre', 'ジャンル', label_column]
    # 実際に存在する列のみを絞り込んで削除
    cols_to_drop = [col for col in non_feature_cols if col in df.columns]
    
    X = df.drop(columns=cols_to_drop)
    Y = df[label_column]
    
    # ラベルが整数型であることを確認（必要な場合）
    # Y = Y.astype(int) 

    # 2.3 訓練データとテストデータに分割
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42, stratify=Y)

    # 2.4 LightGBMモデルの訓練
    # 注意: objective と num_class は、ご自身のラベルに合わせて調整が必要な場合があります
    # ラベルが多クラス分類（例: 0,1,2,3がそれぞれ異なる感情を表す）の場合は 'multiclass' を使用
    # 二値分類（0,1）の場合は 'binary' を使用
    lgbm = lgb.LGBMClassifier(objective='multiclass', num_class=4, random_state=42) # ターゲット感情が4カテゴリあると仮定
    
    lgbm.fit(X_train, Y_train,
             eval_set=[(X_test, Y_test)],
             eval_metric='multi_logloss')

    # 2.5 モデルの保存
    model_filename = f"model_{mood_name.replace('/', '-')}.joblib"
    joblib.dump(lgbm, model_filename)
    trained_models[mood_name] = lgbm
    print(f"モデルの訓練が完了しました。保存先: {model_filename}")

print("\n--- 全てのモデルの訓練が完了しました！ ---")