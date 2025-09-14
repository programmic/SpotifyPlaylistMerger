#!/usr/bin/env python3
"""
Enhanced Terminal Menu System for Spotify Liked Songs Merger
Provides comprehensive terminal interface for managing Spotify playlists
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.colors import green, red, yellow, blue, clear, cyan, magenta
from scripts.liked_songs_merger import (
    get_liked_songs_ordered,
    find_missing_songs,
    display_song_list,
    confirm_addition
)
from scripts.main import *
import scripts.localServer as localServer

class TerminalMenu:
    """Enhanced terminal menu system for Spotify playlist operations"""
    
    def __init__(self):
        self.access_token = None
        self.current_user = None
        self.current_menu = "main"
        self.selected_songs = []
        self.source_playlist = None
        self.target_playlist = None
        
    def authenticate(self) -> bool:
        """Handle Spotify authentication"""
        print(f"\n{green}=== Spotify Authentication ==={clear}")
        
        try:
            # Start local server for authentication
            localServer.start_server()
            
            print(f"{yellow}Opening browser for authentication...{clear}")
            auth_code = get_auth_code_via_browser()
            
            if not auth_code:
                print(f"{red}Failed to get authorization code{clear}")
                return False
                
            self.access_token = get_access_token(auth_code)
            
            if not self.access_token:
                print(f"{red}Failed to get access token{clear}")
                return False
                
            self.current_user = get_current_user(self.access_token)
            
            if self.current_user and 'display_name' in self.current_user:
                print(f"{green}Successfully logged in as: {self.current_user['display_name']}{clear}")
                return True
            else:
                print(f"{red}Failed to retrieve user information{clear}")
                return False
                
        except Exception as e:
            print(f"{red}Authentication error: {str(e)}{clear}")
            return False
    
    def display_main_menu(self) -> str:
        """Display main menu options"""
        print(f"\n{green}=== Spotify Liked Songs Merger ==={clear}")
        print(f"{cyan}Logged in as: {self.current_user.get('display_name', 'Unknown')}{clear}")
        print("\n1. Merge Liked Songs to Playlist")
        print("2. View Liked Songs")
        print("3. View Playlists")
        print("4. Create New Playlist from Liked Songs")
        print("5. Backup Liked Songs")
        print("6. Settings")
        print("0. Exit")
        
        while True:
            choice = input(f"\n{yellow}Select option (0-6): {clear}").strip()
            if choice in ['0', '1', '2', '3', '4', '5', '6']:
                return choice
            print(f"{red}Invalid choice. Please select 0-6.{clear}")
    
    def merge_liked_songs(self):
        """Merge liked songs to a selected playlist"""
        if not self.access_token:
            print(f"{red}Please authenticate first{clear}")
            return
            
        print(f"\n{yellow}Fetching liked songs...{clear}")
        liked_songs = get_liked_songs_ordered(self.access_token)
        
        if not liked_songs:
            print(f"{red}No liked songs found{clear}")
            return
            
        print(f"{green}Found {len(liked_songs)} liked songs{clear}")
        
        # Get playlists
        print(f"\n{yellow}Fetching playlists...{clear}")
        playlists = getPlaylists(self.access_token)
        
        if not playlists or 'items' not in playlists:
            print(f"{red}No playlists found{clear}")
            return
            
        # Let user select target playlist
        target_playlist = selectPlaylistInteractively(playlists)
        
        if not target_playlist:
            print(f"{red}No playlist selected{clear}")
            return
            
        # Get target playlist songs
        print(f"\n{yellow}Fetching songs from target playlist...{clear}")
        target_songs = getPlaylistItemsDetailed(self.access_token, target_playlist['id'])
        
        if target_songs is None:
            print(f"{red}Failed to fetch target playlist songs{clear}")
            return
            
        # Find missing songs
        missing_songs = find_missing_songs(liked_songs, target_songs)
        
        if not missing_songs:
            print(f"{green}All liked songs are already in the target playlist!{clear}")
            return
            
        print(f"\n{green}Found {len(missing_songs)} songs to add{clear}")
        
        # Display missing songs (newest first)
        missing_reversed = list(reversed(missing_songs))
        display_song_list(missing_reversed, f"Songs to add to '{target_playlist['name']}'")
        
        # Confirm addition
        if not confirm_addition(missing_songs, target_playlist['name']):
            print(f"{yellow}Operation cancelled{clear}")
            return
            
        # Add songs
        track_uris = [song['uri'] for song in missing_reversed]
        
        print(f"\n{yellow}Adding songs to playlist...{clear}")
        success = addSongsToPlaylist(self.access_token, target_playlist['id'], track_uris)
        
        if success:
            print(f"{green}Successfully added {len(missing_songs)} songs to '{target_playlist['name']}'{clear}")
        else:
            print(f"{red}Failed to add songs to playlist{clear}")
    
    def view_liked_songs(self):
        """Display user's liked songs"""
        if not self.access_token:
            print(f"{red}Please authenticate first{clear}")
            return
            
        print(f"\n{yellow}Fetching liked songs...{clear}")
        liked_songs = getLikedSongDetails(self.access_token)
        
        if not liked_songs:
            print(f"{red}No liked songs found{clear}")
            return
            
        print(f"\n{green}Found {len(liked_songs)} liked songs{clear}")
        
        # Display first 10 songs
        display_count = min(10, len(liked_songs))
        display_song_list(liked_songs[:display_count], f"First {display_count} liked songs")
        
        if len(liked_songs) > display_count:
            print(f"\n{yellow}... and {len(liked_songs) - display_count} more songs{clear}")
    
    def view_playlists(self):
        """Display user's playlists"""
        if not self.access_token:
            print(f"{red}Please authenticate first{clear}")
            return
            
        print(f"\n{yellow}Fetching playlists...{clear}")
        playlists = getPlaylists(self.access_token)
        
        if not playlists or 'items' not in playlists:
            print(f"{red}No playlists found{clear}")
            return
            
        print(f"\n{green}Your Playlists:{clear}")
        print("-" * 60)
        
        for idx, playlist in enumerate(playlists['items'], 1):
            playlist_type = "Collaborative" if playlist.get('collaborative') else "Personal"
            if playlist.get('public'):
                playlist_type = "Public"
                
            print(f"{idx:2d}. {playlist['name']:<30} ({playlist['tracks']['total']:3d} tracks) [{playlist_type}]")
    
    def create_new_playlist(self):
        """Create a new playlist from liked songs"""
        if not self.access_token:
            print(f"{red}Please authenticate first{clear}")
            return
            
        playlist_name = input(f"\n{yellow}Enter new playlist name: {clear}").strip()
        
        if not playlist_name:
            print(f"{red}Playlist name cannot be empty{clear}")
            return
            
        print(f"\n{yellow}Creating playlist '{playlist_name}'...{clear}")
        
        # This would need additional implementation for playlist creation
        print(f"{yellow}Playlist creation functionality coming soon...{clear}")
    
    def backup_liked_songs(self):
        """Backup liked songs to JSON file"""
        if not self.access_token:
            print(f"{red}Please authenticate first{clear}")
            return
            
        print(f"\n{yellow}Fetching liked songs for backup...{clear}")
        liked_songs = getLikedSongDetails(self.access_token)
        
        if not liked_songs:
            print(f"{red}No liked songs found{clear}")
            return
            
        filename = f"liked_songs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(liked_songs, f, indent=2, ensure_ascii=False)
                
            print(f"{green}Backup saved to: {filename}{clear}")
            print(f"{green}Backed up {len(liked_songs)} songs{clear}")
            
        except Exception as e:
            print(f"{red}Error creating backup: {str(e)}{clear}")
    
    def settings_menu(self):
        """Display settings options"""
        print(f"\n{green}=== Settings ==={clear}")
        print("1. Change authentication method")
        print("2. Export settings")
        print("3. Import settings")
        print("4. Reset to defaults")
        print("0. Back to main menu")
        
        choice = input(f"\n{yellow}Select option: {clear}").strip()
        
        if choice == "1":
            print(f"{yellow}Re-authentication...{clear}")
            self.authenticate()
        elif choice == "2":
            print(f"{yellow}Export functionality coming soon...{clear}")
        elif choice == "3":
            print(f"{yellow}Import functionality coming soon...{clear}")
        elif choice == "4":
            print(f"{yellow}Reset functionality coming soon...{clear}")
    
    def run(self):
        """Main application loop"""
        print(f"{green}=== Spotify Liked Songs Merger Terminal ==={clear}")
        
        # Initial authentication
        if not self.authenticate():
            print(f"{red}Failed to authenticate. Exiting...{clear}")
            return
            
        while True:
            choice = self.display_main_menu()
            
            if choice == "0":
                print(f"\n{green}Thank you for using Spotify Liked Songs Merger!{clear}")
                break
            elif choice == "1":
                self.merge_liked_songs()
            elif choice == "2":
                self.view_liked_songs()
            elif choice == "3":
                self.view_playlists()
            elif choice == "4":
                self.create_new_playlist()
            elif choice == "5":
                self.backup_liked_songs()
            elif choice == "6":
                self.settings_menu()
            
            input(f"\n{yellow}Press Enter to continue...{clear}")

def main():
    """Entry point for the terminal menu application"""
    try:
        menu = TerminalMenu()
        menu.run()
    except KeyboardInterrupt:
        print(f"\n\n{green}Goodbye!{clear}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{red}An error occurred: {str(e)}{clear}")
        sys.exit(1)

if __name__ == "__main__":
    main()
