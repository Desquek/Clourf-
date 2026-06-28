from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from supabase import create_client, Client
import sqlite3

app = Flask(__name__)
app.secret_key = "clourf_conecta_secret"

# ============================================
# SUPABASE CONFIGURATION
# ============================================

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase conectado!")
    else:
        print("⚠️ Supabase não configurado.")
except Exception as e:
    print(f"❌ Erro Supabase: {e}")

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
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES users(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS interessados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problema_id INTEGER,
        usuario_id INTEGER,
        mensagem TEXT,
        status TEXT DEFAULT 'pendente',
        data_interesse TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (problema_id) REFERENCES problemas(id),
        FOREIGN KEY (usuario_id) REFERENCES users(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS mensagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        remetente_id INTEGER,
        destinatario_id INTEGER,
        problema_id INTEGER,
        conteudo TEXT NOT NULL,
        lida INTEGER DEFAULT 0,
        data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (remetente_id) REFERENCES users(id),
        FOREIGN KEY (destinatario_id) REFERENCES users(id),
        FOREIGN KEY (problema_id) REFERENCES problemas(id)
    )''')
    
    conn.commit()
    conn.close()

init_db()

# ============================================
# FUNÇÃO PARA BUSCAR DADOS (SUPABASE OU SQLITE)
# ============================================

def get_user_by_email(email):
    if supabase:
        try:
            response = supabase.table('users').select('*').eq('email', email).execute()
            if response.data:
                return response.data[0]
        except:
            pass
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, nome, email, telefone, senha, localizacao, bio, foto, data_registo FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    if user:
        return {
            'id': user[0], 'nome': user[1], 'email': user[2],
            'telefone': user[3], 'senha': user[4], 'localizacao': user[5],
            'bio': user[6], 'foto': user[7], 'data_registo': user[8]
        }
    return None

def create_user(nome, email, telefone, senha):
    if supabase:
        try:
            user_data = {'nome': nome, 'email': email, 'telefone': telefone, 'senha': senha}
            response = supabase.table('users').insert(user_data).execute()
            return response.data[0] if response.data else None
        except:
            pass
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO users (nome, email, telefone, senha) VALUES (?, ?, ?, ?)",
             (nome, email, telefone, senha))
    conn.commit()
    user_id = c.lastrowid
    conn.close()
    return {'id': user_id, 'nome': nome, 'email': email}

def get_problemas():
    if supabase:
        try:
            response = supabase.table('problemas').select('*, users(nome, foto)').order('data_criacao', desc=True).limit(10).execute()
            return response.data
        except:
            pass
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT p.*, u.nome, u.foto FROM problemas p JOIN users u ON p.usuario_id = u.id ORDER BY p.data_criacao DESC")
    problemas = c.fetchall()
    conn.close()
    return [{'id': p[0], 'titulo': p[1], 'descricao': p[2], 'categoria': p[3], 
             'localizacao': p[4], 'usuario_id': p[5], 'data_criacao': p[6],
             'users': {'nome': p[7], 'foto': p[8]}} for p in problemas]

def create_problema(titulo, descricao, categoria, localizacao, usuario_id):
    if supabase:
        try:
            data = {'titulo': titulo, 'descricao': descricao, 'categoria': categoria,
                    'localizacao': localizacao, 'usuario_id': usuario_id}
            supabase.table('problemas').insert(data).execute()
            return True
        except:
            pass
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO problemas (titulo, descricao, categoria, localizacao, usuario_id) VALUES (?, ?, ?, ?, ?)",
             (titulo, descricao, categoria, localizacao, usuario_id))
    conn.commit()
    conn.close()
    return True

def get_problema_by_id(problema_id):
    if supabase:
        try:
            response = supabase.table('problemas').select('*, users(nome, telefone, foto, localizacao, bio)').eq('id', problema_id).execute()
            if response.data:
                return response.data[0]
        except:
            pass
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT p.*, u.nome, u.telefone, u.foto, u.localizacao, u.bio FROM problemas p JOIN users u ON p.usuario_id = u.id WHERE p.id = ?", (problema_id,))
    p = c.fetchone()
    conn.close()
    if p:
        return {
            'id': p[0], 'titulo': p[1], 'descricao': p[2], 'categoria': p[3],
            'localizacao': p[4], 'usuario_id': p[5], 'data_criacao': p[6],
            'users': {'nome': p[7], 'telefone': p[8], 'foto': p[9], 'localizacao': p[10], 'bio': p[11]}
        }
    return None

def get_meus_problemas(usuario_id):
    if supabase:
        try:
            response = supabase.table('problemas').select('*').eq('usuario_id', usuario_id).order('data_criacao', desc=True).execute()
            return response.data
        except:
            pass
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM problemas WHERE usuario_id = ? ORDER BY data_criacao DESC", (usuario_id,))
    problemas = c.fetchall()
    conn.close()
    return [{'id': p[0], 'titulo': p[1], 'descricao': p[2], 'categoria': p[3],
             'localizacao': p[4], 'usuario_id': p[5], 'data_criacao': p[6]} for p in problemas]

def add_interessado(problema_id, usuario_id, mensagem):
    if supabase:
        try:
            data = {'problema_id': problema_id, 'usuario_id': usuario_id, 'mensagem': mensagem}
            supabase.table('interessados').insert(data).execute()
            return True
        except:
            pass
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO interessados (problema_id, usuario_id, mensagem) VALUES (?, ?, ?)",
             (problema_id, usuario_id, mensagem))
    conn.commit()
    conn.close()
    return True

def get_interessados(problema_id):
    if supabase:
        try:
            response = supabase.table('interessados').select('*, users(nome, foto, telefone)').eq('problema_id', problema_id).execute()
            return response.data
        except:
            pass
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT i.*, u.nome, u.foto, u.telefone FROM interessados i JOIN users u ON i.usuario_id = u.id WHERE i.problema_id = ?", (problema_id,))
    interessados = c.fetchall()
    conn.close()
    return [{'id': i[0], 'problema_id': i[1], 'usuario_id': i[2], 'mensagem': i[3],
             'status': i[4], 'data_interesse': i[5], 'users': {'nome': i[6], 'foto': i[7], 'telefone': i[8]}} for i in interessados]

# ============================================
# CONFIGURAÇÃO PARA UPLOAD DE FOTOS
# ============================================

UPLOAD_FOLDER = 'static/perfil'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================
# ROTAS DE AUTENTICAÇÃO
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
        telefone = request.form['telefone']
        senha = request.form['senha']
        
        if get_user_by_email(email):
            flash("Email já registado!")
            return render_template('register.html')
        
        user = create_user(nome, email, telefone, senha)
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
    
    problemas = get_problemas()
    meus_problemas = get_meus_problemas(session['user_id'])
    
    return render_template('dashboard.html', problemas=problemas, meus_problemas=meus_problemas, nome=session['nome'])

@app.route('/novo-problema', methods=['GET', 'POST'])
def novo_problema():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        categoria = request.form['categoria']
        localizacao = request.form['localizacao']
        
        if create_problema(titulo, descricao, categoria, localizacao, session['user_id']):
            flash("Problema publicado com sucesso!")
        else:
            flash("Erro ao publicar problema!")
        return redirect(url_for('dashboard'))
    
    return render_template('novo_problema.html')

@app.route('/problema/<int:problema_id>')
def ver_problema(problema_id):
    problema = get_problema_by_id(problema_id)
    if not problema:
        flash("Problema não encontrado!")
        return redirect(url_for('index'))
    
    ja_interessado = False
    if 'user_id' in session:
        interessados = get_interessados(problema_id)
        ja_interessado = any(i['usuario_id'] == session['user_id'] for i in interessados)
    
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
    
    interessados = get_interessados(problema_id)
    if any(i['usuario_id'] == session['user_id'] for i in interessados):
        flash("Você já se interessou por este problema!")
        return redirect(url_for('ver_problema', problema_id=problema_id))
    
    if add_interessado(problema_id, session['user_id'], mensagem):
        flash("Você manifestou interesse! O autor será notificado.")
    else:
        flash("Erro ao manifestar interesse!")
    
    return redirect(url_for('ver_problema', problema_id=problema_id))

@app.route('/interessados/<int:problema_id>')
def ver_interessados(problema_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    problema = get_problema_by_id(problema_id)
    if not problema or problema['usuario_id'] != session['user_id']:
        flash("Apenas o autor pode ver os interessados!")
        return redirect(url_for('ver_problema', problema_id=problema_id))
    
    interessados = get_interessados(problema_id)
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
    c.execute('''SELECT DISTINCT 
        CASE WHEN remetente_id = ? THEN destinatario_id ELSE remetente_id END as outro_id,
        u.nome, u.foto,
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
            CASE WHEN remetente_id = ? THEN destinatario_id ELSE remetente_id END
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
    
    user = get_user_by_email(session['email']) if 'email' in session else None
    if not user:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT nome, email, telefone, foto, localizacao, bio, data_registo FROM users WHERE id = ?", (session['user_id'],))
        user = c.fetchone()
        conn.close()
        if user:
            user = {'nome': user[0], 'email': user[1], 'telefone': user[2], 
                    'foto': user[3], 'localizacao': user[4], 'bio': user[5], 'data_registo': user[6]}
    
    return render_template('perfil.html', user=user)

@app.route('/perfil/<int:user_id>')
def perfil_publico(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, nome, email, telefone, foto, localizacao, bio, data_registo FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        flash("Utilizador não encontrado!")
        return redirect(url_for('index'))
    
    user_dict = {'id': user[0], 'nome': user[1], 'email': user[2], 'telefone': user[3],
                 'foto': user[4], 'localizacao': user[5], 'bio': user[6], 'data_registo': user[7]}
    
    problemas = get_meus_problemas(user_id)
    return render_template('perfil_publico.html', user=user_dict, problemas=problemas)

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
    
    publicacoes = get_meus_problemas(session['user_id'])
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