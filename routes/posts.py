from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db

posts = Blueprint('posts', __name__)

# ============================================
# PUBLICAR PROBLEMA
# ============================================

@posts.route('/novo-problema', methods=['GET', 'POST'])
def novo_problema():
    if 'user_id' not in session:
        flash("Faça login para publicar.", "warning")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        categoria = request.form['categoria']
        localizacao = request.form['localizacao']

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO problemas (titulo, descricao, categoria, localizacao, usuario_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (titulo, descricao, categoria, localizacao, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()

        flash("Problema publicado com sucesso!", "success")
        return redirect(url_for('home.inicio'))

    return render_template('novo_problema.html')


# ============================================
# VER PROBLEMA (COM VERIFICAÇÃO DE PROPOSTA)
# ============================================

@posts.route('/problema/<int:problema_id>')
def ver_problema(problema_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.*, u.id AS autor_id, u.nome AS autor_nome, u.foto AS autor_foto, u.telefone
        FROM problemas p
        JOIN users u ON p.usuario_id = u.id
        WHERE p.id = %s
    """, (problema_id,))
    problema = cur.fetchone()
    cur.close()
    conn.close()

    if not problema:
        flash("Problema não encontrado.", "danger")
        return redirect(url_for('home.inicio'))

    # Verificar se o utilizador já enviou proposta
    ja_proposto = False
    if 'user_id' in session:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM mensagens WHERE remetente_id = %s AND problema_id = %s", 
                   (session['user_id'], problema_id))
        ja_proposto = cur.fetchone() is not None
        cur.close()
        conn.close()

    return render_template('problema.html', problema=problema, ja_proposto=ja_proposto)


# ============================================
# EDITAR PROBLEMA
# ============================================

@posts.route('/editar-problema/<int:problema_id>', methods=['GET', 'POST'])
def editar_problema(problema_id):
    if 'user_id' not in session:
        flash("Faça login para editar.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM problemas WHERE id = %s AND usuario_id = %s", 
                (problema_id, session['user_id']))
    problema = cur.fetchone()
    cur.close()

    if not problema:
        flash("Problema não encontrado ou não tem permissão.", "danger")
        conn.close()
        return redirect(url_for('home.inicio'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        categoria = request.form['categoria']
        localizacao = request.form['localizacao']

        cur = conn.cursor()
        cur.execute("""
            UPDATE problemas
            SET titulo = %s, descricao = %s, categoria = %s, localizacao = %s
            WHERE id = %s AND usuario_id = %s
        """, (titulo, descricao, categoria, localizacao, problema_id, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()

        flash("Problema atualizado!", "success")
        return redirect(url_for('posts.ver_problema', problema_id=problema_id))

    return render_template('editar_problema.html', problema=problema)


# ============================================
# APAGAR PROBLEMA
# ============================================

@posts.route('/apagar-problema/<int:problema_id>', methods=['POST'])
def apagar_problema(problema_id):
    if 'user_id' not in session:
        flash("Faça login para apagar.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM problemas WHERE id = %s AND usuario_id = %s", 
                (problema_id, session['user_id']))
    conn.commit()
    cur.close()
    conn.close()

    flash("Problema apagado!", "success")
    return redirect(url_for('home.inicio'))