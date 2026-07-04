from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from database import get_db

search = Blueprint('search', __name__)

# ============================================
# PÁGINA DE PESQUISA
# ============================================

@search.route('/pesquisar')
def pesquisar():
    if 'user_id' not in session:
        flash("Faça login para pesquisar.", "warning")
        return redirect(url_for('auth.login'))

    query = request.args.get('q', '').strip()
    categoria = request.args.get('categoria', '')
    localizacao = request.args.get('localizacao', '')

    if not query and not categoria and not localizacao:
        return render_template('pesquisa.html', problemas=[], query='')

    conn = get_db()
    cur = conn.cursor()

    # Construir a consulta SQL dinâmica
    sql = """
        SELECT
            p.*,
            u.nome AS autor_nome,
            u.foto AS autor_foto
        FROM problemas p
        JOIN users u ON p.usuario_id = u.id
        WHERE 1=1
    """
    params = []

    if query:
        sql += " AND (p.titulo ILIKE %s OR p.descricao ILIKE %s)"
        params.append(f"%{query}%")
        params.append(f"%{query}%")

    if categoria:
        sql += " AND p.categoria = %s"
        params.append(categoria)

    if localizacao:
        sql += " AND p.localizacao ILIKE %s"
        params.append(f"%{localizacao}%")

    sql += " ORDER BY p.data_criacao DESC"

    cur.execute(sql, tuple(params))
    resultados = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        'pesquisa.html',
        problemas=resultados,
        query=query,
        categoria=categoria,
        localizacao=localizacao
    )


# ============================================
# PESQUISA RÁPIDA (AJAX)
# ============================================

@search.route('/pesquisa-rapida')
def pesquisa_rapida():
    if 'user_id' not in session:
        return {"erro": "Não autenticado"}, 401

    query = request.args.get('q', '').strip()

    if not query or len(query) < 2:
        return {"resultados": []}

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.id,
            p.titulo,
            p.categoria,
            p.localizacao,
            u.nome AS autor_nome
        FROM problemas p
        JOIN users u ON p.usuario_id = u.id
        WHERE p.titulo ILIKE %s
           OR p.descricao ILIKE %s
        ORDER BY p.data_criacao DESC
        LIMIT 5
    """, (f"%{query}%", f"%{query}%"))

    resultados = cur.fetchall()
    cur.close()
    conn.close()

    return {
        "resultados": [
            {
                "id": r["id"],
                "titulo": r["titulo"],
                "categoria": r["categoria"],
                "localizacao": r["localizacao"],
                "autor": r["autor_nome"]
            }
            for r in resultados
        ]
    }