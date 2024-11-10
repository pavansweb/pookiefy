from flask import Flask, request, jsonify, send_from_directory, render_template
import requests
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

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Load credentials and configuration from environment variables
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
MY_GITHUB_TOKEN = os.getenv('MY_GITHUB_TOKEN_FOR_POOKIEFY')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'pavansweb/pookiefy-song-storage')
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/"
RAPIDAPI_KEYS = [os.getenv('RAPIDAPI_KEY1'), os.getenv('RAPIDAPI_KEY2'), os.getenv('RAPIDAPI_KEY3'), os.getenv('RAPIDAPI_KEY4')]
RAPIDAPI_KEY = random.choice(RAPIDAPI_KEYS)

spotify_token_cache = TTLCache(maxsize=1, ttl=3600)

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
    print(SPOTIFY_CLIENT_ID)
    return render_template('index.html')

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
 