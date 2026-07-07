# main.py
import sys
from scripts.liked_songs_merger import main as merger_main

if __name__ == '__main__':
    # Unified entry point: run the merger as described in the README
    quiet_flag = '--quiet'
    quiet = quiet_flag in sys.argv
    
    flag_use_default_playlist = '--default'
    use_default_playlist = flag_use_default_playlist in sys.argv
    merger_main(quiet=quiet, default_playlist=use_default_playlist)