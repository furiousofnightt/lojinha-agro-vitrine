from app import DB_PATH, init_db as app_init_db
from werkzeug.security import generate_password_hash
import sqlite3

# Esse script:
# Garante que todas as tabelas e colunas existam.
# Não deleta nenhum dado.
# Só cria o admin se ainda não houver um. 

def init_db():
    """
    Inicializa as tabelas do banco sem apagar dados existentes.
    Cria a coluna 'banned' na tabela 'usuarios' se ainda não existir.
    """
    # Inicializa as demais tabelas do app
    app_init_db()

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Cria tabela usuarios caso não exista
        c.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                security_question TEXT NOT NULL,
                security_answer TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                banned BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()

        # Garante que a coluna 'banned' exista
        try:
            c.execute("ALTER TABLE usuarios ADD COLUMN banned BOOLEAN DEFAULT 0")
            print("Coluna 'banned' adicionada à tabela 'usuarios'.")
        except sqlite3.OperationalError:
            # Coluna já existe
            pass


def create_admin():
    """
    Cria usuário admin se ainda não existir.
    """
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Verifica se já existe um admin
        c.execute("SELECT id FROM usuarios WHERE is_admin = 1 LIMIT 1")
        admin_exists = c.fetchone()

        if admin_exists:
            print("Usuário admin já existe. Nenhuma modificação feita.")
        else:
            c.execute('''
                INSERT INTO usuarios (username, email, phone, password, security_question, security_answer, is_admin, banned)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            ''', (
                'seu-usuario',
                'seu-email@gmail.com',
                'seu-telefone',
                generate_password_hash('sua-senha'),
                '1',  # Pergunta secreta
                'sua-resposta-secreta',
                True
            ))
            conn.commit()
            print("Usuário admin criado com sucesso!")


def main():
    try:
        # Inicializa o banco de dados
        init_db()
        print("Estrutura do banco de dados criada/verificada com sucesso!")

        # Cria admin se não existir
        create_admin()

        print("\nTudo pronto! Você pode iniciar o servidor com 'python app.py'")
        print("Credenciais do admin padrão (caso tenha sido criado agora):")
        print("Email: admin@exemplo.com")
        print("Senha: mudar-essa-senha-123")

    except Exception as e:
        print(f"Erro durante a inicialização: {str(e)}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
