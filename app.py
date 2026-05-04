from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))
app.secret_key = "clourf_secret_key"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

# Criar pastas necessárias
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ============================================
# BANCO DE DADOS COMPLETO
# ============================================

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    # Tabela de usuários
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        foto TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Tabela de grupos
    c.execute('''CREATE TABLE IF NOT EXISTS grupos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        dono_id INTEGER,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dono_id) REFERENCES users (id)
    )''')
    
    # Tabela de membros dos grupos
    c.execute('''CREATE TABLE IF NOT EXISTS grupo_membros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grupo_id INTEGER,
        usuario_id INTEGER,
        data_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (grupo_id) REFERENCES grupos (id),
        FOREIGN KEY (usuario_id) REFERENCES users (id)
    )''')
    
    # Tabela de arquivos
    c.execute('''CREATE TABLE IF NOT EXISTS arquivos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        caminho TEXT NOT NULL,
        tipo TEXT,
        tamanho REAL,
        usuario_id INTEGER,
        grupo_id INTEGER,
        data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES users (id),
        FOREIGN KEY (grupo_id) REFERENCES grupos (id)
    )''')
    
    # Tabela de notas
    c.execute('''CREATE TABLE IF NOT EXISTS notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT,
        conteudo TEXT,
        usuario_id INTEGER,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()

init_db()

# ============================================
# ROTAS PRINCIPAIS
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')
        
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                     (username, password, email))
            conn.commit()
            conn.close()
            flash("Conta criada com sucesso! Faça login.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Usuário já existe!")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE username = ? AND password = ?", 
                 (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash(f"Bem-vindo, {user[1]}!")
            return redirect(url_for('dashboard'))
        else:
            flash("Usuário ou senha inválidos!")
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    # Buscar arquivos do usuário
    c.execute("SELECT id, nome, tipo, tamanho, data_upload FROM arquivos WHERE usuario_id = ? ORDER BY id DESC LIMIT 10", 
             (session['user_id'],))
    arquivos = c.fetchall()
    
    # Contar total de arquivos
    c.execute("SELECT COUNT(*) FROM arquivos WHERE usuario_id = ?", (session['user_id'],))
    total_arquivos = c.fetchone()[0]
    
    # Buscar notas do usuário
    c.execute("SELECT id, titulo, conteudo, data_criacao FROM notas WHERE usuario_id = ? ORDER BY id DESC", 
             (session['user_id'],))
    notas = c.fetchall()
    
    # Buscar grupos do usuário
    c.execute('''SELECT g.id, g.nome, g.descricao FROM grupos g
                 JOIN grupo_membros gm ON g.id = gm.grupo_id
                 WHERE gm.usuario_id = ?''', (session['user_id'],))
    grupos = c.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         arquivos=arquivos, 
                         total_arquivos=total_arquivos,
                         notas=notas,
                         grupos=grupos)

@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'file' not in request.files:
        flash("Nenhum arquivo selecionado")
        return redirect(url_for('dashboard'))
    
    file = request.files['file']
    if file.filename == '':
        flash("Nenhum arquivo selecionado")
        return redirect(url_for('dashboard'))
    
    if file:
        filename = secure_filename(file.filename)
        # Identificar tipo do arquivo
        tipo = 'documento'
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            tipo = 'foto'
        elif filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            tipo = 'video'
        elif filename.lower().endswith(('.pdf', '.doc', '.docx', '.txt')):
            tipo = 'documento'
        
        tamanho = os.path.getsize(file.filename) / (1024 * 1024) if os.path.exists(file.filename) else 0
        caminho = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(caminho)
        
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO arquivos (nome, caminho, tipo, tamanho, usuario_id) VALUES (?, ?, ?, ?, ?)",
                 (filename, caminho, tipo, tamanho, session['user_id']))
        conn.commit()
        conn.close()
        
        flash("Arquivo enviado com sucesso!")
    return redirect(url_for('dashboard'))

@app.route('/nota/add', methods=['POST'])
def add_nota():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    titulo = request.form.get('titulo', 'Sem título')
    conteudo = request.form.get('conteudo', '')
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO notas (titulo, conteudo, usuario_id) VALUES (?, ?, ?)",
             (titulo, conteudo, session['user_id']))
    conn.commit()
    conn.close()
    
    flash("Nota adicionada!")
    return redirect(url_for('dashboard'))

@app.route('/grupo/criar', methods=['POST'])
def criar_grupo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    nome = request.form['nome']
    descricao = request.form.get('descricao', '')
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO grupos (nome, descricao, dono_id) VALUES (?, ?, ?)",
             (nome, descricao, session['user_id']))
    grupo_id = c.lastrowid
    
    # Adicionar o criador como membro
    c.execute("INSERT INTO grupo_membros (grupo_id, usuario_id) VALUES (?, ?)",
             (grupo_id, session['user_id']))
    conn.commit()
    conn.close()
    
    flash(f"Grupo '{nome}' criado com sucesso!")
    return redirect(url_for('dashboard'))

@app.route('/perfil')
def perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT username, email, data_criacao FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()
    conn.close()
    
    return render_template('perfil.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash("Você saiu do sistema!")
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)