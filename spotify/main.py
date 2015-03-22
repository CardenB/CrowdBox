import json
from flask import Flask, request, redirect, g, render_template, session
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
app.secret_key = os.environ['FLASK_SECRET_KEY']

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
CACHE_PATH = None

spotifyOAuth = spotipy.oauth2.SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        state=STATE,
        scope=SCOPE,
        cache_path=CACHE_PATH
        )

def retrieveTokensFromSession():
    return session["token_info"]["access_token"],\
            session["token_info"]["refresh_token"],\
            session["token_info"]["token_type"],\
            session["token_info"]["expires_in"]

def get_cached_token():
    if "token_info" in session:
        return session["token_info"]
    else:
        return None

@app.route("/")
def index():
    # Auth Step 1: Authorization
    return redirect(spotifyOAuth.get_authorize_url())


@app.route("/callback/")
def callback():
    def load_token_json(token_json):
        access_token = token_json["access_token"]
        refresh_token = token_json["refresh_token"]
        token_type = token_json["token_type"]
        expires_in = token_json["expires_in"]
        return access_token, refresh_token, \
               token_type, expires_in
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    # get cahched token, refresh token if not cached
    token_json = get_cached_token()
    if token_json is None:
        token_json = spotifyOAuth.get_access_token(str(auth_token))

    # extend the session dictionary with the key, value token store
    session["token_info"] = token_json
    access_token, refresh_token, token_type, expires_in = \
            retrieveTokensFromSession()


    # Auth Step 6: Use the access token to access Spotify API
    # authorization_header = {"Authorization":"Bearer {}".format(access_token)}

    # create the object used to access the spotify api wrappers
    sp = spotipy.Spotify(auth=session["token_info"]["access_token"])

    # Get profile data
    profile_data = sp.current_user()
    username = profile_data["id"]

    # Get user playlist data
    playlist_data = sp.user_playlists(username)
    
    # get the track name for every track in the display
    for playlist in playlist_data["items"]:
        # get playlist track data
        track_data = sp.user_playlist_tracks(username, playlist["id"])
        tracks = [item["track"] for item in track_data["items"]]
        print tracks

    # display all the playlists for the user
    display_arr = [playlist["name"] for playlist in\
            sp.user_playlists(username)["items"]]
    return render_template("index.html",sorted_array=display_arr)


if __name__ == "__main__":
    app.run(debug=True,port=PORT)
