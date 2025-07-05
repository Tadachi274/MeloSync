import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')
SPOTIPY_USERNAME = os.getenv('SPOTIPY_USERNAME')




# Set up the Spotify API client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope="playlist-modify-public playlist-read-private user-library-read user-read-email user-read-private"))

def filter_tracks(tracks):
    # 例：人気度が50より高いトラックのみを含める
    # Example filter: Only include tracks with popularity > 50
    filtered_tracks = [track for track in tracks if track['track']['popularity'] > 50]
    return filtered_tracks

def create_filtered_playlist(original_playlist_id, new_playlist_name):
    """
    Copies tracks from an original playlist to a new playlist, applying a filter.
    """
    # Get tracks from the original playlist
    results = sp.playlist_items(original_playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    # Filter the tracks
    filtered_tracks = filter_tracks(tracks)

    # Create a new playlist
    user_id = sp.me()['id']
    new_playlist = sp.user_playlist_create(user_id, new_playlist_name, public=True)
    new_playlist_id = new_playlist['id']

    # Add tracks to the new playlist (Spotify API requires track URIs)
    track_uris = [track['track']['uri'] for track in filtered_tracks]

    # Spotify API only allows adding 100 tracks at a time
    for i in range(0, len(track_uris), 100):
        sp.playlist_add_items(new_playlist_id, track_uris[i:i+100])

    print(f"New playlist created: {new_playlist['external_urls']['spotify']}")

if __name__ == '__main__':
    original_playlist_id = '3B9bBOeWrobjNookz6h3cl'  # Replace with the playlist ID you want to copy from
    new_playlist_name = 'Filtered Playlist'  # Replace with the desired name for the new playlist
    #create_filtered_playlist(original_playlist_id, new_playlist_name)
