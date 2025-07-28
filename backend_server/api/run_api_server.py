#!/usr/bin/env python3
"""
MeloSync Playlist Generator API サーバー起動スクリプト
"""

import uvicorn
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def main():
    """APIサーバーを起動する"""
    print("🎵 MeloSync Playlist Generator API サーバーを起動中...")
    print("=" * 50)
    
    # 環境変数の確認
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("⚠️  警告: SPOTIFY_CLIENT_ID または SPOTIFY_CLIENT_SECRET が設定されていません。")
        print("   .envファイルに以下の設定を追加してください：")
        print("   SPOTIFY_CLIENT_ID=your_client_id")
        print("   SPOTIFY_CLIENT_SECRET=your_client_secret")
        print()
    
    print("📡 APIサーバー設定:")
    print(f"   - ホスト: 0.0.0.0")
    print(f"   - ポート: 8000")
    print(f"   - APIドキュメント: http://localhost:8000/docs")
    print(f"   - ヘルスチェック: http://localhost:8000/health")
    print("=" * 50)
    
    try:
        # サーバーを起動
        uvicorn.run(
            "playlist_api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,  # 開発用にホットリロードを有効化
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 サーバーを停止しました。")
    except Exception as e:
        print(f"❌ サーバー起動中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main()