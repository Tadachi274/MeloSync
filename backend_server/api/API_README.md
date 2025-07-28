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
uvicorn playlist_api:app --host 0.0.0.0 --port 8000 --reload
```

### 4. APIドキュメントの確認

ブラウザで以下のURLにアクセスしてAPIドキュメントを確認できます：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

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
  "top_k": 10
}
```

**パラメータ:**
- `playlist_url` (必須): SpotifyプレイリストのURL
- `current_mood` (必須): 現在の感情（利用可能な感情のいずれか）
- `target_mood` (必須): 目標の感情（利用可能な感情のいずれか）
- `top_k` (オプション): 推薦する楽曲の最大数（デフォルト: 10000）

**成功時のレスポンス例:**
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
  "error": null
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

# プレイリスト生成
curl -X POST http://localhost:8000/generate-playlist \
  -H "Content-Type: application/json" \
  -d '{
    "playlist_url": "https://open.spotify.com/playlist/6rEdUNfBu6BiWgp0PNXIO4?si=1611984fbf574d02",
    "current_mood": "Relax/Chill",
    "target_mood": "Happy/Excited",
    "top_k": 10
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

## 🚨 注意事項

1. **Spotify API認証**: 有効なSpotify Client IDとClient Secretが必要です
2. **プレイリストURL**: 公開されているSpotifyプレイリストのURLのみ対応
3. **モデルファイル**: 必要な機械学習モデルファイル（.joblib）が`model/`ディレクトリに存在する必要があります
4. **ネットワーク接続**: Spotify APIとSoundStat APIへの接続が必要です

## 🔄 移行スコアについて

移行スコアは0-100の範囲で、現在の感情から目標感情への移行の適切さを示します：
- **高いスコア**: より適切な移行
- **低いスコア**: 移行に適さない楽曲

スコアは機械学習モデルによる確率を正規化して算出されます。