# Spotify Liked Songs Lister

A simple Python script to connect to the Spotify API and list all your liked songs.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create a Spotify App:**
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Click "Create an App"
   - Fill in the app name and description
   - **Select "Web API"** (this is what spotipy uses)
   - Accept the terms and create the app

3. **Get your credentials:**
   - In your app settings, you'll find:
     - Client ID
     - Client Secret
   - **Add a redirect URI**: `http://127.0.0.1:8888/callback`
     - Click "Edit Settings" in your app
     - Under "Redirect URIs", add: `http://127.0.0.1:8888/callback`
     - Click "Add" and then "Save"

4. **Set environment variables (optional):**
   
   The script has credentials hardcoded, but for better security you can use environment variables instead:
   ```bash
   export SPOTIPY_CLIENT_ID='your_client_id_here'
   export SPOTIPY_CLIENT_SECRET='your_client_secret_here'
   export SPOTIPY_REDIRECT_URI='http://127.0.0.1:8888/callback'
   ```

   Or create a `.env` file (make sure to add it to `.gitignore`):
   ```
   SPOTIPY_CLIENT_ID=your_client_id_here
   SPOTIPY_CLIENT_SECRET=your_client_secret_here
   SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
   ```
   
   **Important**: The redirect URI must be `http://127.0.0.1:8888/callback` (not `localhost`) to avoid deprecation warnings.

## Usage

Run the script:
```bash
python get_liked_songs.py
```

The first time you run it, you'll be redirected to your browser to authorize the app. After authorization, the script will:
- Display all your liked songs in the terminal
- Save them to a file called `liked_songs.txt`

## Features

- Lists all liked songs (handles pagination automatically)
- Shows track name, artist(s), album, and date added
- Includes Spotify URLs for each track
- Saves output to a text file

## Creating Playlists

The script includes a `create_playlist()` function that you can use to create playlists. Example:

```python
from get_liked_songs import create_playlist, get_liked_songs, get_track_uris

# Get your liked songs
tracks = get_liked_songs()

# Extract track URIs
track_uris = get_track_uris(tracks)

# Create a playlist with all your liked songs
playlist = create_playlist(
    name="My Liked Songs Playlist",
    description="All my liked songs",
    public=False,  # Make it private
    track_uris=track_uris
)
```

## Notes

- The script uses the following scopes:
  - `user-library-read`: Read access to your saved tracks
  - `playlist-modify-public`: Create and modify public playlists
  - `playlist-modify-private`: Create and modify private playlists
- Your authentication token is cached locally (in `.cache-username`) so you won't need to re-authenticate every time
- The redirect URI must match exactly what you set in your Spotify app settings
- **Important**: When creating your Spotify app, select **"Web API"** as the API/SDK you're planning to use

