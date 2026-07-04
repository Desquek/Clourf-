from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db

favorites = Blueprint('favorites', __name__)

# ============================================
# LISTAR FAVORITOS DO UTILIZADOR
# ============================================

@favorites.route('/favoritos')
def favoritos():
    if 'user_id' not in session:
        flash("Faça login para ver os seus favoritos.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.*,
            u.nome AS autor_nome,
            u.foto AS autor_foto
        FROM favoritos f
        JOIN problemas p ON f.problema_id = p.id
        JOIN users u ON p.usuario_id = u.id
        WHERE f.usuario_id = %s
        ORDER BY f.data_favorito DESC
    """, (session['user_id'],))

    favoritos = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('favoritos.html', favoritos=favoritos)


# ============================================
# ADICIONAR AOS FAVORITOS
# ============================================

@favorites.route('/favoritar/<int:problema_id>')
def favoritar(problema_id):
    if 'user_id' not in session:
        flash("Faça login para favoritar.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor()

    # Verificar se o problema existe
    cur.execute("SELECT id FROM problemas WHERE id = %s", (problema_id,))
    if not cur.fetchone():
        flash("Problema não encontrado.", "danger")
        cur.close()
        conn.close()
        return redirect(url_for('home.inicio'))

    # Verificar se já está nos favoritos
    cur.execute("""
        SELECT id FROM favoritos
        WHERE usuario_id = %s AND problema_id = %s
    """, (session['user_id'], problema_id))
    
    if cur.fetchone():
        flash("Este problema já está nos seus favoritos.", "info")
        cur.close()
        conn.close()
        return redirect(url_for('posts.ver_problema', problema_id=problema_id))

    # Adicionar aos favoritos
    cur.execute("""
        INSERT INTO favoritos (usuario_id, problema_id)
        VALUES (%s, %s)
    """, (session['user_id'], problema_id))
    conn.commit()

    cur.close()
    conn.close()

    flash("Problema adicionado aos favoritos!", "success")
    return redirect(url_for('posts.ver_problema', problema_id=problema_id))


# ============================================
# REMOVER DOS FAVORITOS
# ============================================

@favorites.route('/desfavoritar/<int:problema_id>')
def desfavoritar(problema_id):
    if 'user_id' not in session:
        flash("Faça login para remover dos favoritos.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM favoritos
        WHERE usuario_id = %s AND problema_id = %s
    """, (session['user_id'], problema_id))
    conn.commit()

    cur.close()
    conn.close()

    flash("Problema removido dos favoritos.", "success")
    return redirect(url_for('favorites.favoritos'))


# ============================================
# VERIFICAR SE UM PROBLEMA ESTÁ NOS FAVORITOS
# ============================================

@favorites.route('/verificar-favorito/<int:problema_id>')
def verificar_favorito(problema_id):
    if 'user_id' not in session:
        return {"favorito": False}

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM favoritos
        WHERE usuario_id = %s AND problema_id = %s
    """, (session['user_id'], problema_id))
    result = cur.fetchone()
    cur.close()
    conn.close()

    return {"favorito": result is not None}