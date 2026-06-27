from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "clourf_conecta_secret"

# ============================================
# CONFIGURAÇÃO DO SUPABASE
# ============================================

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ozbnlyevbheypglmcbtx.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im96Ym5seWV2YmhleXBnbG1jYnR4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkxMjA5MDcsImV4cCI6MjA5NDY5NjkwN30.JVR-vUoEIAeEgeKy7DL4cl6TSeTyVa_6trJLqKF_TJk")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
# FUNÇÕES DE INICIALIZAÇÃO (TABELAS NO SUPABASE)
# ============================================

def init_supabase():
    """Cria as tabelas no Supabase via SQL"""
    try:
        # Tabela de usuários
        supabase.table('users').select('*').limit(1).execute()
    except:
        # Se a tabela não existir, cria
        sql = """
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
        """
        supabase.sql(sql).execute()
    
    try:
        supabase.table('problemas').select('*').limit(1).execute()
    except:
        sql = """
        CREATE TABLE problemas (
            id SERIAL PRIMARY KEY,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            localizacao TEXT,
            usuario_id INTEGER REFERENCES users(id),
            status TEXT DEFAULT 'aberto',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        supabase.sql(sql).execute()
    
    try:
        supabase.table('interessados').select('*').limit(1).execute()
    except:
        sql = """
        CREATE TABLE interessados (
            id SERIAL PRIMARY KEY,
            problema_id INTEGER REFERENCES problemas(id),
            usuario_id INTEGER REFERENCES users(id),
            mensagem TEXT,
            status TEXT DEFAULT 'pendente',
            data_interesse TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        supabase.sql(sql).execute()
    
    try:
        supabase.table('mensagens').select('*').limit(1).execute()
    except:
        sql = """
        CREATE TABLE mensagens (
            id SERIAL PRIMARY KEY,
            remetente_id INTEGER REFERENCES users(id),
            destinatario_id INTEGER REFERENCES users(id),
            problema_id INTEGER REFERENCES problemas(id),
            conteudo TEXT NOT NULL,
            lida INTEGER DEFAULT 0,
            data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        supabase.sql(sql).execute()

def seed_supabase():
    """Adiciona dados de exemplo se não houver problemas"""
    try:
        # Verificar se já existem problemas
        response = supabase.table('problemas').select('*').limit(1).execute()
        if len(response.data) == 0:
            # Criar utilizador de teste
            user_data = {
                'nome': 'Didi',
                'email': 'didi@email.com',
                'telefone': '84 123 4567',
                'senha': '1234',
                'localizacao': 'Maputo',
                'bio': 'Adoro conectar pessoas a soluções!'
            }
            user_response = supabase.table('users').insert(user_data).execute()
            user_id = user_response.data[0]['id']
            
            # Problemas de exemplo
            exemplos = [
                ("Preciso de um eletricista", "Instalação de tomadas e fiação em casa. Urgente.", "Serviços", "Maputo"),
                ("Preciso de um logo", "Logo para minha marca de roupas. Estilo minimalista.", "Design", "Nampula"),
                ("Preciso de um entregador", "Entregue de encomenda urgente na baixa da cidade.", "Transporte", "Beira"),
                ("Preciso de aulas de inglês", "Aulas particulares de inglês para iniciantes.", "Aulas", "Matola"),
                ("Preciso de um DJ", "Evento de aniversário com 50 pessoas.", "Eventos", "Maputo"),
            ]
            
            for titulo, desc, cat, local in exemplos:
                problema_data = {
                    'titulo': titulo,
                    'descricao': desc,
                    'categoria': cat,
                    'localizacao': local,
                    'usuario_id': user_id
                }
                supabase.table('problemas').insert(problema_data).execute()
    except Exception as e:
        print(f"Erro no seed: {e}")

# Inicializar
init_supabase()
seed_supabase()

# ============================================
# ROTAS DE AUTENTICAÇÃO
# ============================================

@app.route('/')
def index():
    if 'user_id' in session:
        response = supabase.table('problemas').select('*, users(nome, foto)').order('data_criacao', desc=True).limit(10).execute()
        problemas = response.data
        return render_template('dashboard.html', problemas=problemas)
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        senha = request.form['senha']
        
        # Verificar se email já existe
        existing = supabase.table('users').select('*').eq('email', email).execute()
        if len(existing.data) > 0:
            flash("Email já registado!")
            return render_template('register.html')
        
        # Criar novo utilizador
        user_data = {
            'nome': nome,
            'email': email,
            'telefone': telefone,
            'senha': senha
        }
        try:
            supabase.table('users').insert(user_data).execute()
            flash("Conta criada com sucesso!")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Erro ao criar conta: {e}")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        response = supabase.table('users').select('id, nome').eq('email', email).eq('senha', senha).execute()
        user = response.data
        
        if user:
            session['user_id'] = user[0]['id']
            session['nome'] = user[0]['nome']
            flash(f"Bem-vindo, {user[0]['nome']}!")
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
    
    # Problemas de todos os utilizadores
    response = supabase.table('problemas').select('*, users(nome, foto)').order('data_criacao', desc=True).limit(10).execute()
    problemas = response.data
    
    # Meus problemas
    response_meus = supabase.table('problemas').select('*').eq('usuario_id', session['user_id']).order('data_criacao', desc=True).execute()
    meus_problemas = response_meus.data
    
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
        
        problema_data = {
            'titulo': titulo,
            'descricao': descricao,
            'categoria': categoria,
            'localizacao': localizacao,
            'usuario_id': session['user_id']
        }
        supabase.table('problemas').insert(problema_data).execute()
        
        flash("Problema publicado com sucesso!")
        return redirect(url_for('dashboard'))
    
    return render_template('novo_problema.html')

@app.route('/problema/<int:problema_id>')
def ver_problema(problema_id):
    response = supabase.table('problemas').select('*, users(nome, telefone, foto, localizacao, bio)').eq('id', problema_id).execute()
    
    if not response.data:
        flash("Problema não encontrado!")
        return redirect(url_for('index'))
    
    problema = response.data[0]
    
    # Verificar se já está interessado
    ja_interessado = False
    if 'user_id' in session:
        interesse_response = supabase.table('interessados').select('*').eq('problema_id', problema_id).eq('usuario_id', session['user_id']).execute()
        ja_interessado = len(interesse_response.data) > 0
    
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
    
    # Verificar se já está interessado
    existing = supabase.table('interessados').select('*').eq('problema_id', problema_id).eq('usuario_id', session['user_id']).execute()
    if len(existing.data) > 0:
        flash("Você já se interessou por este problema!")
        return redirect(url_for('ver_problema', problema_id=problema_id))
    
    # Adicionar interesse
    interesse_data = {
        'problema_id': problema_id,
        'usuario_id': session['user_id'],
        'mensagem': mensagem
    }
    supabase.table('interessados').insert(interesse_data).execute()
    
    flash("Você manifestou interesse! O autor será notificado.")
    return redirect(url_for('ver_problema', problema_id=problema_id))

@app.route('/interessados/<int:problema_id>')
def ver_interessados(problema_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Verificar se é o autor
    problema_response = supabase.table('problemas').select('usuario_id').eq('id', problema_id).execute()
    if not problema_response.data or problema_response.data[0]['usuario_id'] != session['user_id']:
        flash("Apenas o autor pode ver os interessados!")
        return redirect(url_for('ver_problema', problema_id=problema_id))
    
    # Buscar interessados
    response = supabase.table('interessados').select('*, users(nome, foto, telefone)').eq('problema_id', problema_id).execute()
    interessados = response.data
    
    return render_template('interessados.html', interessados=interessados, problema_id=problema_id)

# ============================================
# MENSAGENS
# ============================================

@app.route('/mensagens')
def mensagens():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Buscar conversas (simplificado)
    response = supabase.table('mensagens').select('*').or_(f'remetente_id.eq.{session["user_id"]},destinatario_id.eq.{session["user_id"]}').execute()
    
    # Agrupar por utilizador
    conversas_dict = {}
    for msg in response.data:
        outro_id = msg['destinatario_id'] if msg['remetente_id'] == session['user_id'] else msg['remetente_id']
        if outro_id not in conversas_dict:
            # Buscar dados do outro utilizador
            user_response = supabase.table('users').select('id, nome, foto').eq('id', outro_id).execute()
            if user_response.data:
                user = user_response.data[0]
                conversas_dict[outro_id] = {
                    'outro_id': user['id'],
                    'nome': user['nome'],
                    'foto': user['foto'],
                    'ultima': msg['conteudo'],
                    'ultima_data': msg['data_envio']
                }
    
    conversas = list(conversas_dict.values())
    return render_template('mensagens.html', conversas=conversas)

@app.route('/mensagens/<int:outro_id>')
def conversa(outro_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Buscar dados do outro utilizador
    user_response = supabase.table('users').select('id, nome, foto').eq('id', outro_id).execute()
    if not user_response.data:
        flash("Utilizador não encontrado!")
        return redirect(url_for('mensagens'))
    outro = user_response.data[0]
    
    # Buscar mensagens entre os dois
    response = supabase.table('mensagens').select('*').or_(f'and(remetente_id.eq.{session["user_id"]},destinatario_id.eq.{outro_id}),and(remetente_id.eq.{outro_id},destinatario_id.eq.{session["user_id"]})').order('data_envio').execute()
    mensagens_lista = response.data
    
    # Marcar como lidas
    supabase.table('mensagens').update({'lida': 1}).eq('remetente_id', outro_id).eq('destinatario_id', session['user_id']).execute()
    
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
    
    msg_data = {
        'remetente_id': session['user_id'],
        'destinatario_id': destinatario_id,
        'conteudo': conteudo,
        'problema_id': problema_id
    }
    supabase.table('mensagens').insert(msg_data).execute()
    
    return redirect(url_for('conversa', outro_id=destinatario_id))

# ============================================
# NOTIFICAÇÕES
# ============================================

@app.route('/notificacoes')
def notificacoes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Mensagens não lidas
    msgs_response = supabase.table('mensagens').select('*').eq('destinatario_id', session['user_id']).eq('lida', 0).execute()
    mensagens_nao_lidas = len(msgs_response.data)
    
    # Interesses pendentes
    interesses_response = supabase.table('interessados').select('*, users(nome), problemas(titulo)').eq('status', 'pendente').execute()
    interesses_pendentes = len(interesses_response.data)
    
    # Detalhes das notificações
    notificacoes_mensagens = []
    for msg in msgs_response.data[:5]:
        user_resp = supabase.table('users').select('nome').eq('id', msg['remetente_id']).execute()
        if user_resp.data:
            notificacoes_mensagens.append({
                'conteudo': msg['conteudo'],
                'nome': user_resp.data[0]['nome'],
                'data_envio': msg['data_envio']
            })
    
    notificacoes_interesses = []
    for interesse in interesses_response.data[:5]:
        user_resp = supabase.table('users').select('nome').eq('id', interesse['usuario_id']).execute()
        if user_resp.data:
            notificacoes_interesses.append({
                'mensagem': interesse['mensagem'],
                'nome': user_resp.data[0]['nome'],
                'data_interesse': interesse['data_interesse'],
                'titulo': interesse.get('problemas', {}).get('titulo', 'Problema')
            })
    
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
    
    response = supabase.table('users').select('nome, email, telefone, foto, localizacao, bio, data_registo').eq('id', session['user_id']).execute()
    user = response.data[0] if response.data else None
    
    return render_template('perfil.html', user=user)

@app.route('/perfil/<int:user_id>')
def perfil_publico(user_id):
    response = supabase.table('users').select('id, nome, email, telefone, foto, localizacao, bio, data_registo').eq('id', user_id).execute()
    user = response.data[0] if response.data else None
    
    if not user:
        flash("Utilizador não encontrado!")
        return redirect(url_for('index'))
    
    # Problemas do utilizador
    problemas_response = supabase.table('problemas').select('*').eq('usuario_id', user_id).order('data_criacao', desc=True).execute()
    problemas = problemas_response.data
    
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
        
        supabase.table('users').update({'foto': filename}).eq('id', session['user_id']).execute()
        
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
    
    supabase.table('users').update({campo: valor}).eq('id', session['user_id']).execute()
    
    flash(f"Campo atualizado com sucesso!")
    return redirect(url_for('perfil'))

# ============================================
# CATEGORIAS E AJUDA
# ============================================

@app.route('/categorias')
def categorias():
    # Buscar contagem por categoria
    response = supabase.table('problemas').select('categoria').execute()
    contagem_dict = {}
    for item in response.data:
        cat = item['categoria']
        contagem_dict[cat] = contagem_dict.get(cat, 0) + 1
    contagem = [(cat, count) for cat, count in contagem_dict.items()]
    
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
    
    response = supabase.table('problemas').select('*').eq('usuario_id', session['user_id']).order('data_criacao', desc=True).execute()
    publicacoes = response.data
    
    return render_template('minhas_publicacoes.html', publicacoes=publicacoes)

@app.route('/ajuda')
def ajuda():
    return render_template('ajuda.html')

# ============================================
# ROTA PARA RESETAR BANCO (TEMPORÁRIA)
# ============================================

@app.route('/resetar-banco')
def resetar_banco():
    # Esta rota só funciona para o SQLite, removida para Supabase
    return "Com Supabase não é necessário resetar. Os dados são persistentes!"

# ============================================
# INICIAR SERVIDOR
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)