#!/bin/bash

# Definir variáveis
PROJECT_DIR="/home/fury765/mysite/notorios-informatica"
VENV_DIR="/home/fury765/.virtualenvs/myenv"
PYTHON_VERSION="3.11.11"

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Iniciando setup do projeto ===${NC}"

# 1. Criar virtualenv
echo -e "\n${GREEN}1. Configurando virtualenv...${NC}"
python$PYTHON_VERSION -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# 2. Instalar dependências
echo -e "\n${GREEN}2. Instalando dependências...${NC}"
pip install -r $PROJECT_DIR/requirements.txt

# 3. Criar diretórios necessários
echo -e "\n${GREEN}3. Criando diretórios...${NC}"
mkdir -p $PROJECT_DIR/static/uploads/produtos

# 4. Configurar permissões
echo -e "\n${GREEN}4. Configurando permissões...${NC}"
chmod -R 775 $PROJECT_DIR/static/uploads
chown -R fury765:www-data $PROJECT_DIR/static/uploads

# 5. Configurar banco de dados
echo -e "\n${GREEN}5. Configurando banco de dados...${NC}"
python3 $PROJECT_DIR/init_db.py

echo -e "\n${GREEN}=== Setup concluído! ===${NC}"
echo -e "Não esqueça de:"
echo -e "1. Configurar o arquivo .env"
echo -e "2. Recarregar a aplicação no painel do PythonAnywhere"