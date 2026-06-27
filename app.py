from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "clourf_secret"

def get_db():
    return sqlite3.connect("database.db")

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return "Clourf está a funcionar!"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (nome, email, senha) VALUES (?, ?, ?)",
                     (nome, email, senha))
            conn.commit()
            conn.close()
            return "Conta criada com sucesso!"
        except:
            conn.close()
            return "Email já registado!"
    return '''
        <form method="POST">
            Nome: <input type="text" name="nome"><br>
            Email: <input type="email" name="email"><br>
            Senha: <input type="password" name="senha"><br>
            <button type="submit">Registar</button>
        </form>
    '''

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)