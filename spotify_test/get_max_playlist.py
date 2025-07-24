import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
print("DEBUG SPOTIPY_CLIENT_ID =", SPOTIPY_CLIENT_ID)  # Debug print to check if the variable is loaded
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')
SPOTIPY_USERNAME = os.getenv('SPOTIPY_USERNAME')
if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET or not SPOTIPY_REDIRECT_URI:
    raise ValueError("Please set the SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, and SPOTIPY_REDIRECT_URI environment variables.")


# Set up the Spotify API client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope="playlist-modify-public playlist-read-private user-library-read user-read-email user-read-private"))

def get_max_playlist_information():
    """
    指定されたユーザーのitem数が最大のプレイリストのIDを取得します。
    """
    # ユーザーのプレイリストを取得
    playlists = sp.current_user_playlists(limit=50, offset=0)
    for pl in playlists['items']:
        print(pl['name'], pl['id'])
    
    # プレイリストをフィルタリング
    max_count = 0
    for pl in playlists['items']:
        name = pl['name']
        pid = pl['id']
        # メタデータとして返ってくる tracks.total をそのまま使う
        count = pl['tracks']['total']

        if count > max_count:
            max_count = count
            max_playlist = {
                    'name': name,
                    'id': pid,
                    'count': count
                }
    
    # item数が最大のIDを返す
    return max_playlist

if __name__ == '__main__':
    username = SPOTIPY_USERNAME  # ユーザー名を指定
    max_playlist = get_max_playlist_information(username)
    
    if max_playlist:
        print(f"item数が最大のプレイリスト{max_playlist['name']}のID: {max_playlist['id']}")
    else:
        print("item数が最大のプレイリストが見つかりませんでした。")