# MeloSync Playlist Generator API

ユーザーの現在の感情と目標感情に基づいて、Spotifyプレイリストから最適な楽曲を推薦するAPIです。

## 🚀 クイックスタート

### 1. 環境設定

`.env`ファイルを作成し、Spotify APIの認証情報を設定してください：

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. APIサーバーの起動

#### 方法1: APIディレクトリから実行
```bash
cd backend_server/api
python start_server.py
```

#### 方法2: backend_serverディレクトリから実行
```bash
cd backend_server
python start_api.py
```

#### 方法3: uvicornを直接使用
```bash
cd backend_server/api
uvicorn playlist_api:app --host 0.0.0.0 --port 8004 --reload
```

### 4. APIドキュメントの確認

ブラウザで以下のURLにアクセスしてAPIドキュメントを確認できます：
- Swagger UI: http://localhost:8004/docs
- ReDoc: http://localhost:8004/redoc

## 📡 API エンドポイント

### 1. ヘルスチェック

**GET** `/health`

APIサーバーの状態を確認します。

**レスポンス例:**
```json
{
  "status": "healthy",
  "message": "MeloSync API is running"
}
```

### 2. 利用可能な感情の取得

**GET** `/moods`

利用可能な感情のリストを取得します。

**レスポンス例:**
```json
{
  "success": true,
  "available_moods": [
    "Angry/Frustrated",
    "Happy/Excited", 
    "Relax/Chill",
    "Tired/Sad"
  ]
}
```

### 3. プレイリスト生成

**POST** `/generate-playlist`

ユーザーの現在の感情と目標感情に基づいてプレイリストを生成します。

**リクエスト例:**
```json
{
  "playlist_url": "https://open.spotify.com/playlist/6rEdUNfBu6BiWgp0PNXIO4?si=1611984fbf574d02",
  "current_mood": "Relax/Chill",
  "target_mood": "Happy/Excited",
  "top_k": 10,
  "create_spotify_playlist": true,
  "max_tracks": 20
}
```

**パラメータ:**
- `playlist_url` (必須): SpotifyプレイリストのURL
- `current_mood` (必須): 現在の感情（利用可能な感情のいずれか）
- `target_mood` (必須): 目標の感情（利用可能な感情のいずれか）
- `top_k` (オプション): 推薦する楽曲の最大数（デフォルト: 10000）
- `create_spotify_playlist` (オプション): Spotifyプレイリストを作成するかどうか（デフォルト: false）
- `max_tracks` (オプション): プレイリストに追加する最大楽曲数（デフォルト: 20）

### 4. 全プレイリスト生成（複数ソース）

**POST** `/generate-all-playlists`

複数のプレイリストから楽曲を統合して、4つの感情状態の組み合わせで16個のプレイリストを一括生成します。

**リクエスト例（ランキングのみ）:**
```json
{
  "playlist_ids": [
    "6rEdUNfBu6BiWgp0PNXIO4",
    "37i9dQZF1DX5Vy6DFOcx00",
    "37i9dQZF1DX4WYpdgoIcn6"
  ],
  "top_k": 10,
  "create_spotify_playlists": false,
  "max_tracks": 20
}
```

**リクエスト例（Spotifyプレイリストも作成）:**
```json
{
  "playlist_ids": [
    "6rEdUNfBu6BiWgp0PNXIO4"
  ],
  "top_k": 10,
  "create_spotify_playlists": true,
  "max_tracks": 20
}
```

**パラメータ:**
- `playlist_ids` (必須): SpotifyプレイリストIDのリスト（例: "6rEdUNfBu6BiWgp0PNXIO4"）
- `top_k` (オプション): 推薦する楽曲の最大数（デフォルト: 10000）
- `create_spotify_playlists` (オプション): Spotifyプレイリストを作成するかどうか（デフォルト: false）
- `max_tracks` (オプション): プレイリストに追加する最大楽曲数（デフォルト: 20）

**成功時のレスポンス例（generate-playlist）:**
```json
{
  "success": true,
  "message": "「Relax/Chill」から「Happy/Excited」への推薦プレイリストを生成しました。",
  "playlist": [
    {
      "rank": 1,
      "track_id": "4iV5W9uYEdYUVa79Axb7Rh",
      "transition_score": 95.2
    },
    {
      "rank": 2,
      "track_id": "7lEptt4wbM0yJTvSG5EBof",
      "transition_score": 87.8
    }
  ],
  "spotify_playlist_url": "https://open.spotify.com/playlist/37i9dQZF1DX...",
  "error": null
}
```

**成功時のレスポンス例（generate-all-playlists）:**
```json
{
  "success": true,
  "message": "1個のプレイリストから楽曲を統合して16個のプレイリストを生成しました。成功: 16/16",
  "playlists": {
    "Angry/Frustrated": {
      "Angry/Frustrated": {
        "success": true,
        "playlist": [
          {
            "rank": 1,
            "track_id": "4iV5W9uYEdYUVa79Axb7Rh",
            "transition_score": 95.2
          }
        ],
        "count": 10
      }
    }
  },
  "spotify_playlist_urls": {
    "Angry/Frustrated": {
      "Angry/Frustrated": "https://open.spotify.com/playlist/37i9dQZF1DX...",
      "Happy/Excited": "https://open.spotify.com/playlist/37i9dQZF1DX...",
      "Relax/Chill": "https://open.spotify.com/playlist/37i9dQZF1DX...",
      "Tired/Sad": "https://open.spotify.com/playlist/37i9dQZF1DX..."
    }
  }
}
```

**エラー時のレスポンス例:**
```json
{
  "success": false,
  "message": "プレイリスト生成に失敗しました。",
  "playlist": null,
  "error": "有効なSpotifyプレイリストのURLを指定してください。"
}
```

## 🧪 テスト

APIの動作をテストするには：

```bash
cd backend_server/api
python test_api.py
```

## 📋 利用可能な感情

| 感情 | 説明 |
|------|------|
| Angry/Frustrated | 怒り/フラストレーション |
| Happy/Excited | 幸せ/興奮 |
| Relax/Chill | リラックス/落ち着き |
| Tired/Sad | 疲労/悲しみ |

## 🔧 エラーハンドリング

APIは以下のエラーを適切に処理します：

- **400 Bad Request**: 無効な入力パラメータ
- **500 Internal Server Error**: サーバー内部エラー

## 📝 使用例

### cURLを使用した例

```bash
# ヘルスチェック
curl http://localhost:8000/health

# 利用可能な感情の取得
curl http://localhost:8000/moods

# プレイリスト生成（ランキングのみ）
curl -X POST http://localhost:8000/generate-playlist \
  -H "Content-Type: application/json" \
  -d '{
    "playlist_url": "https://open.spotify.com/playlist/6rEdUNfBu6BiWgp0PNXIO4?si=1611984fbf574d02",
    "current_mood": "Relax/Chill",
    "target_mood": "Happy/Excited",
    "top_k": 10
  }'

# プレイリスト生成（Spotifyプレイリストも作成）
curl -X POST http://localhost:8000/generate-playlist \
  -H "Content-Type: application/json" \
  -d '{
    "playlist_url": "https://open.spotify.com/playlist/6rEdUNfBu6BiWgp0PNXIO4?si=1611984fbf574d02",
    "current_mood": "Relax/Chill",
    "target_mood": "Happy/Excited",
    "top_k": 10,
    "create_spotify_playlist": true,
    "max_tracks": 20
  }'

# 全プレイリスト生成（ランキングのみ）
curl -X POST http://localhost:8000/generate-all-playlists \
  -H "Content-Type: application/json" \
  -d '{
    "playlist_ids": [
      "6rEdUNfBu6BiWgp0PNXIO4",
      "37i9dQZF1DX5Vy6DFOcx00",
      "37i9dQZF1DX4WYpdgoIcn6"
    ],
    "top_k": 10,
    "create_spotify_playlists": false,
    "max_tracks": 20
  }'

# 全プレイリスト生成（Spotifyプレイリストも作成）
curl -X POST http://localhost:8000/generate-all-playlists \
  -H "Content-Type: application/json" \
  -d '{
    "playlist_ids": [
      "6rEdUNfBu6BiWgp0PNXIO4"
    ],
    "top_k": 10,
    "create_spotify_playlists": true,
    "max_tracks": 20
  }'
```

### Python requestsを使用した例

```python
import requests

# プレイリスト生成
response = requests.post(
    "http://localhost:8000/generate-playlist",
    json={
        "playlist_url": "https://open.spotify.com/playlist/6rEdUNfBu6BiWgp0PNXIO4?si=1611984fbf574d02",
        "current_mood": "Relax/Chill",
        "target_mood": "Happy/Excited",
        "top_k": 10
    }
)

if response.status_code == 200:
    data = response.json()
    if data['success']:
        print(f"生成された楽曲数: {len(data['playlist'])}")
        for track in data['playlist']:
            print(f"トラックID: {track['track_id']}, スコア: {track['transition_score']}")
    else:
        print(f"エラー: {data['error']}")
else:
    print(f"HTTPエラー: {response.status_code}")
```

## 🎵 Spotifyプレイリスト作成機能

### プレイリスト作成について
- `create_spotify_playlist: true`を指定すると、推薦された楽曲で実際のSpotifyプレイリストを作成します
- プレイリスト名は「現在の感情-to-未来の感情」の形式で自動生成されます
- 例: `Relax/Chill-to-Happy/Excited`
- プレイリストは公開設定で作成され、ユーザーのSpotifyアカウントに保存されます

## 🔄 複数プレイリスト統合機能

### 全プレイリスト生成について
- `generate-all-playlists`エンドポイントでは、複数のプレイリストIDを指定できます
- 指定された全てのプレイリストから楽曲を収集し、重複を除去して統合します
- 統合された楽曲プールから、4つの感情状態の組み合わせで16個のプレイリストを生成します
- 各プレイリストは移行スコアに基づいてランキング形式で楽曲を表示します

### 処理フロー
1. 指定された複数のプレイリストから楽曲を収集
2. 重複する楽曲を除去してユニークな楽曲リストを作成
3. 各楽曲の特徴を分析・処理
4. 4つの感情状態（現在の感情）× 4つの感情状態（目標感情）= 16個のプレイリストを生成
5. 各プレイリスト内で楽曲を移行スコア順にランキング

### 必要な認証設定
Spotifyプレイリスト作成機能を使用するには、以下の環境変数を設定してください：

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

初回実行時は、ブラウザでSpotify認証画面が開き、ユーザー認証が必要です。

## 🚨 注意事項

1. **Spotify API認証**: 有効なSpotify Client IDとClient Secretが必要です
2. **プレイリストURL**: 公開されているSpotifyプレイリストのURLのみ対応
3. **モデルファイル**: 必要な機械学習モデルファイル（.joblib）が`model/`ディレクトリに存在する必要があります
4. **ネットワーク接続**: Spotify APIとSoundStat APIへの接続が必要です
5. **ユーザー認証**: プレイリスト作成にはSpotifyユーザー認証が必要です

## 🔄 移行スコアについて

移行スコアは0-100の範囲で、現在の感情から目標感情への移行の適切さを示します：
- **高いスコア**: より適切な移行
- **低いスコア**: 移行に適さない楽曲

スコアは機械学習モデルによる確率を正規化して算出されます。