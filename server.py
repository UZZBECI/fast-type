import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Xavfsizlik uchun faqat o'z domeni manzilingizni qo'shishingiz mumkin
CORS(app)

# Ma'lumotlar bazasi yo'li (Renderda /data yoki loyiha ildizida)
# Eslatma: Doimiy saqlash uchun Render "Disk" ulash lozim, aks holda db o'chib ketadi
DB_PATH = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Ma'lumotlarni lug'at ko'rinishida olish uchun
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         fullname TEXT UNIQUE, 
                         password TEXT, 
                         bestWPM INTEGER DEFAULT 0, 
                         bestAcc INTEGER DEFAULT 0)''')
        conn.commit()

# Server ishga tushganda bazani yaratish
init_db()

@app.route('/')
def index():
    return jsonify({"status": "online", "message": "Server muvaffaqiyatli ishlayapti!"})

@app.route('/api/auth', methods=['POST'])
def auth():
    data = request.json
    name = data.get('fullname')
    password = data.get('password')
    
    if not name or not password:
        return jsonify({"status": "error", "message": "Ma'lumotlar to'liq emas"}), 400

    with get_db_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE fullname = ?", (name,)).fetchone()
        
        if user:
            if user['password'] == password:
                return jsonify({
                    "status": "login", 
                    "user": {
                        "fullname": user['fullname'], 
                        "bestWPM": user['bestWPM'], 
                        "bestAcc": user['bestAcc']
                    }
                })
            return jsonify({"status": "error", "message": "Parol xato!"}), 401

        # Yangi foydalanuvchi ro'yxatdan o'tkazish
        try:
            conn.execute("INSERT INTO users (fullname, password) VALUES (?, ?)", (name, password))
            conn.commit()
            return jsonify({"status": "registered", "user": {"fullname": name, "bestWPM": 0, "bestAcc": 0}})
        except sqlite3.IntegrityError:
            return jsonify({"status": "error", "message": "Bu foydalanuvchi mavjud"}), 400

@app.route('/api/update', methods=['POST'])
def update():
    data = request.json
    with get_db_connection() as conn:
        # Faqat natija oldingisidan yaxshi bo'lsa yangilaydi
        conn.execute("""
            UPDATE users 
            SET bestWPM = ?, bestAcc = ? 
            WHERE fullname = ? AND bestWPM < ?
        """, (data['wpm'], data['acc'], data['fullname'], data['wpm']))
        conn.commit()
    return jsonify({"status": "updated"})

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    with get_db_connection() as conn:
        users = conn.execute("SELECT fullname, bestWPM, bestAcc FROM users ORDER BY bestWPM DESC LIMIT 10").fetchall()
    
    return jsonify([dict(u) for u in users])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
