# Spotify True Shuffle

## Motivation
Unfortunately, in large playlists (over 150 songs), the shuffle option prioritizes the songs that Spotify perceives you enjoy the most; this is why you might notice that some songs are repeated while listening on shuffle. 

I don't want that. 

Through GitHub Actions, this repository is creates a new list of 150 songs **randomly** chosen from my Liked Songs. 

Want to set this up yourself? Read Setup for this repo to get the correct credentials and run it locally. Read GITHUB_ACTIONS_SETUP.md to see how to set up GitHub Actions to do this automatically.

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
python src/update_true_shuffle.py
```

## Notes

- The script uses the following scopes:
  - `user-library-read`: Read access to your saved tracks
  - `playlist-modify-public`: Create and modify public playlists
  - `playlist-modify-private`: Create and modify private playlists
- Your authentication token is cached locally (in `.cache-username`) so you won't need to re-authenticate every time
- The redirect URI must match exactly what you set in your Spotify app settings
- **Important**: When creating your Spotify app, select **"Web API"** as the API/SDK you're planning to use

