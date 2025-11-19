"""
Utility functions for Spotify API operations.
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Get credentials from environment variables
# These MUST be set via environment variables (e.g., GitHub Secrets for CI/CD)
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:8888/callback')

# Validate required credentials
if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
    raise ValueError(
        "Missing required environment variables: SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET. "
        "Please set these via environment variables or GitHub Secrets."
    )


def get_spotify_client(scope="user-library-read playlist-modify-private"):
    """
    Create and return an authenticated Spotify client.
    
    Args:
        scope: OAuth scopes (default: "user-library-read playlist-modify-private")
    
    Returns:
        spotipy.Spotify: Authenticated Spotify client
    """
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=scope
    ))
    
    return sp


def get_track_uris(tracks):
    """
    Extract track URIs from a list of track items.
    
    Args:
        tracks: List of track dictionaries from Spotify API
    
    Returns:
        list: List of track URIs
    """
    return [item['track']['uri'] for item in tracks]


def create_playlist(name, description="", public=True, track_uris=None, sp=None):
    """
    Create a new playlist and optionally add tracks to it.
    
    Args:
        name: Name of the playlist
        description: Description of the playlist (optional)
        public: Whether the playlist should be public (default: True)
        track_uris: List of Spotify track URIs to add to the playlist (optional)
        sp: Authenticated Spotify client (optional, will create one if not provided)
    
    Returns:
        dict: Playlist information from Spotify API
    """
    if sp is None:
        sp = get_spotify_client()
    
    # Get current user's ID
    user_id = sp.current_user()['id']
    
    # Create the playlist
    playlist = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=public,
        description=description
    )
    
    print(f"\nCreated playlist: {name}")
    print(f"Playlist ID: {playlist['id']}")
    print(f"Playlist URL: {playlist['external_urls']['spotify']}")
    
    # Add tracks if provided
    if track_uris:
        # Spotify API allows adding up to 100 tracks at a time
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i + 100]
            sp.playlist_add_items(playlist['id'], batch)
        
        print(f"Added {len(track_uris)} tracks to the playlist")
    
    return playlist


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

