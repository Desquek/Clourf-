from flask import Blueprint, render_template, session, redirect, url_for, flash
from database import get_db

home = Blueprint('home', __name__)

# ============================================
# DASHBOARD (APÓS LOGIN)
# ============================================

@home.route('/inicio')
def inicio():
    if 'user_id' not in session:
        flash("Faça login para aceder ao dashboard.", "warning")
        return redirect(url_for('auth.login'))

    conn = get_db()
    if conn is None:
        flash("Erro ao conectar à base de dados!", "danger")
        return render_template('inicio.html', problemas=[])

    cur = conn.cursor()
    is_postgres = hasattr(cur, 'mogrify')
    
    try:
        if is_postgres:
            cur.execute("""
                SELECT p.*, u.nome AS autor_nome, u.foto AS autor_foto
                FROM problemas p
                JOIN users u ON p.usuario_id = u.id
                ORDER BY p.data_criacao DESC
            """)
        else:
            cur.execute("""
                SELECT p.*, u.nome AS autor_nome, u.foto AS autor_foto
                FROM problemas p
                JOIN users u ON p.usuario_id = u.id
                ORDER BY p.data_criacao DESC
            """)
        
        problemas = cur.fetchall()
        cur.close()
        conn.close()
        
        return render_template('inicio.html', problemas=problemas)
    except Exception as e:
        print(f"❌ Erro no inicio: {e}")
        flash("Erro ao carregar problemas.", "danger")
        return render_template('inicio.html', problemas=[])