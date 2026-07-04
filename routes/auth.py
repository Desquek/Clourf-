from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
import bcrypt
import os

auth = Blueprint('auth', __name__)

# ============================================
# REGISTO
# ============================================
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        senha = request.form['senha']
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())

        conn = get_db()
        if conn is None:
            flash("Erro ao conectar à base de dados.", "danger")
            return render_template('register.html')

        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO users (nome, email, telefone, senha_hash)
                VALUES (%s, %s, %s, %s)
            """, (nome, email, telefone, senha_hash.decode('utf-8')))
            conn.commit()
            flash("Conta criada com sucesso! Faça login.", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            conn.rollback()
            if 'duplicate key' in str(e).lower():
                flash("Este email já está registado.", "danger")
            else:
                flash(f"Erro ao criar conta: {e}", "danger")
        finally:
            cur.close()
            conn.close()

    return render_template('register.html')

# ============================================
# LOGIN
# ============================================
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = get_db()
        if conn is None:
            flash("Erro ao conectar à base de dados.", "danger")
            return render_template('login.html')

        cur = conn.cursor()
        cur.execute("""
            SELECT id, nome, senha_hash FROM users WHERE email = %s
        """, (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and bcrypt.checkpw(senha.encode('utf-8'), user['senha_hash'].encode('utf-8')):
            session['user_id'] = user['id']
            session['nome'] = user['nome']
            flash(f"Bem-vindo, {user['nome']}!", "success")
            return redirect(url_for('home.index'))
        else:
            flash("Email ou senha inválidos.", "danger")

    return render_template('login.html')

# ============================================
# LOGOUT
# ============================================
@auth.route('/logout')
def logout():
    session.clear()
    flash("Saiu com sucesso!", "success")
    return redirect(url_for('auth.login'))