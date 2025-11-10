from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_key"

# --- Создание БД ---
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    score INTEGER,
                    date TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

init_db()

# --- Регистрация ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Имя пользователя уже занято"
        conn.close()
        return redirect('/login')
    return render_template('register.html')

# --- Вход ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = username
            return redirect('/dashboard')
        else:
            return "Неверное имя пользователя или пароль"
    return render_template('login.html')

# --- Главная ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Опрос ---
@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        answers = [request.form.get(f'q{i}') for i in range(1, 6)]
        score = sum(1 for a in answers if a == 'a')  # Примерная логика

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO results (user_id, score, date) VALUES (?, ?, ?)",
                  (session['user_id'], score, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()

        return redirect('/dashboard')

    return render_template('survey.html')

# --- Личный кабинет ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT score, date FROM results WHERE user_id=? ORDER BY date DESC", (session['user_id'],))
    results = c.fetchall()
    conn.close()

    return render_template('dashboard.html', username=session['username'], results=results)

# --- Выход ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)