from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db

admin = Blueprint('admin', __name__)

# ============================================
# VERIFICAR SE O UTILIZADOR É ADMIN
# ============================================

def is_admin(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result and result['is_admin'] is True


# ============================================
# PAINEL ADMIN (DASHBOARD)
# ============================================

@admin.route('/admin')
def admin_dashboard():
    if 'user_id' not in session:
        flash("Faça login para aceder ao painel.", "warning")
        return redirect(url_for('auth.login'))

    if not is_admin(session['user_id']):
        flash("Acesso negado. Apenas administradores.", "danger")
        return redirect(url_for('home.inicio'))

    conn = get_db()
    cur = conn.cursor()

    # Estatísticas
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()['count']

    cur.execute("SELECT COUNT(*) FROM problemas")
    total_problemas = cur.fetchone()['count']

    cur.execute("SELECT COUNT(*) FROM problemas WHERE DATE(data_criacao) = CURRENT_DATE")
    problemas_hoje = cur.fetchone()['count']

    cur.execute("SELECT COUNT(*) FROM users WHERE DATE(data_registo) = CURRENT_DATE")
    novos_usuarios = cur.fetchone()['count']

    # Últimos utilizadores
    cur.execute("""
        SELECT id, nome, email, data_registo
        FROM users
        ORDER BY data_registo DESC
        LIMIT 10
    """)
    ultimos_utilizadores = cur.fetchall()

    # Últimos problemas
    cur.execute("""
        SELECT p.id, p.titulo, u.nome AS autor, p.data_criacao
        FROM problemas p
        JOIN users u ON p.usuario_id = u.id
        ORDER BY p.data_criacao DESC
        LIMIT 10
    """)
    ultimos_problemas = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_problemas=total_problemas,
        problemas_hoje=problemas_hoje,
        novos_usuarios=novos_usuarios,
        ultimos_utilizadores=ultimos_utilizadores,
        ultimos_problemas=ultimos_problemas
    )


# ============================================
# LISTAR UTILIZADORES (ADMIN)
# ============================================

@admin.route('/admin/usuarios')
def admin_usuarios():
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


# ============================================
# LISTAR PROBLEMAS (ADMIN)
# ============================================

@admin.route('/admin/problemas')
def admin_problemas():
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


# ============================================
# APAGAR UTILIZADOR (ADMIN)
# ============================================

@admin.route('/admin/usuario/apagar/<int:user_id>', methods=['POST'])
def admin_apagar_usuario(user_id):
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash("Acesso negado.", "danger")
        return redirect(url_for('home.inicio'))

    if user_id == session['user_id']:
        flash("Não pode apagar a sua própria conta.", "danger")
        return redirect(url_for('admin.admin_usuarios'))

    conn = get_db()
    cur = conn.cursor()

    # Apagar mensagens
    cur.execute("DELETE FROM mensagens WHERE remetente_id = %s OR destinatario_id = %s", (user_id, user_id))
    # Apagar interessados
    cur.execute("DELETE FROM interessados WHERE usuario_id = %s", (user_id,))
    # Apagar problemas
    cur.execute("DELETE FROM problemas WHERE usuario_id = %s", (user_id,))
    # Apagar favoritos
    cur.execute("DELETE FROM favoritos WHERE usuario_id = %s", (user_id,))
    # Apagar utilizador
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))

    conn.commit()
    cur.close()
    conn.close()

    flash("Utilizador apagado com sucesso!", "success")
    return redirect(url_for('admin.admin_usuarios'))


# ============================================
# APAGAR PROBLEMA (ADMIN)
# ============================================

@admin.route('/admin/problema/apagar/<int:problema_id>', methods=['POST'])
def admin_apagar_problema(problema_id):
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash("Acesso negado.", "danger")
        return redirect(url_for('home.inicio'))

    conn = get_db()
    cur = conn.cursor()

    # Apagar interessados
    cur.execute("DELETE FROM interessados WHERE problema_id = %s", (problema_id,))
    # Apagar favoritos
    cur.execute("DELETE FROM favoritos WHERE problema_id = %s", (problema_id,))
    # Apagar problema
    cur.execute("DELETE FROM problemas WHERE id = %s", (problema_id,))

    conn.commit()
    cur.close()
    conn.close()

    flash("Problema apagado com sucesso!", "success")
    return redirect(url_for('admin.admin_problemas'))