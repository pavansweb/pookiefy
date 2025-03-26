from flask import Flask, request, jsonify,render_template
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

@app.route('/search')
def search():
    query = request.args.get('query', '')
    url = f"https://jio-saavan-api-gold.vercel.app/api/search/songs?query={query}&page=1&limit=40"
    response = requests.get(url)
    return jsonify(response.json())

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
