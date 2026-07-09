from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db

messages = Blueprint('messages', __name__)

# ============================================
# LISTAR CONVERSAS DO UTILIZADOR
# ============================================

@messages.route('/mensagens')
def mensagens():
    if 'user_id' not in session:
        flash("Faça login para aceder às mensagens.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor()

    # Buscar todas as conversas do utilizador
    cur.execute("""
        SELECT DISTINCT
            CASE 
                WHEN remetente_id = %s THEN destinatario_id 
                ELSE remetente_id 
            END AS outro_id,
            u.nome AS outro_nome,
            u.foto AS outro_foto,
            (
                SELECT conteudo 
                FROM mensagens 
                WHERE (remetente_id = %s AND destinatario_id = u.id) 
                   OR (remetente_id = u.id AND destinatario_id = %s)
                ORDER BY data_envio DESC 
                LIMIT 1
            ) AS ultima_mensagem,
            (
                SELECT data_envio 
                FROM mensagens 
                WHERE (remetente_id = %s AND destinatario_id = u.id) 
                   OR (remetente_id = u.id AND destinatario_id = %s)
                ORDER BY data_envio DESC 
                LIMIT 1
            ) AS ultima_data
        FROM mensagens m
        JOIN users u ON u.id = (
            CASE 
                WHEN remetente_id = %s THEN destinatario_id 
                ELSE remetente_id 
            END
        )
        WHERE remetente_id = %s OR destinatario_id = %s
        GROUP BY outro_id
        ORDER BY ultima_data DESC
    """, (
        session['user_id'],  # para CASE
        session['user_id'], session['user_id'],  # para subqueries
        session['user_id'], session['user_id'],  # para subqueries data
        session['user_id'],  # para CASE no JOIN
        session['user_id'], session['user_id']   # para WHERE
    ))

    conversas = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('mensagens.html', conversas=conversas)


# ============================================
# VER CONVERSA COM UM UTILIZADOR
# ============================================

@messages.route('/mensagens/<int:outro_id>')
def conversa(outro_id):
    if 'user_id' not in session:
        flash("Faça login para ver a conversa.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor()

    # Buscar dados do outro utilizador
    cur.execute("""
        SELECT id, nome, foto, localizacao
        FROM users
        WHERE id = %s
    """, (outro_id,))
    outro = cur.fetchone()

    if not outro:
        flash("Utilizador não encontrado.", "danger")
        return redirect(url_for('messages.mensagens'))

    # Buscar mensagens entre os dois
    cur.execute("""
        SELECT 
            m.*,
            u.nome AS remetente_nome,
            u.foto AS remetente_foto
        FROM mensagens m
        JOIN users u ON u.id = m.remetente_id
        WHERE (remetente_id = %s AND destinatario_id = %s)
           OR (remetente_id = %s AND destinatario_id = %s)
        ORDER BY data_envio ASC
    """, (session['user_id'], outro_id, outro_id, session['user_id']))

    mensagens = cur.fetchall()

    # Marcar mensagens como lidas
    cur.execute("""
        UPDATE mensagens
        SET lida = 1
        WHERE remetente_id = %s AND destinatario_id = %s
    """, (outro_id, session['user_id']))
    conn.commit()

    cur.close()
    conn.close()

    return render_template('conversa.html', outro=outro, mensagens=mensagens)


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
# INICIAR CONVERSA A PARTIR DE UM PROBLEMA
# ============================================
{% extends "base.html" %}

{% block title %}{{ problema.titulo }} - Clourf{% endblock %}

{% block content %}
<div class="problema-detalhes">
    <div class="problema-card">
        <div class="problema-header">
            <div class="autor-info">
                <img src="{{ url_for('static', filename='uploads/perfil/' + problema.autor_foto) if problema.autor_foto else url_for('static', filename='img/default.png') }}" 
                     alt="{{ problema.autor_nome }}" class="avatar">
                <div>
                    <a href="{{ url_for('profile.perfil_publico', user_id=problema.autor_id) }}" class="autor-nome">
                        {{ problema.autor_nome }}
                    </a>
                    <span class="autor-localizacao">{{ problema.localizacao or '' }}</span>
                </div>
            </div>
            <span class="categoria-badge">{{ problema.categoria }}</span>
        </div>

        <h1>{{ problema.titulo }}</h1>

        <div class="problema-descricao">
            <p>{{ problema.descricao }}</p>
        </div>

        <div class="problema-footer">
            <span><i class="fas fa-map-marker-alt"></i> {{ problema.localizacao or 'Local não definido' }}</span>
            <span><i class="fas fa-clock"></i> {{ problema.data_criacao.strftime('%d/%m/%Y às %H:%M') }}</span>
        </div>

        <!-- ===== BOTÃO ENVIAR PROPOSTA ===== -->
        {% if session.user_id and session.user_id != problema.autor_id %}
            <div class="problema-actions" style="margin-top: 2rem;">
                {% if ja_proposto %}
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle"></i> Já enviou uma proposta para este problema. Aguarde resposta do autor.
                    </div>
                {% else %}
                    <button onclick="abrirModalProposta()" class="btn-primary">
                        <i class="fas fa-paper-plane"></i> Enviar Proposta
                    </button>
                    <a href="{{ url_for('messages.conversa', outro_id=problema.autor_id) }}" class="btn-secondary">
                        <i class="fas fa-comment"></i> Mensagem
                    </a>
                {% endif %}
            </div>
        {% endif %}

        <!-- ===== SE FOR O AUTOR ===== -->
        {% if session.user_id == problema.autor_id %}
            <div class="problema-actions" style="margin-top: 2rem;">
                <a href="{{ url_for('posts.editar_problema', problema_id=problema.id) }}" class="btn-primary">
                    <i class="fas fa-edit"></i> Editar
                </a>
                <form method="POST" action="{{ url_for('posts.apagar_problema', problema_id=problema.id) }}" style="display: inline;">
                    <button type="submit" class="btn-danger" onclick="return confirm('Tem certeza?')">
                        <i class="fas fa-trash"></i> Apagar
                    </button>
                </form>
                <a href="{{ url_for('messages.conversa', outro_id=problema.autor_id) }}" class="btn-secondary">
                    <i class="fas fa-comment"></i> Ver mensagens
                </a>
            </div>
        {% endif %}

        <!-- ===== MENSAGEM PARA QUEM NÃO ESTÁ LOGADO ===== -->
        {% if not session.user_id %}
            <div class="problema-actions" style="margin-top: 2rem; text-align: center; color: var(--cinza-claro);">
                <p><i class="fas fa-lock"></i> Faça <a href="{{ url_for('auth.login') }}" style="color: var(--azul-muito-claro);">login</a> para enviar uma proposta.</p>
            </div>
        {% endif %}
    </div>
</div>

<!-- ===== MODAL DE ENVIAR PROPOSTA ===== -->
<div class="modal" id="modalProposta" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 2000; justify-content: center; align-items: center;">
    <div class="modal-content" style="background: var(--azul-medio); padding: 2rem; border-radius: var(--radius); max-width: 500px; width: 90%;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h2 style="color: var(--branco);"><i class="fas fa-paper-plane"></i> Enviar Proposta</h2>
            <button onclick="fecharModalProposta()" style="background: none; border: none; color: var(--branco); font-size: 1.5rem; cursor: pointer;">&times;</button>
        </div>
        <p style="color: var(--cinza-claro); margin-bottom: 1rem;">Descreva como pode ajudar a resolver o problema "{{ problema.titulo }}".</p>
        <form method="POST" action="{{ url_for('messages.enviar_proposta', problema_id=problema.id) }}">
            <div class="form-group">
                <textarea name="conteudo" rows="4" placeholder="Descreva a sua proposta..." required style="width: 100%; padding: 0.8rem; border-radius: var(--radius-sm); border: 1px solid var(--cinza-escuro); background: var(--azul-escuro); color: var(--branco);"></textarea>
            </div>
            <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                <button type="submit" class="btn-primary"><i class="fas fa-paper-plane"></i> Enviar</button>
                <button type="button" onclick="fecharModalProposta()" class="btn-secondary">Cancelar</button>
            </div>
        </form>
    </div>
</div>

<script>
function abrirModalProposta() {
    document.getElementById('modalProposta').style.display = 'flex';
}

function fecharModalProposta() {
    document.getElementById('modalProposta').style.display = 'none';
}

// Fechar modal ao clicar fora
document.getElementById('modalProposta').addEventListener('click', function(e) {
    if (e.target === this) {
        fecharModalProposta();
    }
});
</script>
{% endblock %}


@messages.route('/contactar-autor/<int:problema_id>')
def contactar_autor(problema_id):
    if 'user_id' not in session:
        flash("Faça login para contactar o autor.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor()

    # Buscar o autor do problema
    cur.execute("""
        SELECT usuario_id FROM problemas
        WHERE id = %s
    """, (problema_id,))
    problema = cur.fetchone()
    cur.close()
    conn.close()

    if not problema:
        flash("Problema não encontrado.", "danger")
        return redirect(url_for('home.inicio'))

    autor_id = problema['usuario_id']

    if autor_id == session['user_id']:
        flash("Não pode enviar mensagem para si mesmo.", "warning")
        return redirect(url_for('posts.ver_problema', problema_id=problema_id))

    return redirect(url_for('messages.conversa', outro_id=autor_id))

