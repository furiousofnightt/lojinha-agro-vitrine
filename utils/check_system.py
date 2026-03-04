import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def check_environment():
    """Verifica e exibe informações sobre o ambiente"""
    print("\n=== Verificação do Ambiente ===")
    
    # 1. Variáveis de ambiente
    env_vars = {
        'PYTHONANYWHERE_DOMAIN': os.environ.get('PYTHONANYWHERE_DOMAIN'),
        'FLASK_ENV': os.environ.get('FLASK_ENV'),
        'FLASK_DEBUG': os.environ.get('FLASK_DEBUG'),
        'PATH': os.environ.get('PATH')
    }
    
    print("\n1. Variáveis de ambiente:")
    for var, value in env_vars.items():
        print(f"{var}: {value}")
    
    # 2. Diretórios
        if os.environ.get('PYTHONANYWHERE_DOMAIN'):
            project_dir = '/home/lojinha-agro/mysite'
    else:
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    dirs_to_check = [
        (project_dir, "Projeto"),
        (os.path.join(project_dir, 'static'), "Static"),
        (os.path.join(project_dir, 'static/uploads'), "Uploads"),
        (os.path.join(project_dir, 'static/uploads/produtos'), "Produtos"),
        (os.path.join(project_dir, 'templates'), "Templates")
    ]
    
    print("\n2. Diretórios:")
    for path, name in dirs_to_check:
        exists = os.path.exists(path)
        print(f"\n{name}: {path}")
        print(f"Existe: {exists}")
        if exists:
            print(f"Permissões: {oct(os.stat(path).st_mode)[-3:]}")
            print(f"Conteúdo: {os.listdir(path)[:5]}...")

def check_database():
    """Verifica o estado do banco de dados"""
    print("\n=== Verificação do Banco de Dados ===")
    
    if os.environ.get('PYTHONANYWHERE_DOMAIN'):
            project_dir = '/home/lojinha-agro/mysite'
    else:
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    instance_dir = os.path.join(project_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, 'usuarios.db')
    
    print(f"\nBanco de dados: {db_path}")
    print(f"Existe: {os.path.exists(db_path)}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            
            # 1. Verificar tabelas
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = c.fetchall()
            print("\n1. Tabelas encontradas:", [t[0] for t in tables])
            
            # 2. Verificar usuário admin
            c.execute('SELECT id, username, email, is_admin, banned FROM usuarios WHERE is_admin = 1')
            admins = c.fetchall()
            print("\n2. Usuários admin:")
            for admin in admins:
                print(f"ID: {admin[0]}, Username: {admin[1]}, Email: {admin[2]}, Banido: {bool(admin[4])}")
            
            # 3. Contagem de registros
            print("\n3. Contagem de registros:")
            for table in [t[0] for t in tables]:
                c.execute(f"SELECT COUNT(*) FROM {table}")
                count = c.fetchone()[0]
                print(f"{table}: {count}")
    
    except Exception as e:
        print(f"\nErro ao verificar banco de dados: {str(e)}")

def main():
    """Função principal que executa todas as verificações"""
    check_environment()
    check_database()

if __name__ == '__main__':
    main()