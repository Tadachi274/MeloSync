# Installation

## languages

Some tools for development needs runtime for programming language.  
These tools only run in our local computers and don't in a production server.

Install Go.  
https://go.dev/doc/install

## tools

First, install [Task](https://taskfile.dev). It is a simple task runner.  
This will help define utility commands.

```bash
npm install -g @go-task/cli
```

You can install other tools using task. The `install-dev-tools` command installs all other tools.

```bash
task install-dev-tools
```

This will install PostgreSQL and other development dependencies.

---

# Development Environment Setup

## 1. Install Docker Desktop

Download and install Docker Desktop from the official site:  
https://www.docker.com/products/docker-desktop/  
Make sure it is running before the next steps.

## 2. Start containers for database and services

```bash
task compose-up
```

This will start the required services (e.g., PostgreSQL) inside Docker.

## 3. Apply database migrations

```bash
task local-migrate-up
```

This will create the necessary tables in the database.

## 4. Create `.env` file in project root (`Melosync/.env`)

```env
SOUNDSTAT_API_KEY=your_soundstat_api_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=your_redirect_uri
SPOTIFY_USERNAME=your_spotify_username

DB_USER=user
DB_PASSWORD=password
DB_NAME=devdb
DB_HOST=localhost
DB_PORT=5433

LOCAL_DB_URL=postgres://user:password@localhost:5433/devdb?sslmode=disable

JWT_SECRET_KEY=your_jwt_secret
FERNET_KEY=your_fernet_key
OPENAI_API_KEY=your_openai_api_key
```

** front_server/app/src/main/java/com/example/com/melosync/ui/auth内のLoginScreen.kt内のclientIdとredirectUriも適宜変える必要あり(悪の設計)**

** front_server/app/src/main/java/com/example/com/melosyncのApiClient内のbaseUrlを自身のWifiの番号にする必要あり **

** SpotifyViewModel.ktの_jwtの初期値も変える必要あり,jwtを正しく更新できていない（悪設計）**

## 5. Install Python dependencies

```bash
cd backend_server
pip install -r requirements.txt
```

---

# Run Servers

Use the following tasks to run each service locally:

| Task command              | Description                                        | Port  |
|---------------------------|----------------------------------------------------|--------|
| `task run-auth-server`    | JWT issuance, Spotify auth, save to DB             | 8000   |
| `task run-spotify-server` | Fetch playlists and track data from Spotify        | 8003   |
| `task run-AI-server`      | AI model service for playlist generation           | 8004   |
| `task run-GPT-server`     | GPT-based emotion estimation                       | 5000   |

---

# How to Use

1. Start `task run-auth-server` and authenticate via your client app.  
   → This will issue a JWT and store user and playlist info in the database.

2. Use `task run-spotify-server` to fetch detailed Spotify playlist and track data.

3. Use `task run-AI-server` to classify music or generate playlists using AI models.

4. Use `task run-GPT-server` to estimate emotions from input text and integrate the result into your music recommendation flow.

Make sure all environment variables are correctly set up in `.env`, and all services are running when testing the application.

---

# MeloSync 機能紹介

以下にアプリの機能説明図を掲載します。

## 機能①: ログインとSpotify認証
![機能1](./Screenshot_1.png)

## 機能②: プレイリスト作成
![機能2](./Screenshot_2.png)

## 機能③: 感情リクエスト〜音楽再生
![機能3](./Screenshot_3.png)
