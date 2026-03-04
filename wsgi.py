import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# ===============================
# Caminho do projeto e virtualenv
# ===============================
project_home = '/home/Farelojp/mysite'
venv_path = '/home/Farelojp/venv/lib/python3.13/site-packages'

for path in (project_home, venv_path):
    if path not in sys.path:
        sys.path.insert(0, path)

# ===============================
# Variáveis de ambiente
# ===============================
os.environ['FLASK_ENV'] = 'production'
os.environ['PYTHONANYWHERE_DOMAIN'] = 'pythonanywhere.com'

# ===============================
# Configuração de logs
# ===============================
log_dir = os.path.join(project_home, 'logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, 'farelojp_error.log')
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('farelojp')
file_handler = RotatingFileHandler(log_file, maxBytes=100000, backupCount=10)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)
logger.info('Farelojp WSGI startup')

try:
    # ===============================
    # Importa a aplicação Flask
    # ===============================
    from app import app as application

    # ===============================
    # Configuração de logs na aplicação
    # ===============================
    application.logger.addHandler(file_handler)
    application.logger.setLevel(logging.DEBUG)

    # ===============================
    # Configuração de pastas estáticas e uploads
    # ===============================
    application.static_folder = os.path.join(project_home, 'static')
    application.config['UPLOAD_FOLDER'] = os.path.join(project_home, 'static', 'uploads', 'produtos')
    application.config['PRODUTOS_FOLDER'] = os.path.join(project_home, 'static', 'produtos')
    application.config['DB_PATH'] = os.path.join(project_home, 'usuarios.db')

    # Criação das pastas se não existirem (somente dentro de mysite)
    for folder in [application.config['UPLOAD_FOLDER'], application.config['PRODUTOS_FOLDER'], log_dir]:
        os.makedirs(folder, exist_ok=True)

    # ===============================
    # Verificação de permissões básicas
    # ===============================
    if not os.access(application.config['DB_PATH'], os.R_OK | os.W_OK):
        logger.warning(f"Não é possível ler/escrever no banco de dados: {application.config['DB_PATH']}")

    logger.info('Configurações da aplicação:')
    logger.info(f"SECRET_KEY configurada: {'SECRET_KEY' in application.config}")
    logger.info(f"DB_PATH: {application.config['DB_PATH']}")
    logger.info(f"UPLOAD_FOLDER: {application.config['UPLOAD_FOLDER']}")
    logger.info(f"PRODUTOS_FOLDER: {application.config['PRODUTOS_FOLDER']}")
    logger.info(f"DEBUG: {application.config.get('DEBUG', False)}")

    # ===============================
    # Middleware para log de requisições
    # ===============================
    class RequestLoggerMiddleware:
        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            path = environ.get('PATH_INFO', '')
            method = environ.get('REQUEST_METHOD', '')
            logger.info(f'Request: {method} {path}')

            def custom_start_response(status, headers, *args, **kwargs):
                logger.info(f'Response: {status}')
                return start_response(status, headers, *args, **kwargs)

            try:
                return self.app(environ, custom_start_response)
            except Exception as e:
                logger.error(f'Erro na requisição: {str(e)}', exc_info=True)
                raise e

    # Ativa o middleware
    application.wsgi_app = RequestLoggerMiddleware(application.wsgi_app)

    logger.info('Aplicação inicializada com sucesso')

except Exception as e:
    logger.error(f'Erro ao inicializar aplicação: {str(e)}', exc_info=True)
    raise e
