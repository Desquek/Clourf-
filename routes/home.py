from flask import Blueprint, render_template, session, redirect, url_for
from database import get_db

home = Blueprint("home", __name__)

# ==========================
# PÁGINA PÚBLICA (LANDING)
# ==========================

@home.route("/")
def index():
    """Página pública - mostra os problemas mais recentes"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            problemas.*,
            users.nome AS autor_nome,
            users.foto AS autor_foto
        FROM problemas
        JOIN users ON problemas.usuario_id = users.id
        ORDER BY problemas.data_criacao DESC
        LIMIT 10
    """)

    problemas = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("index.html", problemas=problemas)


# ==========================
# DASHBOARD (UTILIZADOR LOGADO)
# ==========================

@home.route("/inicio")
def inicio():
    """Página inicial do utilizador logado"""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            problemas.*,
            users.nome AS autor_nome,
            users.foto AS autor_foto
        FROM problemas
        JOIN users ON problemas.usuario_id = users.id
        ORDER BY problemas.data_criacao DESC
    """)

    problemas = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("inicio.html", problemas=problemas)