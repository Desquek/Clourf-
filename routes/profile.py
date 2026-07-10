from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
import os
import re
from werkzeug.utils import secure_filename

profile = Blueprint('profile', __name__)

# ============================================
# CONFIGURAÇÃO DE UPLOAD
# ============================================

UPLOAD_FOLDER = 'static/uploads/perfil'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Criar pasta se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================
# VALIDAR NÚMERO DE TELEMÓVEL
# ============================================

def validar_telefone(telefone):
    if not telefone:
        return True
    telefone = re.sub(r'[\s\+\(\)\-]', '', telefone)
    return bool(re.match(r'^[89]\d{8}$', telefone))

def formatar_telefone(telefone):
    if not telefone:
        return ''
    telefone = re.sub(r'[\s\+\(\)\-]', '', telefone)
    if len(telefone) == 9:
        return f"{telefone[:2]} {telefone[2:5]} {telefone[5:]}"
    return telefone


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
    
    # Verificar se é PostgreSQL ou SQLite
    is_postgres = hasattr(cur, 'mogrify')
    
    if is_postgres:
        cur.execute("""
            SELECT id, nome, email, telefone, localizacao, bio, foto, data_registo
            FROM users
            WHERE id = %s
        """, (session['user_id'],))
    else:
        cur.execute("""
            SELECT id, nome, email, telefone, localizacao, bio, foto, data_registo
            FROM users
            WHERE id = ?
        """, (session['user_id'],))
    
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        # Formatar telefone
        telefone = user['telefone'] if is_postgres else user[3]
        if telefone:
            user['telefone_formatado'] = formatar_telefone(telefone)
        else:
            user['telefone_formatado'] = ''

    return render_template('perfil.html', user=user)


# ============================================
# VER PERFIL PÚBLICO
# ============================================

@profile.route('/perfil/<int:user_id>')
def perfil_publico(user_id):
    conn = get_db()
    cur = conn.cursor()
    
    is_postgres = hasattr(cur, 'mogrify')
    
    if is_postgres:
        cur.execute("""
            SELECT id, nome, email, telefone, localizacao, bio, foto, data_registo
            FROM users
            WHERE id = %s
        """, (user_id,))
    else:
        cur.execute("""
            SELECT id, nome, email, telefone, localizacao, bio, foto, data_registo
            FROM users
            WHERE id = ?
        """, (user_id,))
    
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        flash("Utilizador não encontrado.", "danger")
        return redirect(url_for('home.inicio'))

    telefone = user['telefone'] if is_postgres else user[3]
    if telefone:
        user['telefone_formatado'] = formatar_telefone(telefone)
    else:
        user['telefone_formatado'] = ''

    # Buscar problemas do utilizador
    conn = get_db()
    cur = conn.cursor()
    
    if is_postgres:
        cur.execute("""
            SELECT id, titulo, descricao, categoria, localizacao, data_criacao
            FROM problemas
            WHERE usuario_id = %s
            ORDER BY data_criacao DESC
        """, (user_id,))
    else:
        cur.execute("""
            SELECT id, titulo, descricao, categoria, localizacao, data_criacao
            FROM problemas
            WHERE usuario_id = ?
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
        nome = request.form.get('nome', '').strip()
        telefone = request.form.get('telefone', '').strip()
        localizacao = request.form.get('localizacao', '').strip()
        bio = request.form.get('bio', '').strip()

        if not nome:
            flash("O nome não pode estar vazio.", "danger")
            return render_template('editar_perfil.html', user={'nome': nome, 'telefone': telefone, 'localizacao': localizacao, 'bio': bio})

        if telefone and not validar_telefone(telefone):
            flash("Número de telemóvel inválido. Deve ter 9 dígitos e começar com 8 ou 9.", "danger")
            return render_template('editar_perfil.html', user={'nome': nome, 'telefone': telefone, 'localizacao': localizacao, 'bio': bio})

        if telefone:
            telefone = re.sub(r'[\s\+\(\)\-]', '', telefone)

        conn = get_db()
        cur = conn.cursor()
        is_postgres = hasattr(cur, 'mogrify')
        
        if is_postgres:
            cur.execute("""
                UPDATE users
                SET nome = %s, telefone = %s, localizacao = %s, bio = %s
                WHERE id = %s
            """, (nome, telefone, localizacao, bio, session['user_id']))
        else:
            cur.execute("""
                UPDATE users
                SET nome = ?, telefone = ?, localizacao = ?, bio = ?
                WHERE id = ?
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
    is_postgres = hasattr(cur, 'mogrify')
    
    if is_postgres:
        cur.execute("""
            SELECT nome, telefone, localizacao, bio
            FROM users
            WHERE id = %s
        """, (session['user_id'],))
    else:
        cur.execute("""
            SELECT nome, telefone, localizacao, bio
            FROM users
            WHERE id = ?
        """, (session['user_id'],))
    
    user = cur.fetchone()
    cur.close()
    conn.close()

    return render_template('editar_perfil.html', user=user)


# ============================================
# UPLOAD DE FOTO DE PERFIL (VERSÃO SIMPLES - LOCAL)
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

    if not allowed_file(foto.filename):
        flash("Formato inválido. Use JPG, PNG ou GIF.", "danger")
        return redirect(url_for('profile.perfil'))

    # Salvar a foto localmente
    ext = foto.filename.rsplit('.', 1)[1].lower()
    filename = f"user_{session['user_id']}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    foto.save(filepath)

    # Guardar o nome do ficheiro no banco
    conn = get_db()
    cur = conn.cursor()
    is_postgres = hasattr(cur, 'mogrify')
    
    if is_postgres:
        cur.execute("UPDATE users SET foto = %s WHERE id = %s", (filename, session['user_id']))
    else:
        cur.execute("UPDATE users SET foto = ? WHERE id = ?", (filename, session['user_id']))
    
    conn.commit()
    cur.close()
    conn.close()

    flash("Foto de perfil atualizada com sucesso!", "success")
    return redirect(url_for('profile.perfil'))