"""
Script to update the "True Shuffle" playlist with 150 random songs from liked songs.
This script can be run daily to refresh the playlist.
"""

import random
from get_liked_songs import get_spotify_client, get_liked_songs, get_track_uris

# Playlist ID for "True Shuffle" - must be set via environment variable
# For public repositories, never hardcode IDs or secrets
import os
TRUE_SHUFFLE_PLAYLIST_ID = os.getenv('TRUE_SHUFFLE_PLAYLIST_ID')

if not TRUE_SHUFFLE_PLAYLIST_ID:
    raise ValueError(
        "Missing required environment variable: TRUE_SHUFFLE_PLAYLIST_ID. "
        "Please set this via environment variable or GitHub Secret."
    )


def get_or_create_playlist(sp, playlist_id, playlist_name, description="", public=False):
    """
    Get an existing playlist by ID, or create it if it doesn't exist.
    Ensures the playlist has the correct privacy setting.
    
    Args:
        sp: Authenticated Spotify client
        playlist_id: Spotify playlist ID
        playlist_name: Name of the playlist
        description: Description for the playlist (if creating new)
        public: Whether the playlist should be public (if creating new)
    
    Returns:
        dict: Playlist information
    """
    try:
        # Try to get the playlist by ID
        playlist = sp.playlist(playlist_id)
        
        print(f"Found playlist: {playlist_name}")
        
        # Ensure the playlist has the correct privacy setting
        if playlist.get('public') != public:
            print(f"Updating playlist privacy to {'public' if public else 'private'}...")
            sp.playlist_change_details(playlist_id, public=public)
            # Refresh playlist info
            playlist = sp.playlist(playlist_id)
        
        print(f"Playlist ID: {playlist_id}")
        print(f"Playlist URL: {playlist['external_urls']['spotify']}")
        return playlist
    except Exception as e:
        # Playlist doesn't exist or can't be accessed, create it
        print(f"Playlist not found or error accessing it: {e}")
        print(f"Creating new playlist: {playlist_name}...")
        user_id = sp.current_user()['id']
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=public,
            description=description
        )
        print(f"Created playlist: {playlist_name} (private: {not public})")
        print(f"Playlist ID: {playlist['id']}")
        print(f"Playlist URL: {playlist['external_urls']['spotify']}")
        print(f"Note: Update TRUE_SHUFFLE_PLAYLIST_ID in the script to: {playlist['id']}")
        return playlist


def clear_playlist(sp, playlist_id):
    """
    Remove all tracks from a playlist.
    
    Args:
        sp: Authenticated Spotify client
        playlist_id: ID of the playlist to clear
    """
    # Get all tracks in the playlist
    tracks_to_remove = []
    results = sp.playlist_items(playlist_id, limit=100)
    tracks_to_remove.extend(results['items'])
    
    # Continue fetching if there are more tracks
    while results['next']:
        results = sp.next(results)
        tracks_to_remove.extend(results['items'])
    
    if not tracks_to_remove:
        print("Playlist is already empty.")
        return
    
    # Extract track URIs (filter out None values in case of deleted tracks)
    track_uris = [
        item['track']['uri'] 
        for item in tracks_to_remove 
        if item['track'] and item['track']['uri']
    ]
    
    if not track_uris:
        print("No valid tracks to remove.")
        return
    
    # Remove tracks in batches of 100 (Spotify API limit)
    for i in range(0, len(track_uris), 100):
        batch = track_uris[i:i + 100]
        sp.playlist_remove_all_occurrences_of_items(playlist_id, batch)
    
    print(f"Removed {len(track_uris)} tracks from the playlist.")


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
    
    # Get or create the "True Shuffle" playlist
    playlist = get_or_create_playlist(
        sp,
        playlist_id=TRUE_SHUFFLE_PLAYLIST_ID,
        playlist_name="True Shuffle",
        description="A daily shuffled selection of 150 random songs from your liked songs",
        public=False
    )
    playlist_id = playlist['id']
    
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

