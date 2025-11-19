"""
Script to update the "True Shuffle" playlist with 150 random songs from liked songs.
This script can be run daily to refresh the playlist.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import random
from src.retrieve_liked_songs import get_liked_songs
from src.utils import get_spotify_client, get_track_uris, get_or_create_playlist, clear_playlist

# Playlist ID for "True Shuffle" - must be set via environment variable
# For public repositories, never hardcode IDs or secrets
TRUE_SHUFFLE_PLAYLIST_ID = os.getenv('TRUE_SHUFFLE_PLAYLIST_ID')

if not TRUE_SHUFFLE_PLAYLIST_ID:
    raise ValueError(
        "Missing required environment variable: TRUE_SHUFFLE_PLAYLIST_ID. "
        "Please set this via environment variable or GitHub Secret."
    )


def update_true_shuffle(num_songs=150):
    """
    Update the "True Shuffle" playlist with random songs from liked songs.
    
    Args:
        num_songs: Number of random songs to add (default: 150)
    """
    print("=" * 80)
    print("Updating True Shuffle playlist")
    print("=" * 80)
    
    # Get authenticated Spotify client
    sp = get_spotify_client()
    
    # Generate description with current timestamp
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    description = f"A daily shuffled selection of 150 random songs from your liked songs. Last updated: {current_time}"
    
    # Get or create the "True Shuffle" playlist
    playlist = get_or_create_playlist(
        sp,
        playlist_id=TRUE_SHUFFLE_PLAYLIST_ID,
        playlist_name="True Shuffle",
        description=description,
        public=False
    )
    playlist_id = playlist['id']
    
    # Update the playlist description to include the timestamp
    # (get_or_create_playlist only sets description when creating, so we update it here)
    sp.playlist_change_details(playlist_id, description=description)
    
    # Clear the playlist
    print("\nClearing existing tracks from playlist...")
    clear_playlist(sp, playlist_id)
    
    # Get all liked songs (will use cache if available to minimize API calls)
    print("\nFetching your liked songs...")
    liked_tracks = get_liked_songs(save_to_disk=True, use_cache=True)
    print(f"Found {len(liked_tracks)} liked songs.")
    
    # Check if we have enough songs
    if len(liked_tracks) < num_songs:
        print(f"Warning: You only have {len(liked_tracks)} liked songs, but requested {num_songs}.")
        print(f"Using all {len(liked_tracks)} songs instead.")
        num_songs = len(liked_tracks)
    
    # Select random songs
    print(f"\nSelecting {num_songs} random songs...")
    random_tracks = random.sample(liked_tracks, num_songs)
    track_uris = get_track_uris(random_tracks)
    
    # Add tracks to playlist
    print(f"\nAdding {len(track_uris)} tracks to the playlist...")
    # Spotify API allows adding up to 100 tracks at a time
    for i in range(0, len(track_uris), 100):
        batch = track_uris[i:i + 100]
        sp.playlist_add_items(playlist_id, batch)
        print(f"Added batch {i//100 + 1} ({len(batch)} tracks)")
    
    print("\n" + "=" * 80)
    print("True Shuffle playlist updated successfully!")
    print(f"Playlist URL: {playlist['external_urls']['spotify']}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        update_true_shuffle()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

