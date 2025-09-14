# main.py

import os
import time
import requests
import webbrowser
from urllib.parse import urlencode
from dotenv import load_dotenv
import localServer
import helpful_fuctions as h
import colors as c

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:8888/callback')
REDIRECT_URI = 'http://localhost:8888/callback'
SCOPE = 'playlist-read-private playlist-modify-private playlist-modify-public user-library-read'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1'

def get_access_token(auth_code):
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code != 200:
        print(f"\033[31mFailed to get access token: {response.status_code}\033[0;0m")
        print(response.json())
        exit(1)
    return response.json()['access_token']

def get_current_user(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f"{API_BASE_URL}/me", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None



def get_auth_code_via_browser():
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE
    }
    url = f"{AUTH_URL}?{urlencode(params)}"
    print(f"Opening browser for Spotify authentication...\n→ {url}")
    webbrowser.open(url)

    # Warten bis flask_redirect_server.auth_code gesetzt ist
    print("Waiting for auth code from redirect...")
    for _ in range(60):  # Timeout nach 60 Sekunden
        code = localServer.get_auth_code()
        if code:
            return code
        time.sleep(1)

    print("\033[31mTimeout: No auth code received.\033[0;0m")
    exit(1)

def getPlaylists(accessToken):
    headers = {'Authorization': f'Bearer {accessToken}'}
    response = requests.get(f"{API_BASE_URL}/me/playlists", headers=headers)
    if response.status_code == 200:

        return response.json()
    else:
        print("\033[31mFailed to recieve playlist data. Token", response.status_code)
        return None

def printPlaylistData(data):
    if data is not None and isinstance(data, dict):
        print(data.keys())
        for i in data["items"]:
            print("\n\n", "#"*50, "\n\n")
            keys = i.keys()
            for x in keys:
                t = type(i[x])
                if t == str or t == bool or i[x] is None:
                    print(h.lenformat(x, 15), ":", i[x])
                elif t == dict:
                    print(h.lenformat(x, 15), ":")

                    tmp = i[x].keys()
                    for c, n in enumerate(tmp):
                        print(" " * 15, n)
                elif t == list:
                    print(h.lenformat(x, 15), ":")
                    for n in i[x]:
                        print(" " * 15, n)
                else:
                    print("\033[35m" + str(h.lenformat("<REDACTED>", 15)) + str(i[x]) + "\033[0;0m")

def getPlaylistItems(accessToken, UPLID):
    headers = {'Authorization': f'Bearer {accessToken}'}
    response = requests.get(f"{API_BASE_URL}/playlists/{UPLID}/tracks", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:

        print(c.red + f"Error fetching playlist items for playlist {UPLID} - Token {response.status_code}" +c.clear)
        return None

def getLikedSongDetails(access_token):
    """Return a list of liked songs with details (name, uri, artists, added_at)."""
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f"{API_BASE_URL}/me/tracks"
    songs = []
    params = {'limit': 50, 'offset': 0}
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(c.red + f"Error fetching liked songs: {response.status_code}" + c.clear)
            break
        data = response.json()
        for item in data.get('items', []):
            track = item.get('track')
            if not track:
                continue
            songs.append({
                'name': track.get('name'),
                'uri': track.get('uri'),
                'artists': ', '.join([artist['name'] for artist in track.get('artists', [])]),
                'added_at': item.get('added_at', ''),
            })
        if data.get('next'):
            params['offset'] += params['limit']
        else:
            break
    return songs

def getPlaylistItemsDetailed(access_token, playlist_id):
    """Return a list of track dicts with details for a playlist."""
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f"{API_BASE_URL}/playlists/{playlist_id}/tracks"
    tracks = []
    params = {'limit': 100, 'offset': 0}
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(c.red + f"Error fetching playlist items: {response.status_code}" + c.clear)
            break
        data = response.json()
        for item in data.get('items', []):
            track = item.get('track')
            if not track:
                continue
            tracks.append({
                'name': track.get('name'),
                'uri': track.get('uri'),
                'artists': ', '.join([artist['name'] for artist in track.get('artists', [])]),
                'added_at': item.get('added_at', ''),
            })
        if data.get('next'):
            params['offset'] += params['limit']
        else:
            break
    return tracks

def selectPlaylistInteractively(playlists):
    """Prompt user to select a playlist from a list."""
    items = playlists.get('items', [])
    if not items:
        print(c.red + "No playlists available." + c.clear)
        return None
    print(c.green + "\nAvailable Playlists:" + c.clear)
    for idx, pl in enumerate(items, 1):
        print(f"{idx:2d}. {c.blue}{pl['name']}{c.clear} ({c.cyan}{pl['id']}{c.clear})")
    while True:
        try:
            choice = int(input(c.yellow + "Select playlist number: " + c.clear))
            if 1 <= choice <= len(items):
                return items[choice-1]
        except Exception:
            pass
        print(c.red + "Invalid selection. Try again." + c.clear)

def addSongsToPlaylist(access_token, playlist_id, track_uris):
    """Add a list of track URIs to a playlist. Returns True if successful."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = f"{API_BASE_URL}/playlists/{playlist_id}/tracks"
    # Spotify API allows max 100 tracks per request
    for i in range(0, len(track_uris), 100):
        uris = track_uris[i:i+100]
        payload = {'uris': uris}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code not in (200, 201):
            print(c.red + f"Failed to add tracks: {response.status_code}" + c.clear)
            return False
    return True
if __name__ == '__main__':
    # Unified entry point: run the merger as described in the README
    from liked_songs_merger import main as merger_main
    merger_main()