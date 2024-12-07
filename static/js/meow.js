// Run the function when the page loads and when the window is resized
window.addEventListener('load', toggleNavbarVisibility);
window.addEventListener('resize', toggleNavbarVisibility);
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

document.addEventListener("DOMContentLoaded", () => {
    
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
    const logoutLink = document.getElementById('logout-link');
    const dynamicMainContent = document.getElementById('dynamic-content');

    let currentSong = null;
    let playlist = [];
    let currentIndex = 0;
    let isShuffled = false;
    let repeatMode = 'none'; // 'none', 'one', 'all'
    let get_audio_error = 0;
    let searchTimeout = null;
    let currentPage = "home";
    console.log(currentPage);



    const libraryBtn = document.querySelector('#library-btn');
    const loginModal = document.getElementById('login-modal');
    const closeBtn = document.querySelector('.close-btn');
    const spotifyLoginBtn = document.querySelector('.spotify-login-btn');

    // Function to show the modal
    function showModal() {
        if (loginModal) {
            loginModal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }

    // Function to hide the modal
    function hideModal() {
        if (loginModal) {
            loginModal.classList.remove('show');
            document.body.style.overflow = 'auto';
        }
    }

    
    function displayMessage(message, duration = null) {
        const messageContainer = document.getElementById('custom-message');
        const messageContent = document.getElementById('message-content');
        const closeButton = document.getElementById('message-close');

        // Set message text
        messageContent.textContent = message;

        // Show the message
        messageContainer.style.display = 'block';

        // Close button event
        closeButton.onclick = () => {
            messageContainer.style.display = 'none';
        };

        // Auto-close if duration is specified
        if (duration !== null) {
            setTimeout(() => {
                messageContainer.style.display = 'none';
            }, duration * 1000);
        }
    }

    

    if (isLoggedIn) {
        
        console.log("User is logged in. Loading personalized content...");
        checkUserLogin()
        document.querySelector('.logout-btn-nav').style.display = 'block';
        document.querySelector('#header-login-link').style.display = "none"
        // Add event listener to the home button
        document.getElementById('home-button').addEventListener('click', loadLoggedInUserHomePageContent);


        // Load logged-in content
        function loadLoggedInUserHomePageContent() {
            
        toggleNavbarVisibility();
            console.log('hi');
            $.ajax({
                url: '/logged-in-user',  // Flask route for logged-in users
                type: 'GET',
                success: function(response) {
                    if (response.success) {
                        console.log(response);
                        currentPage = "home";
                        $('#dynamic-content').html(response.user_data);  // Replace main content with the logged-in partial
                        checkUserLogin();  // Function to check if the user is logged in (assuming it's already defined)
                        document.getElementById('search-input').focus();
                    } else {
                        alert("You need to log in");
                    }
                },
                error: function() {
                    alert("Error loading logged-in content");
                }
            });
        }
        

        libraryBtn.addEventListener('click', (e) => {
            $.get('/library', function(data) {
                // On success, inject the returned HTML content into the libraryContainer
                $('#dynamic-content').html(data);
                currentPage = "library";
                toggleNavbarVisibility();
                console.log(currentPage);
            }).fail(function() {
                alert('Error loading library data');
            });
        });

        // Logout functionality
        logoutLink.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                const response = await fetch('/logout', { method: 'POST' });
                if (response.ok) {
                    window.location.href = "/";
                } else {
                    console.error('Logout failed');
                }
            } catch (error) {
                console.error('Error during logout:', error);
            }
        });


        async function checkUserLogin() {
            try {
                const response = await fetch('/user');  
        
                if (!response.ok) {
                    return;
                }
        
                const data = await response.json();
        
                if (data.success && data.user_data) {
                    console.log(data);
                    updateLoginState(true, data);
                } else {
                    console.log('User is not logged in.');
                    updateLoginState(false);
                }
            } catch (error) {
                console.error('Error checking user login:', error.message);
                updateLoginState(false);
            }
        }
        
        function updateLoginState(isLoggedIn, data = null) {
            console.log(isLoggedIn,data);
            const userProfile = document.querySelector('.user-profile');
            const userName = document.getElementById('user-name');
            const profilePicture = document.getElementById('profile-picture');
        
            if (isLoggedIn) {
                userProfile.style.display = 'flex';
                userName.textContent = data.user_data.display_name;
                profilePicture.src = data.user_data.images[0]?.url || 'https://via.placeholder.com/32';
                profilePicture.alt = data.user_data.display_name;
        
                document.querySelector('.homepage-container').style.display = 'flex'
                displayFavoriteSongs(data.favorite_tracks);
                displayFavoriteArtists(data.favorite_artists);
                displayRecentlyPlayed(data.recently_played);
            } else {
                
            }
        }


        
        function displayFavoriteSongs(favoriteTracks) {
            const topSongsContainer = document.querySelector('#top-songs .item-grid');
            topSongsContainer.innerHTML = ''; // Clear existing content

            favoriteTracks.forEach(track => {
                const trackElement = document.createElement('div');
                trackElement.classList.add('item');

                // Album image
                const albumImage = document.createElement('img');
                albumImage.src = track.album.images[0]?.url || 'https://via.placeholder.com/150';
                albumImage.alt = track.name;

                // Song name
                const trackName = document.createElement('h3');
                trackName.textContent = track.name;

                // Artist names
                const artistNames = document.createElement('p');
                artistNames.textContent = track.artists.map(artist => artist.name).join(', ');

                // Append elements to the track item
                trackElement.appendChild(albumImage);
                trackElement.appendChild(trackName);
                trackElement.appendChild(artistNames);

                // Add click event to play the song
                trackElement.addEventListener('click', () => {
                    playlist = favoriteTracks;
                    currentIndex = favoriteTracks.indexOf(track);
                    playSong(track);
                });

                // Append track item to the container
                topSongsContainer.appendChild(trackElement);
            });
        }

        function displayRecentlyPlayed(recentlyPlayedTracks) {
            const recentlyPlayedContainer = document.querySelector('#recently-played .item-grid');
            recentlyPlayedContainer.innerHTML = ''; // Clear existing content

            recentlyPlayedTracks.forEach(track => {
                const trackElement = document.createElement('div');
                trackElement.classList.add('item');

                // Album image
                const albumImage = document.createElement('img');
                albumImage.src = track.album.images[0]?.url || 'https://via.placeholder.com/150';
                albumImage.alt = track.name;

                // Track name
                const trackName = document.createElement('h3');
                trackName.textContent = track.name;

                // Artist names
                const artistNames = document.createElement('p');
                artistNames.textContent = track.artists.map(artist => artist.name).join(', ');

                // Append elements to the track item
                trackElement.appendChild(albumImage);
                trackElement.appendChild(trackName);
                trackElement.appendChild(artistNames);

                // Add click event to play the song
                trackElement.addEventListener('click', () => {
                    playlist = recentlyPlayedTracks;
                    currentIndex = recentlyPlayedTracks.indexOf(track);
                    playSong(track);
                });

                // Append track item to the container
                recentlyPlayedContainer.appendChild(trackElement);
            });
        }

        // Populate favorite artists in the "Favorite Artists" section
        function displayFavoriteArtists(favoriteArtists) {
            const favoriteArtistsContainer = document.querySelector('#favorite-artists .item-grid');
            favoriteArtistsContainer.innerHTML = ''; // Clear existing content

            favoriteArtists.forEach(artist => {
                const artistElement = document.createElement('div');
                artistElement.classList.add('item');

                // Artist image
                const artistImage = document.createElement('img');
                artistImage.src = artist.images[0]?.url || 'https://via.placeholder.com/150';
                artistImage.alt = artist.name;

                // Artist name
                const artistName = document.createElement('h3');
                artistName.textContent = artist.name;

                // Append elements to the artist item
                artistElement.appendChild(artistImage);
                artistElement.appendChild(artistName);

                // Append artist item to the container
                favoriteArtistsContainer.appendChild(artistElement);
            });

            

        }

    } else { // is user is not logged in else block
        console.log("User is not logged in. Showing guest content...");
        document.querySelector('.logout-btn-nav').style.display = 'none';
        document.querySelector('#header-login-link').style.display = "block"

        libraryBtn.addEventListener('click', (e) =>{
            showModal();
         })
        

    }


    function displaySearchResults(songs , isLoggedIn) {
        console.log("Displaying Search Results");
        if (isLoggedIn) {
            document.querySelector('.homepage-container').style.display = 'none'
        } else {
            document.querySelector('.defaultHomePageWithoutLogin').style.display = 'none';
        }
        document.querySelector('#searchResultsHeading').style.display = 'block'
        
    const searchResults = document.getElementById('search-results');
        
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
    
    
    document.getElementById('nav-search-btn').addEventListener('click', function () {
        toggleNavbarVisibility();
        if (currentPage !== "home") {
            loadLoggedInUserHomePageContent();
        } else {

            document.getElementById('search-input').focus();
            document.getElementById('search-input').placeholder = "Search here!!";
        }
    });
    
    document.getElementById('hamburger-btn').addEventListener('click', function() {
        toggleNavbarVisibility();
    });
    function toggleNavbarVisibility() {
        if (window.innerWidth <= 760) {
            const navbar = document.querySelector('.navbar');
            if (navbar.style.display == 'none') {
                navbar.style.display = 'block'; // Hide the navbar
            } else {
                navbar.style.display = 'none'; // Show the navbar
            }
        } else {

        }

    }
    
  

    searchInput.addEventListener('input', () => {

        if (window.innerWidth <= 768) {
            
        document.querySelector('.navbar').style.display = 'none';
        }
        
        if (currentPage != "home") {
            loadLoggedInUserHomePageContent();
        }
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const searchTerm = searchInput.value.trim();
            if (searchTerm.length > 0) {
                performSearch(searchTerm);
            } else {
                searchResults.innerHTML = '';
            }
        }, 10);
    });

    document.getElementById('search-input').addEventListener('input', () =>{
        const searchTerm = document.getElementById('search-input').value.trim;
        if (searchTerm.length > 0) {
            performSearch(searchTerm);
        } else {
            searchResults.innerHTML = '';
        }
    })
    
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
                displaySearchResults(data.songs , isLoggedIn);
                console.log("Completed Performing Search")
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
    shuffleButton.addEventListener('click', toggleShuffle);
    repeatButton.addEventListener('click', toggleRepeat);
    
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
    
    function toggleShuffle() {
        isShuffled = !isShuffled;
        shuffleButton.style.color = isShuffled ? '#1DB954' : '#b3b3b3';
        if (isShuffled) {
            shufflePlaylist();
        } else {
            // Restore original order
            playlist.sort((a, b) => a.originalIndex - b.originalIndex);
        }
    }
    
    function shufflePlaylist() {
        for (let i = playlist.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [playlist[i], playlist[j]] = [playlist[j], playlist[i]];
        }
        currentIndex = playlist.findIndex(song => song.id === currentSong.id);
    }
    
    function toggleRepeat() {
        if (repeatMode === 'none') {
            repeatMode = 'all';
            repeatButton.style.color = '#1DB954';
        } else if (repeatMode === 'all') {
            repeatMode = 'one';
            repeatButton.style.color = '#1DB954';
            repeatButton.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="17 1 21 5 17 9"></polyline>
                    <path d="M3 11V9a4 4 0 0 1 4-4h14"></path>
                    <polyline points="7 23 3 19 7 15"></polyline>
                    <path d="M21 13v2a4 4 0 0 1-4 4H8"></path>
                    <text x="11" y="15" font-size="8" fill="currentColor">1</text>
                </svg>
            `;
        } else {
            repeatMode = 'none';
            repeatButton.style.color = '#b3b3b3';
            repeatButton.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="17 1 21 5 17 9"></polyline>
                    <path d="M3 11V9a4 4 0 0 1 4-4h14"></path>
                    <polyline points="7 23 3 19 7 15"></polyline>
                    <path d="M21 13v2a4 4 0 0 1-4 4H3"></path>
                </svg>
            `;
        }
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
});
