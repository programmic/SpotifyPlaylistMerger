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
import json
import tempfile
from pathlib import Path

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
    token_data = response.json()
    # token_data contains access_token, token_type, expires_in, refresh_token (maybe), scope
    save_tokens_from_response(token_data)
    return token_data.get('access_token')


def refresh_access_token(refresh_token):
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code != 200:
        return None
    token_data = response.json()
    # Spotify may not return a new refresh_token on refresh; keep the old one if missing
    if 'refresh_token' not in token_data:
        token_data['refresh_token'] = refresh_token
    save_tokens_from_response(token_data)
    return token_data.get('access_token')


# Simple file-based token storage (stored in user home). For a more secure
# solution use the OS keyring via the `keyring` package.
TOKEN_FILE = str(Path.home() / '.spotify_tokens.json')


def save_tokens_from_response(token_response: dict):
    # token_response expected fields: access_token, expires_in, refresh_token
    now = int(time.time())
    data = {}
    data['access_token'] = token_response.get('access_token')
    expires_in = token_response.get('expires_in')
    if expires_in:
        data['expires_at'] = now + int(expires_in)
    else:
        data['expires_at'] = now + 3600
    if 'refresh_token' in token_response and token_response.get('refresh_token'):
        data['refresh_token'] = token_response.get('refresh_token')
    else:
        # Preserve existing refresh_token if present
        existing = load_tokens()
        if existing and existing.get('refresh_token'):
            data['refresh_token'] = existing.get('refresh_token')

    try:
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception:
        pass


def load_tokens():
    try:
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def token_valid(tokens: dict) -> bool:
    if not tokens:
        return False
    access = tokens.get('access_token')
    expires_at = tokens.get('expires_at', 0)
    if not access:
        return False
    # consider token invalid if expiring within 30 seconds
    return int(time.time()) + 30 < int(expires_at)


def get_or_refresh_access_token(interactive=True):
    """Return a valid access token. If possible, refresh using stored refresh
    token. If interactive=True and no valid token, perform full auth flow.
    """
    tokens = load_tokens()
    if token_valid(tokens):
        return tokens.get('access_token')

    # Try to refresh
    if tokens and tokens.get('refresh_token'):
        new_access = refresh_access_token(tokens.get('refresh_token'))
        if new_access:
            return new_access

    if not interactive:
        return None

    # Do interactive auth flow
    # Caller should have started localServer.start_server() before calling this
    code = get_auth_code_via_browser()
    if not code:
        return None
    return get_access_token(code)

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
    auth_url = f"{AUTH_URL}?{urlencode(params)}"

    # Create a small launcher HTML that opens the auth URL as a popup. This
    # improves the ability of the popup to close itself after redirect.
    launcher_html = f'''<!doctype html>
<html><head><meta charset="utf-8"><title>Spotify Auth</title></head>
<body>
  <p>Opening authentication window...</p>
  <script>
    var popup = window.open("{auth_url}", "spotify_auth_popup", "width=900,height=800");
    // Listen for message from the popup (the popup will postMessage on success)
    window.addEventListener('message', function(evt){{
      try{{
        if(evt.data && evt.data.type === 'spotify_auth'){{
          // Optionally notify user and close
          window.close();
        }}
      }}catch(e){{}}
    }}, false);
  </script>
</body></html>'''

    # Write to a temporary file and open it with the system default browser
    try:
        fd, path = tempfile.mkstemp(prefix='spotify_auth_', suffix='.html')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(launcher_html)
        file_url = Path(path).as_uri()
        print(f"Opening browser for Spotify authentication...\n→ {auth_url}")
        webbrowser.open(file_url)
    except Exception:
        # Fallback: open the auth URL directly
        webbrowser.open(auth_url)

    # Wait for the redirect to set the auth code in localServer
    print("Waiting for auth code from redirect...")
    for _ in range(120):  # Timeout after 120 seconds
        code = localServer.get_auth_code()
        if code:
            return code
        time.sleep(1)

    print("\033[31mTimeout: No auth code received.\033[0;0m")
    return None

def getPlaylists(accessToken):
    """Fetch all playlists for the current user and return only those the
    user can edit (playlists they own or collaborative playlists).

    Returns a dict with an 'items' list (to keep compatibility with callers),
    or None on error.
    """
    headers = {'Authorization': f'Bearer {accessToken}'}

    # First get current user id
    user_resp = requests.get(f"{API_BASE_URL}/me", headers=headers)
    if user_resp.status_code != 200:
        print("\033[31mFailed to retrieve current user. Token", user_resp.status_code)
        return None
    user = user_resp.json()
    user_id = user.get('id')

    # Page through /me/playlists to collect all playlists
    items = []
    url = f"{API_BASE_URL}/me/playlists"
    params = {'limit': 50, 'offset': 0}
    while True:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            print("\033[31mFailed to receive playlist data. Token", resp.status_code)
            return None
        data = resp.json()
        page_items = data.get('items', [])
        items.extend(page_items)
        if data.get('next'):
            params['offset'] += params['limit']
        else:
            break

    # Filter to playlists the user can edit: owned by user or collaborative
    editable = []
    for pl in items:
        owner = pl.get('owner', {}) or {}
        owner_id = owner.get('id')
        if owner_id == user_id or pl.get('collaborative'):
            editable.append(pl)

    return {'items': editable}

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