import os
from dotenv import load_dotenv

# Carregar variáveis do ficheiro .env (se existir)
load_dotenv()

class Config:
    # Chave secreta para sessões
    SECRET_KEY = os.environ.get("SECRET_KEY", "uma_chave_secreta_muito_segura_e_unica_para_dev")
    
    # URL da base de dados (Neon PostgreSQL)
    DATABASE_URL = os.environ.get("DATABASE_URL")
    
    # Modo de depuração
    DEBUG = os.environ.get("DEBUG", False)
    
    # Porta do servidor
    PORT = int(os.environ.get("PORT", 5000))