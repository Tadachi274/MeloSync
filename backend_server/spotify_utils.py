# spotify_utils.py

import os
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

# --- 配置加载 ---
# 为了让这个工具模块在任何地方都能正确加载配置，我们明确指定.env文件的路径
# 假设.env文件在项目根目录
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') 
# 如果.env文件和这个utils文件在同一目录，可以使用下面的路径
# dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

def get_spotify_access_token() -> str:
    """
    Spotify APIのアクセストークンを取得する (Client Credentials Flow)
    """
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set.")
        
    auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
    access_token = auth_manager.get_access_token(as_dict=False)
    return access_token

def get_playlist_tracks(playlist_id: str, access_token: str) -> list:
    """
    获取指定Spotify播放列表中的所有曲目，自动处理分页以获取超过100首的歌曲。

    Args:
        playlist_id (str): Spotify播放列表的ID。
        access_token (str): 已获取的Spotify API访问令牌。

    Returns:
        list: 包含所有曲目项目的列表。
    """
    # 使用获取到的访问令牌初始化spotipy客户端
    sp = spotipy.Spotify(auth=access_token)
    
    # 初始化一个空列表来存储所有曲目
    all_tracks = []
    
    # 第一次请求，获取第一页的100首歌曲
    try:
        response = sp.playlist_items(playlist_id, limit=100)
    except Exception as e:
        print(f"Error fetching initial playlist tracks: {e}")
        return []

    # 将第一页的曲目添加到列表中
    all_tracks.extend(response['items'])
    
    # 检查返回结果中是否有'next'字段，如果有，说明还有下一页
    while response['next']:
        try:
            # sp.next() 会自动请求'next'字段中的URL
            response = sp.next(response)
            # 将新一页的曲目追加到列表中
            all_tracks.extend(response['items'])
        except Exception as e:
            print(f"Error fetching next page of tracks: {e}")
            # 如果在获取某一页时出错，则中断循环并返回已获取的部分
            break
            
    return all_tracks
