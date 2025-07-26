# recreate_playlist.py
import os
import psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import get_max_playlist
from cryptography.fernet import Fernet

load_dotenv()

# Spotify クライアント情報
CLIENT_ID     = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
REDIRECT_URI  = os.getenv('SPOTIPY_REDIRECT_URI')
USERNAME      = os.getenv('SPOTIPY_USERNAME')

# DB 接続情報
DB_HOST     = os.getenv('DB_HOST')
DB_PORT     = 5433
DB_NAME     = os.getenv('DB_NAME')
DB_USER     = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

#鍵の読み込み
FERNET_KEY = os.getenv('FERNET_KEY')

print(f"DB_HOST={DB_HOST}  DB_PORT={DB_PORT}  DB_USER={DB_USER}  DB_NAME={DB_NAME}")

def fetch_latest_token():
    """PostgreSQL から最新のトークンを取得"""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT access_token, refresh_token, expires_at
          FROM spotify_tokens
        ORDER BY expires_at DESC
        LIMIT 1
    """)
    access_token, refresh_token, expires_at = cur.fetchone()
    key= FERNET_KEY.encode('utf-8')
    access_token = decrypt(key, access_token)
    refresh_token = decrypt(key, refresh_token)
    print(f"Fetched token: {access_token}, expires at: {expires_at}")
    cur.close()
    conn.close()
    return access_token, refresh_token, expires_at

def decrypt(key: str, data: str):
    fernet = Fernet(bytes(key, 'utf-8'))
    decrypted_pass = fernet.decrypt(bytes(data, 'utf-8'))
    print(decrypted_pass)
    print(decrypted_pass.decode('utf-8'))
    return decrypted_pass.decode('utf-8')

def get_spotify_client():
    """DB から取得したトークンを使って Spotipy クライアントを返す"""
    access_token, refresh_token, expires_at = fetch_latest_token()

    now_ts = datetime.now(timezone.utc).timestamp()
    # トークン期限切れならリフレッシュ
    if now_ts >= expires_at:
        oauth = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope="playlist-modify-public playlist-read-private user-library-read user-read-email user-read-private"
        )
        new_token = oauth.refresh_access_token(refresh_token)
        access_token  = new_token['access_token']
        refresh_token = new_token.get('refresh_token', refresh_token)
        # （任意）ここで DB に新しい expires_at / refresh_token を UPDATE しておくと次回以降もスムーズ

    # Spotipy に直接アクセストークンを渡してインスタンス化
    return spotipy.Spotify(auth=access_token)

def filter_tracks(tracks):
    return [t for t in tracks if t['track']['popularity'] > 50]

def create_or_update_playlist(new_playlist_name, max_playlist_id):
    sp = get_spotify_client()
    user_id = sp.me()['id']

    # プレイリスト検索／作成
    new_id = None
    for pl in sp.current_user_playlists()['items']:
        if pl['name'] == new_playlist_name:
            new_id = pl['id']
            break
    if not new_id:
        new_id = sp.user_playlist_create(user_id, new_playlist_name, public=True)['id']

    # 既存トラック取得
    existing_uris = []
    results = sp.playlist_items(new_id)
    existing_uris += [item['track']['uri'] for item in results['items']]
    while results['next']:
        results = sp.next(results)
        existing_uris += [item['track']['uri'] for item in results['items']]

    # お気に入りプレイリストのトラック取得
    max_tracks = []
    results = sp.playlist_items(max_playlist_id)
    max_tracks += results['items']
    while results['next']:
        results = sp.next(results)
        max_tracks += results['items']

    # フィルタリング + 追加済み除外
    to_add = []
    for item in max_tracks:
        uri = item['track']['uri']
        if uri not in existing_uris and uri in [t['track']['uri'] for t in filter_tracks([item])]:
            to_add.append(uri)

    # 追加（100 件ずつ）
    for i in range(0, len(to_add), 100):
        sp.playlist_add_items(new_id, to_add[i:i+100])

    print(f"Added {len(to_add)} tracks to “{new_playlist_name}”")
    print(f"https://open.spotify.com/playlist/{new_id}")

if __name__ == '__main__':
    NEW_NAME = 'Filtered Playlist'
    #MAX_PL_ID = get_max_playlist.get_max_playlist_information(USERNAME)['id']  # 例：最大アイテム数のプレイリストIDを取得
    MAX_PL_ID = '3B9bBOeWrobjNookz6h3cl'  # 例：お気に入りプレイリストID
    create_or_update_playlist(NEW_NAME, MAX_PL_ID)

