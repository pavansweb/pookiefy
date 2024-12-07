from flask import Flask, request, jsonify, render_template, redirect, session, url_for
import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
import base64
from dotenv import load_dotenv
from cachetools import TTLCache
from flask_cors import CORS  # Import Flask-CORS

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)  
app.secret_key = os.urandom(24)

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins
 
# Load credentials and configuration from environment variables
SPOTIFY_CLIENT_ID = '9241546ed80f472785347051926375e2'
SPOTIFY_CLIENT_SECRET = 'ca7e1e03d6084328ad96faf52930b171'
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI') 


spotify_token_cache = {}  # Use a simple dictionary without expiration

 
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

# Function to ping a website
def ping_website(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return {"message": f"{url}  is up", "status_code": response.status_code}
        else:
            return {"message": "Website is down or unreachable", "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"message": "Error reaching the website", "error": str(e)}
    
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

def get_spotify_client():
    token_info = session.get('token_info')

    if not token_info:
        return None

    # Check if token has expired and refresh it
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info  # Update session with the new token info

    return Spotify(auth=token_info['access_token'])


@app.route('/non-logged-in')
def non_logged_in():
    # For non-logged-in users, render the guest main content
    return render_template('partials/guest_main.html')

@app.route('/logged-in-user')
def user():
    # For logged-in users, render the logged-in main content
    user_info = session.get('user_info', None)
    if user_info:
        # Render the template for logged-in users
        rendered_content = render_template('partials/logged_in_main.html', user_info=user_info)
        return jsonify({'success': True, 'user_data': rendered_content})
    else:
        # If not logged in, return a failure response
        return jsonify({'success': False, 'error': 'You need to log in'}), 401

# Route for non-logged-in users
@app.route('/')
def index():
    # Ping a website to ensure it's up
    print(ping_website('https://pookiefy-song-routes.onrender.com'))

    # Check if the user is logged in
    user_info = session.get('user_info', None)
    is_logged_in = bool(user_info)

    if user_info: 
        # User is logged in: Load logged-in content
        main_content = render_template('partials/logged_in_main.html', user_info=user_info)
    else:
        # User is not logged in: Load guest content
        main_content = render_template('partials/guest_main.html')

    # Render the landing page with dynamic main content
    return render_template('landing_page.html', main_content=main_content ,is_logged_in=is_logged_in)

@app.route('/library')
def library():
    # Check if the user is logged in
    token_info = session.get('token_info')
    
    print("Token info:", token_info)  # Debug print to check token information
    
    if token_info:
        try:
            # Create a Spotify instance using the stored access token
            sp = Spotify(auth=token_info['access_token'])
            print("Spotify instance created successfully.")  # Debug print
            
            # Fetch the user's playlists
            playlists = sp.current_user_playlists(limit=10)  # Fetch top 10 playlists
            print("Fetched playlists:", playlists)  # Debug print to check fetched playlists

            # Check if 'items' exists in the response
            if 'items' in playlists:
                print("'items' found in playlists.")  # Debug print
                # Format the playlists to be passed to the template
               # Filter out None values from playlists
                formatted_playlists = [
                    {
                        'name': playlist['name'],
                        'id': playlist['id'],
                        'description': playlist['description'],
                        'external_urls': playlist['external_urls'],
                        'images': playlist['images'],
                    }
                    for playlist in playlists['items'] if playlist is not None
                ]

                print("Formatted playlists:", formatted_playlists)  # Debug print to check formatted playlists
            else:
                print("'items' not found in playlists response.")  # Debug print if 'items' is missing
                formatted_playlists = []

            # Render the library template with the playlists
            return render_template('partials/library.html', playlists=formatted_playlists)
        
        except Exception as e:
            print("Error occurred:", e)  # Debug print to check error
            return jsonify({'success': False, 'error': str(e)}), 500
    else:
        print("User is not logged in.")  # Debug print to check if the user is logged in
        # User is not logged in
        return redirect(url_for('index'))


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
            
            # Fetch the user's info
            user_data = sp.current_user()

            # Fetch the user's favorite songs (top tracks)
            favorite_tracks = sp.current_user_top_tracks(limit=10)

            # Fetch the user's favorite artists (top artists)
            favorite_artists = sp.current_user_top_artists(limit=10)

            # Fetch the user's recently played tracks
            recently_played = sp.current_user_recently_played(limit=10)

            # Organize the favorite tracks, artists, and recently played tracks
            formatted_favorite_tracks = [
                {
                    'album': track['album'],
                    'artists': track['artists'],
                    'available_markets': track['available_markets'],
                    'disc_number': track['disc_number'],
                    'duration_ms': track['duration_ms'],
                    'explicit': track['explicit'],
                    'external_ids': track['external_ids'],
                    'external_urls': track['external_urls'],
                    'href': track['href'],
                    'id': track['id'],
                    'is_local': track['is_local'],
                    'name': track['name'],
                    'popularity': track['popularity'],
                    'preview_url': track['preview_url'],
                    'track_number': track['track_number'],
                    'type': track['type'],
                    'uri': track['uri']
                }
                for track in favorite_tracks['items']
            ]

            formatted_favorite_artists = [
                {
                    'name': artist['name'],
                    'genres': artist['genres'],
                    'href': artist['href'],
                    'id': artist['id'],
                    'images': artist['images'],
                    'popularity': artist['popularity'],
                    'type': artist['type'],
                    'uri': artist['uri']
                }
                for artist in favorite_artists['items']
            ]

            formatted_recently_played = [
                {
                    'album': item['track']['album'],
                    'artists': item['track']['artists'],
                    'available_markets': item['track']['available_markets'],
                    'disc_number': item['track']['disc_number'],
                    'duration_ms': item['track']['duration_ms'],
                    'explicit': item['track']['explicit'],
                    'external_ids': item['track']['external_ids'],
                    'external_urls': item['track']['external_urls'],
                    'href': item['track']['href'],
                    'id': item['track']['id'],
                    'is_local': item['track']['is_local'],
                    'name': item['track']['name'],
                    'popularity': item['track']['popularity'],
                    'preview_url': item['track']['preview_url'],
                    'track_number': item['track']['track_number'],
                    'type': item['track']['type'],
                    'uri': item['track']['uri']
                }
                for item in recently_played['items']
            ]

            # Return data in the required format
            return jsonify({
                'success': True,
                'user_data': user_data,
                'favorite_tracks': formatted_favorite_tracks,
                'favorite_artists': formatted_favorite_artists,
                'recently_played': formatted_recently_played
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    else:
        # User is not logged in
        return jsonify({'success': False, 'error': 'User is not logged in'}), 401



# Define a /logout route to clear session and log out the user
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()

    # Path to the Spotify cache file (this path is where SpotifyOAuth stores the cache by default)
    cache_path = f".cache-{SPOTIFY_CLIENT_ID}"
    if os.path.exists(cache_path):
        os.remove(cache_path)  # Delete the cached token file

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=2007)