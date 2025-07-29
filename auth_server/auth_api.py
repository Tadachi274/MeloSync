import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from jose import jwt
from dotenv import load_dotenv
import uuid
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
import get_save_accesstoken as db_utils
import return_jwt as return_jwt

# ─── 環境変数読み込み ─────────────────────────────────────
load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 6
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
print("DEBUG JWT_SECRET:", SECRET_KEY)

# ─── FastAPI インスタンス ─────────────────────────────────
app = FastAPI()

# ─── リクエストボディの定義 ─────────────────────────────────
class GoogleLoginRequest(BaseModel):
    id_token: str

# ─── エンドポイント：Google ログイン → JWT 返却 ────────────────
@app.post("/api/auth/google-login")
async def google_login():
    print("Received Login Request")
    user_id = str(uuid.uuid4())
    print("user_id:", user_id)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid Google ID token")

    access_token = return_jwt.create_jwt(user_id)
    print("access_token:", access_token)
    return {"access_token": access_token}

# ─── JWT 更新エンドポイント ─────────────────────────────────
@app.post("/api/auth/refresh-token")
async def refresh_token(authorization: str = Header(...)):
    """
    フロント側から渡されたJWTを検証し、期限切れの場合は新しいJWTを返す。
    """
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Authorization header malformed")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        exp = payload.get("exp")

        if not user_id or not exp:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Check if the token has expired
        if datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            # Issue a new JWT
            new_token = return_jwt.create_jwt(user_id)
            return {"access_token": new_token}
        else:
            return {"access_token": token}  # Return the same token if not expired

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token validation failed")

@app.post("/api/spotify/callback")
async def spotify_callback(
    request: Request,
    user_id: str = Depends(db_utils.get_current_user)
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
        if resp.status_code == 429:
            print("DEBUG Headers:", resp.headers)  # ← 追加
            retry_after = resp.headers.get("Retry-After")
            print("DEBUG Retry-After:", retry_after)  # ← 追加
            raise HTTPException(status_code=429, detail=f"Rate limit hit. Retry after {retry_after} seconds.")
        if resp.status_code != 200:
        # 失敗時はステータスと Spotify のエラー内容をそのまま投げる
            print("DEBUG Error Response:", detail)
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
        encrypted_access = db_utils.encrypt(key, access_token)
        encrypted_refresh = db_utils.encrypt(key, refresh_token)

        db_utils.save_tokens_to_db(user_id, encrypted_access, encrypted_refresh, expires_at)

        # これでバックエンドはユーザーのプレイリストを取得できる
        #playlists = db_utils.get_user_playlists(access_token)
        #print(playlists)

        #return {"status": "success", "playlists": playlists}
        return {"status": "success"}

    except requests.exceptions.HTTPError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": str(e)})
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
