from app import DB_PATH, init_db as app_init_db
from werkzeug.security import generate_password_hash
import sqlite3

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
                is_admin BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()

        # Adiciona coluna 'banned' caso ainda não exista
        try:
            c.execute('ALTER TABLE usuarios ADD COLUMN banned BOOLEAN DEFAULT 0')
            print("Coluna 'banned' adicionada à tabela 'usuarios'.")
        except sqlite3.OperationalError:
            # Coluna já existe
            pass

def main():
    try:
        # Inicializa o banco de dados
        init_db()
        print("Estrutura do banco de dados criada/verificada com sucesso!")

        # Reset completo do banco, removendo todos os dados e reiniciando IDs
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Remove todos os dados das tabelas principais
            c.execute('DELETE FROM produto_midias')
            c.execute('DELETE FROM itens_carrinho')
            c.execute('DELETE FROM carrinhos')
            c.execute('DELETE FROM pedidos')
            c.execute('DELETE FROM produtos')
            c.execute('DELETE FROM categorias')
            c.execute('DELETE FROM usuarios')
            conn.commit()
            # Reinicia os autoincrementos (SQLite)
            c.execute("DELETE FROM sqlite_sequence WHERE name IN ('usuarios', 'categorias', 'produtos')")
            conn.commit()
            # Insere apenas o admin padronizado
            c.execute('''
                INSERT INTO usuarios (username, email, phone, password, security_question, security_answer, is_admin, banned)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            ''', (
                'fury777',
                'seu-email',
                'seu-telefone',
                generate_password_hash('sua-senha'),
                '1',  # Animal de estimação
                'sua-resposta-secreta',
                True
            ))
            conn.commit()
            print("Banco resetado! IDs de categorias e produtos reiniciados. Usuário admin criado.")

        print("\nTudo pronto! Você pode iniciar o servidor com 'python app.py'")
        print("Credenciais do admin:")
        print("Email: seu-email")
        print("Senha: sua-senha")

    except Exception as e:
        print(f"Erro durante a inicialização: {str(e)}")
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
