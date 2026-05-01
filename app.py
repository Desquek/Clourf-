from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import sqlite3
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(base_dir, "templates"))
app.secret_key = "clourf_secret_key"
app.config["UPLOAD_FOLDER"] = os.path.join(base_dir, "uploads")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def init_db():
    conn = sqlite3.connect(os.path.join(base_dir, "database.db"))
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = sqlite3.connect(os.path.join(base_dir, "database.db"))
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            flash("Conta criada com sucesso! Faça login.")
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Erro: {e}")
            flash("Usuário já existe ou erro no banco")
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(os.path.join(base_dir, "database.db"))
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            flash("Login realizado com sucesso!")
            return redirect(url_for('dashboard'))
        else:
            flash("Login inválido")
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(os.path.join(base_dir, "database.db"))
    c = conn.cursor()
    c.execute("SELECT content FROM notes WHERE user_id = ? ORDER BY id DESC", (session['user_id'],))
    notes = c.fetchall()
    
    c.execute("SELECT filename FROM files WHERE user_id = ? ORDER BY id DESC", (session['user_id'],))
    files = c.fetchall()
    conn.close()
    
    return render_template('dashboard.html', notes=notes, files=files)

@app.route('/add_note', methods=['POST'])
def add_note():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    note_content = request.form.get('note')
    if note_content:
        conn = sqlite3.connect(os.path.join(base_dir, "database.db"))
        c = conn.cursor()
        c.execute("INSERT INTO notes (content, user_id) VALUES (?, ?)", (note_content, session['user_id']))
        conn.commit()
        conn.close()
        flash("Nota adicionada")
    else:
        flash("Conteúdo vazio")
    
    return redirect(url_for('dashboard'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if 'file' not in request.files:
        flash("Nenhum arquivo selecionado")
        return redirect(url_for('dashboard'))

    file = request.files['file']
    if file.filename == '':
        flash("Nenhum arquivo selecionado")
        return redirect(url_for('dashboard'))

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = sqlite3.connect(os.path.join(base_dir, "database.db"))
        c = conn.cursor()
        c.execute("INSERT INTO files (filename, user_id) VALUES (?, ?)", (filename, session['user_id']))
        conn.commit()
        conn.close()

        flash("Arquivo enviado com sucesso")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logout realizado")
    return redirect(url_for('index'))

@app.route('/reset_db')
def reset_db():
    try:
        db_path = os.path.join(base_dir, "database.db")
        if os.path.exists(db_path):
            os.remove(db_path)
        init_db()
        return "Banco de dados resetado com sucesso! <a href='/'>Voltar ao início</a>"
    except Exception as e:
        return f"Erro ao resetar: {e}"

with app.app_context():
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)