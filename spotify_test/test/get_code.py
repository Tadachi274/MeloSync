from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

app = FastAPI()

# ユーザーを Spotify 認証ページにリダイレクト
@app.get("/login")
def login():
    client_id = 'ced2ee375b444183a40d0a95de22d132'
    redirect_uri = 'http://127.0.0.1:8000/melosync/callback'
    scope = "playlist-modify-public playlist-read-private"
    state = "random_state_string"
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={client_id}"
        "&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope.replace(' ', '%20')}"
        f"&state={state}"
    )
    return RedirectResponse(auth_url)

# Spotify からリダイレクトされてくるエンドポイント
@app.get("/callback")
async def callback(request: Request):
    error = request.query_params.get("error")
    if error:
        return {"error": error}
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    # ここで state を検証するとより安全です

    # 次に、取得した code を使ってアクセストークンをリクエスト
    return {"authorization_code": code}
