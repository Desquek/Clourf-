from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clourf_conecta_secret"

def get_db():
    return sqlite3.connect("database.db")

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Tabela de usuários
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        telefone TEXT,
        senha TEXT NOT NULL,
        data_registo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Tabela de problemas
    c.execute('''CREATE TABLE IF NOT EXISTS problemas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        categoria TEXT NOT NULL,
        localizacao TEXT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'aberto',
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM problemas ORDER BY data_criacao DESC LIMIT 10")
    problemas = c.fetchall()
    conn.close()
    return render_template('index.html', problemas=problemas)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        senha = request.form['senha']
        
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT INTO users (nome, email, telefone, senha) VALUES (?, ?, ?, ?)",
                     (nome, email, telefone, senha))
            conn.commit()
            conn.close()
            flash("Conta criada com sucesso!")
            return redirect(url_for('login'))
        except:
            flash("Email já registado!")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, nome FROM users WHERE email = ? AND senha = ?", (email, senha))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['nome'] = user[1]
            flash(f"Bem-vindo, {user[1]}!")
            return redirect(url_for('dashboard'))
        else:
            flash("Email ou senha inválidos!")
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM problemas WHERE usuario_id = ? ORDER BY data_criacao DESC", (session['user_id'],))
    meus_problemas = c.fetchall()
    conn.close()
    
    return render_template('dashboard.html', meus_problemas=meus_problemas)

@app.route('/novo-problema', methods=['GET', 'POST'])
def novo_problema():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        categoria = request.form['categoria']
        localizacao = request.form['localizacao']
        
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO problemas (titulo, descricao, categoria, localizacao, usuario_id) VALUES (?, ?, ?, ?, ?)",
                 (titulo, descricao, categoria, localizacao, session['user_id']))
        conn.commit()
        conn.close()
        
        flash("Problema publicado com sucesso!")
        return redirect(url_for('dashboard'))
    
    return render_template('novo_problema.html')

@app.route('/problema/<int:problema_id>')
def ver_problema(problema_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT p.*, u.nome, u.telefone FROM problemas p JOIN users u ON p.usuario_id = u.id WHERE p.id = ?", (problema_id,))
    problema = c.fetchone()
    conn.close()
    
    if not problema:
        flash("Problema não encontrado!")
        return redirect(url_for('index'))
    
    return render_template('problema.html', problema=problema)

@app.route('/logout')
def logout():
    session.clear()
    flash("Saiu com sucesso!")
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
