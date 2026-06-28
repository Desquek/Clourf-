from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from supabase import create_client, Client
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "clourf_conecta_secret"

# ============================================
# SUPABASE
# ============================================

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ozbnlyevbheypglmcbtx.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im96Ym5seWV2YmhleXBnbG1jYnR4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkxMjA5MDcsImV4cCI6MjA5NDY5NjkwN30.JVR-vUoEIAeEgeKy7DL4cl6TSeTyVa_6trJLqKF_TJk")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase conectado!")
except Exception as e:
    print(f"❌ Erro: {e}")
    supabase = None

# ============================================
# INICIALIZAR TABELAS
# ============================================

def init_supabase():
    if supabase is None:
        return
    
    try:
        supabase.table('users').select('*').limit(1).execute()
        print("✅ Tabela users OK")
    except:
        print("⚠️ Criando tabela users...")
        try:
            supabase.sql("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                telefone TEXT,
                senha TEXT NOT NULL,
                localizacao TEXT,
                bio TEXT,
                foto TEXT DEFAULT 'default.png',
                data_registo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """).execute()
            print("✅ Tabela users criada!")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    try:
        supabase.table('problemas').select('*').limit(1).execute()
        print("✅ Tabela problemas OK")
    except:
        print("⚠️ Criando tabela problemas...")
        try:
            supabase.sql("""
            CREATE TABLE problemas (
                id SERIAL PRIMARY KEY,
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                categoria TEXT NOT NULL,
                localizacao TEXT,
                usuario_id INTEGER REFERENCES users(id),
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """).execute()
            print("✅ Tabela problemas criada!")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    try:
        supabase.table('interessados').select('*').limit(1).execute()
        print("✅ Tabela interessados OK")
    except:
        print("⚠️ Criando tabela interessados...")
        try:
            supabase.sql("""
            CREATE TABLE interessados (
                id SERIAL PRIMARY KEY,
                problema_id INTEGER REFERENCES problemas(id),
                usuario_id INTEGER REFERENCES users(id),
                mensagem TEXT,
                status TEXT DEFAULT 'pendente',
                data_interesse TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """).execute()
            print("✅ Tabela interessados criada!")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    try:
        supabase.table('mensagens').select('*').limit(1).execute()
        print("✅ Tabela mensagens OK")
    except:
        print("⚠️ Criando tabela mensagens...")
        try:
            supabase.sql("""
            CREATE TABLE mensagens (
                id SERIAL PRIMARY KEY,
                remetente_id INTEGER REFERENCES users(id),
                destinatario_id INTEGER REFERENCES users(id),
                problema_id INTEGER REFERENCES problemas(id),
                conteudo TEXT NOT NULL,
                lida INTEGER DEFAULT 0,
                data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """).execute()
            print("✅ Tabela mensagens criada!")
        except Exception as e:
            print(f"❌ Erro: {e}")

init_supabase()

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
# FUNÇÕES DE ACESSO A DADOS
# ============================================

def get_user_by_email(email):
    if supabase is None:
        return None
    try:
        response = supabase.table('users').select('*').eq('email', email).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        print(f"Erro: {e}")
    return None

def get_user_by_id(user_id):
    if supabase is None:
        return None
    try:
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        if response.data:
            return response.data[0]
    except:
        pass
    return None

def create_user(nome, email, telefone, senha):
    if supabase is None:
        return None
    try:
        data = {'nome': nome, 'email': email, 'telefone': telefone, 'senha': senha}
        response = supabase.table('users').insert(data).execute()
        if response.data:
            return response.data[0]
    except:
        pass
    return None

def update_user(user_id, campo, valor):
    if supabase is None:
        return False
    try:
        supabase.table('users').update({campo: valor}).eq('id', user_id).execute()
        return True
    except:
        return False

def get_problemas(limit=10):
    if supabase is None:
        return []
    try:
        response = supabase.table('problemas').select('*, users(nome, foto)').order('data_criacao', desc=True).limit(limit).execute()
        return response.data
    except:
        return []

def get_problema_by_id(problema_id):
    if supabase is None:
        return None
    try:
        response = supabase.table('problemas').select('*, users(nome, telefone, foto, localizacao, bio)').eq('id', problema_id).execute()
        if response.data:
            return response.data[0]
    except:
        pass
    return None

def create_problema(titulo, descricao, categoria, localizacao, usuario_id):
    if supabase is None:
        return False
    try:
        data = {'titulo': titulo, 'descricao': descricao, 'categoria': categoria,
                'localizacao': localizacao, 'usuario_id': usuario_id}
        supabase.table('problemas').insert(data).execute()
        return True
    except:
        return False

def get_meus_problemas(usuario_id):
    if supabase is None:
        return []
    try:
        response = supabase.table('problemas').select('*').eq('usuario_id', usuario_id).order('data_criacao', desc=True).execute()
        return response.data
    except:
        return []

def add_interessado(problema_id, usuario_id, mensagem):
    if supabase is None:
        return False
    try:
        data = {'problema_id': problema_id, 'usuario_id': usuario_id, 'mensagem': mensagem}
        supabase.table('interessados').insert(data).execute()
        return True
    except:
        return False

def get_interessados(problema_id):
    if supabase is None:
        return []
    try:
        response = supabase.table('interessados').select('*, users(nome, foto, telefone)').eq('problema_id', problema_id).execute()
        return response.data
    except:
        return []

def get_conversas(usuario_id):
    if supabase is None:
        return []
    try:
        response = supabase.table('mensagens').select('*').or_(f'remetente_id.eq.{usuario_id},destinatario_id.eq.{usuario_id}').execute()
        conversas = {}
        for msg in response.data:
            outro = msg['destinatario_id'] if msg['remetente_id'] == usuario_id else msg['remetente_id']
            if outro not in conversas:
                user = get_user_by_id(outro)
                if user:
                    conversas[outro] = {
                        'outro_id': outro,
                        'nome': user['nome'],
                        'foto': user['foto'],
                        'ultima': msg['conteudo'],
                        'ultima_data': msg['data_envio']
                    }
        return list(conversas.values())
    except:
        return []

def get_mensagens(usuario_id, outro_id):
    if supabase is None:
        return []
    try:
        response = supabase.table('mensagens').select('*').or_(f'and(remetente_id.eq.{usuario_id},destinatario_id.eq.{outro_id}),and(remetente_id.eq.{outro_id},destinatario_id.eq.{usuario_id})').order('data_envio').execute()
        return response.data
    except:
        return []

def send_mensagem(remetente_id, destinatario_id, conteudo, problema_id=None):
    if supabase is None:
        return False
    try:
        data = {'remetente_id': remetente_id, 'destinatario_id': destinatario_id,
                'conteudo': conteudo, 'problema_id': problema_id}
        supabase.table('mensagens').insert(data).execute()
        return True
    except:
        return False

def marcar_lidas(usuario_id, outro_id):
    if supabase is None:
        return False
    try:
        supabase.table('mensagens').update({'lida': 1}).eq('remetente_id', outro_id).eq('destinatario_id', usuario_id).execute()
        return True
    except:
        return False

def get_notificacoes(usuario_id):
    if supabase is None:
        return {'mensagens_nao_lidas': 0, 'interesses_pendentes': 0, 'notificacoes_mensagens': [], 'notificacoes_interesses': []}
    
    mensagens_nao_lidas = 0
    interesses_pendentes = 0
    notificacoes_mensagens = []
    notificacoes_interesses = []
    
    try:
        msgs_response = supabase.table('mensagens').select('*, remetente:nome').eq('destinatario_id', usuario_id).eq('lida', 0).execute()
        mensagens_nao_lidas = len(msgs_response.data)
        for msg in msgs_response.data[:5]:
            notificacoes_mensagens.append({
                'conteudo': msg['conteudo'],
                'nome': msg.get('remetente', {}).get('nome', 'Alguém'),
                'data_envio': msg['data_envio']
            })
    except:
        pass
    
    try:
        interesses_response = supabase.table('interessados').select('*, users(nome), problemas(titulo)').eq('status', 'pendente').execute()
        interesses_pendentes = len(interesses_response.data)
        for interesse in interesses_response.data[:5]:
            notificacoes_interesses.append({
                'mensagem': interesse['mensagem'],
                'nome': interesse.get('users', {}).get('nome', 'Alguém'),
                'data_interesse': interesse['data_interesse'],
                'titulo': interesse.get('problemas', {}).get('titulo', 'Problema')
            })
    except:
        pass
    
    return {
        'mensagens_nao_lidas': mensagens_nao_lidas,
        'interesses_pendentes': interesses_pendentes,
        'notificacoes_mensagens': notificacoes_mensagens,
        'notificacoes_interesses': notificacoes_interesses
    }

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
            session['email'] = user['email']
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

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    problemas = get_problemas()
    meus_problemas = get_meus_problemas(session['user_id'])

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
        flash("Interesse manifestado com sucesso!")
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

@app.route('/mensagens')
def mensagens():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conversas = get_conversas(session['user_id'])
    return render_template('mensagens.html', conversas=conversas)

@app.route('/mensagens/<int:outro_id>')
def conversa(outro_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    outro = get_user_by_id(outro_id)
    if not outro:
        flash("Utilizador não encontrado!")
        return redirect(url_for('mensagens'))

    mensagens_lista = get_mensagens(session['user_id'], outro_id)
    marcar_lidas(session['user_id'], outro_id)

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

    if send_mensagem(session['user_id'], destinatario_id, conteudo, problema_id):
        flash("Mensagem enviada!")
    else:
        flash("Erro ao enviar mensagem!")

    return redirect(url_for('conversa', outro_id=destinatario_id))

@app.route('/notificacoes')
def notificacoes():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    notificacoes_data = get_notificacoes(session['user_id'])
    
    return render_template('notificacoes.html', 
                         mensagens_nao_lidas=notificacoes_data['mensagens_nao_lidas'],
                         interesses_pendentes=notificacoes_data['interesses_pendentes'],
                         notificacoes_mensagens=notificacoes_data['notificacoes_mensagens'],
                         notificacoes_interesses=notificacoes_data['notificacoes_interesses'])

@app.route('/perfil')
def perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = get_user_by_id(session['user_id'])
    return render_template('perfil.html', user=user)

@app.route('/perfil/<int:user_id>')
def perfil_publico(user_id):
    user = get_user_by_id(user_id)
    if not user:
        flash("Utilizador não encontrado!")
        return redirect(url_for('index'))

    problemas = get_meus_problemas(user_id)
    return render_template('perfil_publico.html', user=user, problemas=problemas)

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

        update_user(session['user_id'], 'foto', filename)
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

    if update_user(session['user_id'], campo, valor):
        flash(f"Campo atualizado com sucesso!")
    else:
        flash("Erro ao atualizar!")

    return redirect(url_for('perfil'))

@app.route('/categorias')
def categorias():
    if supabase is None:
        return render_template('categorias.html', categorias=[], contagem=[])
    
    contagem = []
    try:
        response = supabase.table('problemas').select('categoria').execute()
        contagem_dict = {}
        for item in response.data:
            cat = item['categoria']
            contagem_dict[cat] = contagem_dict.get(cat, 0) + 1
        contagem = [(cat, count) for cat, count in contagem_dict.items()]
    except:
        pass

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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)