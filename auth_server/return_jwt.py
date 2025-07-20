import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jose import jwt
from dotenv import load_dotenv

# ─── 環境変数読み込み ─────────────────────────────────────
load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 6
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


# ─── Google ID トークン検証のスタブ ─────────────────────────
def verify_google_id_token(id_token: str) -> str:
    """
    本番では google.oauth2.id_token.verify_oauth2_token を使って
    id_token の正当性を検証し、payload['sub'] を返します。
    ここでは例示のためスタブ実装としています。
    """
    # 例：
    # from google.oauth2 import id_token as google_id_token
    # from google.auth.transport import requests
    # id_info = google_id_token.verify_oauth2_token(
    #     id_token,
    #     requests.Request(),
    #     os.getenv("GOOGLE_CLIENT_ID")
    # )
    # return id_info["sub"]
    return "example_user_id"


# ─── エンドポイント：Google ログイン → JWT 返却 ────────────────
@app.post("/api/auth/google-login")
async def google_login(req: GoogleLoginRequest):
    print("Received Google ID token:", req.id_token)
    user_id = verify_google_id_token(req.id_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid Google ID token")

    # ── ここで user_id を元に「ユーザーの新規作成 or 既存確認」を行う ──
    # （例：DBに保存したり、既存レコードを検索したり）

    access_token = create_jwt(user_id)
    print("access_token:", access_token)
    return {"access_token": access_token}
