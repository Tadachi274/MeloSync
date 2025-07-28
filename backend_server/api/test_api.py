#!/usr/bin/env python3
"""
MeloSync Playlist Generator API テストスクリプト
"""

import requests
import json
import time

# APIサーバーのベースURL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """ヘルスチェックエンドポイントのテスト"""
    print("🔍 ヘルスチェックテスト...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ ヘルスチェック成功")
            print(f"   レスポンス: {response.json()}")
        else:
            print(f"❌ ヘルスチェック失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
    print()

def test_get_moods():
    """利用可能な感情の取得テスト"""
    print("🎭 利用可能な感情の取得テスト...")
    try:
        response = requests.get(f"{BASE_URL}/moods")
        if response.status_code == 200:
            print("✅ 感情リスト取得成功")
            data = response.json()
            print(f"   利用可能な感情: {data['available_moods']}")
        else:
            print(f"❌ 感情リスト取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 感情リスト取得エラー: {e}")
    print()

def test_generate_playlist():
    """プレイリスト生成のテスト"""
    print("🎵 プレイリスト生成テスト...")
    
    # テスト用のリクエストデータ
    test_data = {
        "playlist_url": "https://open.spotify.com/playlist/6rEdUNfBu6BiWgp0PNXIO4?si=1611984fbf574d02",
        "current_mood": "Relax/Chill",
        "target_mood": "Happy/Excited",
        "top_k": 10
    }
    
    try:
        print(f"   リクエストデータ: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{BASE_URL}/generate-playlist",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ プレイリスト生成成功")
            data = response.json()
            print(f"   成功: {data['success']}")
            print(f"   メッセージ: {data['message']}")
            
            if data['playlist']:
                print(f"   生成された楽曲数: {len(data['playlist'])}")
                print("   上位5曲:")
                for i, track in enumerate(data['playlist'][:5]):
                    print(f"     {track['rank']}. トラックID: {track['track_id']} | スコア: {track['transition_score']}")
        else:
            print(f"❌ プレイリスト生成失敗: {response.status_code}")
            print(f"   エラー: {response.text}")
            
    except Exception as e:
        print(f"❌ プレイリスト生成エラー: {e}")
    print()

def test_invalid_inputs():
    """無効な入力のテスト"""
    print("🚫 無効な入力のテスト...")
    
    # 無効な感情のテスト
    invalid_mood_data = {
        "playlist_url": "https://open.spotify.com/playlist/6rEdUNfBu6BiWgp0PNXIO4?si=1611984fbf574d02",
        "current_mood": "InvalidMood",
        "target_mood": "Happy/Excited"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate-playlist", json=invalid_mood_data)
        if response.status_code == 400:
            print("✅ 無効な感情の検証成功")
        else:
            print(f"❌ 無効な感情の検証失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 無効な感情のテストエラー: {e}")
    
    # 無効なURLのテスト
    invalid_url_data = {
        "playlist_url": "https://invalid-url.com",
        "current_mood": "Relax/Chill",
        "target_mood": "Happy/Excited"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate-playlist", json=invalid_url_data)
        if response.status_code == 400:
            print("✅ 無効なURLの検証成功")
        else:
            print(f"❌ 無効なURLの検証失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 無効なURLのテストエラー: {e}")
    
    print()

def main():
    """メイン関数"""
    print("🧪 MeloSync Playlist Generator API テスト開始")
    print("=" * 60)
    
    # サーバーが起動するまで少し待機
    print("⏳ APIサーバーの起動を待機中...")
    time.sleep(2)
    
    # 各テストを実行
    test_health_check()
    test_get_moods()
    test_generate_playlist()
    test_invalid_inputs()
    
    print("🎉 テスト完了!")
    print("=" * 60)

if __name__ == "__main__":
    main()