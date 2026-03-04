from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import re
import sqlite3
import os
import time
import sys
import os
import shutil 


# Adiciona o diretório atual ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from forms import RegistroForm, LoginForm

app = Flask(__name__)
app.debug = True  # Ativa o modo debug

# Proteção contra brute force
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1000 per day"],  # Limite diário global
    storage_uri="memory://"
)

# Configurar limites específicos para endpoints
limiter.limit("20 per minute")(app.route('/login', methods=['GET', 'POST']))

# Importar configurações do ambiente
from dotenv import load_dotenv
load_dotenv()

# -------------------- CONFIGURAÇÕES DE SEGURANÇA E SESSÃO --------------------
# Secret Key - vem do .env ou usa fallback em dev
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_secret_key_for_testing')

# Configurações de sessão
app.config['SESSION_PROTECTION'] = 'strong'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutos

# Cookies de sessão
app.config['SESSION_COOKIE_HTTPONLY'] = True   # Bloqueia acesso por JS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Evita CSRF básico
app.config['SESSION_COOKIE_SECURE'] = not app.debug  # Só envia via HTTPS em produção
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Cookies do remember-me
app.config['REMEMBER_COOKIE_DURATION'] = 1800  # 30 minutos
app.config['REMEMBER_COOKIE_REFRESH_EACH_REQUEST'] = True
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SECURE'] = not app.debug

# Configuração do CSRF
csrf = CSRFProtect(app)

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Rota para onde redirecionar quando precisar de login
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'basic'  # Nível de proteção básico para permitir acesso às páginas públicas
login_manager.refresh_view = 'login'
login_manager.needs_refresh_message = 'Por favor, faça login novamente para continuar.'
login_manager.needs_refresh_message_category = 'info'

# Define uma função para verificar se a rota atual precisa de autenticação
def is_public_route():
    public_routes = ['redefinir_senha', 'nova_senha', 'login', 'registro', 'index']
    return request.endpoint in public_routes

# Atualiza o user_loader para permitir acesso a rotas públicas
@login_manager.unauthorized_handler
def unauthorized():
    if is_public_route():
        return None
    return redirect(url_for('login'))

# Configuração de uploads
if os.environ.get('PYTHONANYWHERE_DOMAIN'):
    project_dir = '/home/lojinha-agro/mysite'
    app.config['UPLOAD_FOLDER'] = os.path.join(project_dir, 'static', 'uploads', 'produtos')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Configurar regras para servir arquivos estáticos no PythonAnywhere
    from flask import send_from_directory
    
    @app.route('/static/<path:filename>')
    def custom_static(filename):
        # Caminho base para arquivos estáticos
        static_dir = os.path.join(project_dir, 'static')
        return send_from_directory(static_dir, filename)

    # Criar diretórios necessários
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
else:
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads', 'produtos')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Limite de upload
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64MB máx
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
# ---------------------------------------------------------------------------

# Caminho do banco de dados SQLite — usa a pasta `instance/` por padrão
# Para produção (PythonAnywhere) usa o caminho dentro do projeto remoto,
# para desenvolvimento usa `app.instance_path` (ou cria `instance/` ao lado do código).
if os.environ.get('PYTHONANYWHERE_DOMAIN'):
    # Em PythonAnywhere esperamos a estrutura: /home/<user>/mysite/instance/usuarios.db
    project_dir = '/home/lojinha-agro/mysite'
    instance_dir = os.path.join(project_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    DB_PATH = os.path.join(instance_dir, 'usuarios.db')
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    # Preferir o caminho gerenciado pelo Flask (app.instance_path) quando disponível
    try:
        instance_dir = app.instance_path
    except Exception:
        instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    DB_PATH = os.path.join(instance_dir, 'usuarios.db')

# Classe de usuário para o Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, is_admin=False, is_banned=False):
        self.id = id
        self.username = username
        self.email = email
        self._is_admin = bool(is_admin)  # Armazena como booleano
        self._is_banned = bool(is_banned)  # Status de banimento

    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return not self._is_banned  # Usuários banidos não estão ativos

    @property
    def is_anonymous(self):
        return False

    @property
    def is_admin(self):
        return self._is_admin  # Retorna o valor booleano

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"Verificando acesso admin - Usuário autenticado: {current_user.is_authenticated}")  # Debug
        if current_user.is_authenticated:
            print(f"Usuário {current_user.username} - Admin: {current_user.is_admin}")  # Debug
        
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acesso negado. Você precisa ser um administrador.', 'error')
            print("Acesso negado: Usuário não é admin")  # Debug
            return redirect(url_for('home'))
        print("Acesso permitido: Usuário é admin")  # Debug
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT id, username, email, is_admin, banned FROM usuarios WHERE id = ?', (user_id,))
        user = c.fetchone()
        if user:
            # Garante que is_admin e banned sejam booleanos
            is_admin = bool(user[3])
            is_banned = bool(user[4]) if user[4] is not None else False
            print(f"Carregando usuário - ID: {user[0]}, Admin: {is_admin}, Banned: {is_banned}")  # Debug
            return User(user[0], user[1], user[2], is_admin, is_banned)
    return None

    # Criar banco de dados se não existir
def init_db():
    print(f"Inicializando banco de dados em: {DB_PATH}")  # Log para debug
    
    # Cria diretório caso exista caminho
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('PRAGMA foreign_keys = ON')

        # Tabela de usuários
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

        # Tabela de categorias
        c.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                descricao TEXT
            )
        ''')

        # Tabela de produtos
        c.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT,
                preco DECIMAL(10,2) NOT NULL,
                estoque INTEGER NOT NULL DEFAULT 0,
                categoria_id INTEGER,
                imagem TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL
            )
        ''')

        # Tabela de carrinhos
        c.execute('''
            CREATE TABLE IF NOT EXISTS carrinhos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'aberto',
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
            )
        ''')

        # Tabela de itens do carrinho
        c.execute('''
            CREATE TABLE IF NOT EXISTS itens_carrinho (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                carrinho_id INTEGER NOT NULL,
                produto_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                preco_unitario DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (carrinho_id) REFERENCES carrinhos(id) ON DELETE CASCADE,
                FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
            )
        ''')

        # Tabela de pedidos
        c.execute('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                carrinho_id INTEGER NOT NULL,
                endereco TEXT NOT NULL,
                cidade TEXT NOT NULL,
                estado TEXT NOT NULL,
                cep TEXT NOT NULL,
                status TEXT DEFAULT 'pendente',
                data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                FOREIGN KEY (carrinho_id) REFERENCES carrinhos(id) ON DELETE CASCADE
            )
        ''')

        # Tabela de mídias dos produtos
        c.execute('''
            CREATE TABLE IF NOT EXISTS produto_midias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                caminho TEXT NOT NULL,
                ordem INTEGER DEFAULT 0,
                FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        print("Todas as tabelas foram criadas/verificadas com sucesso!")


# Popular categorias e produtos fake - versão agro
def popular_fake_data():
    categorias = [
        ("Máquinas Agrícolas", "Tratores, colheitadeiras e implementos"),
        ("Insumos", "Fertilizantes, sementes e defensivos"),
        ("Tecnologia Agrícola", "Drones, sensores e softwares de gestão"),
        ("Equipamentos de Irrigação", "Bombas, aspersores e sistemas de irrigação"),
    ]
    produtos = [
        ("Trator 4x4 Turbo 75cv", "Trator agrícola com motor turbo diesel, cabine fechada e tração 4x4.", 189999.00, 3, 1, "uploads/produtos/trator.jpg"),
        ("Colheitadeira Axial 350", "Colheitadeira de grãos com sistema axial, alta capacidade e eficiência.", 499999.00, 2, 1, "uploads/produtos/colheitadeira.jpg"),
        ("Semeadora Pneumática 12 Linhas", "Semeadora com distribuição precisa e sistema pneumático.", 89999.00, 5, 1, None),
        ("Fertilizante NPK 20-10-10", "Fertilizante granulado para culturas diversas, alta solubilidade.", 129.90, 50, 2, "uploads/produtos/fertilizante.jpg"),
        ("Sementes de Milho Híbrido", "Sementes de milho híbrido com alto rendimento e resistência.", 399.90, 40, 2, None),
        ("Herbicida Sistêmico 1L", "Defensivo agrícola para controle de plantas daninhas em lavouras.", 89.90, 60, 2, None),
        ("Drone Agrícola X200", "Drone para pulverização e mapeamento de áreas agrícolas.", 15999.00, 4, 3, "uploads/produtos/drone-agro.jpg"),
        ("Sensor de Umidade de Solo", "Sensor digital para monitoramento da umidade em tempo real.", 499.90, 15, 3, None),
        ("Software de Gestão Rural", "Plataforma para controle de produção, estoque e finanças agrícolas.", 999.00, 10, 3, None),
        ("Kit Irrigação por Gotejamento", "Sistema completo para irrigação eficiente em hortas e lavouras.", 799.00, 25, 4, None),
        ("Bomba Submersa 2HP", "Bomba elétrica para captação de água em poços e reservatórios.", 1299.00, 12, 4, None),
    ]

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        for nome, desc in categorias:
            c.execute('INSERT OR IGNORE INTO categorias (nome, descricao) VALUES (?, ?)', (nome, desc))
        c.execute('SELECT id, nome FROM categorias')
        cat_map = {nome: id for id, nome in c.fetchall()}
        for nome, desc, preco, estoque, cat_id, imagem in produtos:
            c.execute('SELECT COUNT(*) FROM produtos WHERE nome=?', (nome,))
            if c.fetchone()[0] == 0:
                c.execute('''
                    INSERT INTO produtos (nome, descricao, preco, estoque, categoria_id, imagem)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (nome, desc, preco, estoque, cat_id, imagem))
        conn.commit()
        print("Fake data de categorias e produtos inserida com sucesso!")

# Inicialização

# -------------------- ROTAS --------------------

@app.route('/')
def index():
    return render_template('index.html')

# -------------------- HOME (requer autenticação) --------------------
@app.route('/home')
@login_required
def home():
    # Se não estiver autenticado, o @login_required já redireciona para login
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Buscar todas as categorias
            c.execute('SELECT id, nome FROM categorias')
            categorias = c.fetchall()
            # Buscar até 12 produtos por categoria (para telas grandes e médias, o grid já é responsivo)
            cat_produtos = {}
            for cat_id, cat_nome in categorias:
                c.execute('''SELECT p.*, c.nome as categoria_nome FROM produtos p LEFT JOIN categorias c ON p.categoria_id = c.id WHERE p.categoria_id = ? ORDER BY p.data_criacao DESC LIMIT 12''', (cat_id,))
                produtos = c.fetchall()
                if produtos:
                    cat_produtos[(cat_id, cat_nome)] = produtos
        return render_template('home.html', cat_produtos=cat_produtos, categorias=categorias)
    except Exception as e:
        print(f"Erro ao carregar home: {str(e)}")
        flash('Erro ao carregar produtos', 'error')
        return redirect(url_for('home'))

@app.route('/produtos')
def produtos():
    try:
        categoria_id = request.args.get('categoria', type=int)
        search = request.args.get('q', '').strip()

        import unicodedata

        # Função normalize robusta para remover acentos e lidar com None
        def normalize(text):
            if not text:
                return ''
            return unicodedata.normalize('NFKD', str(text))\
                               .encode('ASCII', 'ignore')\
                               .decode('ASCII')\
                               .lower()

        with sqlite3.connect(DB_PATH) as conn:
            conn.create_function('normalize', 1, normalize)
            c = conn.cursor()
            
            # Buscar o nome da categoria selecionada
            cat_nome = None
            if categoria_id:
                c.execute('SELECT nome FROM categorias WHERE id = ?', (categoria_id,))
                result = c.fetchone()
                if result:
                    cat_nome = result[0]

            sql = '''
                SELECT p.*, c.nome as categoria_nome 
                FROM produtos p 
                LEFT JOIN categorias c ON p.categoria_id = c.id
            '''
            
            where_clauses = []
            params = []

            # Filtro por categoria
            if categoria_id:
                where_clauses.append('p.categoria_id = ?')
                params.append(categoria_id)

            # Filtro por busca
            if search:
                search_norm = f'%{normalize(search)}%'
                where_clauses.append('(' +
                    'normalize(COALESCE(p.nome, "")) LIKE ? OR ' +
                    'normalize(COALESCE(p.descricao, "")) LIKE ? OR ' +
                    'normalize(COALESCE(c.nome, "")) LIKE ?' +
                ')')
                params.extend([search_norm, search_norm, search_norm])

            if where_clauses:
                sql += ' WHERE ' + ' AND '.join(where_clauses)

            sql += ' ORDER BY p.data_criacao DESC'  # produtos mais recentes primeiro

            # Debug opcional
            # print("SQL:", sql)
            # print("Params:", params)

            produtos = c.execute(sql, params).fetchall()

            # Todas categorias para filtros
            c.execute('SELECT * FROM categorias')
            categorias = c.fetchall()

        return render_template('produtos.html', produtos=produtos, categorias=categorias, 
                               categoria_atual=categoria_id, categoria_nome=cat_nome, search=search)

    except Exception as e:
        print(f"Erro ao carregar produtos: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('Erro ao carregar produtos', 'error')
        return redirect(url_for('home'))

@app.route('/produto/<int:id>')
def produto(id):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT p.*, c.nome as categoria_nome 
                FROM produtos p 
                LEFT JOIN categorias c ON p.categoria_id = c.id 
                WHERE p.id = ?
            ''', (id,))
            row = c.fetchone()
            if not row:
                flash('Produto não encontrado', 'error')
                return redirect(url_for('produtos'))
            # Montar dicionário compatível com o template
            produto = {
                'id': row[0],
                'nome': row[1],
                'descricao': row[2],
                'preco': row[3],
                'estoque': row[4],
                'categoria_id': row[5],
                'imagem_principal': row[6] if row[6] else '',
                'imagens_extra': [],
                'video': None,
                'categoria_nome': row[8] if len(row) > 8 else ''
            }
            # Buscar imagens e vídeo do produto
            c.execute('SELECT tipo, caminho FROM produto_midias WHERE produto_id=? ORDER BY tipo, ordem', (produto['id'],))
            midias = c.fetchall()
            imagens = [m[1] for m in midias if m[0] == 'imagem']
            video = next((m[1] for m in midias if m[0] == 'video'), None)
            produto['imagens_extra'] = imagens
            produto['video'] = video
            # Buscar produtos relacionados da mesma categoria
            relacionados = []
            if produto['categoria_id']:
                c.execute('''
                    SELECT * FROM produtos 
                    WHERE categoria_id = ? AND id != ? 
                    LIMIT 4
                ''', (produto['categoria_id'], id))
                relacionados = c.fetchall()
        return render_template('produto.html', produto=produto, relacionados=relacionados)
    except Exception as e:
        print(f"Erro ao carregar produto: {str(e)}")
        flash('Erro ao carregar produto', 'error')
        return redirect(url_for('produtos'))

# ===== LOGIN =====
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute;20 per hour")
def login():
    try:
        print("\n=== Nova tentativa de login ===\nMétodo:", request.method)  # Debug
        # Se já estiver logado, redireciona
        if current_user.is_authenticated:
            print(f"Usuário já está autenticado: {current_user.username}, Admin: {current_user.is_admin}")  # Debug
            return redirect(url_for('admin_dashboard') if current_user.is_admin else url_for('home'))
        
        form = LoginForm()
        
        # GET: mostra o formulário
        if request.method == 'GET':
            return render_template('login.html', form=form)

        # POST: processa login
        if request.method == 'POST':
            print("Iniciando processo de login POST...")  # Debug
            identifier = request.form['identifier'].strip()  # Remove espaços extras
            password = request.form['password']

            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                # Verificar o tipo de identificador
                is_email = '@' in identifier
                is_phone = bool(re.match(r'^[\d\s\+\-\(\)]+$', identifier))

                user = None

                if is_phone:
                    clean_number = re.sub(r'[^0-9]', '', identifier)
                    if clean_number.startswith('0'):
                        clean_number = clean_number[1:]
                    phone_formats = [clean_number]
                    if len(clean_number) == 11:
                        phone_formats.extend(['55' + clean_number, '+55' + clean_number])
                    elif len(clean_number) == 13 and clean_number.startswith('55'):
                        phone_formats.extend([clean_number, '+' + clean_number, clean_number[2:]])
                    elif len(clean_number) == 9:
                        phone_formats.extend([clean_number, '55' + identifier])
                    placeholders = ','.join(['?' for _ in phone_formats])
                    query = f'SELECT id, username, email, phone, password, is_admin, banned FROM usuarios WHERE phone IN ({placeholders})'
                    c.execute(query, phone_formats)
                    user = c.fetchone()

                elif is_email:
                    c.execute('''
                        SELECT id, username, email, phone, password, is_admin, banned 
                        FROM usuarios WHERE LOWER(email) = LOWER(?)
                    ''', (identifier,))
                    user = c.fetchone()

                else:
                    from unicodedata import normalize as uni_normalize
                    def normalize(text):
                        return uni_normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').strip().lower()
                    identifier_norm = normalize(identifier)
                    c.execute('SELECT id, username, email, phone, password, is_admin, banned FROM usuarios')
                    all_users = c.fetchall()
                    for u in all_users:
                        username_norm = normalize(u[1])
                        if username_norm == identifier_norm:
                            user = u
                            break

                # Apenas mostra o nick (username) em logs de debug
                if user:
                    print(f"Tentativa de login para usuário: {user[1]}")
                else:
                    print("Tentativa de login para usuário não encontrado")

            if user:
                user_id, username, email, phone, hashed_pw, is_admin, is_banned = user
                print(f"\nUsuário encontrado: {username}")
                print(f"ID: {user_id}, Email: {email}, Admin: {bool(is_admin)}, Banido: {bool(is_banned)}")
                print("Verificando senha...")  # Debug
                
                senha_valida = check_password_hash(hashed_pw, password)
                print(f"Resultado da verificação de senha: {senha_valida}")
                
                if senha_valida:
                    print("\nSenha correta! Iniciando login...")  # Debug
                    is_admin = bool(is_admin)
                    is_banned = bool(is_banned)
                    if is_banned:
                        print("Usuário está banido, negando acesso")
                        flash('Esta conta está temporariamente suspensa. Entre em contato com o suporte.', 'error')
                        return redirect(url_for('login'))

                    user_obj = User(int(user_id), username, email, is_admin, is_banned)
                    login_result = login_user(user_obj)
                    print(f"\nResultado do login_user: {login_result}")
                    print(f"Usuário autenticado: {current_user.is_authenticated}")
                    print(f"Admin: {current_user.is_admin}")
                    
                    if login_result:
                        print("Login realizado com sucesso!")  # Debug
                        flash(f'Bem-vindo, {username}!', 'success')

                        next_page = request.args.get('next')
                        if next_page:
                            print(f"Redirecionando para página solicitada: {next_page}")
                            return redirect(next_page)

                        destino = url_for('admin_dashboard' if user_obj.is_admin else 'home')
                        print(f"Redirecionando para: {destino}")
                        return redirect(destino)
                    else:
                        print("Erro: login_user retornou False")
                        flash('Erro ao fazer login. Tente novamente.', 'error')
                        return redirect(url_for('login'))
                else:
                    print("Senha incorreta")
                    flash('Usuário ou senha inválidos', 'error')
            else:
                print(f"Usuário não encontrado para o identificador: {identifier}")
                flash('Usuário ou senha inválidos', 'error')

            return redirect(url_for('login'))

    except Exception as e:
        print(f"Erro no login: {str(e)}")  # Debug do erro
        import traceback
        print(f"Traceback completo: {traceback.format_exc()}")  # Debug completo
        flash('Erro no servidor. Por favor, tente novamente.', 'error')
        return redirect(url_for('login'))

    return render_template('login.html', form=form)

# ===== VALIDAÇÕES =====
def validar_senha(senha):
    if len(senha) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres"
    if not re.search("[a-z]", senha):
        return False, "A senha deve conter pelo menos uma letra minúscula"
    if not re.search("[A-Z]", senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula"
    if not re.search("[0-9]", senha):
        return False, "A senha deve conter pelo menos um número"
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", senha):
        return False, "A senha deve conter pelo menos um caractere especial"
    return True, ""


def validar_email(email):
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(padrao, email))


def validar_telefone(telefone, para_login=False):
    """
    Valida e formata números de telefone.
    
    - Para registro: retorna (bool_valido, telefone_formatado)
    - Para login: retorna telefone_formatado, pronto para buscar no banco
    """
    import re

    try:
        if not telefone:
            return (False, '') if not para_login else None

        # Remove tudo que não for número
        numeros = re.sub(r'[^0-9]', '', telefone)

        # Ajuste para login: retorna apenas números limpos para combinar no DB
        if para_login:
            return numeros

        # Para registro: deve ter DDD + número (8-9 dígitos)
        # Permite +55 ou 0DDD, mas sempre salva no formato +55DDDNUM
        if numeros.startswith('0') and len(numeros) >= 10:
            numeros = numeros[1:]  # remove zero à esquerda

        if not numeros.startswith('55'):
            numeros = '55' + numeros

        telefone_formatado = '+' + numeros

        # Valida tamanho básico: DDD + número (10 a 13 dígitos sem o +)
        if 10 <= len(numeros) <= 13:
            return True, telefone_formatado

        return False, telefone_formatado

    except Exception as e:
        print("Erro na validação do telefone:", e)
        return (False, '') if not para_login else None

# ===== REGISTRO =====
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    # Se já estiver logado, redireciona para index
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistroForm()

    if request.method == 'GET':
        return render_template('registro.html', form=form)

    if request.method == 'POST':
        try:
            # Debug para POST requests
            print("Erros do form:", form.errors)
            form_valid = form.validate_on_submit()
            print("Form válido:", form_valid)

            if form_valid:
                username = form.username.data
                email = form.email.data
                phone = form.phone.data
                password = form.password.data
                security_question = form.securityQuestion.data
                security_answer = form.securityAnswer.data
                print(f"Dados recebidos - Username: {username}, Email: {email}, Phone: {phone}")
                print(f"Pergunta de segurança: {security_question}, Resposta fornecida: {security_answer}")

                telefone_valido, telefone_formatado = validar_telefone(phone)
                if not telefone_valido:
                    flash('Número de telefone inválido. Use o formato (XX) XXXXX-XXXX', 'error')
                    return redirect(url_for('registro'))

                senha_valida, msg_erro = validar_senha(password)
                if not senha_valida:
                    flash(msg_erro, 'error')
                    return redirect(url_for('registro'))

                # Usa o telefone formatado para salvar no banco
                phone = telefone_formatado
                hashed_password = generate_password_hash(password)

                with sqlite3.connect(DB_PATH) as conn:
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO usuarios (username, email, phone, password, security_question, security_answer)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (username, email, phone, hashed_password, security_question, security_answer))
                    conn.commit()

                flash('Conta criada com sucesso! Faça login.', 'success')
                return redirect(url_for('login'))

            else:
                # Form inválido: imprime erros detalhados
                print("Formulário inválido:", form.errors)
                flash('Erro nos dados do formulário. Verifique os campos e tente novamente.', 'error')
                return redirect(url_for('registro'))

        except sqlite3.IntegrityError as e:
            print("Erro de integridade no banco:", e)
            flash('Usuário, e-mail ou telefone já cadastrado', 'error')
            return redirect(url_for('registro'))

        except Exception as e:
            import traceback
            print("Erro inesperado durante registro:", e)
            print(traceback.format_exc())
            flash('Erro no servidor durante o registro.', 'error')
            return redirect(url_for('registro'))

    # Sempre retorna o template caso GET ou se algo falhar
    return render_template('registro.html', form=form)

# ===== REDEFINIR SENHA =====
@app.route('/redefinir-senha', methods=['GET', 'POST'])
def redefinir_senha():
    if request.method == 'POST':

        username = request.form['usuario'].strip()
        email = request.form['email'].strip().lower()
        phone = ''.join(filter(str.isdigit, request.form['telefone']))
        # Padronizar para DDD+telefone (últimos 11 dígitos)
        phone = phone[-11:]
        question = request.form['pergunta'].strip()
        answer = request.form['resposta'].strip().lower()

        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Buscar por telefone padronizado (últimos 11 dígitos)
            c.execute('''
                SELECT id FROM usuarios
                WHERE TRIM(LOWER(username))=?
                  AND TRIM(LOWER(email))=?
                  AND substr(REPLACE(REPLACE(REPLACE(phone, '-', ''), '(', ''), ')', ''), -11)=?
                  AND security_question=?
                  AND TRIM(LOWER(security_answer))=?
            ''', (username.lower(), email, phone, question, answer))
            user = c.fetchone()

        if user:
            return redirect(url_for('nova_senha', token=user[0]))
        else:
            flash('Dados não conferem', 'error')
            return redirect(url_for('redefinir_senha'))

    return render_template('redefinir-senha.html')


# ===== NOVA SENHA =====
@app.route('/nova-senha/<token>', methods=['GET', 'POST'])
def nova_senha(token):

    if request.method == 'POST':
        senha = request.form['senha']
        confirmar = request.form['confirmar']

        if senha != confirmar:
            flash('As senhas não coincidem', 'error')
            return redirect(url_for('nova_senha', token=token))

        senha_valida, msg_erro = validar_senha(senha)
        if not senha_valida:
            flash(msg_erro, 'error')
            return redirect(url_for('nova_senha', token=token))

        hashed_password = generate_password_hash(senha)
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('UPDATE usuarios SET password=? WHERE id=?', (hashed_password, token))
            conn.commit()
        flash('Senha alterada com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('nova-senha.html', token=token)


# ===== LOGOUT =====
@app.route('/logout')
@login_required
def logout():
    # Remove a sessão do usuário
    logout_user()
    
    # Limpa a sessão atual
    session.clear()
    
    # Cria resposta de redirecionamento
    response = redirect(url_for('index'))
    
    # Remove todos os cookies relacionados à sessão
    response.delete_cookie('session')
    response.delete_cookie('remember_token')
    response.delete_cookie('_flashes')  # Cookie de mensagens flash
    response.delete_cookie('_id')  # Cookie de identificação do usuário
    
    # Em desenvolvimento, força a limpeza dos cookies com domínio local
    if not os.environ.get('VERCEL_ENV'):
        for cookie in ['session', 'remember_token', '_flashes', '_id']:
            response.delete_cookie(cookie, domain='localhost')
    
    flash('Você foi desconectado com sucesso!', 'success')
    return response


# -------------------- ADMIN -------------------
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    print(f"Acessando dashboard admin - Usuário: {current_user.username}, Admin: {current_user.is_admin}")  # Debug
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            
            # Contagem de usuários
            c.execute('SELECT COUNT(*) FROM usuarios')
            total_usuarios = c.fetchone()[0]
            print(f"Total de usuários: {total_usuarios}")  # Debug
            
            # Contagem de produtos
            c.execute('SELECT COUNT(*) FROM produtos')
            total_produtos = c.fetchone()[0]
            print(f"Total de produtos: {total_produtos}")  # Debug
            
            # Contagem de pedidos
            c.execute('SELECT COUNT(*) FROM carrinhos WHERE status = "fechado"')
            total_pedidos = c.fetchone()[0]
            print(f"Total de pedidos: {total_pedidos}")  # Debug
            
            # Contagem de categorias
            c.execute('SELECT COUNT(*) FROM categorias')
            total_categorias = c.fetchone()[0]
            print(f"Total de categorias: {total_categorias}")  # Debug
            
            # Últimos pedidos
            c.execute('''
                SELECT c.id, u.username, COUNT(ic.id) as total_itens,
                       SUM(ic.quantidade * ic.preco_unitario) as valor_total,
                       c.data_criacao
                FROM carrinhos c
                JOIN usuarios u ON c.usuario_id = u.id
                JOIN itens_carrinho ic ON c.id = ic.carrinho_id
                WHERE c.status = "fechado"
                GROUP BY c.id
                ORDER BY c.data_criacao DESC
                LIMIT 5
            ''')
            ultimos_pedidos = c.fetchall()
            print(f"Carregados {len(ultimos_pedidos)} últimos pedidos")  # Debug
            
            print("Renderizando template admin.html")  # Debug
            return render_template('admin.html', 
                                 total_usuarios=total_usuarios,
                                 total_produtos=total_produtos,
                                 total_pedidos=total_pedidos,
                                 total_categorias=total_categorias,
                                 ultimos_pedidos=ultimos_pedidos)
    except Exception as e:
        print(f"Erro ao carregar dashboard: {str(e)}")  # Debug
        print(f"Traceback completo:", e.__traceback__)  # Debug detalhado
        flash('Erro ao carregar informações do dashboard', 'error')
        return redirect(url_for('home'))

# -------------------- USUÁRIOS --------------------
@app.route('/admin/usuarios')
@login_required
@admin_required
def admin_usuarios():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT id, username, email, phone, is_admin, banned FROM usuarios')
        usuarios = c.fetchall()
    return render_template('admin_usuarios.html', usuarios=usuarios)

@app.route('/admin/usuario/ban/<int:id>', methods=['POST'])
@login_required
@admin_required
def banir_usuario(id):
    if id == current_user.id:
        return jsonify({'error': 'Você não pode banir sua própria conta'}), 400
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('UPDATE usuarios SET banned = 1 WHERE id = ?', (id,))
            conn.commit()
        return jsonify({'message': 'Usuário banido com sucesso'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/usuario/unban/<int:id>', methods=['POST'])
@login_required
@admin_required
def desbanir_usuario(id):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('UPDATE usuarios SET banned = 0 WHERE id = ?', (id,))
            conn.commit()
        return jsonify({'message': 'Banimento removido com sucesso'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/usuario/<int:id>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def gerenciar_usuario(id):
    if request.method == 'DELETE':
        if id == current_user.id:
            return jsonify({'error': 'Você não pode deletar sua própria conta'}), 400
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM itens_carrinho WHERE carrinho_id IN (SELECT id FROM carrinhos WHERE usuario_id=?)', (id,))
            c.execute('DELETE FROM carrinhos WHERE usuario_id=?', (id,))
            c.execute('DELETE FROM usuarios WHERE id=?', (id,))
            conn.commit()
        return jsonify({'message': 'Usuário removido com sucesso'}), 200
    elif request.method == 'PUT':
        data = request.get_json()
        if id == current_user.id and not data.get('is_admin', True):
            return jsonify({'error': 'Não pode remover seus próprios privilégios de admin'}), 400
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('UPDATE usuarios SET username=?, email=?, phone=?, is_admin=? WHERE id=?',
                      (data['username'], data['email'], data['phone'], data['is_admin'], id))
            conn.commit()
        return jsonify({'message': 'Usuário atualizado com sucesso'}), 200

# -------------------- PRODUTOS --------------------
@app.route('/admin/produtos', methods=['GET'])
@login_required
@admin_required
def admin_produtos():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT p.*, c.nome as categoria_nome FROM produtos p LEFT JOIN categorias c ON p.categoria_id=c.id')
        produtos = c.fetchall()
        c.execute('SELECT * FROM categorias')
        categorias = c.fetchall()
    return render_template('admin_produtos.html', produtos=produtos, categorias=categorias)

@app.route('/admin/produto/novo', methods=['POST'])
@login_required
@admin_required
def novo_produto():
    nome = request.form['nome']
    descricao = request.form['descricao']
    preco_str = request.form['preco']
    preco_str = preco_str.strip()
    # Se houver vírgula, ela é o separador decimal
    if ',' in preco_str:
        preco_str = preco_str.replace('.', '')
        preco_str = preco_str.replace(',', '.')
    else:
        # Se houver mais de um ponto, o último é separador decimal
        if preco_str.count('.') > 1:
            partes = preco_str.split('.')
            decimal = partes[-1]
            inteiro = ''.join(partes[:-1])
            preco_str = inteiro + '.' + decimal
    try:
        preco = float(preco_str)
    except ValueError:
        preco = 0.0
    estoque = int(request.form.get('estoque', 0))
    categoria_id = request.form.get('categoria_id', type=int)
    from upload_helper import salvar_arquivo
    imagens = request.files.getlist('imagens')
    video = request.files.get('video')
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO produtos (nome, descricao, preco, estoque, categoria_id, imagem) VALUES (?, ?, ?, ?, ?, ?)',
                      (nome, descricao, preco, estoque, categoria_id, None))
            produto_id = c.lastrowid
            # Salvar imagens (até 5)
            img_salvas = 0
            for idx, img in enumerate(imagens[:5]):
                caminho_rel = salvar_arquivo(img, tipo='imagem')
                if caminho_rel:
                    c.execute('INSERT INTO produto_midias (produto_id, tipo, caminho, ordem) VALUES (?, ?, ?, ?)',
                              (produto_id, 'imagem', caminho_rel, idx))
                    if img_salvas == 0:
                        c.execute('UPDATE produtos SET imagem=? WHERE id=?', (caminho_rel, produto_id))
                    img_salvas += 1
            # Salvar vídeo (apenas 1)
            if video:
                caminho_rel = salvar_arquivo(video, tipo='video')
                if caminho_rel:
                    c.execute('INSERT INTO produto_midias (produto_id, tipo, caminho, ordem) VALUES (?, ?, ?, ?)',
                              (produto_id, 'video', caminho_rel, 0))
            conn.commit()
        flash('Produto adicionado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao adicionar produto: {str(e)}', 'error')
    return redirect(url_for('admin_produtos'))

@app.route('/admin/produto/<int:id>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def gerenciar_produto(id):
    if request.method == 'DELETE':
        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                # Buscar todas as mídias do produto
                c.execute('SELECT caminho FROM produto_midias WHERE produto_id=?', (id,))
                midias = c.fetchall()
                for midia in midias:
                    caminho_arquivo = os.path.join(app.root_path, 'static', midia[0])
                    try:
                        if os.path.exists(caminho_arquivo):
                            os.remove(caminho_arquivo)
                    except OSError:
                        pass
                # Remover imagem principal se existir
                c.execute('SELECT imagem FROM produtos WHERE id=?', (id,))
                produto = c.fetchone()
                if produto and produto[0]:
                    caminho_img = os.path.join(app.root_path, 'static', produto[0])
                    try:
                        if os.path.exists(caminho_img):
                            os.remove(caminho_img)
                    except OSError:
                        pass
                # Excluir produto (mídias são removidas por ON DELETE CASCADE)
                c.execute('DELETE FROM produtos WHERE id=?', (id,))
                conn.commit()
            return jsonify({'message': 'Produto removido com sucesso'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    elif request.method == 'PUT':
        data = request.get_json()
        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute('UPDATE produtos SET nome=?, descricao=?, preco=?, estoque=?, categoria_id=? WHERE id=?',
                          (data['nome'], data['descricao'], data['preco'], data['estoque'], data['categoria_id'], id))
                conn.commit()
            return jsonify({'message': 'Produto atualizado com sucesso'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# -------------------- CATEGORIAS --------------------
@app.route('/admin/categorias', methods=['GET', 'POST'], endpoint='admin_categorias')
@login_required
@admin_required
def gerenciar_categorias():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute('INSERT INTO categorias (nome, descricao) VALUES (?, ?)', (nome, descricao))
                conn.commit()
            flash('Categoria adicionada com sucesso!', 'success')
        except sqlite3.IntegrityError:
            flash('Categoria já existe', 'error')
        except Exception as e:
            flash(f'Erro ao adicionar categoria: {str(e)}', 'error')
        return redirect(url_for('admin_categorias'))

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM categorias')
        categorias = c.fetchall()
    return render_template('admin_categorias.html', categorias=categorias)

@app.route('/admin/categoria/<int:id>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def gerenciar_categoria(id):
    if request.method == 'DELETE':
        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute('SELECT COUNT(*) FROM produtos WHERE categoria_id=?', (id,))
                if c.fetchone()[0] > 0:
                    return jsonify({'error': 'Existem produtos nesta categoria'}), 400
                c.execute('DELETE FROM categorias WHERE id=?', (id,))
                conn.commit()
            return jsonify({'message': 'Categoria removida com sucesso'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    elif request.method == 'PUT':
        data = request.get_json()
        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute('UPDATE categorias SET nome=?, descricao=? WHERE id=?',
                          (data['nome'], data['descricao'], id))
                conn.commit()
            return jsonify({'message': 'Categoria atualizada com sucesso'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# -------------------- CARRINHO --------------------

@app.route('/carrinho')
@login_required
def ver_carrinho():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Busca o carrinho aberto do usuário ou cria um novo
        c.execute('''
            SELECT id FROM carrinhos 
            WHERE usuario_id = ? AND status = 'aberto'
        ''', (current_user.id,))
        carrinho = c.fetchone()
        if not carrinho:
            c.execute('''
                INSERT INTO carrinhos (usuario_id)
                VALUES (?)
            ''', (current_user.id,))
            conn.commit()
            carrinho_id = c.lastrowid
        else:
            carrinho_id = carrinho[0]
        # Busca os itens do carrinho
        c.execute('''
            SELECT 
                ic.id,
                ic.quantidade,
                ic.preco_unitario,
                p.id as produto_id,
                p.nome as produto_nome,
                REPLACE(
                    COALESCE(
                        (SELECT caminho FROM produto_midias 
                         WHERE produto_id = p.id AND tipo = 'imagem' 
                         ORDER BY ordem LIMIT 1),
                        p.imagem
                    ),
                    '\\',
                    '/'
                ) as produto_imagem
            FROM itens_carrinho ic
            JOIN produtos p ON ic.produto_id = p.id
            WHERE ic.carrinho_id = ?
        ''', (carrinho_id,))
        itens_raw = c.fetchall()
        itens = [
            {
                'id': item[0],
                'quantidade': item[1],
                'preco': float(item[2]),
                'produto_id': item[3],
                'nome': item[4],
                'imagem': item[5],
            }
            for item in itens_raw
        ]
        total = 0
        for item in itens:
            item['preco'] = float(item['preco'])  # Garante que o preço é float
            item['subtotal'] = item['quantidade'] * item['preco']  # Calcula o subtotal
            total += item['subtotal']  # Adiciona ao total
            
    # Se for AJAX, retorna JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'carrinho': itens, 'total': total})
    return render_template('carrinho.html', carrinho=itens, total=total)

@app.route('/carrinho/adicionar/<int:produto_id>', methods=['POST'])
@login_required
def adicionar_ao_carrinho(produto_id):
    quantidade = int(request.form.get('quantidade', 1))
    
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        
        # Verifica se o produto existe e tem estoque
        c.execute('SELECT preco, estoque FROM produtos WHERE id = ?', (produto_id,))
        produto = c.fetchone()
        
        if not produto:
            return jsonify({'error': 'Produto não encontrado'}), 404
            
        if produto[1] < quantidade:
            return jsonify({'error': 'Quantidade indisponível em estoque'}), 400
        
        # Busca ou cria carrinho
        c.execute('''
            SELECT id FROM carrinhos 
            WHERE usuario_id = ? AND status = 'aberto'
        ''', (current_user.id,))
        carrinho = c.fetchone()
        
        if not carrinho:
            c.execute('''
                INSERT INTO carrinhos (usuario_id)
                VALUES (?)
            ''', (current_user.id,))
            conn.commit()
            carrinho_id = c.lastrowid
        else:
            carrinho_id = carrinho[0]
        
        # Verifica se o produto já está no carrinho
        c.execute('''
            SELECT id, quantidade FROM itens_carrinho
            WHERE carrinho_id = ? AND produto_id = ?
        ''', (carrinho_id, produto_id))
        item = c.fetchone()
        
        if item:
            # Atualiza a quantidade
            nova_quantidade = item[1] + quantidade
            if nova_quantidade > produto[1]:  # Verifica estoque
                return jsonify({'error': 'Quantidade indisponível em estoque'}), 400
                
            c.execute('''
                UPDATE itens_carrinho
                SET quantidade = ?
                WHERE id = ?
            ''', (nova_quantidade, item[0]))
        else:
            # Adiciona novo item
            c.execute('''
                INSERT INTO itens_carrinho (carrinho_id, produto_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?)
            ''', (carrinho_id, produto_id, quantidade, produto[0]))
        
        conn.commit()
        
    flash('Produto adicionado ao carrinho!', 'success')
    return redirect(url_for('ver_carrinho'))

@app.route('/carrinho/atualizar/<int:item_id>', methods=['PUT'])
@login_required
def atualizar_item_carrinho(item_id):
    data = request.get_json()
    quantidade = int(data.get('quantidade', 1))
    
    if quantidade < 1:
        return jsonify({'error': 'Quantidade inválida'}), 400
    
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        
        # Verifica se o item pertence ao carrinho do usuário
        c.execute('''
            SELECT ic.produto_id, p.estoque
            FROM itens_carrinho ic
            JOIN carrinhos c ON ic.carrinho_id = c.id
            JOIN produtos p ON ic.produto_id = p.id
            WHERE ic.id = ? AND c.usuario_id = ? AND c.status = 'aberto'
        ''', (item_id, current_user.id))
        item = c.fetchone()
        
        if not item:
            return jsonify({'error': 'Item não encontrado'}), 404
            
        if item[1] < quantidade:
            return jsonify({'error': 'Quantidade indisponível em estoque'}), 400
        
        c.execute('''
            UPDATE itens_carrinho
            SET quantidade = ?
            WHERE id = ?
        ''', (quantidade, item_id))
        conn.commit()
        
    return jsonify({'message': 'Quantidade atualizada'}), 200

@app.route('/carrinho/remover/<int:item_id>', methods=['DELETE'])
@login_required
def remover_do_carrinho(item_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        
        # Verifica se o item pertence ao carrinho do usuário
        c.execute('''
            SELECT ic.id
            FROM itens_carrinho ic
            JOIN carrinhos c ON ic.carrinho_id = c.id
            WHERE ic.id = ? AND c.usuario_id = ? AND c.status = 'aberto'
        ''', (item_id, current_user.id))
        
        if not c.fetchone():
            return jsonify({'error': 'Item não encontrado'}), 404
        
        c.execute('DELETE FROM itens_carrinho WHERE id = ?', (item_id,))
        conn.commit()
        
    return jsonify({'message': 'Item removido do carrinho'}), 200

# -------------------- PEDIDOS --------------------

@app.route('/finalizar-compra', methods=['GET', 'POST'])
@login_required
def finalizar_compra():
    if request.method == 'POST':
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            
            # Busca o carrinho aberto do usuário
            c.execute('''
                SELECT c.id, COUNT(ic.id) as total_itens
                FROM carrinhos c
                LEFT JOIN itens_carrinho ic ON c.id = ic.carrinho_id
                WHERE c.usuario_id = ? AND c.status = 'aberto'
                GROUP BY c.id
            ''', (current_user.id,))
            carrinho = c.fetchone()
            
            if not carrinho or carrinho[1] == 0:
                flash('Seu carrinho está vazio', 'error')
                return redirect(url_for('ver_carrinho'))
            
            # Coleta dados do endereço
            endereco = request.form['endereco']
            cidade = request.form['cidade']
            estado = request.form['estado']
            cep = request.form['cep']
            
            # Cria o pedido
            c.execute('''
                INSERT INTO pedidos (usuario_id, carrinho_id, endereco, cidade, estado, cep)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (current_user.id, carrinho[0], endereco, cidade, estado, cep))
            
            # Atualiza o status do carrinho
            c.execute('''
                UPDATE carrinhos
                SET status = 'fechado'
                WHERE id = ?
            ''', (carrinho[0],))
            
            # Atualiza o estoque dos produtos
            c.execute('''
                UPDATE produtos
                SET estoque = estoque - (
                    SELECT quantidade 
                    FROM itens_carrinho 
                    WHERE carrinho_id = ? AND produto_id = produtos.id
                )
                WHERE id IN (
                    SELECT produto_id 
                    FROM itens_carrinho 
                    WHERE carrinho_id = ?
                )
            ''', (carrinho[0], carrinho[0]))
            
            conn.commit()
            
            flash('Pedido realizado com sucesso!', 'success')
            return redirect(url_for('meus_pedidos'))
            
    return render_template('finalizar-compra.html')

@app.route('/meus-pedidos')
@login_required
def meus_pedidos():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT 
                p.id,
                p.data_pedido,
                p.status,
                COUNT(ic.id) as total_itens,
                SUM(ic.quantidade * ic.preco_unitario) as valor_total,
                p.endereco,
                p.cidade,
                p.estado,
                p.cep
            FROM pedidos p
            JOIN carrinhos c ON p.carrinho_id = c.id
            JOIN itens_carrinho ic ON c.id = ic.carrinho_id
            WHERE p.usuario_id = ?
            GROUP BY p.id
            ORDER BY p.data_pedido DESC
        ''', (current_user.id,))
        pedidos = c.fetchall()
        
    return render_template('meus-pedidos.html', pedidos=pedidos)

@app.route('/pedido/<int:id>')
@login_required
def detalhes_pedido(id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        
        # Busca informações do pedido
        c.execute('''
            SELECT 
                p.*,
                SUM(ic.quantidade * ic.preco_unitario) as valor_total
            FROM pedidos p
            JOIN carrinhos c ON p.carrinho_id = c.id
            JOIN itens_carrinho ic ON c.id = ic.carrinho_id
            WHERE p.id = ? AND p.usuario_id = ?
            GROUP BY p.id
        ''', (id, current_user.id))
        pedido = c.fetchone()
        
        if not pedido:
            flash('Pedido não encontrado', 'error')
            return redirect(url_for('meus_pedidos'))
        
        # Busca itens do pedido
        c.execute('''
            SELECT 
                p.nome as produto_nome,
                p.imagem as produto_imagem,
                ic.quantidade,
                ic.preco_unitario,
                (ic.quantidade * ic.preco_unitario) as subtotal
            FROM itens_carrinho ic
            JOIN produtos p ON ic.produto_id = p.id
            JOIN carrinhos c ON ic.carrinho_id = c.id
            JOIN pedidos pd ON c.id = pd.carrinho_id
            WHERE pd.id = ?
        ''', (id,))
        itens = c.fetchall()
        
    return render_template('pedido.html', pedido=pedido, itens=itens)

@app.route('/admin/pedidos')
@login_required
@admin_required
def admin_pedidos():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT 
                p.id,
                u.username,
                p.data_pedido,
                p.status,
                COUNT(ic.id) as total_itens,
                SUM(ic.quantidade * ic.preco_unitario) as valor_total,
                p.endereco,
                p.cidade,
                p.estado,
                p.cep
            FROM pedidos p
            JOIN usuarios u ON p.usuario_id = u.id
            JOIN carrinhos c ON p.carrinho_id = c.id
            JOIN itens_carrinho ic ON c.id = ic.carrinho_id
            GROUP BY p.id
            ORDER BY p.data_pedido DESC
        ''')
        pedidos = c.fetchall()
        
    return render_template('admin.html', pedidos=pedidos)

@app.route('/admin/pedido/<int:id>', methods=['PUT'])
@login_required
@admin_required
def atualizar_status_pedido(id):
    data = request.get_json()
    novo_status = data.get('status')
    
    if novo_status not in ['pendente', 'em_processamento', 'enviado', 'entregue', 'cancelado']:
        return jsonify({'error': 'Status inválido'}), 400
        
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            UPDATE pedidos
            SET status = ?
            WHERE id = ?
        ''', (novo_status, id))
        conn.commit()
        
    return jsonify({'message': 'Status do pedido atualizado com sucesso'}), 200

# -------------------- PÁGINAS ESTÁTICAS --------------------

@app.route('/contato')
def contato():
    return render_template('contato.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/privacidade')
def privacidade():
    return render_template('privacidade.html')

@app.route('/termos')
def termos():
    return render_template('termos.html')


# -------------------- EXECUÇÃO --------------------
if __name__ == '__main__':
    # Usar variáveis de ambiente para configuração de produção
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
