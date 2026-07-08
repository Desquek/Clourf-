import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db():
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL não configurada!")
        return psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return None

def init_db():
    """Cria as tabelas se elas não existirem."""
    conn = get_db()
    if conn is None:
        print("❌ Falha ao conectar.")
        return

    cur = conn.cursor()
    try:
        # Tabela users
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
        # Tabela problemas
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
        # Tabela mensagens
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
        # Tabela favoritos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS favoritos (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                problema_id INTEGER REFERENCES problemas(id) ON DELETE CASCADE,
                data_favorito TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(usuario_id, problema_id)
            )
        """)
        # Tabela interessados
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
        print("✅ Tabelas verificadas/criadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

# ============================================
# INICIALIZAR AUTOMATICAMENTE
# ============================================
print("🚀 A verificar/criar tabelas...")
init_db()