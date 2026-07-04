from flask import Blueprint, render_template, session, redirect, url_for, flash
from database import get_db

notifications = Blueprint('notifications', __name__)

# ============================================
# LISTAR NOTIFICAÇÕES
# ============================================

@notifications.route('/notificacoes')
def notificacoes():
    if 'user_id' not in session:
        flash("Faça login para ver as notificações.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor()

    # Buscar notificações (mensagens não lidas e interesses pendentes)
    cur.execute("""
        SELECT 
            'mensagem' AS tipo,
            m.conteudo AS descricao,
            u.nome AS de,
            m.data_envio AS data,
            m.id AS id
        FROM mensagens m
        JOIN users u ON u.id = m.remetente_id
        WHERE m.destinatario_id = %s AND m.lida = 0
        ORDER BY m.data_envio DESC
        LIMIT 10
    """, (session['user_id'],))
    mensagens_nao_lidas = cur.fetchall()

    cur.execute("""
        SELECT 
            'interesse' AS tipo,
            i.mensagem AS descricao,
            u.nome AS de,
            i.data_interesse AS data,
            p.titulo AS problema_titulo,
            p.id AS problema_id
        FROM interessados i
        JOIN users u ON u.id = i.usuario_id
        JOIN problemas p ON p.id = i.problema_id
        WHERE p.usuario_id = %s AND i.status = 'pendente'
        ORDER BY i.data_interesse DESC
        LIMIT 10
    """, (session['user_id'],))
    interesses_pendentes = cur.fetchall()

    cur.close()
    conn.close()

    # Combinar e ordenar por data
    notificacoes = list(mensagens_nao_lidas) + list(interesses_pendentes)
    notificacoes.sort(key=lambda x: x['data'], reverse=True)

    return render_template('notificacoes.html', notificacoes=notificacoes)


# ============================================
# MARCAR NOTIFICAÇÃO COMO LIDA
# ============================================

@notifications.route('/notificacao/lida/<int:notificacao_id>/<string:tipo>')
def marcar_lida(notificacao_id, tipo):
    if 'user_id' not in session:
        flash("Faça login.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor()

    if tipo == 'mensagem':
        cur.execute("""
            UPDATE mensagens
            SET lida = 1
            WHERE id = %s AND destinatario_id = %s
        """, (notificacao_id, session['user_id']))
    elif tipo == 'interesse':
        cur.execute("""
            UPDATE interessados
            SET status = 'visto'
            WHERE id = %s
        """, (notificacao_id,))
    else:
        flash("Tipo de notificação inválido.", "danger")
        cur.close()
        conn.close()
        return redirect(url_for('notifications.notificacoes'))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('notifications.notificacoes'))