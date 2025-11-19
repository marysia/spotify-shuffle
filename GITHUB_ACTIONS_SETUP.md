# GitHub Actions Setup Guide

This guide explains how to set up the GitHub Action to automatically update your "True Shuffle" playlist daily at 3:00 AM.

## Overview

The workflow will:
- Run daily at 3:00 AM UTC (configurable)
- Use cached OAuth tokens (no re-authentication needed after setup)
- Use cached liked songs data (minimizes API calls)
- Update your "True Shuffle" playlist with 150 random songs

## Step 1: Set Up GitHub Secrets

Add these secrets to your GitHub repository:

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:

### Required Secrets

| Secret Name | Description | Example |
|------------|-------------|---------|
| `SPOTIPY_CLIENT_ID` | Your Spotify app Client ID | 
| `SPOTIPY_CLIENT_SECRET` | Your Spotify app Client Secret |
| `SPOTIPY_REDIRECT_URI` | Your redirect URI | 
| `TRUE_SHUFFLE_PLAYLIST_ID` | Your playlist ID |

### Optional Secret (for first run)

| Secret Name | Description | When to Use |
|------------|-------------|-------------|
| `SPOTIFY_CACHE_BASE64` | Base64-encoded OAuth cache file | Only needed for the first run (see Step 2) |

## Step 2: Initial Authentication & Cache Setup

The Spotify OAuth flow requires browser-based authentication. Here's how to set it up:

### 2.1 Authenticate Locally

**Important**: Before running the script, make sure your Spotify app's redirect URI is set correctly:
- Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- Select your app → **Edit Settings**
- Under **Redirect URIs**, add: `http://127.0.0.1:8888/callback`
- Click **Add** and **Save**
- **Do NOT use** external URLs like `https://developer.spotify.com/dashboard` - the OAuth flow requires a local URL that spotipy can listen on

1. **Run the script locally** to authenticate:
   ```bash
   python src/update_true_shuffle.py
   ```
   This will:
   - Open your browser for Spotify authentication (you'll need to log in and authorize the app)
   - **Automatically create** a `.cache-*` file with your OAuth token (contains refresh token)
     - The filename will be something like `.cache-yourusername` (created automatically by spotipy)
   - **Automatically create** `liked_songs_cache.json` with your liked songs
   
   **Note**: You don't need to create these files manually - they are generated automatically during the authentication process.
   
   **Troubleshooting**: If the `.cache-*` file is not created:
   - Verify your redirect URI in Spotify dashboard is exactly `http://127.0.0.1:8888/callback`
   - Make sure port 8888 is not blocked by a firewall
   - Check that your environment variables are set correctly
   - Try running the script again after fixing the redirect URI

2. **Verify cache files were created**:
   ```bash
   # Universal command (works in all shells):
   # Note: Cache file might be named .cache or .cache-username
   find . -maxdepth 1 \( -name ".cache*" -o -name "liked_songs_cache.json" \)
   
   # Or for bash/zsh:
   ls -la .cache* liked_songs_cache.json
   ```
   
   **Note**: The cache file might be named `.cache` or `.cache-username` - both are valid. The important thing is that it exists.

### 2.2 Prepare Cache for GitHub Actions

For the **first GitHub Actions run**, you need to provide the OAuth cache file:

1. **Find your cache file**:
   ```bash
   # Universal command (works in all shells):
   # Cache file might be named .cache or .cache-username
   find . -maxdepth 1 -name ".cache*"
   
   # Or for bash/zsh:
   ls -la .cache*
   
   # Note the filename (e.g., .cache or .cache-username)
   ```

2. **Encode the cache file** (replace `.cache` or `.cache-username` with your actual filename):
   ```bash
   # On macOS/Linux (if your file is named .cache):
   base64 -i .cache | pbcopy  # Copies to clipboard
   
   # Or if it's named .cache-username:
   base64 -i .cache-username | pbcopy  # Copies to clipboard
   
   # Or save to file:
   base64 -i .cache > cache_base64.txt  # Use your actual filename
   cat cache_base64.txt  # Review the content
   ```

3. **Add as GitHub Secret**:
   - Go to **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `SPOTIFY_CACHE_BASE64`
   - Value: Paste the base64 content
   - Click **Add secret**

4. **After first successful run**: You can delete the `SPOTIFY_CACHE_BASE64` secret - it's no longer needed. The cache will be persisted by GitHub Actions.

## Step 3: Commit and Push

1. **Commit your code** (cache files are gitignored, so they won't be committed):
   ```bash
   git add .
   git commit -m "Add GitHub Actions workflow"
   git push
   ```

2. **Verify the workflow file exists**:
   ```bash
   ls -la .github/workflows/update-playlist.yml
   ```

## Step 4: Test the Workflow

1. Go to the **Actions** tab in your GitHub repository
2. Click **Update True Shuffle Playlist** workflow
3. Click **Run workflow** → **Run workflow** (manual trigger)
4. Watch the workflow run
5. Check the logs to ensure it completed successfully

## Step 5: Verify It Works

1. Check your Spotify "True Shuffle" playlist
2. It should now contain 150 random songs from your liked songs
3. The workflow will run automatically daily at 3:00 AM UTC

## Understanding the Cache

The workflow uses GitHub Actions cache to persist:

- **OAuth tokens** (`.cache-*` files): Contains your refresh token, so you don't need to re-authenticate
- **Liked songs cache** (`liked_songs_cache.json`): Reduces API calls by caching your liked songs

**Cache behavior**:
- First run: Uses `SPOTIFY_CACHE_BASE64` secret if provided
- Subsequent runs: Uses GitHub Actions cache (automatically restored)
- Cache persists between runs (no expiration unless manually cleared)

## Customizing the Schedule

To change when the workflow runs, edit `.github/workflows/update-playlist.yml`:

```yaml
schedule:
  - cron: '0 3 * * *'  # 3:00 AM UTC daily
```

Cron format: `'minute hour day month day-of-week'`

Examples:
- `'0 8 * * *'` = 8:00 AM UTC daily
- `'0 0 * * 1'` = Midnight UTC every Monday
- `'0 */6 * * *'` = Every 6 hours

[Cron expression help](https://crontab.guru/)

## Troubleshooting

### First Run Fails with Authentication Error

**Expected behavior** if `SPOTIFY_CACHE_BASE64` secret is not set. Solution:
1. Follow Step 2.2 to create and add the `SPOTIFY_CACHE_BASE64` secret
2. Re-run the workflow

### Cache Not Persisting

- Check that cache files exist after the workflow runs
- Verify the cache action steps are completing successfully
- Check GitHub Actions cache limits (10 GB per repository)

### Rate Limiting

Spotify API has generous rate limits for personal use. If you hit limits:
- The cache helps minimize API calls
- Consider running less frequently
- Check your Spotify Developer Dashboard for quota

### Workflow Not Running on Schedule

- Verify the cron syntax is correct
- Check GitHub Actions is enabled for your repository
- Note: Scheduled workflows may be delayed during high load

## Public Repository Safety

✅ **This repository is safe to make public** because:

- ✅ **No hardcoded secrets**: All credentials are read from environment variables
- ✅ **GitHub Secrets are encrypted**: Even in public repos, secrets are never exposed
- ✅ **Cache files are gitignored**: `.cache-*` and `liked_songs_cache.json` won't be committed
- ✅ **Code is safe**: The Python scripts contain no sensitive data

**What's visible in a public repo:**
- ✅ Python code (safe - no secrets)
- ✅ Workflow files (safe - uses secrets, not hardcoded values)
- ✅ Documentation (safe - examples only, no real credentials)

**What's NOT visible:**
- ❌ GitHub Secrets (encrypted, never in code)
- ❌ Cache files (gitignored)
- ❌ OAuth tokens (stored in cache, never committed)

## Security Notes

✅ **Secrets are encrypted** and never exposed in logs  
✅ **Cache files are stored securely** by GitHub  
✅ **OAuth tokens in cache** are repository-scoped  
✅ **Code is public-safe** - no hardcoded credentials  
⚠️ **Never commit** `.cache-*` or `liked_songs_cache.json` files  
⚠️ **Never hardcode** credentials in code  
⚠️ **Rotate secrets** if you suspect they're compromised  
⚠️ **Review your `.gitignore`** to ensure cache files are excluded

## Manual Trigger

You can manually trigger the workflow anytime:
1. Go to **Actions** tab
2. Select **Update True Shuffle Playlist**
3. Click **Run workflow** → **Run workflow**

## Files Overview

- `.github/workflows/update-playlist.yml` - GitHub Actions workflow definition
- `src/update_true_shuffle.py` - Main script that updates the playlist
- `src/retrieve_liked_songs.py` - Handles Spotify API and caching
- `.gitignore` - Ensures cache files are never committed

## Need Help?

- Check the workflow logs in the **Actions** tab
- Verify all secrets are set correctly
- Ensure your Spotify app has the correct scopes:
  - `user-library-read`
  - `playlist-modify-public`
  - `playlist-modify-private`
