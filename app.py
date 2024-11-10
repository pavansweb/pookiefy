from flask import Flask, request, jsonify, send_from_directory, render_template
import requests
import os
import base64
import json
from datetime import datetime
from dotenv import load_dotenv
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
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY1')
RAPIDAPI_KEY2 = os.getenv('RAPIDAPI_KEY2')
RAPIDAPI_KEY3 = os.getenv('RAPIDAPI_KEY3')
RAPIDAPI_KEY4 = os.getenv('RAPIDAPI_KEY4')

# Define the directory to save downloads
DOWNLOAD_FOLDER = os.path.join(app.root_path, 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def sanitize_filename(song_name, author_name):
    combined_name = f"{song_name} - {author_name}" if author_name else song_name
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        combined_name = combined_name.replace(char, '_')
    return combined_name.strip().rstrip('.')


# Define the GitHub upload function
def github_upload_function(filename, filepath):
    try:
        with open(filepath, 'rb') as f:
            file_content = f.read()
        encoded_content = base64.b64encode(file_content).decode()

        file_url = f"downloads/{filename}"
        payload = {
            "message": f"Add {filename}",
            "content": encoded_content,
            "branch": "main"
        }

        headers = {
            "Authorization": f"Bearer {MY_GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        response = requests.put(f'{GITHUB_API_URL}{file_url}', headers=headers, data=json.dumps(payload))

        if response.status_code == 201:
            file_info = response.json()
            download_url = file_info['content']['download_url']
            return {'success': True, 'download_url': download_url}
        else:
            print("Error uploading file to GitHub:", response.json())
            return {'success': False, 'error': response.json()}

    except Exception as e:
        print("Error in github_upload_function:", e)
        return {'success': False, 'error': str(e)}
 
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

        token_response = requests.post('https://accounts.spotify.com/api/token', data={
            'grant_type': 'client_credentials'
        }, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + base64.b64encode(f'{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}'.encode()).decode()
        })
        token_data = token_response.json()
        token = token_data.get('access_token')

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

        if not song_name or not spotify_song_url:
            return jsonify({'success': False, 'error': 'Both song name and Spotify URL are required'}), 400

        print("Received song name:", song_name)
        print("Received Spotify song URL:", spotify_song_url)

        sanitized_song_name = sanitize_filename(song_name,author_name)
        filename = f"{sanitized_song_name}.mp3"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)

        file_url = f"downloads/{filename}"
        github_headers = {
            "Authorization": f"Bearer {MY_GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        response = requests.get(f'{GITHUB_API_URL}{file_url}', headers=github_headers)

        if response.status_code == 200:
            file_info = response.json() 
            download_url = file_info['download_url']
            print("The song file already exists in GitHub. Providing the direct link:", download_url)          
            return jsonify({
                'success': True,
                'audio_url': download_url,
                'song_name': song_name,
            })
        elif response.status_code == 404:
            print(f"File does not exist on GitHub, proceeding to download: {filename}")

            if os.path.exists(filepath):
                print(f"File already exists locally: {filename}")
                
                # Call the new route for GitHub upload
                upload_url = request.host_url + 'github-upload'
                upload_response = requests.post(upload_url, json={'filename': filename, 'filepath': filepath})
                upload_data = upload_response.json()

                if upload_data.get('success') and upload_data.get('download_url'):
                    os.remove(filepath)  # Remove local file after uploading
                    print(f"Local file {filename} removed after upload.")
                    return jsonify({
                        'success': True,
                        'audio_url': upload_data['download_url'],
                        'song_name': song_name,
                    })
                else:
                    return jsonify({'success': False, 'error': 'Error uploading file to GitHub'}), 500

            api_url = "https://spotify-downloader9.p.rapidapi.com/downloadSong"
            querystring = {"songId": spotify_song_url}
            headers = {
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": "spotify-downloader9.p.rapidapi.com"
            }

            response = requests.get(api_url, headers=headers, params=querystring)
            response_data = response.json()

            if response.status_code == 200 and response_data.get('success'):
                data = response_data.get('data', {})
                download_link = data.get('downloadLink')

                if download_link:
                    audio_response = requests.get(download_link, stream=True)
                    with open(filepath, 'wb') as f:
                        f.write(audio_response.content)

                    upload_data = github_upload_function(filename, filepath)
                    if upload_data['success']:
                        os.remove(filepath)  # Remove the local file after upload
                        return jsonify({
                            'success': True,
                            'audio_url': upload_data['download_url'],
                            'song_name': song_name,
                        })
                    else:
                        return jsonify({'success': False, 'error': 'Error uploading file to GitHub'}), 500
                else: 
                    return jsonify({'success': False, 'error': 'No download link found in response'}), 500
            else:
                error_message = response_data.get('message', 'Unknown error from Spotify API')
                print("Error from Spotify downloader API:", error_message)
                return jsonify({'success': False, 'error': error_message}), 500
        else:
            print("Error checking file on GitHub:", response.json())
            return jsonify({'success': False, 'error': 'Error checking file on GitHub'}), 500

    except Exception as e:
        print("Error in song_info_to_audio route:", e)
        return jsonify({'success': False, 'error': str(e)}), 500
        

@app.route('/song-info-to-audio-yt', methods=['POST'])
def song_info_to_audio_yt():
    try:
        data = request.json
        song_name = data.get('songName')
        author_name = data.get('authorName')  # Get the author's name from the request data
        print(song_name,"by", author_name) 

        if not song_name:
            return jsonify({'success': False, 'error': 'Song name is required'}), 400

        # Step 1: Check if the file already exists on GitHub
        sanitized_song_name = sanitize_filename(song_name,author_name)
        filename = f"{sanitized_song_name}.mp3"
        file_url = f"downloads/{filename}"
        github_headers = {
            "Authorization": f"Bearer {MY_GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Check if the file exists on GitHub
        response = requests.get(f'{GITHUB_API_URL}{file_url}', headers=github_headers)

        if response.status_code == 200:
            file_info = response.json()
            download_url = file_info['download_url']
            print(f"The song file already exists in GitHub. Providing the direct link: {download_url}")
            return jsonify({
                'success': True,
                'audio_url': download_url,
                'song_name': song_name,
            })
        elif response.status_code == 404:
            print(f"File does not exist on GitHub, proceeding to download: {filename}")

            # Step 2: Search YouTube for the song using both song name and author
            search_url = "https://www.googleapis.com/youtube/v3/search"
            search_query = f"{song_name} {author_name}" if author_name else song_name  # Include author if available
            search_params = {
                'part': 'snippet',
                'q': search_query,
                'key': YOUTUBE_API_KEY,
                'type': 'video', 
                'maxResults': 1
            } 
            search_response = requests.get(search_url, params=search_params)
            search_data = search_response.json()

            if 'items' not in search_data or not search_data['items']:
                return jsonify({'success': False, 'error': 'No YouTube video found for the song'}), 404

            video_id = search_data['items'][0]['id']['videoId']
            print(f"Found YouTube video ID: {video_id}")

            # Step 3: Convert YouTube video to MP3 using RapidAPI
            conversion_url = "https://youtube-mp36.p.rapidapi.com/dl"
            conversion_params = {"id": video_id}
            conversion_headers = {
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": "youtube-mp36.p.rapidapi.com"
            }
            conversion_response = requests.get(conversion_url, headers=conversion_headers, params=conversion_params)
            conversion_data = conversion_response.json()

            if conversion_data.get("status") != "ok" or "link" not in conversion_data:
                return jsonify({'success': False, 'error': 'Error converting YouTube video to audio'}), 500

            download_link = conversion_data['link']
            print(f"Downloading audio from: {download_link}")

            # Step 4: Download and save the audio file
            filepath = os.path.join(DOWNLOAD_FOLDER, filename)

            audio_response = requests.get(download_link, stream=True)
            with open(filepath, 'wb') as f:
                f.write(audio_response.content)

            print(f"Download complete: {filepath}")

            # Step 5: Upload the file to GitHub using github_upload_function
            upload_data = github_upload_function(filename, filepath)

            if upload_data.get('success') and upload_data.get('download_url'):
                os.remove(filepath)  # Remove the local file after upload
                print(f"Local file {filename} removed after upload.")
                return jsonify({
                    'success': True,
                    'audio_url': upload_data['download_url'],
                    'song_name': song_name,
                })
            else:
                return jsonify({'success': False, 'error': 'Error uploading file to GitHub'}), 500

        else:
            return jsonify({'success': False, 'error': 'Error checking file on GitHub'}), 500

    except Exception as e:
        print("Error in song_info_to_audio_yt route:", e)
        return jsonify({'success': False, 'error': str(e)}), 500





@app.route('/downloads/<path:filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=2007)
 