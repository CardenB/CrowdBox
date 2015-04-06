import json
from flask import Flask, request, redirect, g, render_template, session,\
                  url_for, g
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

sp = None
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


def getUsername(sp):
    return sp.current_user()['id']

def getPlaylistID(sp):
    playlists = sp.user_playlists(getUsername(sp))['items']
    for playlist in playlists:
        return playlist['id']



@app.route("/search", methods=["POST"])
def search():
    return redirect(url_for('search_results', query=request.form["search"]))


@app.route("/search_results/<query>")
def search_results(query):
    auth_token = session["token_info"]["access_token"]
    sp = spotipy.Spotify(auth=auth_token)
    # Get profile data
    profile_data = sp.current_user()
    username = profile_data["id"]
    results = sp.search(q=query, type='track')

    results = [{'name' : track['name'],
                'track_id' : track['id']} \
        for track in results['tracks']['items']]
    print results
    return render_template("index.html", tracks=results)


@app.route("/track/add/<track_id>")
def track_add(track_id):
    auth_token = session["token_info"]["access_token"]
    sp = spotipy.Spotify(auth=auth_token)
    sp.user_playlist_add_tracks(getUsername(sp), getPlaylistID(sp), [track_id])
    return redirect(url_for('index', tracks=[]))


@app.route("/", methods=["GET", "POST"])
def index():
    # create the object used to access the spotify api wrappers
    if "token info" in session.keys():
        auth_token = session["token_info"]["access_token"]
    else:
        # Auth Step 1: Authorization
        return redirect(spotifyOAuth.get_authorize_url())
    return render_template('index.html', tracks=[])


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
    return render_template('index.html', tracks=[])


if __name__ == "__main__":
    app.run(debug=True,port=PORT)
