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
SCOPE = 'playlist-read-private playlist-modify-private playlist-modify-public'
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




if __name__ == '__main__':
    localServer.start_server()
    code = get_auth_code_via_browser()
    print("\033[32mAuth code received.\033[0;0m")

    token = get_access_token(code)
    user = get_current_user(token)
    if user and 'display_name' in user:
        print(f"Logged in as: {user['display_name']}")
    else:
        print("Failed to retrieve user info.")
    playlistData: dict | None = getPlaylists(token)
    if playlistData == None:
        raise ValueError("PlaylistData should not be None")
    
    print("\n\n")
    names = {}
    for i in playlistData["items"]: names[i["name"]] = i["id"]
    for i in names:
        print(c.black + names[i], c.clear + i)


    tracks = getPlaylistItems(token, "20pOuuPJukrQ1SpYi8hlaD")
    if isinstance(tracks, dict):
        for i in tracks:
            if i != "items":
                print(c.cyan, i, c.clear)
                if not isinstance(tracks[i], (int, str)) and tracks[i] is not None:
                    for n in tracks[i]:
                        print(n)
                elif isinstance(tracks[i], str):
                    print(tracks[i])
                else:
                    print(tracks[i])
            if i == "items":
                base = tracks["items"]
                for b in base:
                    for n in b:
                        if type(b[n]) is dict:
                            print(c.blue + n)
                            for x in b[n]:
                                print(c.magenta + x, c.clear + str( b[n][x]))
                            print(c.clear, end="")
                        else:print(c.blue + n, c.clear +str(b[n]))
                    print("\n")