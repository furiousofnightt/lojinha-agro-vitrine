from flask import current_app
from werkzeug.utils import secure_filename
import os
import time
import uuid
from PIL import Image

# Extensões permitidas
ALLOWED_EXTENSIONS_IMG = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_EXTENSIONS_VIDEO = {'mp4', 'webm', 'mov', 'avi'}

def criar_diretorios_upload():
    """Cria os diretórios necessários para uploads"""
    # Diretório base para uploads (ajustável para PythonAnywhere)
    if os.environ.get('PYTHONANYWHERE_DOMAIN'):
        base_dir = '/home/lojinha-agro-vitrine/mysite/static/uploads/produtos'
    else:
        base_dir = os.path.join('static', 'uploads', 'produtos')
    
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def allowed_file(filename, allowed_exts):
    """Verifica se a extensão do arquivo é permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts

def validar_imagem(arquivo):
    """Verifica se o arquivo é uma imagem válida"""
    try:
        img = Image.open(arquivo)
        img.verify()
        arquivo.seek(0)
        return True
    except Exception:
        arquivo.seek(0)
        return False

def salvar_arquivo(arquivo, tipo='imagem'):
    """
    Salva um arquivo de upload de forma segura.
    Retorna o caminho relativo do arquivo salvo.
    tipo: 'imagem' ou 'video'
    """
    if not arquivo or not arquivo.filename:
        return None

    upload_dir = criar_diretorios_upload()
    nome_original = secure_filename(arquivo.filename)
    extensao = os.path.splitext(nome_original)[1].lower()

    # Validação de tipo
    if tipo == 'imagem':
        if not allowed_file(nome_original, ALLOWED_EXTENSIONS_IMG):
            return None
        if not validar_imagem(arquivo):
            return None
    elif tipo == 'video':
        if not allowed_file(nome_original, ALLOWED_EXTENSIONS_VIDEO):
            return None
    else:
        raise ValueError("Tipo inválido. Use 'imagem' ou 'video'.")

    # Gera nome único
    timestamp = str(int(time.time()))
    nome_unico = f"{timestamp}_{uuid.uuid4().hex[:8]}{extensao}"
    caminho_completo = os.path.join(upload_dir, nome_unico)

    # Salva o arquivo
    arquivo.save(caminho_completo)

    # Retorna caminho relativo para salvar no banco
    return os.path.join('uploads', 'produtos', nome_unico)
