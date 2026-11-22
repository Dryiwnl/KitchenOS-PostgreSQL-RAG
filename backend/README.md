# Backend do KitchenOS

Backend em Python, FastAPI, psycopg2 e PostgreSQL.

Funcionalidades atuais:

- CRUD de categorias, fornecedores e produtos;
- dashboard com agregações reais do banco;
- listagens de receitas, pedidos e perdas;
- ficha técnica com ingredientes e sub-receitas expandidas;
- cálculo de custos pelos preços das compras mais recentes;
- embeddings multilíngues reais de 384 dimensões (`paraphrase-multilingual-MiniLM-L12-v2`);
- busca semântica por similaridade de cosseno;
- projeção PCA tridimensional e vizinhos semânticos;
- chat com IA (RAG) integrado à API do Gemini com fallback automático de modelos;
- CRUD genérico e validado das 14 tabelas acadêmicas;
- execução somente-leitura das três consultas da pasta `database/queries`;
- criação, carga inicial e eliminação protegida das tabelas.

## Executar

Na raiz do projeto (com o arquivo `.env` configurado):

    $env:PGCLIENTENCODING="UTF8"
    .\.venv\Scripts\python.exe -m uvicorn backend.api:app --reload

- API: `http://127.0.0.1:8000`;
- documentação interativa: `http://127.0.0.1:8000/docs`.

## Arquivos

- `conexao.py`: conexão com PostgreSQL e leitura do `.env`;
- `api.py`: endpoints e operações SQL;
- `administracao.py`: criação, carga inicial e eliminação das tabelas;
- `embeddings.py`: geração de vetores, busca semântica e projeção PCA 3D;
- `chat_ai.py`: integração com o Gemini, fallback de modelos e persistência do histórico;
- `requirements.txt`: dependências Python.