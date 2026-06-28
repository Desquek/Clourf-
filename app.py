from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import sqlite3
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "clourf_conecta_secret"

# ============================================
# CONFIGURAÇÕES
# ============================================

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Tenta conectar ao Supabase
supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase conectado!")
    else:
        print("⚠️ Supabase não configurado. Usando SQLite.")
except Exception as e:
    print(f"❌ Erro Supabase: {e}. Usando SQLite.")

# ============================================
# SQLITE (FALLBACK)
# ============================================

def get_db():
    return sqlite3.connect("database.db")

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        telefone TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# ============================================
# FUNÇÕES DE BANCO DE DADOS
# ============================================

def get_user_by_email(email):
    # Tenta Supabase primeiro
    if supabase:
        try:
            response = supabase.table('users').select('*').eq('email', email).execute()
            if response.data:
                return response.data[0]
        except:
            pass
    
    # Fallback SQLite
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, nome, email, senha, telefone FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    if user:
        return {'id': user[0], 'nome': user[1], 'email': user[2], 'senha': user[3], 'telefone': user[4]}
    return None

def create_user(nome, email, senha, telefone=''):
    # Tenta Supabase primeiro
    if supabase:
        try:
            user_data = {'nome': nome, 'email': email, 'senha': senha, 'telefone': telefone}
            response = supabase.table('users').insert(user_data).execute()
            if response.data:
                return response.data[0]
        except:
            pass
    
    # Fallback SQLite
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (nome, email, senha, telefone) VALUES (?, ?, ?, ?)",
                 (nome, email, senha, telefone))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return {'id': user_id, 'nome': nome, 'email': email}
    except:
        conn.close()
        return None

# ============================================
# ROTAS
# ============================================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        telefone = request.form.get('telefone', '')
        
        # Verificar se já existe
        if get_user_by_email(email):
            flash("Email já registado!")
            return render_template('register.html')
        
        # Criar utilizador
        user = create_user(nome, email, senha, telefone)
        if user:
            flash("Conta criada com sucesso!")
            return redirect(url_for('login'))
        else:
            flash("Erro ao criar conta!")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        user = get_user_by_email(email)
        if user and user['senha'] == senha:
            session['user_id'] = user['id']
            session['nome'] = user['nome']
            flash(f"Bem-vindo, {user['nome']}!")
            return redirect(url_for('dashboard'))
        else:
            flash("Email ou senha inválidos!")
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', nome=session['nome'])

@app.route('/logout')
def logout():
    session.clear()
    flash("Saiu com sucesso!")
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)