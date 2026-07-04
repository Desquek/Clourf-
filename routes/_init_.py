 from flask import Blueprint

# Importar todos os blueprints
from .auth import auth
from .home import home
from .profile import profile
from .posts import posts
from .messages import messages
from .favorites import favorites
from .notifications import notifications
from .search import search
from .categorias import categorias_bp

# Importar blueprints do admin
from .admin.dashboard import admin_dashboard
from .admin.usuarios import admin_usuarios
from .admin.problemas import admin_problemas

# Lista de todos os blueprints para registar no app.py
blueprints = [
    auth,
    home,
    profile,
    posts,
    messages,
    favorites,
    notifications,
    search,
    categorias_bp,
    admin_dashboard,
    admin_usuarios,
    admin_problemas
]