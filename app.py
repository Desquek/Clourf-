from flask import Flask, render_template

app = Flask(__name__)
app.config["DEBUG"] = True  # 👈 adiciona isso

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")