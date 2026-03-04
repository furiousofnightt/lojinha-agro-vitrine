# lojinha-agro - Sistema E-commerce

Sistema de e-commerce especializado em produtos agropecuários, rações e suplementos para animais, desenvolvido com Flask. Projetado para uma experiência de compra intuitiva e segura.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

[English](README_en.md) | [Português](README.md)

## 🚀 Características Principais

- **Sistema de autenticação completo**
  - Login/Registro de usuários
  - Recuperação de senha com pergunta de segurança
  - Perfil de usuário personalizável
  - Sistema anti-bruteforce integrado

- **Painel Administrativo Robusto**
  - Gerenciamento de produtos e categorias
  - Controle de usuários e permissões
  - Upload de múltiplas imagens por produto
  - Suporte a vídeos de demonstração
  - Dashboard com métricas importantes

- **Catálogo Inteligente**
  - Categorização por tipo de animal
  - Filtros avançados de busca
  - Visualização em grid responsivo
  - Imagens otimizadas para carregamento rápido

- **Experiência de Compra Otimizada**
  - Carrinho de compras intuitivo
  - Sistema de pedidos completo
  - Histórico de compras
  - Múltiplas formas de pagamento

## 🛠️ Tecnologias

- Python 3.11+
- Flask Framework
- SQLite3
- HTML5/CSS3
- JavaScript
- Bootstrap 5

## 📋 Pré-requisitos

- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)
- Git

## 🔧 Instalação Local

1. Clone o repositório:
```bash
git clone https://github.com/furiousofnightt/lojinha-agro-vitrine.git
cd lojinha-agro
```

2. Crie e ative um ambiente virtual:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. Inicialize o banco de dados:
```bash
python init_db.py
```

6. Inicie o servidor:
```bash
python app.py
```

## 🚀 Deploy

Instruções detalhadas para deploy no PythonAnywhere estão disponíveis em [docs_importantes/deploy-pythonanywhere.md](docs_importantes/deploy-pythonanywhere.md)

## 📦 Estrutura do Projeto

```
lojinha-agro/
├── app.py                 # Aplicação principal Flask
├── forms.py              # Formulários WTForms
├── init_db.py           # Inicialização do banco
├── requirements.txt     # Dependências
├── static/              # Arquivos estáticos
│   ├── css/            # Estilos
│   ├── images/         # Imagens do sistema
│   └── uploads/        # Upload de produtos
├── templates/          # Templates HTML
├── utils/             # Scripts utilitários
└── usuarios.db        # Banco SQLite
```

## Segurança

- Proteção contra CSRF em todos os formulários
- Senhas hasheadas com werkzeug.security
- Limitação de taxa em endpoints sensíveis
- Validação de entrada em todos os campos
- Sessões seguras com Flask-Login
- Upload de arquivos com validação de tipo

## Customização

O sistema é altamente customizável através de:
- Variáveis CSS globais (`variables.css`) OBS: "NÃO EM TODOS CSS" , ALGUNS TEM SEUS ROOT PROPRIOS.
- Templates modulares
- Configurações no arquivo `app.py`
- Estilos específicos por página

## Contato e Suporte

Para suporte técnico ou dúvidas sobre o sistema:
- Email: henriquecosta1322d@gmail.com
- WhatsApp: (83) 986711188

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## Funcionalidades

### Área Pública
- Visualização de produtos e categorias
- Registro e login de usuários
- Recuperação de senha
- Carrinho de compras
- Finalização de pedidos

### Área Administrativa
- Gerenciamento de produtos
- Gerenciamento de categorias
- Gerenciamento de usuários
- Visualização de pedidos

## Segurança

- Proteção contra CSRF
- Senhas criptografadas
- Sessões seguras
- Validação de formulários
- Proteção contra uploads maliciosos
- Variáveis de ambiente para segredos
# Observações

- O deploy no Vercel é serverless: arquivos enviados (imagens, vídeos) são temporários e podem ser apagados a cada novo deploy.
- Para produção persistente, use um serviço de storage externo (ex: AWS S3, Google Cloud Storage).
- O banco de dados SQLite é reiniciado a cada build/deploy no Vercel.
