let socket;
let playerId;
let gameId;
let currentHand = [];

function connect() {
    const name = document.getElementById('name').value;
    gameId = document.getElementById('gameId').value;
    playerId = Math.floor(1000 + Math.random() * 9000);
    
    socket = io(document.location.origin);
    
    socket.on('connect', () => {
        document.getElementById('lobby').style.display = 'none';
        document.getElementById('game-area').style.display = 'block';
        document.getElementById('game-id-display').textContent = gameId;

        if (gameId.toLowerCase() === 'new') {
            socket.emit('create_game');
        } else {
            joinGame(name);
        }
    });

    setupSocketListeners();
}

function joinGame(name) {
    socket.emit('join_game', {
        game_id: gameId,
        player_id: playerId,
        name: name
    });

    // // # new changes
    const playerNamesDiv = document.createElement('div');
    playerNamesDiv.className = 'mt-4';
    playerNamesDiv.innerHTML = `
        <h3 class="title is-6">Your Name (your player id): 
            <span class="tags tag is-primary">${name} (${playerId})</span>
        </h3>
        
    `;
    const gameInfo = document.getElementById('game-id-display').parentElement;
    gameInfo.appendChild(playerNamesDiv);
}


function updatePlayersList(players) {

    const playersList = document.getElementById('players-list');
    playersList.innerHTML = players.map(player => {
        const playerName = typeof player === 'string' ? player : player.name;
        return `<div class="tag is-medium m-1 is-primary">${playerName}</div>`;
    }).join('');
}

function setupSocketListeners() {
    socket.on('game_created', data => {
        gameId = data.game_id;
        document.getElementById('game-id-display').textContent = gameId;
        joinGame(document.getElementById('name').value);
    });


    socket.on('game_start', data => {
        updateGameState(data);
    });
    socket.on('turn_start', data => {
        currentHand = data.hand || [];
        updateHandDisplay();
        
        const actionArea = document.getElementById('action-area');
        actionArea.innerHTML = data.player_id === playerId ? 
            createTurnInterface() : 
            `<div class="notification">Waiting for ${data.player_name} (${data.player_id}) to play...</div>`;
    });

    socket.on('cards_played', data => {
        const actionArea = document.getElementById('action-area');
        actionArea.innerHTML = `
            <div class="notification">
                Player ${data.player_id} played ${data.cards} cards!
                ${data.next_player_id === playerId ? createBluffCallInterface() : ''}
            </div>
        `;
    });


    socket.on('player_joined', data => {

        const notification = document.createElement('div');
        notification.className = 'notification is-success is-light mb-2';
        notification.innerHTML = `${data.players[data.players.length-1]} joined!`;
        document.getElementById('players-list').prepend(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    
        updatePlayersList(data.players);
    });
    socket.on('bluff_result', data => {
        alert(`${data.caller_name} calls bluff! ${data.was_bluff ? 'Was bluffing!' : 'Was honest!'} ${data.loser_name} plays with ${data.chamber} chambers!!! ${data.loser_name} ${data.survived ? 'survived!' : 'DIED!'}`);
    });

    socket.on('new_round', updateGameState);
    socket.on('game_over', data => alert(`Game Over! Winner: ${data.winner}`));
}

function createTurnInterface() {
    return `
        <div class="field">
            <label class="label">Select cards to play:</label>
            <div class="select is-multiple">
                <select multiple id="cards-select" class="is-fullwidth">
                    ${currentHand.map(card => `<option value="${card}">${card}</option>`).join('')}
                </select>
            </div>
            <button class="button is-primary mt-2" onclick="playCards()">Play Selected Cards</button>
        </div>
    `;
}

function createBluffCallInterface() {
    return `
        <div class="buttons">
            <button class="button is-danger" onclick="callBluff()">Call Bluff!</button>
            <button class="button" onclick="passTurn()">Pass</button>
        </div>
    `;
}

function updateHandDisplay() {
    const handDiv = document.getElementById('hand');
    handDiv.innerHTML = currentHand.map(card => `
        <div class="column is-2">
            <div class="card has-background-info-light p-2 has-text-centered">${card}</div>
        </div>
    `).join('');
}

function updateGameState(data) {


    document.getElementById('table-card').textContent = data.table_card;
    

    const players = Array.isArray(data.players) ? data.players : [];
    
    const playersHTML = players.map(player => {

        if (typeof player === 'string') {
            return `
                <div class="mb-2">
                    <span class="has-text-weight-bold">${player}</span>
                    <span class="tag is-rounded is-dark ml-2">6 chambers</span>
                </div>`;
        }
        return `
            <div class="mb-2">
                <span class="has-text-weight-bold">${player.name}</span>
                <span class="tag is-rounded is-dark ml-2">${player.chamber} chambers</span>
            </div>`;
    }).join('');
    
    document.getElementById('players-list').innerHTML = playersHTML;

}

// Game Actions
function playCards() {
    const selected = Array.from(document.querySelectorAll('#cards-select option:checked'))
        .map(option => option.value);
    
    socket.emit('play_cards', {
        game_id: gameId,
        player_id: playerId,
        cards: selected
    });
}

function callBluff() {
    socket.emit('call_bluff', { game_id: gameId, player_id: playerId });
}

function passTurn() {
    socket.emit('pass_turn', { game_id: gameId, player_id: playerId });
}