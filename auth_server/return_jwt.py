import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
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


# ─── JWT 発行関数 ─────────────────────────────────────────
def create_jwt(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# ─── エンドポイント：Google ログイン → JWT 返却 ────────────────
@app.post("/api/auth/google-login")
async def google_login():
    print("Received Login Request")
    user_id = str(uuid.uuid4())
    print("user_id:", user_id)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid Google ID token")

    access_token = create_jwt(user_id)
    print("access_token:", access_token)
    return {"access_token": access_token}


