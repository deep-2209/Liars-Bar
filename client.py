# ------------ client.py ------------
import socketio
import random

sio = socketio.Client()
player_id = str(random.randint(1000, 9999))

def display_game_state(data):
    print("\nCurrent Game State:")
    print(f"Table Card: {data.get('table_card', 'Unknown')}")
    print(f"Your Hand: {data.get('hand', [])}")
    print(f"Players: {', '.join(data.get('players', []))}")

@sio.event
def connect():
    print("Connected to server!")

@sio.event
def game_created(data):
    print(f"\nGame created! Share this ID: {data['game_id']}")
    global game_id
    game_id = data['game_id']
    sio.emit('join_game', {
        'game_id': game_id,
        'player_id': player_id,
        'name': name
    })

@sio.event
def player_joined(data):
    print(f"\nPlayer joined: {data['players'][-1]}")

@sio.event
def game_start(data):
    print("\nGame starting!")
    print(f"Table card: {data['table_card']}")
    print(f"Players: {', '.join(data['players'])}")

@sio.event
def turn_start(data):
    if data['player_id'] == player_id:
        print("\n=== YOUR TURN ===\n")
        display_game_state(data)
        cards = input("Enter cards to play (comma-separated): ").split(',')
        sio.emit('play_cards', {
            'game_id': game_id,
            'player_id': player_id,
            'cards': [c.strip() for c in cards]
        })
    else:
        print(f"\nWaiting for {data['player_id']} to play...")


@sio.event
def cards_played(data):
    print(f"\nPlayer {data['player_id']} played {data['cards']} cards!")
    if data['next_player_id'] == player_id:
        print("\nYour current hand:", data.get('hand', []))
        call = input("Call bluff? (y/n): ").lower()
        if call == 'y':
            sio.emit('call_bluff', {
                'game_id': game_id,
                'player_id': player_id
            })
        else:  # Add this else block
            sio.emit('pass_turn', {
                'game_id': game_id,
                'player_id': player_id
            })

@sio.event
def bluff_result(data):
    print(f"\n{data['caller_name']} calls bluff on {data['target_name']}!")
    print(f"{'Was bluffing!' if data['was_bluff'] else 'Was not bluffing!'}")
    print(f"{data['loser_name']} plays Russian roulette with {data['chamber']} chambers...")
    print(f"{'Survived!' if data['survived'] else 'DIED!'}")
    next_player_id = data.get('next_player_id')
    if next_player_id == player_id:
        # print("\nIt's your turn now!")   # check this
        sio.sleep(0.1)  


@sio.event
def new_round(data):
    print("\n=== NEW ROUND ===\n")
    print(f"Table Card: {data['table_card']}")
    print(f"Players: {', '.join(data['players'])}")

@sio.event
def game_over(data):
    print(f"\nGAME OVER! Winner: {data['winner']}")
    sio.disconnect()

if __name__ == '__main__':
    server_url = input("Enter server URL (e.g., http://localhost:5000): ")
    game_id = input("Enter game ID (or 'new' to create): ")
    name = input("Enter your name: ")
    
    sio.connect(server_url)
    
    if game_id.lower() == 'new':
        sio.emit('create_game')
    else:
        sio.emit('join_game', {
            'game_id': game_id,
            'player_id': player_id,
            'name': name
        })
    
    while True:
        sio.sleep(1)

