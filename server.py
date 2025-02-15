# ------------ server.py ------------
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room
from game_logic import GameState, Player
import random
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

games = {}
CARD_TYPES = ["Ace", "King", "Queen", "Jack"]

class GameSession:
    def __init__(self):
        self.players = {}
        self.game_state = None
        self.current_turn_index = 0
        self.table_card = None

    def start_game(self):
        players_list = list(self.players.values())
        self.game_state = GameState(players_list)
        self.table_card = random.choice([c for c in CARD_TYPES if c != "Jack"])
        self.game_state.table_card = self.table_card
        self.game_state.initialize_deck()
        self.game_state.deal_initial_cards()
        
        for p in players_list:
            p.chamber = 6
            p.alive = True

    def start_new_round(self):
        """Reinitialize game state for new round"""
        players_list = [p for p in self.players.values() if p.alive]
        
        # Clear existing hands before dealing new cards
        for player in players_list:
            player.hand = []  

        self.game_state = GameState(players_list)
        self.table_card = random.choice([c for c in CARD_TYPES if c != "Jack"])
        self.game_state.table_card = self.table_card
        self.game_state.initialize_deck()
        self.game_state.deal_initial_cards()

@socketio.on('create_game')
def handle_create_game():
    game_id = str(int(time.time()))[-6:]
    games[game_id] = GameSession()
    emit('game_created', {'game_id': game_id})

@socketio.on('join_game')
def handle_join_game(data):
    game_id = data['game_id']
    player_id = data['player_id']
    name = data['name']
    
    if game_id not in games:
        emit('error', {'message': 'Game not found'})
        return
    
    game = games[game_id]
    if len(game.players) >= 4:
        emit('error', {'message': 'Game is full'})
        return
    
    player = Player(name)
    player.id = player_id
    game.players[player_id] = player
    
    join_room(game_id)

    emit('player_joined', {
        'players': [p.name for p in game.players.values()],
        'player_id': player_id
    }, broadcast=True)
    
    if len(game.players) == 4:
        game.start_game()
        emit('game_start', {
            'table_card': game.table_card,
            'players': [p.name for p in game.players.values()]
        }, room=game_id)
        start_turn(game_id)



def start_turn(game_id):
    game = games[game_id]
    start_index = game.current_turn_index
    while True:
        current_player = list(game.players.values())[game.current_turn_index]
        if current_player.alive:
            break
        game.current_turn_index = (game.current_turn_index + 1) % len(game.players)
        if game.current_turn_index == start_index:
            raise Exception("No Alive Players remaining!")
            break
    # current_player = list(game.players.values())[game.current_turn_index]
    game.next_player_id = current_player.id

    emit('turn_start', {
        'player_id': current_player.id,
        'hand': current_player.hand,
        'table_card': game.table_card
    }, room=game_id)


@socketio.on('play_cards')
def handle_play_cards(data):
    game_id = data['game_id']
    player_id = data['player_id']
    cards = data['cards']
    
    game = games[game_id]
    player = game.players[player_id]
    
    # Validate move
    if not all(card in player.hand for card in cards):
        emit('error', {'message': 'Invalid cards played'})
        return
    
    game.last_played_cards = cards
    # Remove cards from hand
    for card in cards:
        player.hand.remove(card)
    
    # Get next player
    next_index = (game.current_turn_index + 1) % 4
    next_player = list(game.players.values())[next_index]
    
    emit('cards_played', {
        'player_id': player_id,
        'cards': len(cards),
        'next_player_id': next_player.id,
        'hand': next_player.hand
    }, room=game_id)

@socketio.on('pass_turn')
def handle_pass_turn(data):
    game_id = data['game_id']
    game = games[game_id]
    
    # Advance to next player
    game.current_turn_index = (game.current_turn_index + 1) % len(game.players)
    start_turn(game_id)

@socketio.on('call_bluff')
def handle_call_bluff(data):
    game_id = data['game_id']
    caller_id = data['player_id']
    
    game = games[game_id]
    current_player = list(game.players.values())[game.current_turn_index]
    
    was_bluff = current_player.is_bluffing(game.last_played_cards, game.table_card)
    loser = current_player if was_bluff else game.players[caller_id]
    result = russian_roulette(loser)

    # Determine next player
    alive_players = [p for p in game.players.values() if p.alive]
    if result:  # Player died
        loser.alive = False
        alive_players = [p for p in alive_players if p != loser]
        
    # Start new round with remaining players
    game.start_new_round()
    
    # Determine first player for new round
    if result:
        # If loser died, start with next alive player
        next_turn_index = (game.current_turn_index + 1) % len(alive_players)
    else:
        # If survived, loser starts next round
        next_turn_index = alive_players.index(loser)

    game.current_turn_index = next_turn_index
    
    # Emit updates
    emit('bluff_result', {
        'caller_name': game.players[caller_id].name,
        'target_name': current_player.name,
        'loser_name': loser.name,
        'was_bluff': was_bluff,
        'survived': not result,
        'chamber': loser.chamber + 1,
        'next_player_id': alive_players[next_turn_index].id
    }, room=game_id)
    
    emit('new_round', {
        'table_card': game.table_card,
        'players': [p.name for p in alive_players]
    }, room=game_id)
    
    start_turn(game_id)

def russian_roulette(player):
    if player.chamber <= 0:
        return True
    current_chamber = player.chamber
    bullet_chamber = random.randint(1, current_chamber)
    player.chamber -= 1  # Decrement AFTER checking
    
    return bullet_chamber == 1

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)