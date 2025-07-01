# MeloSync Music Classification Model

音楽データを使用した教師あり学習による曲の分類モデルです。Spotify APIを使用して取得した音声特徴量から、曲の感情カテゴリを予測します。

## 概要

このプロジェクトは、以下の機能を提供します：

- **Spotify特徴量抽出器** (`spotify_feature_extractor.py`): Spotify APIを使用して曲の音声特徴量を取得
- **感情分類モデル** (`emotion_classifier.py`): Spotify特徴量から感情カテゴリを予測
- **基本的な分類モデル** (`main.py`): シンプルな特徴量エンジニアリングと複数の機械学習アルゴリズム
- **高度な分類モデル** (`advanced_classifier.py`): 高度な特徴量エンジニアリング、ハイパーパラメータチューニング、アンサンブル学習

## データセット

`melosync_music_data.csv` には以下の情報が含まれています：

- **担当者**: データを入力した人
- **アーティスト**: アーティスト名
- **曲名**: 曲のタイトル
- **URL**: Spotifyのリンク
- **感情カテゴリ**: Happy/Excited, Angry/Frustrated, Tired/Sad, Relax/Chill
- **ジャンル**: 曲のジャンル分類（応援ソング、恋愛ソング、失恋ソングなど）

## Spotify API特徴量

Spotify APIから取得される音声特徴量：

- **danceability**: ダンス性（0-1）
- **energy**: エネルギー（0-1）
- **valence**: 明るさ（0-1）
- **tempo**: テンポ（BPM）
- **loudness**: 音量（dB）
- **acousticness**: アコースティック性（0-1）
- **instrumentalness**: 器楽性（0-1）
- **liveness**: ライブ性（0-1）
- **speechiness**: 話声性（0-1）
- **mode**: 調性（0=短調, 1=長調）
- **key**: 調（0-11）
- **time_signature**: 拍子記号
- **popularity**: 人気度（0-100）
- **duration_ms**: 長さ（ミリ秒）
- **explicit**: 露骨な内容（0-1）

## 特徴量

### Spotify特徴量抽出器 (`spotify_feature_extractor.py`)
- Spotify APIから取得される音声特徴量（上記参照）
- ピッチ、ティムブレの統計量
- セグメント、セクション数

### 感情分類モデル (`emotion_classifier.py`)
- Spotify音声特徴量
- 各感情カテゴリ（Happy/Excited, Angry/Frustrated, Tired/Sad, Relax/Chill）を予測

### 基本モデル (`main.py`)
- アーティスト名（エンコード済み）
- 曲名の長さ
- URLの長さ
- 各感情カテゴリ（エンコード済み）

### 高度なモデル (`advanced_classifier.py`)
- アーティスト関連: アーティスト名、アーティストごとの曲数
- 感情関連: 感情の多様性、主要感情、感情パターン
- テキスト関連: 曲名の長さ、単語数、特殊文字数
- URL関連: URLの長さ、パラメータの有無
- ジャンル関連: ジャンルの出現頻度
- 組み合わせ特徴量: アーティスト×ジャンル、感情パターン

## 使用アルゴリズム

### Spotify特徴量抽出器
- Spotify Web API
- 音声分析API

### 感情分類モデル
- Random Forest
- Gradient Boosting
- XGBoost
- LightGBM
- SVM
- アンサンブルモデル（Voting Classifier）

### 基本モデル
- Random Forest
- Gradient Boosting
- Logistic Regression
- SVM

### 高度なモデル
- Random Forest（ハイパーパラメータチューニング付き）
- Gradient Boosting（ハイパーパラメータチューニング付き）
- XGBoost（ハイパーパラメータチューニング付き）
- LightGBM
- SVM
- アンサンブルモデル（Voting Classifier）

## インストール

1. 必要なライブラリをインストール：
```bash
pip install -r requirements.txt
```

2. Spotify API認証情報を設定：
```bash
export SPOTIFY_CLIENT_ID='your_client_id'
export SPOTIFY_CLIENT_SECRET='your_client_secret'
```

Spotify API認証情報の取得方法：
1. [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) にアクセス
2. アプリケーションを作成
3. Client IDとClient Secretを取得

## 使用方法

### 1. Spotify特徴量の抽出
```bash
python spotify_feature_extractor.py
```

### 2. 感情分類モデルの実行
```bash
python emotion_classifier.py
```

### 3. 基本モデルの実行
```bash
python main.py
```

### 4. 高度なモデルの実行
```bash
python advanced_classifier.py
```

## 出力ファイル

実行後、以下のファイルが生成されます：

### Spotify特徴量抽出器
- `melosync_music_data_with_spotify_features.csv`: Spotify特徴量を含む拡張データ
- `failed_tracks.csv`: 特徴量取得に失敗したトラックのリスト

### 感情分類モデル
- `emotion_correlation.png`: 感情カテゴリ間の相関
- `emotion_model_comparison.png`: 各感情カテゴリのモデル性能比較
- `confusion_matrix_*.png`: 各感情カテゴリの混同行列
- `feature_importance_*.png`: 各感情カテゴリの特徴量重要度

### 基本モデル
- `emotion_distribution.png`: 感情カテゴリの分布
- `model_comparison.png`: モデル性能比較
- `confusion_matrix.png`: 混同行列
- `feature_importance.png`: 特徴量重要度

### 高度なモデル
- `advanced_model_comparison.png`: 詳細なモデル性能比較
- `advanced_confusion_matrix.png`: 詳細な混同行列
- `advanced_feature_importance.png`: 詳細な特徴量重要度
- `feature_correlation.png`: 特徴量間の相関行列

## 評価指標

- **精度 (Accuracy)**: 全体の正解率
- **F1スコア**: 精度と再現率の調和平均
- **クロスバリデーション**: 5分割交差検証
- **混同行列**: 各クラスごとの予測結果

## 予測機能

### 感情分類モデル
新しい曲の感情カテゴリを予測する機能：

```python
# Spotify特徴量から感情を予測
sample_features = {
    'danceability': 0.8,
    'energy': 0.9,
    'valence': 0.7,
    'tempo': 120,
    'loudness': -5.0,
    'acousticness': 0.1,
    'instrumentalness': 0.0,
    'liveness': 0.3,
    'speechiness': 0.1,
    'mode': 1,
    'key': 5,
    'time_signature': 4,
    'popularity': 80,
    'duration_ms': 180000,
    'explicit': 0
}

predictions, probabilities = classifier.predict_emotions(sample_features)
```

### 基本モデル
新しい曲のジャンルを予測する機能も含まれています：

```python
# 基本モデルの場合
classifier.predict_new_song(
    artist="嵐",
    song_name="Happiness",
    url="https://open.spotify.com/track/example",
    emotions=["Happy/Excited", "Relax/Chill", "Relax/Chill", "Happy/Excited"]
)
```

## プロジェクト構造

```
melosync_ml/
├── spotify_feature_extractor.py    # Spotify特徴量抽出器
├── emotion_classifier.py           # 感情分類モデル
├── main.py                         # 基本分類モデル
├── advanced_classifier.py          # 高度な分類モデル
├── requirements.txt                # 必要なライブラリ
├── README.md                       # このファイル
├── melosync_music_data.csv         # 音楽データ
└── 出力ファイル（実行後生成）
    ├── melosync_music_data_with_spotify_features.csv  # Spotify特徴量付きデータ
    ├── failed_tracks.csv           # 失敗したトラックリスト
    ├── *.png                       # 可視化ファイル
    └── ...
```

## 技術スタック

- **Python**: 3.8+
- **機械学習**: scikit-learn, XGBoost, LightGBM
- **データ処理**: pandas, numpy
- **可視化**: matplotlib, seaborn
- **前処理**: LabelEncoder, StandardScaler

## 今後の拡張予定

- [ ] 音声特徴量の追加
- [ ] 深層学習モデルの実装
- [ ] Web APIの作成
- [ ] リアルタイム予測機能
- [ ] より多くの音楽データの追加

## ライセンス

このプロジェクトは教育目的で作成されています。

## 貢献

バグ報告や機能提案は歓迎します。プルリクエストも受け付けています。

## 連絡先

質問や提案がある場合は、お気軽にお問い合わせください。 