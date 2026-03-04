# lojinha-agro: Guia de Desenvolvimento

## Visão Geral da Arquitetura

O projeto segue uma arquitetura MVC (Model-View-Controller) adaptada para Flask:

```
lojinha-agro/
├── app.py                # Aplicação principal e rotas
├── forms.py             # Formulários e validação
├── models/              # Modelos de dados
└── templates/           # Templates HTML (Views)
```

## Stack Tecnológico

### Backend
- Python 3.11+
- Flask 2.0+
- SQLite3
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- Werkzeug

### Frontend
- HTML5
- CSS3
- JavaScript
- Bootstrap 5
- Font Awesome
- jQuery

## Guias de Desenvolvimento

### Estilo de Código

#### Python
- Siga o PEP 8
- Use tipagem estática quando possível
- Docstrings para todas as funções/classes
- Nomes de variáveis descritivos

```python
def calcular_total_pedido(pedido_id: int) -> float:
    """
    Calcula o valor total de um pedido.

    Args:
        pedido_id (int): ID do pedido

    Returns:
        float: Valor total do pedido
    """
    # implementação
```

#### HTML/Templates
- Use indentação de 2 espaços
- IDs únicos e descritivos
- Classes semânticas
- Comentários para blocos complexos

```html
<!-- Seção de produtos em destaque -->
<section id="produtos-destaque" class="produtos-grid">
  {% for produto in produtos_destaque %}
    {% include 'components/produto-card.html' %}
  {% endfor %}
</section>
```

#### CSS
- BEM (Block Element Modifier)
- Variáveis para cores/tamanhos
- Media queries organizadas
- Comentários para seções

```css
/* Componente: Card de Produto */
.produto-card {
  /* ... */
}

.produto-card__titulo {
  /* ... */
}
```

### Banco de Dados

#### Migrations
- Use `flask db migrate` para criar migrations
- Teste migrations antes do commit
- Documente mudanças complexas

#### Queries
- Use models SQLAlchemy
- Evite N+1 queries
- Index campos de busca

### Segurança

#### Autenticação
- Sempre use `login_required`
- Hash de senhas com Werkzeug
- Proteção CSRF em forms

#### Uploads
- Validação de tipo MIME
- Limites de tamanho
- Sanitização de nomes

### Testing

#### Testes Unitários
```python
def test_calcular_total_pedido():
    # Arrange
    pedido = criar_pedido_teste()
    
    # Act
    total = calcular_total_pedido(pedido.id)
    
    # Assert
    assert total == 100.0
```

#### Testes de Integração
- Use fixtures Flask
- Mock serviços externos
- Test casos de erro

## Deploy

### Checklist
1. Migrations atualizadas
2. Arquivos estáticos compilados
3. Variáveis de ambiente
4. Logs configurados
5. Backup do banco

### Monitoramento
- Configure logs de erro
- Métricas de performance
- Alertas de erro

## Recursos

### Documentação
- [Flask](https://flask.palletsprojects.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Flask-Login](https://flask-login.readthedocs.io/)

### Ferramentas
- VS Code + extensões Python
- SQLite Browser
- Postman/Insomnia

## FAQ

### Problemas Comuns

1. Erro de importação circular
```python
# Solução: Use imports dinâmicos
from . import db

def init_app(app):
    from .models import User
```

2. Sessão SQLAlchemy expirada
```python
# Solução: Refresh session
db.session.refresh(obj)
```

### Otimizações

1. Caching
```python
from flask_caching import Cache

@cache.memoize(timeout=300)
def get_produtos_destaque():
    return Produto.query.filter_by(destaque=True).all()
```

2. Eager Loading
```python
produtos = Produto.query.options(
    joinedload(Produto.categoria)
).all()
```