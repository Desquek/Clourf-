from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db

auth = Blueprint("auth", __name__)

# ==========================
# REGISTAR
# ==========================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        nome = request.form["nome"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM users WHERE email=%s",
            (email,)
        )

        existe = cur.fetchone()

        if existe:
            flash("Este email já existe.")
            cur.close()
            conn.close()
            return redirect(url_for("auth.register"))

        senha = generate_password_hash(password)

        cur.execute("""
        INSERT INTO users
        (nome,username,email,password)
        VALUES(%s,%s,%s,%s)
        """,
        (
            nome,
            username,
            email,
            senha
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash("Conta criada com sucesso!")

        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ==========================
# LOGIN
# ==========================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        cur = conn.cursor()

        cur.execute("""
        SELECT *
        FROM users
        WHERE email=%s
        """,(email,))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user:

            flash("Email não encontrado.")
            return redirect(url_for("auth.login"))

        if not check_password_hash(
            user["password"],
            password
        ):

            flash("Senha incorreta.")
            return redirect(url_for("auth.login"))

        session["user_id"] = str(user["id"])
        session["nome"] = user["nome"]

        flash("Bem-vindo!")

        return redirect(url_for("home.home"))

    return render_template("login.html")


# ==========================
# LOGOUT
# ==========================

@auth.route("/logout")
def logout():

    session.clear()

    flash("Sessão terminada.")

    return redirect(url_for("auth.login"))