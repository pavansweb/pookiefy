from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, session, url_for
import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
import base64
import json
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from cachetools import TTLCache
import random
from flask_cors import CORS  # Import Flask-CORS

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)  
app.secret_key = os.urandom(24)

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Load credentials and configuration from environment variables
YOUTUBE_API_KEY = 'AIzaSyAZMHc8-c0ywvjiRs3CCxgLCnUBBRTTuXg'
SPOTIFY_CLIENT_ID = '9241546ed80f472785347051926375e2'
SPOTIFY_CLIENT_SECRET = 'ca7e1e03d6084328ad96faf52930b171'
SPOTIFY_REDIRECT_URI = "https://literate-space-succotash-q77g59qx6jp93p5p-2007.app.github.dev/callback"

MY_GITHUB_TOKEN = os.getenv('MY_GITHUB_TOKEN_FOR_POOKIEFY')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'pavansweb/pookiefy-song-storage')
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/"
RAPIDAPI_KEYS = ['827a267b18mshccf0ef3588021b6p1eed8djsn6d526d9496ee', '403a0838eamshd14c1848197da01p118343jsn5f0026273ed4', 'a03c8cb70fmsh58312728b82e59ep1c47dejsnb343308fa972', 'f136c0aa68mshb36ffbc4dc13eafp117fecjsn56310af5bb86'
]
RAPIDAPI_KEY = random.choice(RAPIDAPI_KEYS)

spotify_token_cache = TTLCache(maxsize=1, ttl=3600)
 
# Spotify OAuth object
sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-library-read user-top-read playlist-read-private",
    cache_path=".cache",
    show_dialog=True  # This will force the login prompt
)

# Spotify instance
sp = Spotify(auth_manager=sp_oauth)

# Define the directory to save downloads
DOWNLOAD_FOLDER = os.path.join(app.root_path, 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def get_spotify_token():
    if 'token' in spotify_token_cache:
        return spotify_token_cache['token']

    token_response = requests.post('https://accounts.spotify.com/api/token', data={
        'grant_type': 'client_credentials'
    }, headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic ' + base64.b64encode(f'{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}'.encode()).decode()
    })

    token_data = token_response.json()
    token = token_data.get('access_token')
    if token:
        spotify_token_cache['token'] = token  # Cache the token
    return token


def sanitize_filename(song_name, author_name):
    combined_name = f"{song_name} - {author_name}" if author_name else song_name
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        combined_name = combined_name.replace(char, '_')
    return combined_name.strip().rstrip('.')


# Define the GitHub upload function
def github_upload_function(filename, filepath):
    with open(filepath, 'rb') as f:
        file_content = f.read()
    encoded_content = base64.b64encode(file_content).decode()
    file_url = f"downloads/{filename}"
    payload = {"message": f"Add {filename}", "content": encoded_content, "branch": "main"}
    headers = {"Authorization": f"Bearer {MY_GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    response = requests.put(f'{GITHUB_API_URL}{file_url}', headers=headers, data=json.dumps(payload))
    return response.json() if response.status_code == 201 else None
 
@app.route('/')
def index():
    # Retrieve user info from the session if available
    user_info = session.get('user_info', None)
    
    # Check if the user is logged in
    if user_info:
        # Extract profile details
        user_name = user_info['display_name']
        user_image = user_info['images'][0]['url'] if user_info['images'] else None
        user_email = user_info.get('email')
        
        # Pass the user info to the template
        return render_template('index.html', user_info=user_info, user_name=user_name, user_image=user_image, user_email=user_email)
    else:
       return render_template('index.html')

@app.route('/login')
def login():
    # Generate the authorization URL without additional parameters
    auth_url = sp_oauth.get_authorize_url()  # 'show_dialog' is handled in the initialization
    return redirect(auth_url)


# Callback route for Spotify to redirect after successful login
@app.route('/callback')
def callback():
    # Get the authorization code from the response
    token_info = sp_oauth.get_access_token(request.args['code'])
    session['token_info'] = token_info  # Store the token info in the session

    # Fetch the user's Spotify details to confirm login
    sp = Spotify(auth=token_info['access_token'])
    user_info = sp.current_user()

    # Store the user info in session
    session['user_info'] = user_info

    # Redirect to the homepage
    return redirect(url_for('index'))

# Protect routes that require login
@app.route('/user')
def user_info():
    token_info = session.get('token_info')
    
    # Check if the user is logged in by verifying token_info
    if token_info:
        try:
            sp = Spotify(auth=token_info['access_token'])
            user_data = sp.current_user()
            return jsonify({'success': True, 'user_data': user_data})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    else:
        # User is not logged in
        return jsonify({'success': False, 'error': 'User is not logged in'}), 401

# Define a /logout route to clear session and log out the user
@app.route('/logout')
def logout():
    session.clear()

    # Path to the Spotify cache file (this path is where SpotifyOAuth stores the cache by default)
    cache_path = f".cache-{SPOTIFY_CLIENT_ID}"
    if os.path.exists(cache_path):
        os.remove(cache_path)  # Delete the cached token file

    return redirect(url_for('index'))



@app.route('/search-spotify-song', methods=['POST'])
def search_spotify_song():
    try:
        search_term = request.json.get('searchTerm', '').strip()

        if not search_term:
            return jsonify({'success': False, 'error': 'No search term provided'}), 400

        token = get_spotify_token()
        if not token:
            return jsonify({'success': False, 'error': 'Unable to fetch Spotify token'}), 500

        search_response = requests.get(f'https://api.spotify.com/v1/search?q={search_term}&type=track', headers={
            'Authorization': f'Bearer {token}'
        })
        search_data = search_response.json()

        unique_songs = []
        song_set = set()

        for song in search_data.get('tracks', {}).get('items', []):
            song_identifier = f"{song['name']}-{song['artists'][0]['name']}"
            if song_identifier not in song_set:
                song_set.add(song_identifier)
                unique_songs.append(song)

        return jsonify({
            'success': True,
            'songs': unique_songs
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/song-info-to-audio-spotify', methods=['POST'])
def song_info_to_audio():
    try:
        data = request.json
        song_name = data.get('songName')
        author_name = data.get('authorName')
        spotify_song_url = data.get('spotifyUrl')

        if not all([song_name, author_name, spotify_song_url]):
            return jsonify({'success': False, 'error': 'songName, authorName, spotifyUrl are required'}), 400

        print(f"Received to /song-info-to-audio: {song_name} by {author_name}, Spotify URL: {spotify_song_url}")

        sanitized_song_name = sanitize_filename(song_name, author_name)
        filename = f"{sanitized_song_name}.mp3"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        file_url = f"downloads/{filename}"

        # Check if file exists on GitHub
        github_headers = {"Authorization": f"Bearer {MY_GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        response = requests.get(f'{GITHUB_API_URL}{file_url}', headers=github_headers)

        if response.status_code == 200:
            return jsonify({'success': True, 'audio_url': response.json()['download_url'], 'song_name': song_name})

        if os.path.exists(filepath):
            # File already exists locally, upload it to GitHub
            upload_url = request.host_url + 'github-upload'
            upload_response = requests.post(upload_url, json={'filename': filename, 'filepath': filepath}).json()

            if upload_response.get('success'):
                os.remove(filepath)
                return jsonify({'success': True, 'audio_url': upload_response['download_url'], 'song_name': song_name})

        # Fetch and download the song if not found on GitHub or locally
        api_url = "https://spotify-downloader9.p.rapidapi.com/downloadSong"
        querystring = {"songId": spotify_song_url}
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "spotify-downloader9.p.rapidapi.com"
        }

        response = requests.get(api_url, headers=headers, params=querystring).json()

        if response.get('success'): 
            download_link = response['data'].get('downloadLink')

            if download_link:
                # Download the audio file
                audio_response = requests.get(download_link, stream=True)
                with open(filepath, 'wb') as f:
                    f.write(audio_response.content)

                # Upload to GitHub after downloading
                upload_data = github_upload_function(filename, filepath)
                os.remove(filepath)  

                if upload_data['success']:
                    return jsonify({'success': True, 'audio_url': upload_data['download_url'], 'song_name': song_name})
                else:
                    return jsonify({'success': False, 'error': 'Error uploading file to GitHub'}), 500
            else:
                return jsonify({'success': False, 'error': 'No download link found in response'}), 500
        else:
            return jsonify({'success': False, 'error': 'Failed to fetch song from Spotify API'}), 500

    except Exception as e:
        print(f"Error in song_info_to_audio route: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
        

@app.route('/song-info-to-audio-yt', methods=['POST'])
def song_info_to_audio_yt():
    try:
        data = request.json
        song_name = data.get('songName')
        author_name = data.get('authorName', '')

        if not song_name:
            return jsonify({'success': False, 'error': 'Song name is required'}), 400

        filename = f"{sanitize_filename(song_name, author_name)}.mp3"
        file_url = f"downloads/{filename}"

        github_headers = {"Authorization": f"Bearer {MY_GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        response = requests.get(f'{GITHUB_API_URL}{file_url}', headers=github_headers)

        if response.status_code == 200:
            return jsonify({'success': True, 'audio_url': response.json()['download_url'], 'song_name': song_name})

        search_url = "https://www.googleapis.com/youtube/v3/search"
        search_query = f"{song_name} {author_name}".strip()
        search_params = {'part': 'snippet', 'q': search_query, 'key': YOUTUBE_API_KEY, 'type': 'video', 'maxResults': 1}
        
        with ThreadPoolExecutor() as executor:
            search_future = executor.submit(requests.get, search_url, params=search_params)
            search_response = search_future.result()
            video_id = search_response.json()['items'][0]['id']['videoId']

            conversion_url = "https://youtube-mp36.p.rapidapi.com/dl"
            conversion_params = {"id": video_id}
            conversion_headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "youtube-mp36.p.rapidapi.com"}
            conversion_future = executor.submit(requests.get, conversion_url, headers=conversion_headers, params=conversion_params)
            
            conversion_data = conversion_future.result().json()
            download_link = conversion_data.get('link')

            if not download_link:
                return jsonify({'success': False, 'error': 'Failed to convert YouTube video to audio'}), 500

            audio_response = requests.get(download_link, stream=True)
            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            with open(filepath, 'wb') as f:
                for chunk in audio_response.iter_content(chunk_size=1024): 
                    f.write(chunk)

            upload_data = github_upload_function(filename, filepath)
            os.remove(filepath)
            return jsonify({'success': True, 'audio_url': upload_data['content']['download_url'], 'song_name': song_name})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/downloads/<path:filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=2007)
 