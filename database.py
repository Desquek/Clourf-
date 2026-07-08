import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql

# ============================================
# CONFIGURAÇÃO DA BASE DE DADOS
# ============================================

def get_db():
    """Retorna uma conexão com a base de dados Neon (PostgreSQL)"""
    try:
        # Obter a URL da variável de ambiente
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL não configurada! Adicione a variável no Render.")
        
        # Criar a conexão
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao Neon: {e}")
        return None

def init_db():
    """Cria as tabelas se não existirem"""
    conn = get_db()
    if conn is None:
        print("❌ Não foi possível conectar à base de dados para criar tabelas.")
        return
    
    cur = conn.cursor()
    
    try:
        # ===== TABELA DE USUÁRIOS =====
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                telefone TEXT,
                senha_hash TEXT NOT NULL,
                localizacao TEXT,
                bio TEXT,
                foto TEXT DEFAULT 'default.png',
                is_admin BOOLEAN DEFAULT FALSE,
                data_registo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ===== TABELA DE PROBLEMAS =====
        cur.execute("""
            CREATE TABLE IF NOT EXISTS problemas (
                id SERIAL PRIMARY KEY,
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                categoria TEXT NOT NULL,
                localizacao TEXT,
                usuario_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ===== TABELA DE MENSAGENS =====
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mensagens (
                id SERIAL PRIMARY KEY,
                remetente_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                destinatario_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                problema_id INTEGER REFERENCES problemas(id) ON DELETE CASCADE,
                conteudo TEXT NOT NULL,
                lida BOOLEAN DEFAULT FALSE,
                data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ===== TABELA DE FAVORITOS =====
        cur.execute("""
            CREATE TABLE IF NOT EXISTS favoritos (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                problema_id INTEGER REFERENCES problemas(id) ON DELETE CASCADE,
                data_favorito TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(usuario_id, problema_id)
            )
        """)
        
        # ===== TABELA DE INTERESSADOS =====
        cur.execute("""
            CREATE TABLE IF NOT EXISTS interessados (
                id SERIAL PRIMARY KEY,
                problema_id INTEGER REFERENCES problemas(id) ON DELETE CASCADE,
                usuario_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                mensagem TEXT,
                status TEXT DEFAULT 'pendente',
                data_interesse TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("✅ Tabelas criadas/verificadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

# ============================================
# INICIALIZAR A BASE DE DADOS
# ============================================

# Se este ficheiro for executado diretamente, cria as tabelas
if __name__ == '__main__':
    print("🚀 A criar tabelas...")
    init_db()
    print("✅ Concluído!")