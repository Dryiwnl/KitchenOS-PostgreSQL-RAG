# Trabalho Final de Banco de Dados I

> Relatório acadêmico: [`docs/relatorio.md`](docs/relatorio.md)  
> Modelagens: [conceitual](docs/modelagem-conceitual.md) e
> [lógica](docs/modelagem-logica.md)

Este projeto representa o banco de dados de um restaurante. Ele permite
armazenar produtos, fornecedores, compras, receitas, clientes, pedidos e perdas
de estoque.

O banco foi mantido no nível do conteúdo apresentado nas aulas de SQL. O
backend foi desenvolvido em Python e FastAPI, e o frontend em React e
TypeScript.

## Arquivos importantes

    database/
    ├── ddl/
    │   ├── 01_create_tables.sql     # cria as 14 tabelas principais
    │   ├── 02_create_embeddings.sql # cria a tabela auxiliar de vetores das receitas
    │   └── 03_create_chat.sql       # cria a tabela auxiliar de histórico do chat
    ├── seeds/
    │   └── 02_insert_data.sql       # insere dados de exemplo
    └── queries/
        ├── 01_custos_receitas.sql   # custos por receita
        ├── 02_vendas.sql            # vendas pagas por cliente
        └── 03_estoque_perdas.sql    # valor das perdas de estoque

    backend/
    ├── api.py                       # API e CRUDs dinâmicos
    ├── chat_ai.py                   # integração com Gemini e RAG
    ├── conexao.py                   # conexão com PostgreSQL
    ├── embeddings.py                # geração de vetores e projeção PCA 3D
    └── requirements.txt             # bibliotecas Python

    frontend/
    ├── src/App.tsx                  # telas e integração com a API
    ├── src/styles.css             # identidade visual do KitchenOS
    └── package.json                 # dependências React

    iniciar.ps1                      # script automatizado de inicialização (Windows)
    .env.example                     # modelo de configuração local

## Pré-requisitos na máquina

Para executar o projeto em um computador Windows novo, instale:

- **PostgreSQL 16 ou superior** (com pgAdmin e Command Line Tools);
- **Python 3.10 ou superior**;
- **Node.js 18 ou superior (LTS)**;
- **Git** (caso clone o repositório via terminal).

## Executar a aplicação

### Forma 1: Automática (recomendada)

Na primeira execução, crie o arquivo `.env` a partir do modelo e adicione sua
chave da API do Gemini (opcional, necessária apenas para o Chat IA — ou preencha
depois pela própria tela do Chat IA):

    Copy-Item .env.example .env

O `.env.example` já vem pré-configurado para o banco isolado do projeto na porta
`5433`:

    DB_HOST=localhost
    DB_PORT=5433
    DB_NAME=restaurante
    DB_USER=kitchenos
    DB_PASSWORD=
    GEMINI_API_KEY=

Depois, abra o PowerShell na pasta raiz do projeto e execute:

    .\iniciar.ps1

*(Caso o PowerShell bloqueie a execução de scripts, rode `powershell -ExecutionPolicy Bypass -File .\iniciar.ps1`).*

Na **primeira execução**, esse script localiza automaticamente o PostgreSQL
instalado, cria o banco exclusivo do projeto em `.postgres-data` (porta `5433`),
cria o banco `restaurante`, executa os 4 scripts `.sql`, cria a `.venv`, instala
as dependências do backend e do frontend, baixa o modelo de embeddings e gera os
vetores iniciais das receitas. Nas execuções seguintes, ele apenas inicia o
banco, abre backend e frontend em terminais separados e abre
`http://localhost:5173` no navegador.

Para encerrar a aplicação, feche os terminais abertos ou pressione `Ctrl + C` em
cada um deles.

### Forma 2: Manual (usando o serviço padrão do PostgreSQL / pgAdmin)

Caso prefira utilizar o serviço padrão do PostgreSQL já ativo no Windows (porta `5432`):

1. **Configure o `.env`** com a porta `5432`, o usuário `postgres` e a senha
   definida na instalação do PostgreSQL:

       DB_HOST=localhost
       DB_PORT=5432
       DB_NAME=restaurante
       DB_USER=postgres
       DB_PASSWORD=sua_senha_do_postgresql
       GEMINI_API_KEY=

2. **Crie o banco e rode os scripts SQL pelo pgAdmin:**
   1. Abra o pgAdmin e crie um banco chamado `restaurante`.
   2. Clique com o botão direito no banco e abra **Query Tool**.
   3. Abra e execute (`Execute / F5`), nesta ordem exata:
      1. `database/ddl/01_create_tables.sql`
      2. `database/seeds/02_insert_data.sql`
      3. `database/ddl/02_create_embeddings.sql`
      4. `database/ddl/03_create_chat.sql`

   Para confirmar que os dados foram inseridos, execute:

       SELECT * FROM produto;
       SELECT * FROM receita;
       SELECT * FROM pedido;

3. **Instale as dependências e gere os embeddings (apenas na primeira vez):**

       py -m venv .venv
       .\.venv\Scripts\python.exe -m pip install --upgrade pip
       .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
       .\.venv\Scripts\python.exe -c "from backend.embeddings import gerar_embeddings; gerar_embeddings()"

   *(Caso o launcher `py` não esteja disponível, use `python -m venv .venv` na primeira linha).*

       cd frontend
       npm install
       cd ..

4. **Abra dois terminais na pasta raiz do projeto para iniciar os servidores:**

   Terminal do backend:

       $env:PGCLIENTENCODING="UTF8"
       .\.venv\Scripts\python.exe -m uvicorn backend.api:app --reload

   Terminal do frontend:

       cd frontend
       npm run dev

Depois abra:

- aplicação: `http://localhost:5173`;
- documentação da API: `[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)`.

O frontend nunca inventa indicadores. Se o PostgreSQL não estiver configurado,
as telas mostram o erro de conexão e permitem tentar novamente.

## O que existe no arquivo de criação

- `CREATE TABLE`: cria uma tabela.
- `INTEGER`, `VARCHAR`, `NUMERIC`, `DATE` e `TIMESTAMP`: tipos dos atributos.
- `PRIMARY KEY`: identifica cada registro.
- `FOREIGN KEY`: representa o relacionamento entre tabelas.
- `NOT NULL`: não permite valor vazio.
- `UNIQUE`: não permite valores repetidos.
- `CHECK`: impede valores inválidos, como quantidade negativa.

## Observações

A tabela `inclui` representa uma receita que contém outra receita. A tela de
ficha técnica expande as sub-receitas em vários níveis e calcula o custo usando
os preços das compras mais recentes.

O estoque é armazenado diretamente em `produto`. Não há atualização automática
após uma compra, perda ou venda. Essa automação exigiria conteúdos que não foram
usados nesta versão do trabalho.

## Embeddings

O sistema utiliza o modelo real
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Cada receita é
transformada em um vetor de 384 dimensões e persistida na tabela auxiliar
`receita_embedding`.

Como a instalação local do PostgreSQL não possui a extensão pgvector, os
vetores são armazenados em `DOUBLE PRECISION[]` e a similaridade de cosseno é
calculada pelo backend com os vetores originais. Não são usados vetores,
coordenadas ou resultados fictícios.

A aba **Embeddings** usa PCA para projetar os vetores em três dimensões. Ela
começa vazia e recebe pontos conforme as perguntas são feitas no Chat IA. Ao
passar o mouse, mostra o vetor projetado e as coordenadas. Ao selecionar dois
pontos, compara os vetores originais de 384 dimensões e mostra similaridade de
cosseno, ângulo e distância euclidiana.

## Chat IA

O Chat IA usa o Gemini e responde com base em uma cópia controlada dos dados
das 14 tabelas do restaurante. O modelo não recebe permissão para executar SQL
ou alterar o banco. Cada pergunta, resposta, embedding e receitas recuperadas
fica registrada na tabela auxiliar `chat_interacao`.

Na primeira abertura da aba **Chat IA**, clique no link para criar uma chave
gratuita no Google AI Studio e cole-a no campo. A chave é guardada somente no
arquivo `.env` local, que está ignorado pelo Git.

## Requisitos acadêmicos da aplicação

A aba **CRUD 14 tabelas** usa os metadados do PostgreSQL para oferecer inserção,
consulta, atualização e exclusão em todas as tabelas do modelo. Chaves primárias
compostas e referências estrangeiras são identificadas automaticamente.

A aba **Analytics SQL** executa diretamente as três consultas prontas em
`database/queries`. A aplicação apresenta o resultado em tabela e gera um
gráfico usando a última coluna numérica retornada.

A aba **Administrar banco** possui as opções exigidas para criar as tabelas e
carregar os dados iniciais ou eliminar todas as tabelas. As ações exigem que o
usuário digite `CRIAR` ou `ELIMINAR`; a eliminação também possui uma segunda
confirmação visual.