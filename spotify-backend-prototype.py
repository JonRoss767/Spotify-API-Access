from requests import post, get
from dotenv import load_dotenv
from flask import Flask, redirect, request, jsonify, session, render_template
from datetime import datetime, timedelta

import urllib.parse
import json
import os
import base64


app = Flask(__name__)
app.secret_key = '6516443-352379-97629-87263452982'

'''
TODO
1. refactor code
2. handle possible failure (404, 401, 403, 429, etc)

'''

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URL = 'http://127.0.0.1:5000/callback' #'http://localhost:5000/callback'
AUTH_URL = 'https://accounts.spotify.com/authorize/'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'


@app.route('/')
def index():
    return "Welcome to my Spotify App <a href='/login'>login</a> <a href='/playlists'>Get your albums</a> <a href='/tracks'>Get your saved songs</a>"

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email user-library-read'
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URL,
        'show_dialog': True
    }
    
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URL,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = post(TOKEN_URL, data=req_body)
        token_info = json.loads(response.content)

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/')
    
@app.route('/refresh-token')
def refresh_token():
   
    if 'refresh_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = post(TOKEN_URL, data=req_body)
        new_token_info = json.loads(response.content)

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/')
        


@app.route('/playlists')
def get_playlist():

    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }
    
    response = get(API_BASE_URL + 'me/playlists', headers=headers)
    json_playlists = json.loads(response.content)["items"]
    playlists = []
    for p in json_playlists:
        playlists.append(p['name'])

    #return jsonify(playlists)
    return render_template('playlists.html', playlists=playlists)

@app.route('/tracks')
def get_user_songs():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    songs = []
    limit = 50
    offset = 0
    while True:
        
        params = {
            'limit': limit,
            'offset': offset
        }

        url = f"{API_BASE_URL}me/tracks?{urllib.parse.urlencode(params)}"

        response = get(url, headers=headers)
        json_tracks = json.loads(response.content)["items"]
        
        for s in json_tracks:
            songs.append(s['track']['name'])
        
        if len(json_tracks) < 50:
            break

        offset += 50

    #return jsonify(playlists)
    return render_template('tracks.html', songs=songs)



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

