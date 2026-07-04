from flask import Blueprint, render_template, session, flash, redirect, url_for
from database import get_db

admin_dashboard = Blueprint('admin_dashboard', __name__, url_prefix='/admin')

def is_admin(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result and result['is_admin'] is True

@admin_dashboard.route('/')
def dashboard():
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash("Acesso negado.", "danger")
        return redirect(url_for('home.inicio'))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()['count']

    cur.execute("SELECT COUNT(*) FROM problemas")
    total_problemas = cur.fetchone()['count']

    cur.execute("SELECT COUNT(*) FROM problemas WHERE DATE(data_criacao) = CURRENT_DATE")
    problemas_hoje = cur.fetchone()['count']

    cur.execute("SELECT COUNT(*) FROM users WHERE DATE(data_registo) = CURRENT_DATE")
    novos_usuarios = cur.fetchone()['count']

    cur.execute("SELECT id, nome, email, data_registo FROM users ORDER BY data_registo DESC LIMIT 10")
    ultimos_utilizadores = cur.fetchall()

    cur.execute("""
        SELECT p.id, p.titulo, u.nome AS autor, p.data_criacao
        FROM problemas p
        JOIN users u ON p.usuario_id = u.id
        ORDER BY p.data_criacao DESC LIMIT 10
    """)
    ultimos_problemas = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('admin/dashboard.html',
        total_users=total_users,
        total_problemas=total_problemas,
        problemas_hoje=problemas_hoje,
        novos_usuarios=novos_usuarios,
        ultimos_utilizadores=ultimos_utilizadores,
        ultimos_problemas=ultimos_problemas)