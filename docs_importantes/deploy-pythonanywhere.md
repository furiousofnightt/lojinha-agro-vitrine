# Guia de Deploy no PythonAnywhere

Este guia contém todos os passos necessários para fazer o deploy da aplicação no PythonAnywhere.

## 1. Preparação Inicial

1. Acesse [www.pythonanywhere.com](https://www.pythonanywhere.com) e faça login
2. No dashboard, vá para a seção "Web"
3. Clique em "Add a new web app"
4. Escolha "Manual configuration"
5. Selecione Python 3.11 (ou versão mais recente disponível)

## 2. Configuração do Código

1. Abra um console Bash no PythonAnywhere
2. Configure o diretório do projeto:
```bash
cd /home/lojinha-agro-vitrine/mysite
mv lojinha-agro/* .
rm -rf lojinha-agro-vitrine
```

3. Limpe qualquer ambiente virtual existente:
```bash
rm -rf venv
```

4. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configuração do Aplicativo Web

1. Na seção "Code" da página Web:
   - Source code: `/home/lojinha-agro-vitrine/mysite`
   - Working directory: `/home/lojinha-agro-vitrine/mysite`
   - WSGI configuration file: `/var/www/lojinha-agro-vitrine_pythonanywhere_com_wsgi.py`

2. Na seção "Virtualenv":
   - Digite: `/home/lojinha-agro-vitrine/mysite/venv`

## 4. Configuração do WSGI

1. Clique no link do arquivo WSGI na seção "Code"
2. Apague todo o conteúdo existente
3. Cole o conteúdo do arquivo `wsgi-para-pythonanywhere.py` (disponível nesta pasta)

**IMPORTANTE**: O conteúdo do arquivo `wsgi-para-pythonanywhere.py` é o código WSGI principal que deve ser colado no painel de configuração WSGI do PythonAnywhere.

## 5. Configuração dos Diretórios Estáticos

1. Na seção "Static files" adicione:
   - URL: `/static/`
   - Directory: `/home/lojinha-agro-vitrine/mysite/static`

2. Adicione também para uploads:
   - URL: `/static/uploads/`
   - Directory: `/home/lojinha-agro-vitrine/mysite/static/uploads`

## 6. Permissões e Diretórios

1. Crie os diretórios necessários para uploads:
```bash
mkdir -p ~/mysite/static/uploads/produtos
chmod 775 ~/mysite/static/uploads/produtos
```

## 7. Inicialização do Banco de Dados

1. Execute o script de reset do banco (apenas na primeira vez):
```bash
cd ~/mysite
python utils/reset_db.py
```

## 8. Finalização

1. Clique no botão verde "Reload" na página Web
2. Seu site estará disponível em: `seuusuario.pythonanywhere.com`

## Manutenção e Updates

### Para verificar usuários:
```bash
python utils/manage_users.py
```

### Para resetar o banco (cuidado: apaga todos os dados):
```bash
python utils/reset_db.py
```

### Para atualizar o código:
1. No PythonAnywhere, use o botão "Files" para fazer upload dos novos arquivos
2. Substitua os arquivos antigos pelos novos
3. Clique em "Reload" na página Web para aplicar as mudanças

## Troubleshooting

Se encontrar problemas:

1. Verifique os logs de erro na seção "Web" -> "Error log"
2. Certifique-se que todos os diretórios têm as permissões corretas
3. Verifique se o ambiente virtual está ativado ao instalar pacotes
4. Confirme que o caminho do projeto está correto no arquivo WSGI

## Credenciais Admin Padrão

Após executar `reset_db.py`:
- Email: admin@exemplo.com
- Senha: sua_senha_segura_aqui
- Ou o admin que tenha editado no init_db.py