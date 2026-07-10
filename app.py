from flask import Flask, render_template
from config import Config
import os
import database

app = Flask(__name__)
app.config.from_object(Config)

# ============================================
# VERIFICAR E FORÇAR A SECRET_KEY
# ============================================

if not app.config.get('SECRET_KEY'):
    print("⚠️ SECRET_KEY não encontrada! Usando valor temporário.")
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clourf_secret_2026')
else:
    print("✅ SECRET_KEY carregada com sucesso!")

# ============================================
# REGISTAR TODOS OS BLUEPRINTS
# ============================================

from routes.auth import auth
from routes.home import home
from routes.profile import profile
from routes.posts import posts
from routes.messages import messages
from routes.favorites import favorites
from routes.notifications import notifications
from routes.search import search
from routes.categorias import categorias_bp
from routes.admin.dashboard import admin_dashboard
from routes.admin.usuarios import admin_usuarios
from routes.admin.problemas import admin_problemas

app.register_blueprint(auth)
app.register_blueprint(home)
app.register_blueprint(profile)
app.register_blueprint(posts)
app.register_blueprint(messages)
app.register_blueprint(favorites)
app.register_blueprint(notifications)
app.register_blueprint(search)
app.register_blueprint(categorias_bp)
app.register_blueprint(admin_dashboard)
app.register_blueprint(admin_usuarios)
app.register_blueprint(admin_problemas)

# ============================================
# CONTEXT PROCESSOR (COM TRATAMENTO DE ERRO)
# ============================================

@app.context_processor
def inject_user():
    from flask import session
    
    user_id = session.get('user_id')
    notificacoes = 0
    
    if user_id:
        try:
            from routes.messages import contar_nao_lidas
            notificacoes = contar_nao_lidas(user_id)
        except Exception as e:
            print(f"⚠️ Erro ao contar mensagens não lidas: {e}")
            notificacoes = 0
    
    return dict(
        user_id=user_id,
        user_nome=session.get('nome', 'Visitante'),
        notificacoes_nao_lidas=notificacoes
    )

# ============================================
# ERROS PERSONALIZADOS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# ============================================
# INICIAR SERVIDOR
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))