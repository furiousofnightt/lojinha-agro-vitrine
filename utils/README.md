# Utilitários do Sistema

Este diretório contém scripts utilitários para gerenciamento e manutenção do sistema.

## Scripts Disponíveis

### `manage_users.py`
Script interativo para gerenciamento de usuários do sistema.

**Funcionalidades:**
- Criar usuário admin (apenas se não existir)
- Listar todos os usuários do sistema
- Visualização detalhada de cada usuário (ID, username, email, status admin, status banido)

**Uso:**
```bash
python manage_users.py
```

### `reset_db.py`
Script para reinicialização completa do banco de dados.

**ATENÇÃO**: Este script apaga todos os usuários existentes!

**Funcionalidades:**
- Cria/verifica todas as tabelas do banco
- Remove todos os usuários existentes
- Cria um novo usuário admin padrão
- Garante que a coluna 'banned' existe na tabela de usuários

**Uso:**
```bash
python reset_db.py
```

**Credenciais do Admin Padrão:**
- Email: admin@exemplo.com
- Senha: sua_senha_segura_aqui
- Ou o que tenha escolhido

## Quando Usar Cada Script

### Use `manage_users.py` quando:
- Precisar visualizar os usuários do sistema
- Criar um novo admin sem afetar dados existentes
- Fazer manutenção rotineira de usuários

### Use `reset_db.py` quando:
- Inicializar o sistema pela primeira vez
- Precisar fazer um reset completo do banco de dados
- Tiver certeza que pode apagar todos os usuários existentes

## Observações de Segurança
- Sempre faça backup do banco antes de usar `reset_db.py`
- O `manage_users.py` é seguro para uso em produção
- Mantenha as credenciais de admin em local seguro