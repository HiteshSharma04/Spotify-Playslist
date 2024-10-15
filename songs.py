import requests
from bs4 import BeautifulSoup
from datetime import datetime as dt
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import billboard
import time
import os
from pprint import pprint
OAUTH_AUTHORIZE_URL="https://spotipy.readthedocs.io/en/2.13.0/#spotipy.oauth2.SpotifyOAuth.OAUTH_AUTHORIZE_URL"
OAUTH_TOKEN_URL= 'https://accounts.spotify.com/api/token'
CLIENT_ID = "Your ID"
CLIENT_SECRET = "Your Password"
REDIRECT_URI = "Your redirecting Page Url"
SCOPE = "playlist-modify-public playlist-modify-private"
SONGS = []
date = input(f"enter the date in which you wanna go (YYYY-MM-DD): ")

try:
    date = dt.strptime(date, "%Y-%m-%d").date()
    c_date = date.strftime("%Y-%m-%d")
except ValueError:
    print("Invalid date format. Please use YYYY-MM-DD.")
    exit()


chart = billboard.ChartData('hot-100', date=c_date)

SONGS = [{"title": entry.title, "artist":entry.artist} for entry in chart]

# print(f"Top 100 songs from Billboard on {c_date}:")
with open("projects/web/top_100.txt","w") as file:
    for idx, song in enumerate(SONGS, 1):
            file.write(f"{idx}.{song['title']} by {song['artist']} \n")

# print(response.text)
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE, 
    cache_path="projects/web/token.json"
    )

token_info = sp_oauth.get_cached_token()

if not token_info:
    # If no cached token, prompt the user to authorize
    auth_url = sp_oauth.get_authorize_url()
    print(f"\nPlease navigate here to authorize Spotify access:\n{auth_url}\n")
    response = input("After authorization, you will be redirected to a URL.\nPlease paste the full redirect URL here: ")
    code = sp_oauth.parse_response_code(response)
    try:
        token_info = sp_oauth.get_access_token(code)
    except Exception as e:
        print(f"Failed to obtain access token: {e}")
        exit()

if token_info:
    access_token = token_info['access_token']
    print("\nSuccessfully obtained Spotify access token.")
else:
    print("Failed to obtain access token.")
    exit()


sp = spotipy.Spotify(auth=access_token)

playlists = sp.current_user_playlists()
print(playlists)

user_info = sp.current_user()["id"]
# print(user_info["id"])

song_uri = []
skipped_songs = []

for song in SONGS:
    title = song['title']
    artist = song['artist']
    query = f"track:{title} artist:{artist} year:{date.year}"
    
    try:
        result = sp.search(q=query, type='track', limit=1)
        tracks = result['tracks']['items']
        
        if tracks:
            uri = tracks[0]['uri']
            song_uri.append(uri)
            # print(f"Found: {title} by {artist}")
        else:
            # print(f"Song not found on Spotify: {title} by {artist}")
            skipped_songs.append(f"{title} by {artist}")
        
    except Exception as e:
        print(f"Error occurred for {title} by {artist}: {e}")
        skipped_songs.append(f"{title} by {artist}")
    
    
    time.sleep(0.1)

print("\nSpotify URIs collected:")
pprint(song_uri)

if skipped_songs:
    print("\nSongs skipped (not found on Spotify):")
    pprint(skipped_songs)
else:
    print("\nAll songs were found on Spotify!")




if song_uri:
    try:
        playlist_name = f"Billboard Hot 100 {c_date}"
        playlist_description = f"Top 100 songs from Billboard Hot 100 on {c_date}"
        
        # Create a new Spotify playlist
        playlist = sp.user_playlist_create(user=user_info, name=playlist_name, public=False, description=playlist_description)
        print(f"\nCreated playlist: {playlist['name']}")

        # Add songs to the playlist in batches of 100 (Spotify API limit)
        for i in range(0, len(song_uri), 100):
            sp.playlist_add_items(playlist_id=playlist["id"], items=song_uri[i:i+100])
        
        print(f"\nAdded {len(song_uri)} songs to the playlist '{playlist_name}' '{playlist["id"]}'.")
    except Exception as e:
        print(f"Failed to create or populate the playlist: {e}")
else:
    print("\nNo songs were found to add to the playlist.")