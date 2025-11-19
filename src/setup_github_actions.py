"""
Helper script to prepare cache files for GitHub Actions.

This script helps you extract the necessary cache information after
authenticating locally, which can then be used in GitHub Actions.
"""

import json
import base64
from pathlib import Path
import glob


def find_cache_file():
    """Find the Spotify OAuth cache file."""
    cache_files = glob.glob('.cache-*')
    if not cache_files:
        print("No cache file found. Please run 'python update_true_shuffle.py' first to authenticate.")
        return None
    return cache_files[0]


def main():
    print("=" * 80)
    print("GitHub Actions Setup Helper")
    print("=" * 80)
    print()
    
    # Check for cache file
    cache_file = find_cache_file()
    if not cache_file:
        return
    
    print(f"Found cache file: {cache_file}")
    print()
    
    # Read cache content
    try:
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        print("Cache file contains OAuth token information.")
        print()
        print("For GitHub Actions setup:")
        print("1. The cache file will be automatically cached by GitHub Actions")
        print("2. Make sure the cache file is in .gitignore (it should be)")
        print("3. After your first successful local run, commit and push your code")
        print("4. Manually trigger the GitHub Action once to populate the cache")
        print()
        print("IMPORTANT: The cache file contains sensitive tokens.")
        print("Never commit it to the repository!")
        print()
        
        # Check if liked songs cache exists
        liked_songs_cache = Path("liked_songs_cache.json")
        if liked_songs_cache.exists():
            print("✓ Found liked_songs_cache.json")
        else:
            print("⚠ liked_songs_cache.json not found. Run the script once to create it.")
        
        print()
        print("Next steps:")
        print("1. Make sure all secrets are set in GitHub (see GITHUB_ACTIONS_SETUP.md)")
        print("2. Commit and push your code")
        print("3. Go to Actions tab and manually trigger the workflow")
        print("4. The workflow will cache the files for future runs")
        
    except Exception as e:
        print(f"Error reading cache file: {e}")


if __name__ == "__main__":
    main()

