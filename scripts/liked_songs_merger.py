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

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.main import *
from scripts.colors import green, red, yellow, blue, clear, cyan
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
    print(f"{yellow}These songs will be added in reverse chronological order (newest first){clear}")
    
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
    print(f"{green}=== Spotify Liked Songs to Playlist Merger ==={clear}")
    print("This tool will help you add songs from your Liked Songs to another playlist")
    print("in reverse chronological order (newest songs first)\n")
    
    # Start local server and obtain a valid access token (refresh if possible)
    localServer.start_server(quiet=quiet)
    if not quiet:
        print(f"{yellow}Authenticating with Spotify...{clear}")
    access_token = get_or_refresh_access_token(interactive=True)
    
    user = get_current_user(access_token)
    if user and 'display_name' in user:
        print(f"{green}Logged in as: {user['display_name']}{clear}")
    else:
        print(f"{red}Failed to retrieve user info{clear}")
        return
    
    # Step 1: Get liked songs (ordered oldest to newest)
    print(f"\n{yellow}Fetching your liked songs...{clear}")
    liked_songs = get_liked_songs_ordered(access_token)
    
    if not liked_songs:
        print(f"{red}No liked songs found{clear}")
        return
    
    print(f"{green}Found {len(liked_songs)} liked songs{clear}")
    
    # Step 2: Get playlists and let user select target
    print(f"\n{yellow}Fetching your playlists...{clear}")
    playlists = getPlaylists(access_token)
    
    if not playlists or 'items' not in playlists:
        print(f"{red}No playlists found{clear}")
        return
    
    # Display playlists and get selection
    target_playlist = selectPlaylistInteractively(playlists)
    
    if not target_playlist:
        print(f"{red}No playlist selected{clear}")
        return
    
    target_playlist_id = target_playlist['id']
    target_playlist_name = target_playlist['name']
    
    print(f"\n{green}Selected playlist: {target_playlist_name}{clear}")
    
    # Step 3: Get songs from target playlist
    print(f"{yellow}Fetching songs from target playlist...{clear}")
    target_songs = get_target_playlist_songs(access_token, target_playlist_id)
    
    if target_songs is None:
        print(f"{red}Failed to fetch target playlist songs{clear}")
        return
    
    print(f"{green}Found {len(target_songs)} songs in target playlist{clear}")
    
    # Step 4: Find missing songs
    missing_songs = find_missing_songs(liked_songs, target_songs)
    
    if not missing_songs:
        print(f"{green}All liked songs are already in the target playlist!{clear}")
        return
    
    print(f"\n{green}Found {len(missing_songs)} songs to add{clear}")
    
    # Step 5: Display missing songs (in reverse order - newest first)
    missing_reversed = list(reversed(missing_songs))
    display_song_list(missing_reversed, f"Songs to add to '{target_playlist_name}' (newest first)")
    
    # Step 6: Confirm addition
    if not confirm_addition(missing_songs, target_playlist_name):
        print(f"{yellow}Operation cancelled by user{clear}")
        return
    
    # Step 7: Add songs in reverse order (newest first)
    track_uris = [song['uri'] for song in missing_reversed]
    
    print(f"\n{yellow}Adding songs to playlist...{clear}")
    success = addSongsToPlaylist(access_token, target_playlist_id, track_uris)
    
    if success:
        print(f"{green}Successfully added {len(missing_songs)} songs to '{target_playlist_name}'{clear}")
        print(f"{green}Songs added in reverse chronological order (newest first){clear}")
    else:
        print(f"{red}Failed to add songs to playlist{clear}")

if __name__ == "__main__":
    main()
