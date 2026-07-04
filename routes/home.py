from flask import Blueprint, render_template, session, redirect, url_for
from database import get_db

home = Blueprint("home", __name__)

# ==========================
# PÁGINA INICIAL
# ==========================

@home.route("/")
def home():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            posts.*,
            users.nome,
            users.username,
            users.foto
        FROM posts
        JOIN users
        ON posts.user_id = users.id
        ORDER BY criado_em DESC
    """)

    posts = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "home.html",
        posts=posts
    )


# ==========================
# INÍCIO (UTILIZADOR LOGADO)
# ==========================

@home.route("/inicio")
def inicio():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            posts.*,
            users.nome,
            users.username,
            users.foto
        FROM posts
        JOIN users
        ON posts.user_id = users.id
        ORDER BY criado_em DESC
    """)

    posts = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "inicio.html",
        posts=posts
    )