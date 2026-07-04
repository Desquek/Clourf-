from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from database import get_db

categorias_bp = Blueprint('categorias', __name__)

# ============================================
# LISTAR CATEGORIAS E PROBLEMAS POR CATEGORIA
# ============================================

@categorias_bp.route('/categorias')
def categorias():
    if 'user_id' not in session:
        flash("Faça login para ver as categorias.", "warning")
        return redirect(url_for('auth.login'))

    categoria_filtro = request.args.get('cat', '')

    conn = get_db()
    cur = conn.cursor()

    # Buscar todas as categorias com contagem de problemas
    cur.execute("""
        SELECT 
            categoria,
            COUNT(*) AS total
        FROM problemas
        GROUP BY categoria
        ORDER BY total DESC
    """)
    categorias_lista = cur.fetchall()

    # Buscar problemas da categoria selecionada (ou todos)
    if categoria_filtro:
        cur.execute("""
            SELECT
                p.*,
                u.nome AS autor_nome,
                u.foto AS autor_foto
            FROM problemas p
            JOIN users u ON p.usuario_id = u.id
            WHERE p.categoria = %s
            ORDER BY p.data_criacao DESC
        """, (categoria_filtro,))
    else:
        cur.execute("""
            SELECT
                p.*,
                u.nome AS autor_nome,
                u.foto AS autor_foto
            FROM problemas p
            JOIN users u ON p.usuario_id = u.id
            ORDER BY p.data_criacao DESC
            LIMIT 20
        """)

    problemas = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        'categorias.html',
        categorias=categorias_lista,
        problemas=problemas,
        categoria_selecionada=categoria_filtro
    )