
const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');
const audioPlayer = document.getElementById('audio-player');
const playPauseButton = document.getElementById('play-pause-button');
const previousButton = document.getElementById('previous-button');
const nextButton = document.getElementById('next-button');
const shuffleButton = document.getElementById('shuffle-button');
const repeatButton = document.getElementById('repeat-button');
const progressSlider = document.getElementById('progress-slider');
const currentTimeDisplay = document.getElementById('current-time');
const durationDisplay = document.getElementById('duration');
const volumeSlider = document.getElementById('volume-slider');
const currentSongImage = document.getElementById('current-song-image');
const currentSongName = document.getElementById('current-song-name');
const currentSongArtist = document.getElementById('current-song-artist');
const loaderOverlay = document.getElementById('loader-overlay');
const loginLink = document.getElementById('login-link');
const userProfile = document.querySelector('.user-profile');
const profilePicture = document.getElementById('profile-picture');
const profileDropdown = document.querySelector('.profile-dropdown');
document.querySelector('.homepage-container').style.display = 'none'

let currentSong = null;
let playlist = [];
let currentIndex = 0;
let isShuffled = false;
let repeatMode = 'none'; // 'none', 'one', 'all'
let get_audio_error = 0;
let isLoggedIn = false;
let searchTimeout = null;

const artists = ["The weekend","Taylor Swift","The Neighborhood"];
const randomArtist = artists[Math.floor(Math.random() * artists.length)];




document.getElementById('nav-search-btn').addEventListener('click', function() {
    document.getElementById('search-input').focus();
    document.getElementById('search-input').placeholder = "Search here!!" ;
});

document.getElementById('hamburger-btn').addEventListener('click', function() {
    if (document.querySelector('.navbar').style.display == 'none') {
        document.querySelector('.navbar').style.display = 'flex';
    } else {
        document.querySelector('.navbar').style.display = 'none';
    }
});



   

function displaySearchResults(songs) {
    document.querySelector('.homepage-container').style.display = 'none'
    document.querySelector('#searchResultsHeading').style.display = 'block'
    searchResults.innerHTML = '';
    songs.forEach(song => {
        const songCard = document.createElement('div');
        songCard.className = 'song-card';
        songCard.innerHTML = `
            <img src="${song.album.images[0].url}" alt="${song.name} album cover">
            <h3>${song.name}</h3>
            <p>${song.artists.map(artist => artist.name).join(', ')}</p>
        `;
        songCard.addEventListener('click', () => {
            playlist = songs;
            currentIndex = playlist.indexOf(song);
            playSong(song);
        });
        searchResults.appendChild(songCard); 
    });
}








checkUserLogin();

