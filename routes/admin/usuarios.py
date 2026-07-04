from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from database import get_db
from .dashboard import is_admin

admin_usuarios = Blueprint('admin_usuarios', __name__, url_prefix='/admin/usuarios')

@admin_usuarios.route('/')
def listar():
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash("Acesso negado.", "danger")
        return redirect(url_for('home.inicio'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nome, email, telefone, localizacao, data_registo, is_admin
        FROM users
        ORDER BY data_registo DESC
    """)
    usuarios = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('admin/usuarios.html', usuarios=usuarios)

@admin_usuarios.route('/apagar/<int:user_id>', methods=['POST'])
def apagar(user_id):
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash("Acesso negado.", "danger")
        return redirect(url_for('home.inicio'))

    if user_id == session['user_id']:
        flash("Não pode apagar a sua própria conta.", "danger")
        return redirect(url_for('admin_usuarios.listar'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM mensagens WHERE remetente_id = %s OR destinatario_id = %s", (user_id, user_id))
    cur.execute("DELETE FROM interessados WHERE usuario_id = %s", (user_id,))
    cur.execute("DELETE FROM problemas WHERE usuario_id = %s", (user_id,))
    cur.execute("DELETE FROM favoritos WHERE usuario_id = %s", (user_id,))
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    flash("Utilizador apagado com sucesso!", "success")
    return redirect(url_for('admin_usuarios.listar'))