from flask import Flask
from config import Config
from database import init_db

# Importar as rotas
from routes.auth import auth
from routes.home import home
from routes.posts import posts
from routes.profile import profile
from routes.messages import messages
from routes.notifications import notifications

app = Flask(__name__)

# Configurações
app.config.from_object(Config)

# Inicializar base de dados
init_db()

# Registar módulos (Blueprints)
app.register_blueprint(auth)
app.register_blueprint(home)
app.register_blueprint(posts)
app.register_blueprint(profile)
app.register_blueprint(messages)
app.register_blueprint(notifications)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)