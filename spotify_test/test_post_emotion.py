import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()
# Replace with your actual API endpoint
API_ENDPOINT = "http://localhost:8003/api/spotify/emotion-playlist-tracks"  # FastAPIのデフォルト
API_ENDPOINT_PLAYLST = "http://localhost:8003/api/spotify/user-playlists"

# Replace with your actual JWT, before_emotion, and after_emotion values
JWT=os.getenv("JWT")
BEFORE_EMOTION = "Happy"
AFTER_EMOTION = "Happy"

headers = {
    "Authorization": f"Bearer {JWT}"
}

params = {
    "before_emotion": BEFORE_EMOTION,
    "after_emotion": AFTER_EMOTION,
    "chosen_playlist": ["4tSxemnhYNd6Tr43WE5X00", "3TrXthQhsqXFn02bvDxa3e"]  # Replace with the desired playlist names
}

try:
    response_playlst = requests.post(API_ENDPOINT_PLAYLST, headers=headers)
    response_playlst.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

    print("Status Code:", response_playlst.status_code)
    print("Response Playlists JSON:", response_playlst.json())
except requests.exceptions.RequestException as e:
    print("Request PlayList failed:", e)
    print(response_playlst.status_code, response_playlst.text)

try:
    response = requests.post(API_ENDPOINT, headers=headers, params=params)
    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

    print("Status Code:", response.status_code)
    print("Response Track JSON:", response.json())

except requests.exceptions.RequestException as e:
    print("Request failed:", e)
    print(response.status_code, response.text)
