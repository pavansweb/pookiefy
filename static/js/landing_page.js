
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

        let currentSong = null;
        let playlist = [];
        let currentIndex = 0;
        let isShuffled = false;
        let repeatMode = 'none'; // 'none', 'one', 'all'
        let get_audio_error = 0;
        let searchTimeout = null;



        const libraryBtn = document.querySelector('#library-btn');
            const loginModal = document.getElementById('login-modal');
            const closeBtn = document.querySelector('.close-btn');
            const spotifyLoginBtn = document.querySelector('.spotify-login-btn');

    

    // Add event listeners with null checks
    if (shuffleButton) {
        shuffleButton.addEventListener('click', showModal);
    }

    if (repeatButton) {
        repeatButton.addEventListener('click', showModal);
    }

    if (libraryBtn) {
        libraryBtn.addEventListener('click', showModal);
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', hideModal);
    }

    // Close modal if clicking outside the modal content
    if (loginModal) {
        loginModal.addEventListener('click', (event) => {
            if (event.target === loginModal) {
                hideModal();
            }
        });

        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && loginModal.classList.contains('show')) {
                hideModal();
            }
        });
    }

// Function to toggle visibility of the navbar based on screen width
function toggleNavbarVisibility() {
    const navbar = document.querySelector('.navbar');
    
    // Check if the screen width is 768px or smaller
    if (window.innerWidth <= 768) {
        navbar.style.display = 'none'; // Hide the navbar
    } else {
        navbar.style.display = 'block'; // Show the navbar
    }
}

// Run the function when the page loads and when the window is resized
window.addEventListener('load', toggleNavbarVisibility);
window.addEventListener('resize', toggleNavbarVisibility);


async function performSearch(searchTerm) {
    try {
        const response = await fetch('https://pookiefy-song-routes.onrender.com/search-spotify-song', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ searchTerm }),
        });
        const data = await response.json();
        if (data.success) {
            displaySearchResults(data.songs);
            console.log(data.songs)
        } else {
            console.error('Search failed:', data.error);
        }
    } catch (error) {
        console.error('Error during search:', error);
    }
}



async function playSong(song) {
        if (get_audio_error < 1) {
            loaderOverlay.classList.add('active');
            try {
                const response = await fetch('https://pookiefy-song-routes.onrender.com/song-info-to-audio', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        songName: song.name,
                        spotifyUrl: song.external_urls.spotify,
                        authorName: song.artists.map(artist => artist.name).join(', ')
                    }),
                });
                const data = await response.json();
                if (data.success) {
                    get_audio_error = 0;
                    currentSong = {
                        ...song,
                        audioUrl: data.audio_url,
                    };
                    audioPlayer.src = currentSong.audioUrl;
                    audioPlayer.play();
                    loaderOverlay.classList.remove('active');
                    updateNowPlaying();
                } else {
                    get_audio_error += 1;
                    console.error('Failed to get audio:', data.error);
                    playSong(song);
                }
            } catch (error) {
                get_audio_error += 1;
                console.error('Error getting audio:', error);
                playSong(song);
            }
        }
        else {
            loaderOverlay.innerHTML = "<h1>Error</h1>";

            // Wait for 5 seconds
            setTimeout(() => {
                loaderOverlay.classList.remove('active');
            }, 2000); 
        }

    }


function updateNowPlaying() {
    if (currentSong) {
        currentSongImage.src = currentSong.album.images[0].url;
        currentSongName.textContent = currentSong.name;
        currentSongArtist.textContent = currentSong.artists.map(artist => artist.name).join(', ');
    }
}

playPauseButton.addEventListener('click', togglePlayPause);
previousButton.addEventListener('click', playPrevious);
nextButton.addEventListener('click', playNext);

function togglePlayPause() {
    if (audioPlayer.paused) {
        audioPlayer.play();
    } else {
        audioPlayer.pause();
    }
}

function playPrevious() {
    if (currentIndex > 0) {
        currentIndex--;
    } else {
        currentIndex = playlist.length - 1;
    }
    playSong(playlist[currentIndex]);
}

function playNext() {
    if (currentIndex < playlist.length - 1) {
        currentIndex++;
    } else {
        currentIndex = 0;
    }
    playSong(playlist[currentIndex]);
}



audioPlayer.addEventListener('play', () => {
    playPauseButton.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="6" y="4" width="4" height="16"></rect>
            <rect x="14" y="4" width="4" height="16"></rect>
        </svg>
    `;
});

audioPlayer.addEventListener('pause', () => {
    playPauseButton.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
    `;
});

audioPlayer.addEventListener('timeupdate', () => {
    const currentTime = audioPlayer.currentTime;
    const duration = audioPlayer.duration;
    progressSlider.value = (currentTime / duration) * 100;
    currentTimeDisplay.textContent = formatTime(currentTime);
    durationDisplay.textContent = formatTime(duration);
});

audioPlayer.addEventListener('ended', () => {
    if (repeatMode === 'one') {
        audioPlayer.currentTime = 0;
        audioPlayer.play();
    } else if (repeatMode === 'all' || currentIndex < playlist.length - 1) {
        playNext();
    } else {
        currentIndex = 0;
        playSong(playlist[currentIndex]);
    }
});

progressSlider.addEventListener('input', () => {
    const time = (progressSlider.value / 100) * audioPlayer.duration;
    audioPlayer.currentTime = time;
});

volumeSlider.addEventListener('input', () => {
    audioPlayer.volume = volumeSlider.value / 100;
});

function formatTime(time) {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

// Keyboard controls
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space') {
        togglePlayPause();
    } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        audioPlayer.currentTime = Math.max(0, audioPlayer.currentTime - 5);
    } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        audioPlayer.currentTime = Math.min(audioPlayer.duration, audioPlayer.currentTime + 5);
    } else if (e.code === 'ArrowUp') {
        e.preventDefault();
        volumeSlider.value = Math.min(100, parseInt(volumeSlider.value) +

10);
        audioPlayer.volume = volumeSlider.value / 100;
    } else if (e.code === 'ArrowDown') {
        e.preventDefault();
        volumeSlider.value = Math.max(0, parseInt(volumeSlider.value) - 10);
        audioPlayer.volume = volumeSlider.value / 100;
    }
});

document.querySelector('.cta-button').addEventListener('mouseover', function() {
    const waves = document.querySelectorAll('.wave');
    waves.forEach(wave => {
        wave.style.backgroundColor = '#1DB954';
    });
});

document.querySelector('.cta-button').addEventListener('mouseout', function() {
    const waves = document.querySelectorAll('.wave');
    waves.forEach(wave => {
        wave.style.backgroundColor = 'white';
    });
});