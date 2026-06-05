from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))
app.secret_key = "clourf_secret_key_2025"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 999 * 1024 * 1024  # 999MB

# Criar pastas necessárias
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs("static/perfil", exist_ok=True)

# ============================================
# FUNÇÃO DO BANCO DE DADOS
# ============================================

def get_db():
    return sqlite3.connect("database.db", timeout=10)

def init_db():
    conn = get_db()
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
    
    # Tabela de pastas
    c.execute('''CREATE TABLE IF NOT EXISTS pastas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        usuario_id INTEGER,
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
        pasta_id INTEGER,
        data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES users (id),
        FOREIGN KEY (pasta_id) REFERENCES pastas (id)
    )''')
    
    # Tabela de favoritos
    c.execute('''CREATE TABLE IF NOT EXISTS favoritos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        arquivo_id INTEGER,
        usuario_id INTEGER,
        FOREIGN KEY (arquivo_id) REFERENCES arquivos (id),
        FOREIGN KEY (usuario_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()

init_db()

def criar_pastas_padrao(usuario_id):
    conn = get_db()
    c = conn.cursor()
    pastas = ['Documentos', 'Imagens', 'Videos', 'Projetos']
    for pasta in pastas:
        c.execute("INSERT INTO pastas (nome, usuario_id) VALUES (?, ?)", (pasta, usuario_id))
    conn.commit()
    conn.close()

def get_pasta_id(usuario_id, nome_pasta):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM pastas WHERE usuario_id = ? AND nome = ?", (usuario_id, nome_pasta))
    pasta = c.fetchone()
    conn.close()
    return pasta[0] if pasta else None

# ============================================
# ROTAS DE AUTENTICAÇÃO
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
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                     (username, password, email))
            usuario_id = c.lastrowid
            conn.commit()
            conn.close()
            criar_pastas_padrao(usuario_id)
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
        
        conn = get_db()
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

@app.route('/logout')
def logout():
    session.clear()
    flash("Você saiu do sistema!")
    return redirect(url_for('index'))

# ============================================
# DASHBOARD
# ============================================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM arquivos WHERE usuario_id = ?", (session['user_id'],))
    total_arquivos = c.fetchone()[0]
    
    c.execute("SELECT id, nome, tipo, tamanho, data_upload FROM arquivos WHERE usuario_id = ? ORDER BY id DESC LIMIT 10", 
             (session['user_id'],))
    arquivos = c.fetchall()
    
    c.execute("SELECT COUNT(*) FROM arquivos WHERE usuario_id = ? AND tipo = 'foto'", (session['user_id'],))
    imagens_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM arquivos WHERE usuario_id = ? AND tipo = 'video'", (session['user_id'],))
    videos_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM arquivos WHERE usuario_id = ? AND tipo = 'documento'", (session['user_id'],))
    documentos_count = c.fetchone()[0]
    
    # Contar PDFs separadamente
    c.execute("SELECT COUNT(*) FROM arquivos WHERE usuario_id = ? AND tipo = 'pdf'", (session['user_id'],))
    pdf_count = c.fetchone()[0]
    
    c.execute("SELECT foto FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         total_arquivos=total_arquivos,
                         arquivos=arquivos,
                         imagens_count=imagens_count,
                         videos_count=videos_count,
                         documentos_count=documentos_count + pdf_count,
                         user_foto=user[0] if user else None)

# ============================================
# UPLOAD
# ============================================

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
    
    filename = secure_filename(file.filename)
    
    # Identificar tipo
    tipo = 'documento'
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
        tipo = 'foto'
    elif filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
        tipo = 'video'
    elif filename.lower().endswith('.pdf'):
        tipo = 'pdf'
    
    # Pasta destino
    pasta_nome = 'Documentos'
    if tipo == 'foto':
        pasta_nome = 'Imagens'
    elif tipo == 'video':
        pasta_nome = 'Videos'
    
    pasta_id = get_pasta_id(session['user_id'], pasta_nome)
    caminho = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(caminho)
    tamanho = round(os.path.getsize(caminho) / (1024 * 1024), 2)
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO arquivos (nome, caminho, tipo, tamanho, usuario_id, pasta_id) VALUES (?, ?, ?, ?, ?, ?)",
             (filename, caminho, tipo, tamanho, session['user_id'], pasta_id))
    conn.commit()
    conn.close()
    
    flash(f"Arquivo '{filename}' enviado!")
    return redirect(url_for('dashboard'))

# ============================================
# ROTA PARA SERVIR ARQUIVOS
# ============================================

@app.route('/uploads/<path:filename>')
def servir_arquivo(filename):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(caminho):
        return send_file(caminho)
    else:
        return "Arquivo não encontrado", 404

# ============================================
# VISUALIZAR (TUDO DENTRO DO SITE)
# ============================================

@app.route('/visualizar/<int:arquivo_id>')
def visualizar(arquivo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, nome, tipo FROM arquivos WHERE id = ? AND usuario_id = ?", 
             (arquivo_id, session['user_id']))
    arquivo = c.fetchone()
    conn.close()
    
    if not arquivo:
        flash("Arquivo não encontrado!")
        return redirect(url_for('dashboard'))
    
    return render_template('visualizar.html', 
                         arquivo_id=arquivo[0],
                         arquivo_nome=arquivo[1],
                         arquivo_tipo=arquivo[2])

@app.route('/download/<int:arquivo_id>')
def download(arquivo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT caminho, nome FROM arquivos WHERE id = ? AND usuario_id = ?", 
             (arquivo_id, session['user_id']))
    arquivo = c.fetchone()
    conn.close()
    
    if arquivo and os.path.exists(arquivo[0]):
        return send_file(arquivo[0], as_attachment=True, download_name=arquivo[1])
    else:
        flash("Arquivo não encontrado!")
        return redirect(url_for('dashboard'))

# ============================================
# PERFIL
# ============================================

@app.route('/perfil')
def perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT username, email, data_criacao, foto FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()
    conn.close()
    
    return render_template('perfil.html', user=user)

@app.route('/upload-foto', methods=['POST'])
def upload_foto():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'foto' not in request.files:
        flash("Nenhuma foto selecionada")
        return redirect(url_for('perfil'))
    
    foto = request.files['foto']
    if foto.filename == '':
        flash("Nenhuma foto selecionada")
        return redirect(url_for('perfil'))
    
    extensao = foto.filename.split('.')[-1]
    nome_foto = f"user_{session['user_id']}.{extensao}"
    caminho = os.path.join('static/perfil', nome_foto)
    foto.save(caminho)
    
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET foto = ? WHERE id = ?", (f"/static/perfil/{nome_foto}", session['user_id']))
    conn.commit()
    conn.close()
    
    flash("Foto de perfil atualizada!")
    return redirect(url_for('perfil'))

# ============================================
# FAVORITOS
# ============================================

@app.route('/favoritos')
def favoritos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT a.id, a.nome, a.tipo, a.tamanho 
                 FROM favoritos f 
                 JOIN arquivos a ON f.arquivo_id = a.id 
                 WHERE f.usuario_id = ?''', (session['user_id'],))
    favoritos = c.fetchall()
    conn.close()
    
    return render_template('favoritos.html', favoritos=favoritos)

@app.route('/favoritar/<int:arquivo_id>')
def favoritar(arquivo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO favoritos (arquivo_id, usuario_id) VALUES (?, ?)", 
             (arquivo_id, session['user_id']))
    conn.commit()
    conn.close()
    
    flash("Adicionado aos favoritos!")
    return redirect(url_for('dashboard'))

# ============================================
# OUTRAS ROTAS
# ============================================

@app.route('/meus-arquivos')
def meus_arquivos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, nome, tipo, tamanho, data_upload FROM arquivos WHERE usuario_id = ? ORDER BY id DESC", 
             (session['user_id'],))
    arquivos = c.fetchall()
    conn.close()
    
    return render_template('meus_arquivos.html', arquivos=arquivos)

@app.route('/upload-page')
def upload_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('upload.html')

@app.route('/pesquisar-web')
def pesquisar_web():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('q', '')
    if not query:
        return render_template('pesquisar_web.html', query='', resultados=[])
    
    ACCOUNT_ID = "aa6afd44dbad7c50b297ed6ddf481d9b"
    INSTANCE_ID = "a0078fecc7350053df010782b4da912f"
    TOKEN = os.environ.get("CLOUDFLARE_AI_TOKEN")
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai-search/instances/{INSTANCE_ID}/search"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [{"role": "user", "content": query}]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        resultados = []
        if data.get('success'):
            for chunk in data.get('result', {}).get('chunks', []):
                resultados.append({
                    'title': chunk.get('metadata', {}).get('title', 'Sem título'),
                    'url': chunk.get('metadata', {}).get('url', '#'),
                    'content': chunk.get('content', '')[:200]
                })
        
        return render_template('pesquisar_web.html', query=query, resultados=resultados)
    
    except Exception as e:
        flash(f"Erro: {str(e)}")
        return render_template('pesquisar_web.html', query=query, resultados=[])
# ============================================
# INICIAR SERVIDOR
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)