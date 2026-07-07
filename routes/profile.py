from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
import os
from werkzeug.utils import secure_filename

profile = Blueprint('profile', __name__)

# ============================================
# CONFIGURAÇÃO DE UPLOAD
# ============================================

UPLOAD_FOLDER = 'static/uploads/perfil'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================
# VER PERFIL DO UTILIZADOR LOGADO
# ============================================

@profile.route('/perfil')
def perfil():
    if 'user_id' not in session:
        flash("Faça login para aceder ao perfil.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nome, email, telefone, localizacao, bio, foto, data_registo
        FROM users
        WHERE id = %s
    """, (session['user_id'],))

    user = cur.fetchone()
    cur.close()
    conn.close()

    return render_template('perfil.html', user=user)


# ============================================
# VER PERFIL PÚBLICO DE OUTRO UTILIZADOR
# ============================================

@profile.route('/perfil/<int:user_id>')
def perfil_publico(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nome, email, telefone, localizacao, bio, foto, data_registo
        FROM users
        WHERE id = %s
    """, (user_id,))

    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        flash("Utilizador não encontrado.", "danger")
        return redirect(url_for('home.inicio'))

    # Buscar problemas do utilizador
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, titulo, descricao, categoria, localizacao, data_criacao
        FROM problemas
        WHERE usuario_id = %s
        ORDER BY data_criacao DESC
    """, (user_id,))
    problemas = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('perfil_publico.html', user=user, problemas=problemas)


# ============================================
# EDITAR PERFIL
# ============================================

@profile.route('/editar-perfil', methods=['GET', 'POST'])
def editar_perfil():
    if 'user_id' not in session:
        flash("Faça login para editar o perfil.", "warning")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        localizacao = request.form['localizacao']
        bio = request.form['bio']

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE users
            SET nome = %s, telefone = %s, localizacao = %s, bio = %s
            WHERE id = %s
        """, (nome, telefone, localizacao, bio, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()

        session['nome'] = nome
        flash("Perfil atualizado com sucesso!", "success")
        return redirect(url_for('profile.perfil'))

    # GET - Mostra formulário com dados atuais
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT nome, telefone, localizacao, bio
        FROM users
        WHERE id = %s
    """, (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()

    return render_template('editar_perfil.html', user=user)


# ============================================
# UPLOAD DE FOTO DE PERFIL
# ============================================

@profile.route('/upload-foto', methods=['POST'])
def upload_foto():
    if 'user_id' not in session:
        flash("Faça login para atualizar a foto.", "warning")
        return redirect(url_for('auth.login'))

    if 'foto' not in request.files:
        flash("Nenhuma foto selecionada.", "danger")
        return redirect(url_for('profile.perfil'))

    foto = request.files['foto']

    if foto.filename == '':
        flash("Nenhuma foto selecionada.", "danger")
        return redirect(url_for('profile.perfil'))

    if foto and allowed_file(foto.filename):
        # Criar pasta se não existir
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # Nome único para o ficheiro
        ext = foto.filename.rsplit('.', 1)[1].lower()
        filename = f"user_{session['user_id']}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # Guardar a foto
        foto.save(filepath)

        # Atualizar base de dados
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE users
            SET foto = %s
            WHERE id = %s
        """, (filename, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()

        flash("Foto de perfil atualizada com sucesso!", "success")
    else:
        flash("Formato inválido. Use JPG, PNG ou GIF.", "danger")

    return redirect(url_for('profile.perfil'))