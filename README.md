# Liars Bar Multiplayer Game

A multiplayer card game with bluffing and Russian roulette mechanics. This project uses Python, Flask, and Socket.IO for the backend, and a simple HTML/JavaScript frontend.

## Folder Structure

bluff-card-game/
├── static/
│   └── game.js
├── templates/
│   └── index.html
├── client.py
├── game_logic.py
├── README.md
├── server.py
├── requirements.txt
├── runtime.txt
└── Procfile



## Local Setup

1. **Clone the repository:**

   ```bash
   git clone <repo-url>
   cd <repo-folder>

2. **Create and activate a virtual environment:**

    ```bash
    python -m venv venv

    # Windows
    venv\Scripts\activate
    
    # macOS/Linux
    source venv/bin/activate

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt

4. **Run the server**
    
    ```bash
    python server.py


Game will be accessible at localhost:10000

Try it on: https://liars-bar-ulm9.onrender.com/