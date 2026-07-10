from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
import bcrypt
import traceback

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        telefone = request.form.get('telefone', '').strip()
        senha = request.form.get('senha', '')

        if not nome or not email or not senha:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template('register.html')

        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())

        conn = get_db()
        if conn is None:
            flash("Erro ao conectar à base de dados!", "danger")
            return render_template('register.html')

        cur = conn.cursor()
        is_postgres = hasattr(cur, 'mogrify')
        
        try:
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

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')

        if not email or not senha:
            flash("Preencha todos os campos.", "danger")
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
                    session['user_id'] = str(user_id)  # Guardar como string
                    session['nome'] = user_nome
                    flash(f"Bem-vindo, {user_nome}!", "success")
                    return redirect(url_for('home.inicio'))
                else:
                    flash("Email ou senha inválidos.", "danger")
            else:
                flash("Email ou senha inválidos.", "danger")
        except Exception as e:
            flash(f"Erro ao fazer login: {str(e)}", "danger")
            print(traceback.format_exc())

    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.clear()
    flash("Saiu com sucesso!", "success")
    return redirect(url_for('auth.login'))