# Backend do KitchenOS

Backend em Python, FastAPI, psycopg2 e PostgreSQL.

Funcionalidades atuais:

- CRUD de categorias, fornecedores e produtos;
- listagens de receitas, pedidos e perdas;
- ficha técnica com ingredientes e sub-receitas expandidas;
- cálculo de custos pelos preços das compras mais recentes;
- embeddings multilíngues reais de 384 dimensões;
- busca semântica por similaridade de cosseno.
- projeção PCA tridimensional e vizinhos semânticos.
- CRUD genérico e validado das 14 tabelas acadêmicas;
- execução somente-leitura das três consultas da pasta `database/queries`;
- criação, carga inicial e eliminação protegida das tabelas.

## Executar

Na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.api:app --reload
```

- API: `http://127.0.0.1:8000`;
- documentação interativa: `http://127.0.0.1:8000/docs`.

## Arquivos

- `conexao.py`: conexão com PostgreSQL e leitura do `.env`;
- `api.py`: configuração principal da aplicação web;
- `administracao.py`: rotas curtas que ligam o frontend às operações;
- `crud.py`: funções `select`, `insert`, `update` e `delete`;
- `metadados.py`: colunas, chaves e rótulos das 14 tabelas;
- `consultas.py`: execução das três consultas obrigatórias;
- `gerenciar_banco.py`: criação, carga inicial e eliminação das tabelas;
- `embeddings.py`: geração e busca semântica;
- `requirements.txt`: dependências Python.
