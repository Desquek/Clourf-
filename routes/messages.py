from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db

messages = Blueprint('messages', __name__)

# ============================================
# CONTAR MENSAGENS NÃO LIDAS
# ============================================

def contar_nao_lidas(usuario_id):
    """Retorna o número de mensagens não lidas do utilizador"""
    conn = get_db()
    if conn is None:
        return 0
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM mensagens WHERE destinatario_id = %s AND lida = FALSE", (usuario_id,))
    count = cur.fetchone()['count']
    cur.close()
    conn.close()
    return count


# ============================================
# LISTAR CONVERSAS
# ============================================

@messages.route('/mensagens')
def mensagens():
    if 'user_id' not in session:
        flash("Faça login para aceder às mensagens.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    if conn is None:
        flash("Erro ao conectar à base de dados!", "danger")
        return render_template('mensagens.html', conversas=[])

    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT DISTINCT 
                CASE 
                    WHEN remetente_id = %s THEN destinatario_id 
                    ELSE remetente_id 
                END AS outro_id
            FROM mensagens 
            WHERE remetente_id = %s OR destinatario_id = %s
        """, (session['user_id'], session['user_id'], session['user_id']))
        
        ids = cur.fetchall()
        conversas = []
        
        for row in ids:
            outro_id = row['outro_id']
            
            cur.execute("SELECT id, nome, foto FROM users WHERE id = %s", (outro_id,))
            user = cur.fetchone()
            
            if user:
                cur.execute("""
                    SELECT conteudo, data_envio 
                    FROM mensagens 
                    WHERE (remetente_id = %s AND destinatario_id = %s) 
                       OR (remetente_id = %s AND destinatario_id = %s)
                    ORDER BY data_envio DESC 
                    LIMIT 1
                """, (session['user_id'], outro_id, outro_id, session['user_id']))
                ultima = cur.fetchone()
                
                conversas.append({
                    'outro_id': user['id'],
                    'outro_nome': user['nome'],
                    'outro_foto': user['foto'],
                    'ultima_mensagem': ultima['conteudo'] if ultima else 'Nenhuma mensagem',
                    'ultima_data': ultima['data_envio'] if ultima else None
                })
        
        cur.close()
        conn.close()
        
        return render_template('mensagens.html', conversas=conversas)
        
    except Exception as e:
        print(f"❌ Erro ao carregar mensagens: {e}")
        flash("Erro ao carregar mensagens.", "danger")
        return render_template('mensagens.html', conversas=[])


# ============================================
# VER CONVERSA
# ============================================

@messages.route('/mensagens/<int:outro_id>')
def conversa(outro_id):
    if 'user_id' not in session:
        flash("Faça login para ver a conversa.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    if conn is None:
        flash("Erro ao conectar à base de dados!", "danger")
        return redirect(url_for('messages.mensagens'))

    cur = conn.cursor()
    
    cur.execute("SELECT id, nome, foto, localizacao FROM users WHERE id = %s", (outro_id,))
    outro = cur.fetchone()

    if not outro:
        flash("Utilizador não encontrado.", "danger")
        return redirect(url_for('messages.mensagens'))

    cur.execute("""
        SELECT m.*, u.nome AS remetente_nome, u.foto AS remetente_foto
        FROM mensagens m
        JOIN users u ON u.id = m.remetente_id
        WHERE (remetente_id = %s AND destinatario_id = %s)
           OR (remetente_id = %s AND destinatario_id = %s)
        ORDER BY data_envio ASC
    """, (session['user_id'], outro_id, outro_id, session['user_id']))

    mensagens_lista = cur.fetchall()
    
    # Marcar mensagens como lidas
    cur.execute("UPDATE mensagens SET lida = TRUE WHERE remetente_id = %s AND destinatario_id = %s", 
                (outro_id, session['user_id']))
    conn.commit()
    cur.close()
    conn.close()

    return render_template('conversa.html', outro=outro, mensagens=mensagens_lista)


# ============================================
# ENVIAR MENSAGEM
# ============================================

@messages.route('/enviar-mensagem', methods=['POST'])
def enviar_mensagem():
    if 'user_id' not in session:
        flash("Faça login para enviar mensagens.", "warning")
        return redirect(url_for('auth.login'))

    destinatario_id = request.form['destinatario_id']
    conteudo = request.form['conteudo']
    problema_id = request.form.get('problema_id', None)

    if not conteudo.strip():
        flash("A mensagem não pode estar vazia.", "danger")
        return redirect(url_for('messages.conversa', outro_id=destinatario_id))

    conn = get_db()
    if conn is None:
        flash("Erro ao conectar à base de dados!", "danger")
        return redirect(url_for('messages.mensagens'))

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO mensagens (remetente_id, destinatario_id, problema_id, conteudo)
        VALUES (%s, %s, %s, %s)
    """, (session['user_id'], destinatario_id, problema_id, conteudo))
    conn.commit()
    cur.close()
    conn.close()

    flash("Mensagem enviada!", "success")
    return redirect(url_for('messages.conversa', outro_id=destinatario_id))


# ============================================
# ENVIAR PROPOSTA
# ============================================

@messages.route('/enviar-proposta/<int:problema_id>', methods=['POST'])
def enviar_proposta(problema_id):
    if 'user_id' not in session:
        flash("Faça login para enviar uma proposta.", "warning")
        return redirect(url_for('auth.login'))

    conteudo = request.form.get('conteudo', '').strip()

    if not conteudo:
        flash("A proposta não pode estar vazia.", "danger")
        return redirect(url_for('posts.ver_problema', problema_id=problema_id))

    conn = get_db()
    if conn is None:
        flash("Erro ao conectar à base de dados!", "danger")
        return redirect(url_for('home.inicio'))

    cur = conn.cursor()
    cur.execute("SELECT usuario_id FROM problemas WHERE id = %s", (problema_id,))
    problema = cur.fetchone()
    cur.close()

    if not problema:
        flash("Problema não encontrado.", "danger")
        conn.close()
        return redirect(url_for('home.inicio'))

    autor_id = problema['usuario_id']

    if autor_id == session['user_id']:
        flash("Não pode enviar uma proposta para o seu próprio problema.", "warning")
        conn.close()
        return redirect(url_for('posts.ver_problema', problema_id=problema_id))

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO mensagens (remetente_id, destinatario_id, problema_id, conteudo)
        VALUES (%s, %s, %s, %s)
    """, (session['user_id'], autor_id, problema_id, conteudo))
    conn.commit()
    cur.close()
    conn.close()

    flash("Proposta enviada com sucesso! O autor será notificado.", "success")
    return redirect(url_for('posts.ver_problema', problema_id=problema_id))