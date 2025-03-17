// Function to toggle the sidebar visibility
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

// Close sidebar when clicking outside of it
document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('sidebar');
    const hamburger = document.querySelector('.hamburger');
    const searchDropdown = document.getElementById('searchDropdown');
    const searchDropdown2 = document.getElementById('searchDropdown2');
    const searchInput = document.getElementById('searchInput');
    const searchInput2 = document.getElementById('searchInput2');

    // Check if the click is outside of the sidebar and hamburger button
    if (!sidebar.contains(e.target) && !hamburger.contains(e.target)) {
        sidebar.classList.remove('open');
    }

    // Hide search dropdown when clicking outside of it
    if (!searchDropdown.contains(e.target) && e.target !== searchInput) {
        searchDropdown.classList.add('hidden');
    }

    if (!searchDropdown2.contains(e.target) && e.target !== searchInput2) {
        searchDropdown2.classList.add('hidden');
    }
});

// Switch between Games and Users tabs in main search
function switchTab(tab) {
    const gamesTab = document.getElementById('gamesTab');
    const usersTab = document.getElementById('usersTab');
    const gamesPanel = document.getElementById('gamesPanel');
    const usersPanel = document.getElementById('usersPanel');

    if (tab === 'games') {
        gamesTab.classList.add('active-tab');
        usersTab.classList.remove('active-tab');
        gamesPanel.classList.remove('hidden');
        usersPanel.classList.add('hidden');
    } else {
        gamesTab.classList.remove('active-tab');
        usersTab.classList.add('active-tab');
        gamesPanel.classList.add('hidden');
        usersPanel.classList.remove('hidden');
    }
}

// Switch between Games and Users tabs in sidebar search
function switchTab2(tab) {
    const gamesTab = document.getElementById('gamesTab2');
    const usersTab = document.getElementById('usersTab2');
    const gamesPanel = document.getElementById('gamesPanel2');
    const usersPanel = document.getElementById('usersPanel2');

    if (tab === 'games') {
        gamesTab.classList.add('active-tab');
        usersTab.classList.remove('active-tab');
        gamesPanel.classList.remove('hidden');
        usersPanel.classList.add('hidden');
    } else {
        gamesTab.classList.remove('active-tab');
        usersTab.classList.add('active-tab');
        gamesPanel.classList.add('hidden');
        usersPanel.classList.remove('hidden');
    }
}

// Main search functionality
function searchResults() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    const searchDropdown = document.getElementById('searchDropdown');
    const gameResults = document.getElementById('gameResults');
    const userResults = document.getElementById('userResults');

    if (query === '') {
        searchDropdown.classList.add('hidden');
        return;
    }

    searchDropdown.classList.remove('hidden');

    fetch(`/search/?query=${query}`)
        .then(response => response.json())
        .then(data => {
            // Clear previous results
            gameResults.innerHTML = '';
            userResults.innerHTML = '';

            // Add games to results
            if (data.games.length === 0) {
                gameResults.innerHTML = '<li>No games found</li>';
            } else {
                data.games.forEach(game => {
                    const gameItem = document.createElement('li');
                    gameItem.innerHTML = `<a href="/game_detail/${game.id}">${game.name}</a>`;
                    gameResults.appendChild(gameItem);
                });
            }

            // Add users to results
            if (data.users.length === 0) {
                userResults.innerHTML = '<li>No users found</li>';
            } else {
                data.users.forEach(user => {
                    const userItem = document.createElement('li');
                    userItem.innerHTML = `<a href="/view_profile/${user.id}">${user.username}</a>`;
                    userResults.appendChild(userItem);
                });
            }
        });
}

// Sidebar search functionality
function searchResults2() {
    const query = document.getElementById('searchInput2').value.toLowerCase();
    const searchDropdown = document.getElementById('searchDropdown2');
    const gameResults = document.getElementById('gameResults2');
    const userResults = document.getElementById('userResults2');

    if (query === '') {
        searchDropdown.classList.add('hidden');
        return;
    }

    searchDropdown.classList.remove('hidden');

    fetch(`/search/?query=${query}`)
        .then(response => response.json())
        .then(data => {
            // Clear previous results
            gameResults.innerHTML = '';
            userResults.innerHTML = '';

            // Add games to results
            if (data.games.length === 0) {
                gameResults.innerHTML = '<li>No games found</li>';
            } else {
                data.games.forEach(game => {
                    const gameItem = document.createElement('li');
                    gameItem.innerHTML = `<a href="/game_detail/${game.id}">${game.name}</a>`;
                    gameResults.appendChild(gameItem);
                });
            }

            // Add users to results
            if (data.users.length === 0) {
                userResults.innerHTML = '<li>No users found</li>';
            } else {
                data.users.forEach(user => {
                    const userItem = document.createElement('li');
                    userItem.innerHTML = `<a href="/view_profile/${user.id}">${user.username}</a>`;
                    userResults.appendChild(userItem);
                });
            }
        });
}

// Add the event listener to the hamburger button to toggle the sidebar
const hamburger = document.querySelector('.hamburger');
hamburger.addEventListener('click', toggleSidebar);