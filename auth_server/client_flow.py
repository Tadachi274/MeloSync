# client_flow.py
import os
import requests
import webbrowser

# 環境変数かデフォルトで API サーバーのベース URL を設定
JWT_BASE = os.getenv("JWT_BASE_URL", "http://0.0.0.0:8000")
SPOTIFY_BASE = os.getenv("SPOTIFY_BASE_URL", "http://0.0.0.0:8001")
API_BASE = os.getenv("API_BASE_URL", "http://0.0.0.0:8000")

def obtain_jwt():
    """
    /auth/google-login に Google の id_token を送信して JWT を取得
    """
    id_token = os.getenv("GOOGLE_ID_TOKEN") or input("Enter your Google ID token: ")
    resp = requests.post(
        f"{JWT_BASE}/api/auth/google-login",
        json={"id_token": id_token}
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

def obtain_spotify_code():
    """
    /login を開いて Spotify 認可 → ブラウザに出る JSON から code をコピーして貼り付け
    """
    login_url = f"{SPOTIFY_BASE}/api/spotify/login"
    print("Opening Spotify login page in your browser...")
    webbrowser.open(login_url)
    print("After you authorize, your browser will show JSON including “authorization_code”.")
    code = input("Paste the authorization_code here: ").strip()
    return code

def save_tokens(jwt_token: str, code: str):
    """
    3) JWT と code を /api/spotify/callback に POST
       エラー時には詳細を出力してから例外を再スロー
    """
    url = f"{API_BASE}/api/spotify/callback"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }
    payload = {"code": code}

    resp = requests.post(url, json=payload, headers=headers)

    if resp.ok:
        return resp.json()
    else:
        # デバッグ出力
        print("❌ リクエスト失敗:")
        print("  URL    :", url)
        print("  Headers:", headers)
        print("  Body   :", payload)
        print("  Status :", resp.status_code)
        print("  Response body:", resp.text)
        # ここで例外を再スローして呼び出し元にも知らせる
        resp.raise_for_status()

def main():
    # 1. JWT を取得
    jwt_token = obtain_jwt()
    print("✅ Obtained JWT.")

    # 2. Spotify 認可コードを取得
    code = obtain_spotify_code()
    print(f"✅ Received Spotify code: {code[:8]}...")

    # 3. アクセストークンを交換・保存
    result = save_tokens(jwt_token, code)
    print("✅ Spotify tokens saved to database.")
    print("Server response:", result)

if __name__ == "__main__":
    main()
