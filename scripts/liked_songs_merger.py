#!/usr/bin/env python3
"""
Liked Songs to Playlist Merger
Takes songs from user's liked playlist and adds them to a selected playlist
in reverse chronological order (newest first)
"""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any
from helpful_fuctions import clearTerminal, customProgressBar

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.main import *
from scripts.colors import *
import localServer

def get_liked_songs_ordered(access_token: str) -> List[Dict[str, Any]]:
    """Get liked songs ordered by date added (oldest first)"""
    liked_songs = getLikedSongDetails(access_token)
    if not liked_songs:
        return []
    
    # Sort by added_at date (oldest first)
    liked_songs.sort(key=lambda x: x['added_at'])
    return liked_songs

def get_target_playlist_songs(access_token: str, playlist_id: str) -> List[Dict[str, Any]]:
    """Get all songs from target playlist"""
    return getPlaylistItemsDetailed(access_token, playlist_id)

def find_missing_songs(liked_songs: List[Dict], target_songs: List[Dict]) -> List[Dict]:
    """Find songs in liked but not in target playlist"""
    target_uris = {song['uri'] for song in target_songs}
    missing_songs = []
    
    for song in liked_songs:
        if song['uri'] not in target_uris:
            missing_songs.append(song)
    
    return missing_songs

def display_song_list(songs: List[Dict], title: str) -> None:
    """Display a list of songs in a formatted way"""
    print(f"\n{green}{title}{clear}")
    print("-" * 80)
    
    for idx, song in enumerate(songs, 1):
        artists = song['artists']
        name = song['name']
        added_date = datetime.fromisoformat(song['added_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
        print(f"{idx:3d}. {blue}{name}{clear} - {cyan}{artists}{clear} ({yellow}{added_date}{clear})")

def confirm_addition(missing_songs: List[Dict], target_playlist_name: str) -> bool:
    """Ask user for confirmation before adding songs"""
    print(f"\n{green}Ready to add {len(missing_songs)} songs to '{target_playlist_name}'{clear}")
    print(f"{blue}These songs will be added in reverse chronological order (newest first){clear}")
    
    while True:
        choice = input(f"\n{green}Proceed? (y/n): {clear}").lower().strip()
        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False
        else:
            print(f"{red}Please enter 'y' or 'n'{clear}")



def main(quiet: bool = False):
    """Main function to orchestrate the liked songs merging process"""
    clearTerminal()
    print(darkgreen + """
 $$$$$$\                       $$\     $$\     $$\      $$\                                                   
$$  __$$\                      $$ |    \__|    $$$\    $$$ |                                                  
$$ /  \__| $$$$$$\   $$$$$$\ $$$$$$\   $$\ $$\ $$$$\  $$$$ | $$$$$$\   $$$$$$\   $$$$$$\   $$$$$$\   $$$$$$\  
\$$$$$$\  $$  __$$\ $$  __$$\\\_$$  _|  $$ |\__|$$\$$\$$ $$ |$$  __$$\ $$  __$$\ $$  __$$\ $$  __$$\ $$  __$$\ 
 \____$$\ $$ /  $$ |$$ /  $$ | $$ |    $$ |    $$ \$$$  $$ |$$$$$$$$ |$$ |  \__|$$ /  $$ |$$$$$$$$ |$$ |  \__|
$$\   $$ |$$ |  $$ |$$ |  $$ | $$ |$$\ $$ |$$\ $$ |\$  /$$ |$$   ____|$$ |      $$ |  $$ |$$   ____|$$ |      
\$$$$$$  |$$$$$$$  |\$$$$$$  | \$$$$  |$$ |\__|$$ | \_/ $$ |\$$$$$$$\ $$ |      \$$$$$$$ |\$$$$$$$\ $$ |      
 \______/ $$  ____/  \______/   \____/ \__|    \__|     \__| \_______|\__|       \____$$ | \_______|\__|      
          $$ |                                                                  $$\   $$ |                    
          $$ |                                                                  \$$$$$$  |                    
          \__|                                                                   \______/""" + clear)
    # Start local server and obtain a valid access token (refresh if possible)
    localServer.start_server(quiet=quiet)
    if not quiet:
        print(f"{blue}Authenticating with Spotify...{clear}")
    access_token = get_or_refresh_access_token(interactive=True)

    user = get_current_user(access_token)
    if user and 'display_name' in user:
        print(f"{darkgreen}Logged in as: {user['display_name']}{clear}")
    else:
        print(f"{red}Failed to retrieve user info{clear}")
        return

    # Step 1: Get playlists and let user select target
    print(f"\n{blue}Fetching your playlists...{clear}")
    playlists = getPlaylists(access_token)
    if not playlists or 'items' not in playlists:
        print(f"{red}No playlists found{clear}")
        return

    # Apply progress bar to the items in the playlists dictionary
    playlists['items'] = list(customProgressBar(playlists['items'], total=len(playlists['items'])))

    print(f"{green}OK:{clear} Found {len(playlists['items'])}.")

    # Display playlists and get selection
    target_playlist = selectPlaylistInteractively(playlists)

    if not target_playlist: print(f"{red}No playlist selected{clear}") ; return

    target_playlist_id = target_playlist['id']
    target_playlist_name = target_playlist['name']

    # Apply progress bar to liked songs
    print(f"\n{blue}Fetching your liked songs...{clear}")

    # Step 2: Get liked songs (ordered oldest to newest)
    liked_songs = get_liked_songs_ordered(access_token)

    if not liked_songs:
        print(f"{red}No liked songs found{clear}")
        return
    liked_songs = list(customProgressBar(liked_songs, total=len(liked_songs)))
    print(f"{green}OK:{clear} Found {len(liked_songs)}.")

    # Step 3: Get songs from target playlist
    print(f"\n{blue}Fetching songs from target playlist...{clear}")
    # Fetch songs and show progress as they are loaded
    target_songs_raw = get_target_playlist_songs(access_token, target_playlist_id)

    if not target_songs_raw:
        print(f"{red}Failed to fetch target playlist songs{clear}")
        return

    # Use progress bar directly without appending to a new list
    target_songs = list(customProgressBar(target_songs_raw, total=len(target_songs_raw)))
    print(f"{green}OK:{clear} Found {len(target_songs)}.")

    # Step 4: Find missing songs
    missing_songs = find_missing_songs(liked_songs, target_songs)

    if not missing_songs:
        print(f"\n{darkgreen}All liked songs are already in the target playlist!{clear}")
        return

    print(f"\n{green}OK:{clear} Found {len(missing_songs)} to add.")

    # Step 5: Display missing songs (in reverse order - newest first)
    missing_reversed = list(reversed(missing_songs))
    display_song_list(missing_reversed, f"Songs to add to '{target_playlist_name}' (newest first)")

    # Step 6: Confirm addition
    if not confirm_addition(missing_songs, target_playlist_name):
        print(f"{darkred}Operation cancelled by user{clear}")
        return

    # Step 7: Add songs in reverse order (newest first)
    track_uris = [song['uri'] for song in missing_reversed]

    print(f"\nAdding songs to playlist...")
    success = addSongsToPlaylist(access_token, target_playlist_id, track_uris)

    if success:
        print(f"{darkgreen}OK:{clear} Added {len(missing_songs)} songs to '{cyan}{target_playlist_name}{clear}'")
    else:
        print(f"{red}Failed to add songs to playlist{clear}")

if __name__ == "__main__":
    main()
