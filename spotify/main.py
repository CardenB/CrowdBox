import json
from flask import Flask, request, redirect, g, render_template
import requests
import spotipy
from spotipy import oauth2
import base64
import urllib
import os

'''
Authentication Steps, paramaters, and responses are defined at
    https://developer.spotify.com/web-api/authorization-guide/
Visit this url to see all the steps, parameters, and expected response. 
'''

app = Flask(__name__)

#  Client Keys
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)


# Server-side Parameters
CLIENT_SIDE_URL = "http://localhost"
PORT = 8080
REDIRECT_URI = "{}:{}/callback/".format(CLIENT_SIDE_URL, PORT)
SCOPE = ("playlist-read-private "
         "playlist-modify-public "
         "playlist-modify-private"
        )
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

spotifyOAuth = spotipy.oauth2.SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        state=STATE,
        scope=SCOPE,
        cache_path=None
        )

@app.route("/")
def index():
    # Auth Step 1: Authorization
    return redirect(spotifyOAuth.get_authorize_url())


@app.route("/callback/")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
    }
    base64encoded = base64.b64encode("{}:{}".format(CLIENT_ID, CLIENT_SECRET))
    headers = {"Authorization": "Basic {}".format(base64encoded)}
    post_request = requests.post(SPOTIFY_TOKEN_URL,
                                 data=code_payload,
                                 headers=headers)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization":"Bearer {}".format(access_token)}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    # Get user playlist data
    playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)
    
    # get the track name for every track in the display
    display_arr = []
    for playlist in playlist_data["items"]:
        endpoint_str = "{}/{}/tracks".format(playlist_api_endpoint,
                                             playlist["id"])
        tracks_response = requests.get(endpoint_str,
                                       headers=authorization_header)
        track_data = json.loads(tracks_response.text)
        tracks = [item["track"] for item in track_data["items"]]
        display_arr.extend([track["name"] for track in tracks])

    return render_template("index.html",sorted_array=display_arr)


if __name__ == "__main__":
    app.run(debug=True,port=PORT)
