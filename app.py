from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "clourf_conecta_secret"

# ============================================
# SUPABASE CONFIGURATION
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
                senha TEXT NOT NULL
            );
            """).execute()
            print("✅ Tabela users criada!")
        except Exception as e:
            print(f"❌ Erro: {e}")

init_supabase()

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
        
        if supabase is None:
            flash("Erro: Base de dados não disponível!")
            return render_template('register.html')
        
        try:
            # Verificar se email existe
            existing = supabase.table('users').select('*').eq('email', email).execute()
            if existing.data:
                flash("Email já registado!")
                return render_template('register.html')
            
            # Criar utilizador
            user_data = {'nome': nome, 'email': email, 'telefone': telefone, 'senha': senha}
            supabase.table('users').insert(user_data).execute()
            flash("Conta criada com sucesso!")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Erro: {str(e)}")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        if supabase is None:
            flash("Erro: Base de dados não disponível!")
            return render_template('login.html')
        
        try:
            response = supabase.table('users').select('id, nome').eq('email', email).eq('senha', senha).execute()
            if response.data:
                user = response.data[0]
                session['user_id'] = user['id']
                session['nome'] = user['nome']
                flash(f"Bem-vindo, {user['nome']}!")
                return redirect(url_for('dashboard'))
            else:
                flash("Email ou senha inválidos!")
        except Exception as e:
            flash(f"Erro: {str(e)}")
    
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