from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db

auth = Blueprint("auth", __name__)

# ===========================
# REGISTO
# ===========================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

        conn = get_db()
        c = conn.cursor()

        c.execute(
            "SELECT id FROM users WHERE email=?",
            (email,)
        )

        if c.fetchone():

            flash("Este email já existe.")

            conn.close()

            return redirect(url_for("auth.register"))

        senha_hash = generate_password_hash(senha)

        c.execute(
            """
            INSERT INTO users
            (nome,email,senha)
            VALUES(?,?,?)
            """,
            (
                nome,
                email,
                senha_hash
            )
        )

        conn.commit()

        conn.close()

        flash("Conta criada com sucesso.")

        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ===========================
# LOGIN
# ===========================

@auth.route("/login", methods=["GET","POST"])
def login():

    if request.method=="POST":

        email=request.form["email"]

        senha=request.form["senha"]

        conn=get_db()

        c=conn.cursor()

        c.execute(
            """
            SELECT *
            FROM users
            WHERE email=?
            """,
            (email,)
        )

        user=c.fetchone()

        conn.close()

        if user:

            if check_password_hash(user["senha"],senha):

                session["user_id"]=user["id"]

                session["nome"]=user["nome"]

                return redirect(url_for("home.inicio"))

        flash("Email ou senha inválidos.")

    return render_template("login.html")


# ===========================
# LOGOUT
# ===========================

@auth.route("/logout")
def logout():

    session.clear()

    flash("Sessão terminada.")

    return redirect(url_for("auth.login"))