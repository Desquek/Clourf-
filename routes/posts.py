from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db

posts = Blueprint('posts', __name__)

# ============================================
# VER UM PROBLEMA ESPECÍFICO
# ============================================

@posts.route('/problema/<int:problema_id>')
def ver_problema(problema_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.*,
            u.id AS autor_id,
            u.nome AS autor_nome,
            u.foto AS autor_foto,
            u.localizacao AS autor_localizacao,
            u.bio AS autor_bio
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

    return render_template('problema.html', problema=problema)


# ============================================
# PUBLICAR NOVO PROBLEMA
# ============================================

@posts.route('/novo-problema', methods=['GET', 'POST'])
def novo_problema():
    if 'user_id' not in session:
        flash("Faça login para publicar um problema.", "warning")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        categoria = request.form['categoria']
        localizacao = request.form['localizacao']

        if not titulo or not descricao or not categoria:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template('novo_problema.html')

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
# EDITAR PROBLEMA
# ============================================

@posts.route('/editar-problema/<int:problema_id>', methods=['GET', 'POST'])
def editar_problema(problema_id):
    if 'user_id' not in session:
        flash("Faça login para editar.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor()

    # Verificar se o problema existe e pertence ao utilizador
    cur.execute("""
        SELECT * FROM problemas
        WHERE id = %s AND usuario_id = %s
    """, (problema_id, session['user_id']))
    problema = cur.fetchone()
    cur.close()

    if not problema:
        flash("Problema não encontrado ou não tem permissão para editar.", "danger")
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

        flash("Problema atualizado com sucesso!", "success")
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

    cur.execute("""
        DELETE FROM problemas
        WHERE id = %s AND usuario_id = %s
    """, (problema_id, session['user_id']))

    if cur.rowcount == 0:
        flash("Problema não encontrado ou não tem permissão para apagar.", "danger")
    else:
        conn.commit()
        flash("Problema apagado com sucesso!", "success")

    cur.close()
    conn.close()
    return redirect(url_for('home.inicio'))

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