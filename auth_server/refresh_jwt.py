import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from jose import jwt
from dotenv import load_dotenv
import uuid

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
            new_token = create_jwt(user_id)
            return {"access_token": new_token}
        else:
            return {"access_token": token}  # Return the same token if not expired

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token validation failed")
