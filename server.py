from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
# CORS ga Netlify manzilingizni qo'shsangiz yanada xavfsiz bo'ladi
CORS(app)


def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       fullname TEXT UNIQUE, 
                       password TEXT, 
                       bestWPM INTEGER DEFAULT 0, 
                       bestAcc INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()


# --- SAHIFALARNI CHIQARISH (Render uchun shart emas, lekin tursin) ---
@app.route('/')
def index():
    return "Server is running!"  # Render ishlayotganini bilish uchun


# --- API YO'NALISHLARI ---
@app.route('/api/auth', methods=['POST'])
def auth():
    data = request.json
    name = data['fullname']
    password = data['password']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE fullname = ?", (name,))
    user = cursor.fetchone()
    if user:
        if user[2] == password:
            conn.close()  # Connectionni har doim yopish kerak
            return jsonify({"status": "login", "user": {"fullname": user[1], "bestWPM": user[3], "bestAcc": user[4]}})
        conn.close()
        return jsonify({"status": "error", "message": "Parol xato!"}), 401

    cursor.execute("INSERT INTO users (fullname, password) VALUES (?, ?)", (name, password))
    conn.commit()
    conn.close()
    return jsonify({"status": "registered", "user": {"fullname": name, "bestWPM": 0, "bestAcc": 0}})


@app.route('/api/update', methods=['POST'])
def update():
    data = request.json
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET bestWPM = ?, bestAcc = ? WHERE fullname = ? AND bestWPM < ?",
                   (data['wpm'], data['acc'], data['fullname'], data['wpm']))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})


@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT fullname, bestWPM, bestAcc FROM users ORDER BY bestWPM DESC LIMIT 10")
    users = cursor.fetchall()
    conn.close()
    return jsonify([{"fullname": u[0], "bestWPM": u[1], "bestAcc": u[2]} for u in users])


# --- ENG MUHIM QISM: PORT SOZLAMASI ---
if __name__ == '__main__':
    init_db()
    # Render o'zi PORT muhit o'zgaruvchisini beradi
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
