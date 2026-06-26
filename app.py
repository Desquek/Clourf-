from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clourf_conecta_secret"

# Configuração para upload de fotos
UPLOAD_FOLDER = 'static/perfil'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Criar pasta se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        localizacao TEXT,
        bio TEXT,
        foto TEXT DEFAULT 'default.png',
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

def seed_db():
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM problemas")
    if c.fetchone()[0] == 0:
        # Criar utilizador de teste
        c.execute("INSERT OR IGNORE INTO users (nome, email, telefone, senha) VALUES (?, ?, ?, ?)",
                 ("Didi", "didi@email.com", "84 123 4567", "1234"))
        
        # Problemas de exemplo
        exemplos = [
            ("Preciso de um eletricista", "Instalação de tomadas e fiação em casa", "Serviços", "Maputo"),
            ("Preciso de um logo", "Logo para minha marca de roupas", "Design", "Nampula"),
            ("Preciso de um entregador", "Entregue de encomenda urgente", "Transporte", "Beira"),
            ("Preciso de aulas de inglês", "Aulas particulares de inglês para iniciantes", "Aulas", "Matola"),
            ("Preciso de um DJ", "Evento de aniversário com 50 pessoas", "Eventos", "Maputo"),
        ]
        
        for titulo, desc, cat, local in exemplos:
            c.execute("INSERT INTO problemas (titulo, descricao, categoria, localizacao, usuario_id) VALUES (?, ?, ?, ?, 1)",
                     (titulo, desc, cat, local))
        
        conn.commit()
    conn.close()

init_db()
seed_db()

# ============================================
# ROTAS PRINCIPAIS
# ============================================

@app.route('/')
def index():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT p.*, u.nome FROM problemas p JOIN users u ON p.usuario_id = u.id ORDER BY p.data_criacao DESC LIMIT 10")
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

@app.route('/logout')
def logout():
    session.clear()
    flash("Saiu com sucesso!")
    return redirect(url_for('index'))

# ============================================
# DASHBOARD E PROBLEMAS
# ============================================

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

@app.route('/minhas-publicacoes')
def minhas_publicacoes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM problemas WHERE usuario_id = ? ORDER BY data_criacao DESC", (session['user_id'],))
    publicacoes = c.fetchall()
    conn.close()
    
    return render_template('minhas_publicacoes.html', publicacoes=publicacoes)

@app.route('/categorias')
def categorias():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT categoria, COUNT(*) FROM problemas GROUP BY categoria ORDER BY COUNT(*) DESC")
    contagem = c.fetchall()
    conn.close()
    
    # Lista de todas as categorias com ícones
    categorias_lista = [
        {'nome': 'Serviços', 'icone': 'fa-wrench'},
        {'nome': 'Design', 'icone': 'fa-paint-brush'},
        {'nome': 'Reparos', 'icone': 'fa-tools'},
        {'nome': 'Transporte', 'icone': 'fa-truck'},
        {'nome': 'Aulas', 'icone': 'fa-chalkboard-teacher'},
        {'nome': 'Eventos', 'icone': 'fa-calendar-alt'},
    ]
    
    return render_template('categorias.html', categorias=categorias_lista, contagem=contagem)

# ============================================
# PERFIL
# ============================================

@app.route('/perfil')
def perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT nome, email, telefone, foto, localizacao, bio, data_registo FROM users WHERE id = ?", (session['user_id'],))
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
    
    if foto and allowed_file(foto.filename):
        ext = foto.filename.split('.')[-1]
        filename = f"user_{session['user_id']}.{ext}"
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        foto.save(caminho)
        
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE users SET foto = ? WHERE id = ?", (filename, session['user_id']))
        conn.commit()
        conn.close()
        
        flash("Foto atualizada com sucesso!")
    else:
        flash("Formato inválido. Use JPG, PNG ou GIF.")
    
    return redirect(url_for('perfil'))

@app.route('/editar-perfil', methods=['POST'])
def editar_perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    campo = request.form['campo']
    valor = request.form['valor']
    
    campos_validos = ['telefone', 'localizacao', 'bio']
    
    if campo not in campos_validos:
        flash("Campo inválido!")
        return redirect(url_for('perfil'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute(f"UPDATE users SET {campo} = ? WHERE id = ?", (valor, session['user_id']))
    conn.commit()
    conn.close()
    
    flash(f"Campo atualizado com sucesso!")
    return redirect(url_for('perfil'))

# ============================================
# ATIVIDADE
# ============================================

@app.route('/notificacoes')
def notificacoes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('notificacoes.html')

@app.route('/mensagens')
def mensagens():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('mensagens.html')

# ============================================
# AJUDA E SEGURANÇA
# ============================================

@app.route('/ajuda')
def ajuda():
    return render_template('ajuda.html')

# ============================================
# INICIAR SERVIDOR
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)