from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
import bcrypt
import re
import traceback

auth = Blueprint('auth', __name__)

# ============================================
# VALIDAR EMAIL
# ============================================

def validar_email(email):
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email) is not None

# ============================================
# VALIDAR TELEFONE (apenas números, 9 dígitos)
# ============================================

def validar_telefone(telefone):
    # Remove espaços e caracteres especiais
    telefone = re.sub(r'[\s\+\(\)\-]', '', telefone)
    # Verifica se tem 9 dígitos
    return len(telefone) == 9 and telefone.isdigit()

# ============================================
# VALIDAR SENHA FORTE
# ============================================

def validar_senha_forte(senha):
    """
    Senha forte:
    - Mínimo 8 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    - Pelo menos 1 caractere especial
    """
    if len(senha) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."
    
    if not re.search(r'[A-Z]', senha):
        return False, "A senha deve ter pelo menos 1 letra maiúscula."
    
    if not re.search(r'[a-z]', senha):
        return False, "A senha deve ter pelo menos 1 letra minúscula."
    
    if not re.search(r'[0-9]', senha):
        return False, "A senha deve ter pelo menos 1 número."
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
        return False, "A senha deve ter pelo menos 1 caractere especial (!@#$%^&*)."
    
    return True, "Senha forte."

# ============================================
# REGISTO
# ============================================

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        telefone = request.form.get('telefone', '').strip()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        # ===== VALIDAR NOME =====
        if not nome:
            flash("Por favor, insira o seu nome completo.", "danger")
            return render_template('register.html')
        if len(nome) < 3:
            flash("O nome deve ter pelo menos 3 caracteres.", "danger")
            return render_template('register.html')

        # ===== VALIDAR EMAIL =====
        if not email:
            flash("Por favor, insira o seu email.", "danger")
            return render_template('register.html')
        if not validar_email(email):
            flash("Email inválido. Use o formato exemplo@email.com.", "danger")
            return render_template('register.html')

        # ===== VALIDAR TELEFONE =====
        if not telefone:
            flash("Por favor, insira o seu número de telefone.", "danger")
            return render_template('register.html')
        if not validar_telefone(telefone):
            flash("Número de telefone inválido. Deve ter 9 dígitos (ex: 841234567).", "danger")
            return render_template('register.html')

        # ===== VALIDAR SENHA =====
        if not senha:
            flash("Por favor, insira uma senha.", "danger")
            return render_template('register.html')
        
        senha_valida, mensagem = validar_senha_forte(senha)
        if not senha_valida:
            flash(mensagem, "danger")
            return render_template('register.html')

        # ===== CONFIRMAR SENHA =====
        if senha != confirmar_senha:
            flash("As senhas não coincidem.", "danger")
            return render_template('register.html')

        # ===== VERIFICAR SE EMAIL JÁ EXISTE =====
        conn = get_db()
        if conn is None:
            flash("Erro ao conectar à base de dados!", "danger")
            return render_template('register.html')

        cur = conn.cursor()
        is_postgres = hasattr(cur, 'mogrify')
        
        try:
            if is_postgres:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            else:
                cur.execute("SELECT id FROM users WHERE email = ?", (email,))
            
            if cur.fetchone():
                flash("Este email já está registado. Faça login.", "warning")
                cur.close()
                conn.close()
                return render_template('register.html')
            
            # ===== HASH DA SENHA =====
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
            
            # ===== INSERIR UTILIZADOR =====
            if is_postgres:
                cur.execute("""
                    INSERT INTO users (nome, email, telefone, senha_hash)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (nome, email, telefone, senha_hash.decode('utf-8')))
                user_id = cur.fetchone()['id']
            else:
                cur.execute("""
                    INSERT INTO users (nome, email, telefone, senha_hash)
                    VALUES (?, ?, ?, ?)
                """, (nome, email, telefone, senha_hash.decode('utf-8')))
                user_id = cur.lastrowid
            
            conn.commit()
            cur.close()
            conn.close()

            flash("Conta criada com sucesso! Faça login.", "success")
            return redirect(url_for('auth.login'))

        except Exception as e:
            conn.rollback()
            flash(f"Erro ao criar conta: {str(e)}", "danger")
            print(traceback.format_exc())
            return render_template('register.html')

    return render_template('register.html')


# ============================================
# LOGIN
# ============================================

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')

        if not email:
            flash("Por favor, insira o seu email.", "danger")
            return render_template('login.html')
        if not senha:
            flash("Por favor, insira a sua senha.", "danger")
            return render_template('login.html')

        conn = get_db()
        if conn is None:
            flash("Erro ao conectar à base de dados!", "danger")
            return render_template('login.html')

        cur = conn.cursor()
        is_postgres = hasattr(cur, 'mogrify')
        
        try:
            if is_postgres:
                cur.execute("SELECT id, nome, senha_hash FROM users WHERE email = %s", (email,))
            else:
                cur.execute("SELECT id, nome, senha_hash FROM users WHERE email = ?", (email,))
            
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user:
                if is_postgres:
                    user_id = user['id']
                    user_nome = user['nome']
                    user_hash = user['senha_hash']
                else:
                    user_id = user[0]
                    user_nome = user[1]
                    user_hash = user[2]
                
                if bcrypt.checkpw(senha.encode('utf-8'), user_hash.encode('utf-8')):
                    session['user_id'] = user_id
                    session['nome'] = user_nome
                    flash(f"Bem-vindo, {user_nome}!", "success")
                    return redirect(url_for('home.inicio'))
                else:
                    flash("Senha incorreta.", "danger")
            else:
                flash("Email não encontrado.", "danger")
        except Exception as e:
            flash(f"Erro ao fazer login: {str(e)}", "danger")
            print(traceback.format_exc())

    return render_template('login.html')


# ============================================
# LOGOUT
# ============================================

@auth.route('/logout')
def logout():
    session.clear()
    flash("Saiu com sucesso!", "success")
    return redirect(url_for('auth.login'))