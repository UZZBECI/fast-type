from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import sqlite3
import os

# templates papkasini ko'rsatamiz
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         fullname TEXT UNIQUE, 
                         password TEXT, 
                         bestWPM INTEGER DEFAULT 0, 
                         bestAcc INTEGER DEFAULT 0)''')
        conn.commit()

init_db()

# --- SAHIFALARNI CHIQARISH (Frontend) ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/game')
def game_page():
    return render_template('asosiy.html')

@app.route('/leaderboard-page')
def leaderboard_view():
    return render_template('leaderboard.html')

# --- API YO'NALISHLARI ---

@app.route('/api/auth', methods=['POST'])
def auth():
    data = request.json
    name = data.get('fullname')
    password = data.get('password')
    
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE fullname = ?", (name,)).fetchone()
        if user:
            if user['password'] == password:
                return jsonify({
                    "status": "login", 
                    "user": {"fullname": user['fullname'], "bestWPM": user['bestWPM'], "bestAcc": user['bestAcc']}
                })
            return jsonify({"status": "error", "message": "Parol xato!"}), 401

        try:
            conn.execute("INSERT INTO users (fullname, password) VALUES (?, ?)", (name, password))
            conn.commit()
            return jsonify({"status": "registered", "user": {"fullname": name, "bestWPM": 0, "bestAcc": 0}})
        except sqlite3.IntegrityError:
            return jsonify({"status": "error", "message": "Foydalanuvchi mavjud"}), 400

@app.route('/api/update', methods=['POST'])
def update():
    data = request.json
    with get_db() as conn:
        conn.execute("UPDATE users SET bestWPM = ?, bestAcc = ? WHERE fullname = ? AND bestWPM < ?",
                       (data['wpm'], data['acc'], data['fullname'], data['wpm']))
        conn.commit()
    return jsonify({"status": "updated"})

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    with get_db() as conn:
        users = conn.execute("SELECT fullname, bestWPM, bestAcc FROM users ORDER BY bestWPM DESC LIMIT 10").fetchall()
    return jsonify([{"fullname": u['fullname'], "bestWPM": u['bestWPM'], "bestAcc": u['bestAcc']} for u in users])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
