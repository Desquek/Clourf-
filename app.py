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

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    return sqlite3.connect("database.db")

def init_db():
    conn = get_db()
    c = conn.cursor()
    
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
    
    c.execute('''CREATE TABLE IF NOT EXISTS interessados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problema_id INTEGER,
        usuario_id INTEGER,
        mensagem TEXT,
        status TEXT DEFAULT 'pendente',
        data_interesse TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (problema_id) REFERENCES problemas (id),
        FOREIGN KEY (usuario_id) REFERENCES users (id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS mensagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        remetente_id INTEGER,
        destinatario_id INTEGER,
        problema_id INTEGER,
        conteudo TEXT NOT NULL,
        lida INTEGER DEFAULT 0,
        data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (remetente_id) REFERENCES users (id),
        FOREIGN KEY (destinatario_id) REFERENCES users (id),
        FOREIGN KEY (problema_id) REFERENCES problemas (id)
    )''')
    
    conn.commit()
    conn.close()

def seed_db():
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM problemas")
    if c.fetchone()[0] == 0:
        c.execute("INSERT OR IGNORE INTO users (nome, email, telefone, senha, localizacao, bio) VALUES (?, ?, ?, ?, ?, ?)",
                 ("Didi", "didi@email.com", "84 123 4567", "1234", "Maputo", "Adoro conectar pessoas a soluções!"))
        
        exemplos = [
            ("Preciso de um eletricista", "Instalação de tomadas e fiação em casa. Urgente.", "Serviços", "Maputo"),
            ("Preciso de um logo", "Logo para minha marca de roupas. Estilo minimalista.", "Design", "Nampula"),
            ("Preciso de um entregador", "Entregue de encomenda urgente na baixa da cidade.", "Transporte", "Beira"),
            ("Preciso de aulas de inglês", "Aulas particulares de inglês para iniciantes.", "Aulas", "Matola"),
            ("Preciso de um DJ", "Evento de aniversário com 50 pessoas.", "Eventos", "Maputo"),
        ]
        
        for titulo, desc, cat, local in exemplos:
            c.execute("INSERT INTO problemas (titulo, descricao, categoria, localizacao, usuario_id) VALUES (?, ?, ?, ?, 1)",
                     (titulo, desc, cat, local))
        
        conn.commit()
    conn.close()

init_db()
seed_db()

# ============================================
# ROTAS DE AUTENTICAÇÃO
# ============================================

@app.route('/')
def index():
    if 'user_id' in session:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT p.*, u.nome, u.foto FROM problemas p JOIN users u ON p.usuario_id = u.id ORDER BY p.data_criacao DESC LIMIT 10")
        problemas = c.fetchall()
        conn.close()
        return render_template('dashboard.html', problemas=problemas)
    return render_template('landing.html')

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
    c.execute("SELECT p.*, u.nome, u.foto FROM problemas p JOIN users u ON p.usuario_id = u.id ORDER BY p.data_criacao DESC LIMIT 10")
    problemas = c.fetchall()
    
    c.execute("SELECT * FROM problemas WHERE usuario_id = ? ORDER BY data_criacao DESC", (session['user_id'],))
    meus_problemas = c.fetchall()
    conn.close()
    
    return render_template('dashboard.html', problemas=problemas, meus_problemas=meus_problemas)

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
    c.execute("SELECT p.*, u.nome, u.telefone, u.foto, u.localizacao, u.bio FROM problemas p JOIN users u ON p.usuario_id = u.id WHERE p.id = ?", (problema_id,))
    problema = c.fetchone()
    
    if not problema:
        flash("Problema não encontrado!")
        conn.close()
        return redirect(url_for('index'))
    
    ja_interessado = False
    if 'user_id' in session:
        c.execute("SELECT * FROM interessados WHERE problema_id = ? AND usuario_id = ?", (problema_id, session['user_id']))
        ja_interessado = c.fetchone() is not None
    
    conn.close()
    return render_template('problema.html', problema=problema, ja_interessado=ja_interessado)

# ============================================
# INTERESSADOS
# ============================================

@app.route('/interessar/<int:problema_id>', methods=['POST'])
def interessar(problema_id):
    if 'user_id' not in session:
        flash("Faça login para se interessar!")
        return redirect(url_for('login'))
    
    mensagem = request.form.get('mensagem', 'Gostaria de ajudar a resolver este problema.')
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT * FROM interessados WHERE problema_id = ? AND usuario_id = ?", (problema_id, session['user_id']))
    if c.fetchone():
        flash("Você já se interessou por este problema!")
        conn.close()
        return redirect(url_for('ver_problema', problema_id=problema_id))
    
    c.execute("INSERT INTO interessados (problema_id, usuario_id, mensagem) VALUES (?, ?, ?)",
             (problema_id, session['user_id'], mensagem))
    conn.commit()
    conn.close()
    
    flash("Você manifestou interesse! O autor será notificado.")
    return redirect(url_for('ver_problema', problema_id=problema_id))

@app.route('/interessados/<int:problema_id>')
def ver_interessados(problema_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT usuario_id FROM problemas WHERE id = ?", (problema_id,))
    problema = c.fetchone()
    if not problema or problema[0] != session['user_id']:
        flash("Apenas o autor pode ver os interessados!")
        conn.close()
        return redirect(url_for('ver_problema', problema_id=problema_id))
    
    c.execute("SELECT i.*, u.nome, u.foto, u.telefone FROM interessados i JOIN users u ON i.usuario_id = u.id WHERE i.problema_id = ?", (problema_id,))
    interessados = c.fetchall()
    conn.close()
    
    return render_template('interessados.html', interessados=interessados, problema_id=problema_id)

# ============================================
# MENSAGENS
# ============================================

@app.route('/mensagens')
def mensagens():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        SELECT DISTINCT 
            CASE 
                WHEN remetente_id = ? THEN destinatario_id 
                ELSE remetente_id 
            END as outro_id,
            u.nome, 
            u.foto,
            (SELECT conteudo FROM mensagens 
             WHERE (remetente_id = ? AND destinatario_id = u.id) 
                OR (remetente_id = u.id AND destinatario_id = ?)
             ORDER BY data_envio DESC LIMIT 1) as ultima,
            (SELECT data_envio FROM mensagens 
             WHERE (remetente_id = ? AND destinatario_id = u.id) 
                OR (remetente_id = u.id AND destinatario_id = ?)
             ORDER BY data_envio DESC LIMIT 1) as ultima_data
        FROM mensagens m
        JOIN users u ON u.id = (
            CASE 
                WHEN remetente_id = ? THEN destinatario_id 
                ELSE remetente_id 
            END
        )
        WHERE remetente_id = ? OR destinatario_id = ?
        GROUP BY u.id
    ''', (session['user_id'], session['user_id'], session['user_id'], session['user_id'], session['user_id'], session['user_id'], session['user_id']))
    
    conversas = c.fetchall()
    conn.close()
    
    return render_template('mensagens.html', conversas=conversas)

@app.route('/mensagens/<int:outro_id>')
def conversa(outro_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, nome, foto FROM users WHERE id = ?", (outro_id,))
    outro = c.fetchone()
    
    if not outro:
        flash("Utilizador não encontrado!")
        conn.close()
        return redirect(url_for('mensagens'))
    
    c.execute('''SELECT m.*, u.nome, u.foto FROM mensagens m
                 JOIN users u ON u.id = m.remetente_id
                 WHERE (remetente_id = ? AND destinatario_id = ?)
                 OR (remetente_id = ? AND destinatario_id = ?)
                 ORDER BY data_envio ASC''', 
                 (session['user_id'], outro_id, outro_id, session['user_id']))
    mensagens_lista = c.fetchall()
    
    c.execute("UPDATE mensagens SET lida = 1 WHERE remetente_id = ? AND destinatario_id = ?", (outro_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return render_template('conversa.html', outro=outro, mensagens=mensagens_lista)

@app.route('/enviar-mensagem', methods=['POST'])
def enviar_mensagem():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    destinatario_id = request.form['destinatario_id']
    conteudo = request.form['conteudo']
    problema_id = request.form.get('problema_id', None)
    
    if not conteudo.strip():
        flash("Mensagem vazia!")
        return redirect(url_for('conversa', outro_id=destinatario_id))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO mensagens (remetente_id, destinatario_id, problema_id, conteudo) VALUES (?, ?, ?, ?)",
             (session['user_id'], destinatario_id, problema_id, conteudo))
    conn.commit()
    conn.close()
    
    return redirect(url_for('conversa', outro_id=destinatario_id))

# ============================================
# NOTIFICAÇÕES
# ============================================

@app.route('/notificacoes')
def notificacoes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM mensagens WHERE destinatario_id = ? AND lida = 0", (session['user_id'],))
    mensagens_nao_lidas = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM interessados i JOIN problemas p ON i.problema_id = p.id WHERE p.usuario_id = ? AND i.status = 'pendente'", (session['user_id'],))
    interesses_pendentes = c.fetchone()[0]
    
    c.execute('''SELECT 'mensagem' as tipo, m.conteudo, u.nome, m.data_envio 
                 FROM mensagens m JOIN users u ON u.id = m.remetente_id 
                 WHERE m.destinatario_id = ? AND m.lida = 0 
                 ORDER BY m.data_envio DESC LIMIT 5''', (session['user_id'],))
    notificacoes_mensagens = c.fetchall()
    
    c.execute('''SELECT 'interesse' as tipo, i.mensagem, u.nome, i.data_interesse, p.titulo
                 FROM interessados i 
                 JOIN users u ON u.id = i.usuario_id 
                 JOIN problemas p ON p.id = i.problema_id
                 WHERE p.usuario_id = ? AND i.status = 'pendente'
                 ORDER BY i.data_interesse DESC LIMIT 5''', (session['user_id'],))
    notificacoes_interesses = c.fetchall()
    
    conn.close()
    
    return render_template('notificacoes.html', 
                         mensagens_nao_lidas=mensagens_nao_lidas,
                         interesses_pendentes=interesses_pendentes,
                         notificacoes_mensagens=notificacoes_mensagens,
                         notificacoes_interesses=notificacoes_interesses)

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
# CATEGORIAS E AJUDA
# ============================================

@app.route('/categorias')
def categorias():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT categoria, COUNT(*) FROM problemas GROUP BY categoria ORDER BY COUNT(*) DESC")
    contagem = c.fetchall()
    conn.close()
    
    categorias_lista = [
        {'nome': 'Serviços', 'icone': 'fa-wrench'},
        {'nome': 'Design', 'icone': 'fa-paint-brush'},
        {'nome': 'Reparos', 'icone': 'fa-tools'},
        {'nome': 'Transporte', 'icone': 'fa-truck'},
        {'nome': 'Aulas', 'icone': 'fa-chalkboard-teacher'},
        {'nome': 'Eventos', 'icone': 'fa-calendar-alt'},
    ]
    
    return render_template('categorias.html', categorias=categorias_lista, contagem=contagem)

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

@app.route('/ajuda')
def ajuda():
    return render_template('ajuda.html')

# ============================================
# INICIAR SERVIDOR
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)