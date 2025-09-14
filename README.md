# Spotify Playlist Merger

## Description

Spotify Playlist Merger is a tool that lets you append your liked Spotify songs to any of your playlists, maintaining the original (reverse chronological) order. The tool ensures that only songs not already present in the target playlist are added.

## Features

- **Secure Authentication**: Uses OAuth2 with Spotify for secure login.
- **Fetch Liked Songs**: Retrieves all your liked songs.
- **Playlist Selection**: Lets you choose the target playlist via an interactive menu.
- **Duplicate Detection**: Only adds songs not already in the target playlist.
- **Reverse Chronological Order**: Adds songs from newest to oldest.
- **Batch Processing**: Handles large playlists efficiently (max 100 songs per API call).
- **Backup**: Optionally backup your liked songs to a JSON file.

## Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/SpotifyPlaylistMerger.git
   cd SpotifyPlaylistMerger
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up Spotify API credentials:**
   - Create a `.env` file in the project root with:
     ```
     CLIENT_ID=your_spotify_client_id
     CLIENT_SECRET=your_spotify_client_secret
     ```
   - You can get these credentials by registering an app at the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications).

## Usage

1. **Run the tool:**
   ```sh
   python scripts/main.py
   ```
   or
   ```sh
   python scripts/liked_songs_merger.py
   ```

2. **Follow the interactive process:**
   - The tool will open your browser for Spotify authentication.
   - After login, it will fetch your liked songs and playlists.
   - Select a target playlist from the menu.
   - Review the songs to be added (displayed newest first).
   - Confirm to add the songs to your selected playlist.

## Example Workflow

1. Run `python scripts/main.py`
2. Browser opens for Spotify login.
3. Select target playlist from menu.
4. Review the list of songs to add.
5. Confirm addition.
6. Songs are added in reverse chronological order (newest first).

## File Structure

- `scripts/liked_songs_merger.py`: Main script for merging liked songs into a playlist.
- `scripts/main.py`: Entry point and core Spotify API functions.
- `scripts/localServer.py`: Local server for OAuth callback handling.
- `scripts/colors.py`: Terminal color formatting utilities.
- `scripts/helpful_fuctions.py`: Utility functions.
- `scripts/terminal_menu.py`: (Optional) Enhanced terminal menu for advanced operations.

## Troubleshooting

- **Authentication Issues**: Make sure your `CLIENT_ID` and `CLIENT_SECRET` are correct in the `.env` file.
- **API Limits**: The tool respects Spotify's 100 tracks per request limit.
- **Error Handling**: Most errors are displayed in the terminal. If you encounter issues, check your internet connection and credentials.

## License

MIT License