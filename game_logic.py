# ------------ game_logic.py ------------
import random

CARD_TYPES = ["Ace", "King", "Queen", "Jack"]
CARDS_PER_TYPE = {"Ace": 6, "King": 6, "Queen": 6, "Jack": 2}
INITIAL_HAND_SIZE = 5

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.alive = True
        self.chamber = 6
        self.id = None

    def is_bluffing(self, cards_played, table_card):
        for card in cards_played:
            if card != table_card and card != "Jack":
                return True
        return False

class GameState:
    def __init__(self, players):
        self.players = players
        self.deck = []
        self.table_card = None

    def initialize_deck(self):
        self.deck = []
        for card_type, count in CARDS_PER_TYPE.items():
            self.deck.extend([card_type] * count)
        random.shuffle(self.deck)

    def deal_initial_cards(self):
        for _ in range(INITIAL_HAND_SIZE):
            for player in self.players:
                if self.deck:
                    player.hand.append(self.deck.pop())