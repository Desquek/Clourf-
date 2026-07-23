from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
import os
from werkzeug.utils import secure_filename
import json

vitrina = Blueprint('vitrina', __name__)

# ============================================
# CONFIGURAÇÃO
# ============================================

UPLOAD_FOLDER = 'static/uploads/produtos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Criar pasta se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================
# LISTA DE PRODUTOS (VITRINA)
# ============================================

@vitrina.route('/vitrina')
def vitrina_lista():
    conn = get_db()
    cur = conn.cursor()
    is_postgres = hasattr(cur, 'mogrify')
    
    try:
        if is_postgres:
            cur.execute("""
                SELECT p.*, u.nome AS vendedor_nome, u.foto AS vendedor_foto
                FROM produtos p
                JOIN users u ON p.usuario_id = u.id
                WHERE p.status = 'ativo'
                ORDER BY p.data_criacao DESC
            """)
        else:
            cur.execute("""
                SELECT p.*, u.nome AS vendedor_nome, u.foto AS vendedor_foto
                FROM produtos p
                JOIN users u ON p.usuario_id = u.id
                WHERE p.status = 'ativo'
                ORDER BY p.data_criacao DESC
            """)
        
        produtos = cur.fetchall()
        cur.close()
        conn.close()
        
        return render_template('vitrina.html', produtos=produtos)
    except Exception as e:
        print(f"❌ Erro na vitrina: {e}")
        flash("Erro ao carregar produtos.", "danger")
        return render_template('vitrina.html', produtos=[])


# ============================================
# PUBLICAR PRODUTO
# ============================================

@vitrina.route('/vitrina/novo', methods=['GET', 'POST'])
def vitrina_novo():
    if 'user_id' not in session:
        flash("Faça login para publicar.", "warning")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descricao = request.form.get('descricao', '').strip()
        preco = request.form.get('preco', '0').replace(',', '.')
        categoria = request.form.get('categoria', '')
        localizacao = request.form.get('localizacao', '').strip()

        if not titulo or not descricao or not preco or not categoria:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template('vitrina_novo.html')

        # Processar fotos
        fotos = []
        for i in range(1, 5):
            foto = request.files.get(f'foto{i}')
            if foto and foto.filename and allowed_file(foto.filename):
                filename = secure_filename(foto.filename)
                # Nome único para evitar conflitos
                import time
                nome_unico = f"{int(time.time())}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, nome_unico)
                foto.save(filepath)
                fotos.append(f"/{filepath}")

        # Guardar no banco
        conn = get_db()
        cur = conn.cursor()
        is_postgres = hasattr(cur, 'mogrify')
        
        try:
            if is_postgres:
                cur.execute("""
                    INSERT INTO produtos (titulo, descricao, preco, categoria, localizacao, fotos, usuario_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (titulo, descricao, float(preco), categoria, localizacao, fotos, session['user_id']))
            else:
                cur.execute("""
                    INSERT INTO produtos (titulo, descricao, preco, categoria, localizacao, fotos, usuario_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (titulo, descricao, float(preco), categoria, localizacao, json.dumps(fotos), session['user_id']))
            
            conn.commit()
            cur.close()
            conn.close()

            flash("Produto publicado com sucesso!", "success")
            return redirect(url_for('vitrina.vitrina_lista'))
        except Exception as e:
            print(f"❌ Erro ao publicar: {e}")
            flash("Erro ao publicar produto.", "danger")
            return render_template('vitrina_novo.html')

    return render_template('vitrina_novo.html')


# ============================================
# DETALHES DO PRODUTO
# ============================================

@vitrina.route('/vitrina/<int:produto_id>')
def vitrina_detalhe(produto_id):
    conn = get_db()
    cur = conn.cursor()
    is_postgres = hasattr(cur, 'mogrify')
    
    try:
        if is_postgres:
            cur.execute("""
                SELECT p.*, u.nome AS vendedor_nome, u.foto AS vendedor_foto, u.email, u.telefone
                FROM produtos p
                JOIN users u ON p.usuario_id = u.id
                WHERE p.id = %s
            """, (produto_id,))
        else:
            cur.execute("""
                SELECT p.*, u.nome AS vendedor_nome, u.foto AS vendedor_foto, u.email, u.telefone
                FROM produtos p
                JOIN users u ON p.usuario_id = u.id
                WHERE p.id = ?
            """, (produto_id,))
        
        produto = cur.fetchone()
        cur.close()
        conn.close()

        if not produto:
            flash("Produto não encontrado.", "danger")
            return redirect(url_for('vitrina.vitrina_lista'))

        # Converter fotos para lista (se for string)
        if is_postgres:
            fotos = produto['fotos'] if produto['fotos'] else []
        else:
            fotos = json.loads(produto[7]) if produto[7] else []

        return render_template('vitrina_detalhe.html', produto=produto, fotos=fotos)
    except Exception as e:
        print(f"❌ Erro no detalhe: {e}")
        flash("Erro ao carregar produto.", "danger")
        return redirect(url_for('vitrina.vitrina_lista'))


# ============================================
# APAGAR PRODUTO
# ============================================

@vitrina.route('/vitrina/apagar/<int:produto_id>', methods=['POST'])
def vitrina_apagar(produto_id):
    if 'user_id' not in session:
        flash("Faça login.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor()
    is_postgres = hasattr(cur, 'mogrify')
    
    try:
        if is_postgres:
            cur.execute("DELETE FROM produtos WHERE id = %s AND usuario_id = %s", (produto_id, session['user_id']))
        else:
            cur.execute("DELETE FROM produtos WHERE id = ? AND usuario_id = ?", (produto_id, session['user_id']))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash("Produto apagado com sucesso!", "success")
    except Exception as e:
        print(f"❌ Erro ao apagar: {e}")
        flash("Erro ao apagar produto.", "danger")
    
    return redirect(url_for('vitrina.vitrina_lista'))