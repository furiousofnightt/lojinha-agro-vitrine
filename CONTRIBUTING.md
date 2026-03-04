# Contribuindo com o lojinha-agro

Primeiramente, obrigado por considerar contribuir com o projeto! 

## Como contribuir

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Ambiente de desenvolvimento

1. Clone o repositório
2. Crie um ambiente virtual:
```bash
python -m venv venv
```
3. Ative o ambiente virtual:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```
4. Instale as dependências:
```bash
pip install -r requirements.txt
```
5. Copie `.env.example` para `.env` e configure as variáveis

## Estrutura do projeto

```
lojinha-agro/
├── app.py                 # Aplicação principal Flask
├── forms.py              # Formulários WTForms
├── init_db.py           # Inicialização do banco
└── requirements.txt     # Dependências
```

## Guidelines

### Código
- Siga PEP 8
- Escreva docstrings para funções e classes
- Mantenha funções pequenas e focadas
- Use nomes descritivos para variáveis e funções

### Commits
- Use mensagens de commit claras e descritivas
- Cada commit deve representar uma mudança lógica
- Prefixe commits com tipo: feat:, fix:, docs:, etc.

### Pull Requests
- Descreva claramente o que sua PR faz
- Referencie issues relacionadas
- Inclua screenshots para mudanças visuais
- Certifique-se que todos os testes passam

## Reportando Bugs

Use o template de bug report e inclua:
- Passos detalhados para reproduzir
- Comportamento esperado vs atual
- Screenshots se aplicável
- Versão do Python e dependências

## Propondo Funcionalidades

Use o template de feature request e inclua:
- Descrição detalhada da funcionalidade
- Por que ela é necessária
- Como ela deve funcionar
- Mockups ou exemplos se possível