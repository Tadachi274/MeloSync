import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi import Depends, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet
from jose import jwt, JWTError
import psycopg2
from datetime import datetime, timezone
from pathlib import Path

dotenv_path = Path(__file__).parent / ".env"
load_dotenv()

app = FastAPI()

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

DB_HOST     = os.getenv('DB_HOST')
DB_PORT     = 5433
DB_NAME     = os.getenv('DB_NAME')
DB_USER     = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

JWT = os.getenv('JWT')
SPOTIFY_CODE = os.getenv('SPOTIFY_CODE')

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM      = "HS256"
FERNET_KEY = os.getenv('FERNET_KEY').encode('utf-8')  

print(f"DB_HOST={DB_HOST}  DB_PORT={DB_PORT}  DB_USER={DB_USER}  DB_NAME={DB_NAME}")
print("DEBUG SPOTIFY_CLIENT_ID    =", SPOTIFY_CLIENT_ID)
print("DEBUG SPOTIFY_CLIENT_SECRET=", SPOTIFY_CLIENT_SECRET)
print("DEBUG SPOTIFY_REDIRECT_URI =", SPOTIFY_REDIRECT_URI)
print("DEBUG JWT", JWT)

def get_current_user(authorization: str = Header(...)) -> str:
    """
    Authorization ヘッダーから JWT を取り出し、
    user_id を検証・返却する Dependency
    """
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Authorization header malformed")

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="user_id not found in token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token validation failed")

@app.get("/api/test/user")
async def test_user(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id}

@app.post("/api/spotify/callback")
async def spotify_callback(
    request: Request,
    user_id: str = Depends(get_current_user)
    ):
    """
    Androidアプリから送られてきた認証コードを取得し、アクセストークンに交換する。
    """
    try:
        print(f"Received request from user_id: {user_id}")
        data = await request.json()
        auth_code = data.get("code")

        if not auth_code:
            raise HTTPException(status_code=400, detail="Authorization code not found")

        # 認証コードをアクセストークンに交換する
        token_url = "https://accounts.spotify.com/api/token"

        resp = requests.post(
            token_url,
            data={
                "grant_type":   "authorization_code",
                "code":         auth_code,
                "redirect_uri": SPOTIFY_REDIRECT_URI,
            },
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        )
        # Spotify が返す JSON をパース
        try:
            detail = resp.json()
        except ValueError:
            detail = resp.text
        if resp.status_code != 200:
        # 失敗時はステータスと Spotify のエラー内容をそのまま投げる
            raise HTTPException(status_code=resp.status_code, detail=detail)
        token_info = detail
        # 取得したトークンをユーザー情報と紐付けてデータベースに保存する
        access_token = token_info["access_token"]
        refresh_token = token_info["refresh_token"]
        expires_in = token_info["expires_in"]
        expires_at = int(datetime.now(timezone.utc).timestamp() + expires_in)
        print(f"Access Token: {access_token}")
        print(f"Refresh Token: {refresh_token}")

        key = FERNET_KEY
        encrypted_access = encrypt(key, access_token)
        encrypted_refresh = encrypt(key, refresh_token)

        save_tokens_to_db(user_id, encrypted_access, encrypted_refresh, expires_at)

        # これでバックエンドはユーザーのプレイリストを取得できる
        playlists = get_user_playlists(access_token)
        print(playlists)

        return {"status": "success", "playlists": playlists}

    except requests.exceptions.HTTPError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": str(e)})
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})



def encrypt(key: bytes, data: str):
    """
    key: Fernet key as bytes
    data: plaintext string
    """
    fernet = Fernet(key)
    # data を bytes にして暗号化 → bytes
    encrypted_pass = fernet.encrypt(data.encode('utf-8'))
    # DBに保存しやすいように戻り値は文字列に
    return encrypted_pass.decode('utf-8')

def save_tokens_to_db(user_id: str, access_token: str, refresh_token: str, expires_at: int):
    """
    ユーザーのアクセストークンとリフレッシュトークンをデータベースに保存する関数
    """
    print(f"Saving tokens for user_id: {user_id}")

    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO spotify_tokens (
            user_id,
            access_token,
            refresh_token,
            expires_at
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            access_token  = EXCLUDED.access_token,
            refresh_token = EXCLUDED.refresh_token,
            expires_at    = EXCLUDED.expires_at
    """, (user_id, access_token, refresh_token, expires_at))
    
    conn.commit()
    cur.close()
    conn.close()


def get_user_playlists(access_token: str):
    """
    アクセストークンを使ってユーザーのプレイリストを取得する関数
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.spotify.com/v1/me/playlists", headers=headers)
    response.raise_for_status()

    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch playlists")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5001)