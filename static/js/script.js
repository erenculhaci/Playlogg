// Function to toggle the sidebar visibility
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

// Close sidebar when clicking outside of it
document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('sidebar');
    const hamburger = document.querySelector('.hamburger');

    // Check if the click is outside of the sidebar and hamburger button
    if (!sidebar.contains(e.target) && !hamburger.contains(e.target)) {
        sidebar.classList.remove('open');
    }
});
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
                data.games.forEach(game => {
                    const gameItem = document.createElement('li');
                    gameItem.innerHTML = `<a href="/game_detail/${game.id}" class="block py-1 text-gray-800 hover:bg-gray-200">${game.name}</a>`;
                    gameResults.appendChild(gameItem);
                });

                // Add users to results
                data.users.forEach(user => {
                    const userItem = document.createElement('li');
                    userItem.innerHTML = `<a href="/view_profile/${user.id}" class="block py-1 text-gray-800 hover:bg-gray-200">${user.username}</a>`;
                    userResults.appendChild(userItem);
                });
            });
    }

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
                data.games.forEach(game => {
                    const gameItem = document.createElement('li');
                    gameItem.innerHTML = `<a href="/game_detail/${game.id}" class="block py-1 text-gray-800 hover:bg-gray-200">${game.name}</a>`;
                    gameResults.appendChild(gameItem);
                });

                // Add users to results
                data.users.forEach(user => {
                    const userItem = document.createElement('li');
                    userItem.innerHTML = `<a href="/view_profile/${user.id}" class="block py-1 text-gray-800 hover:bg-gray-200">${user.username}</a>`;
                    userResults.appendChild(userItem);
                });
            });
    }


// Add the event listener to the hamburger button to toggle the sidebar
const hamburger = document.querySelector('.hamburger');
hamburger.addEventListener('click', toggleSidebar);
