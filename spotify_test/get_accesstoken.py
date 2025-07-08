import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")


@app.post("/api/spotify/callback")
async def spotify_callback(request: Request):
    """
    Androidアプリから送られてきた認証コードを取得し、アクセストークンに交換する。
    """
    try:
        data = await request.json()
        auth_code = data.get("code")

        if not auth_code:
            raise HTTPException(status_code=400, detail="Authorization code not found")

        # 認証コードをアクセストークンに交換する
        token_url = "https://accounts.spotify.com/api/token"
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": SPOTIFY_REDIRECT_URI,
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET,
        }

        response = requests.post(token_url, data=token_data)
        response.raise_for_status()  # エラーレスポンスをチェック
        token_info = response.json()

        if "error" in token_info:
            raise HTTPException(status_code=400, detail=token_info["error"])

        # 取得したトークンをユーザー情報と紐付けてデータベースに保存する
        access_token = token_info["access_token"]
        refresh_token = token_info["refresh_token"]
        expires_in = token_info["expires_in"]

        # TODO: ここで access_token と refresh_token をDBに保存する処理
        # 例: save_tokens_to_db(user_id, access_token, refresh_token)

        # これでバックエンドはユーザーのプレイリストを取得できる
        playlists = get_user_playlists(access_token)

        return {"status": "success", "playlists": playlists}

    except requests.exceptions.HTTPError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": str(e)})
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


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