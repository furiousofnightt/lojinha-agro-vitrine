import os
import sqlite3
from werkzeug.security import generate_password_hash

def create_admin():
    """Cria um usuário admin se não existir"""
    # Usa a pasta `instance/` do projeto para armazenar o banco
    if os.environ.get('PYTHONANYWHERE_DOMAIN'):
        project_dir = '/home/lojinha-agro/mysite'
    else:
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    instance_dir = os.path.join(project_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, 'usuarios.db')
    
    print("\n=== Criação de Usuário Admin ===")
    
    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            
            # Verificar se já existe admin
            c.execute('SELECT id, username FROM usuarios WHERE is_admin = 1')
            admin = c.fetchone()
            
            if admin:
                print(f"\nJá existe um admin: ID {admin[0]}, Username: {admin[1]}")
                return
            
            # Criar admin
            print("\nCriando usuário admin...")
            c.execute('''
                INSERT INTO usuarios (
                    username, 
                    email, 
                    phone, 
                    password, 
                    security_question, 
                    security_answer, 
                    is_admin
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'fury777',
                'henriquecosta1322d@gmail.com',
                '5583991469269',
                generate_password_hash('13221322Dh$'),
                '1',  # Animal de estimação
                'pretinho',
                True
            ))
            conn.commit()
            print("Admin criado com sucesso!")
            
    except Exception as e:
        print(f"\nErro ao criar admin: {str(e)}")

def list_users():
    """Lista todos os usuários do sistema"""
    if os.environ.get('PYTHONANYWHERE_DOMAIN'):
        project_dir = '/home/lojinha-agro/mysite'
    else:
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    instance_dir = os.path.join(project_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, 'usuarios.db')
    
    print("\n=== Lista de Usuários ===")
    
    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT id, username, email, is_admin, banned FROM usuarios')
            users = c.fetchall()
            
            print("\nID | Username | Email | Admin | Banido")
            print("-" * 60)
            for user in users:
                print(f"{user[0]} | {user[1]} | {user[2]} | {bool(user[3])} | {bool(user[4])}")
    
    except Exception as e:
        print(f"\nErro ao listar usuários: {str(e)}")

def main():
    """Função principal"""
    action = input("""
1. Criar usuário admin
2. Listar usuários
Escolha uma opção: """)
    
    if action == '1':
        create_admin()
    elif action == '2':
        list_users()
    else:
        print("Opção inválida")

if __name__ == '__main__':
    main()