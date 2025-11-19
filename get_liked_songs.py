"""
Script to connect to Spotify API and list all liked songs.
Also supports creating playlists.
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
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

# Cache file for liked songs
LIKED_SONGS_CACHE_FILE = Path("liked_songs_cache.json")


def save_liked_songs_to_disk(tracks):
    """
    Save liked songs to disk as JSON with metadata.
    
    Args:
        tracks: List of track dictionaries from Spotify API
    """
    cache_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_count': len(tracks),
        'tracks': tracks
    }
    
    with open(LIKED_SONGS_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(tracks)} liked songs to {LIKED_SONGS_CACHE_FILE}")


def load_liked_songs_from_disk():
    """
    Load liked songs from disk cache.
    
    Returns:
        tuple: (tracks list, timestamp string) or (None, None) if file doesn't exist
    """
    if not LIKED_SONGS_CACHE_FILE.exists():
        return None, None
    
    try:
        with open(LIKED_SONGS_CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        tracks = cache_data.get('tracks', [])
        timestamp = cache_data.get('timestamp', '')
        return tracks, timestamp
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error reading cache file: {e}")
        return None, None


def get_new_liked_songs_since(sp, since_timestamp=None):
    """
    Check if there are new liked songs since a given timestamp.
    Since Spotify doesn't have a "get songs since X" endpoint, we fetch all
    and compare timestamps. Returns empty list if no new songs, or None if we should fetch all.
    
    Args:
        sp: Authenticated Spotify client
        since_timestamp: ISO format timestamp string to compare against
    
    Returns:
        list: List of new track dictionaries, empty list if no new songs, None if error
    """
    if since_timestamp is None:
        return None
    
    # Get all saved tracks (Spotify doesn't support filtering by date)
    results = sp.current_user_saved_tracks(limit=50)
    all_tracks = results['items']
    
    # Continue fetching if there are more tracks
    while results['next']:
        results = sp.next(results)
        all_tracks.extend(results['items'])
    
    # Parse the timestamp for comparison
    # Normalize to UTC timezone-aware datetime
    try:
        # Try parsing with timezone info first
        if 'Z' in since_timestamp or '+' in since_timestamp or since_timestamp.count('-') > 2:
            since_dt = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
        else:
            # Naive datetime, assume UTC
            since_dt = datetime.fromisoformat(since_timestamp)
            since_dt = since_dt.replace(tzinfo=timezone.utc)
        
        # Ensure it's timezone-aware
        if since_dt.tzinfo is None:
            since_dt = since_dt.replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError) as e:
        print(f"Error parsing cache timestamp: {e}")
        return None
    
    # Filter tracks added after the timestamp
    new_tracks = []
    for item in all_tracks:
        try:
            added_at_str = item['added_at']
            # Parse Spotify timestamp (usually in format like "2023-01-01T00:00:00Z")
            if 'Z' in added_at_str:
                added_at = datetime.fromisoformat(added_at_str.replace('Z', '+00:00'))
            elif '+' in added_at_str or added_at_str.count('-') > 2:
                added_at = datetime.fromisoformat(added_at_str)
            else:
                # Naive datetime, assume UTC
                added_at = datetime.fromisoformat(added_at_str)
                added_at = added_at.replace(tzinfo=timezone.utc)
            
            # Ensure it's timezone-aware
            if added_at.tzinfo is None:
                added_at = added_at.replace(tzinfo=timezone.utc)
            
            if added_at > since_dt:
                new_tracks.append(item)
        except (ValueError, KeyError) as e:
            continue
    
    return new_tracks


def get_spotify_client():
    """
    Create and return an authenticated Spotify client.
    
    Returns:
        spotipy.Spotify: Authenticated Spotify client
    """
    # Set up Spotify OAuth with scopes for reading liked songs and creating playlists
    # user-library-read: Read access to user's saved tracks
    # playlist-modify-private: Create and modify private playlists
    scope = "user-library-read playlist-modify-private"
    
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=scope
    ))
    
    return sp


def get_liked_songs(save_to_disk=True, use_cache=True):
    """
    Connect to Spotify API and retrieve all liked songs.
    Optionally uses disk cache and saves results to disk.
    
    Args:
        save_to_disk: Whether to save the results to disk (default: True)
        use_cache: Whether to check disk cache first (default: True)
    
    Returns:
        list: List of dictionaries containing track information
    """
    # Try to load from cache first
    if use_cache:
        cached_tracks, cache_timestamp = load_liked_songs_from_disk()
        if cached_tracks is not None:
            print(f"Loaded {len(cached_tracks)} liked songs from cache (saved at {cache_timestamp})")
            
            # Check if there are new songs since cache
            sp = get_spotify_client()
            new_tracks = get_new_liked_songs_since(sp, cache_timestamp)
            
            if new_tracks is not None:
                if len(new_tracks) > 0:
                    print(f"Found {len(new_tracks)} new liked songs since cache. Updating cache...")
                    # If there are new tracks, we need to fetch all to get the complete updated list
                    # This ensures we have the most current data
                    use_cache = False  # Fall through to full fetch
                else:
                    print("No new liked songs since cache. Using cached data (no API calls needed).")
                    return cached_tracks
            else:
                # Error checking for new songs, fall back to full fetch
                print("Could not check for new songs. Fetching all liked songs...")
                use_cache = False
    
    # Fetch all liked songs from API
    sp = get_spotify_client()
    
    print("Fetching liked songs from Spotify API...")
    # Get all saved tracks (liked songs)
    # Spotify returns tracks in batches of 50, so we need to paginate
    results = sp.current_user_saved_tracks(limit=50)
    tracks = results['items']
    
    # Continue fetching if there are more tracks
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    
    # Save to disk if requested
    if save_to_disk:
        save_liked_songs_to_disk(tracks)
    
    return tracks


def display_tracks(tracks):
    """
    Display tracks in a readable format.
    
    Args:
        tracks: List of track dictionaries from Spotify API
    """
    print(f"\nTotal liked songs: {len(tracks)}\n")
    print("-" * 80)
    
    for idx, item in enumerate(tracks, 1):
        track = item['track']
        artists = ", ".join([artist['name'] for artist in track['artists']])
        album = track['album']['name']
        name = track['name']
        added_at = item['added_at'][:10]  # Just the date part
        
        print(f"{idx}. {name}")
        print(f"   Artist(s): {artists}")
        print(f"   Album: {album}")
        print(f"   Added: {added_at}")
        print(f"   Spotify URL: {track['external_urls']['spotify']}")
        print("-" * 80)


def save_to_file(tracks, output_file="liked_songs.txt"):
    """
    Save tracks to a text file.
    
    Args:
        tracks: List of track dictionaries from Spotify API
        output_file: Path to output file
    """
    output_path = Path(output_file)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Total liked songs: {len(tracks)}\n\n")
        f.write("=" * 80 + "\n\n")
        
        for idx, item in enumerate(tracks, 1):
            track = item['track']
            artists = ", ".join([artist['name'] for artist in track['artists']])
            album = track['album']['name']
            name = track['name']
            added_at = item['added_at'][:10]
            
            f.write(f"{idx}. {name}\n")
            f.write(f"   Artist(s): {artists}\n")
            f.write(f"   Album: {album}\n")
            f.write(f"   Added: {added_at}\n")
            f.write(f"   Spotify URL: {track['external_urls']['spotify']}\n")
            f.write("-" * 80 + "\n\n")
    
    print(f"\nTracks saved to {output_path}")


def create_playlist(name, description="", public=True, track_uris=None):
    """
    Create a new playlist and optionally add tracks to it.
    
    Args:
        name: Name of the playlist
        description: Description of the playlist (optional)
        public: Whether the playlist should be public (default: True)
        track_uris: List of Spotify track URIs to add to the playlist (optional)
    
    Returns:
        dict: Playlist information from Spotify API
    """
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


def get_track_uris(tracks):
    """
    Extract track URIs from a list of track items.
    
    Args:
        tracks: List of track dictionaries from Spotify API
    
    Returns:
        list: List of track URIs
    """
    return [item['track']['uri'] for item in tracks]


if __name__ == "__main__":
    print("Connecting to Spotify API...")
    print("You may be redirected to your browser for authentication.")
    
    try:
        # Get liked songs (will use cache if available and fetch new ones)
        tracks = get_liked_songs(save_to_disk=True, use_cache=True)
        display_tracks(tracks)
        save_to_file(tracks)
        
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API error: {e}")
    except Exception as e:
        print(f"Error: {e}")

