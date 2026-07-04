from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from database import get_db
from .dashboard import is_admin

admin_problemas = Blueprint('admin_problemas', __name__, url_prefix='/admin/problemas')

@admin_problemas.route('/')
def listar():
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash("Acesso negado.", "danger")
        return redirect(url_for('home.inicio'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.*, u.nome AS autor_nome
        FROM problemas p
        JOIN users u ON p.usuario_id = u.id
        ORDER BY p.data_criacao DESC
    """)
    problemas = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('admin/problemas.html', problemas=problemas)

@admin_problemas.route('/apagar/<int:problema_id>', methods=['POST'])
def apagar(problema_id):
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash("Acesso negado.", "danger")
        return redirect(url_for('home.inicio'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM interessados WHERE problema_id = %s", (problema_id,))
    cur.execute("DELETE FROM favoritos WHERE problema_id = %s", (problema_id,))
    cur.execute("DELETE FROM problemas WHERE id = %s", (problema_id,))
    conn.commit()
    cur.close()
    conn.close()

    flash("Problema apagado com sucesso!", "success")
    return redirect(url_for('admin_problemas.listar'))