from flask import Flask
from config import Config

# Blueprints
from routes.auth import auth
from routes.home import home

app = Flask(__name__)

# Configurações
app.config.from_object(Config)

# Registar Blueprints
app.register_blueprint(auth)
app.register_blueprint(home)

# Iniciar aplicação
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)