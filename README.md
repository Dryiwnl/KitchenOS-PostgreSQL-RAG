# Trabalho Final de Banco de Dados I

> Relatório acadêmico: [`docs/relatorio.md`](docs/relatorio.md)  
> Modelagens: [conceitual](docs/modelagem-conceitual.md) e
> [lógica](docs/modelagem-logica.md)

Este projeto representa o banco de dados de um restaurante. Ele permite
armazenar produtos, fornecedores, compras, receitas, clientes, pedidos e perdas
de estoque.

O banco foi mantido no nível do conteúdo apresentado nas aulas de SQL. O
backend está sendo desenvolvido em Python e FastAPI por etapas.

## Arquivos importantes

```text
database/
├── ddl/
│   └── 01_create_tables.sql   # cria as 14 tabelas
├── seeds/
│   └── 02_insert_data.sql     # insere dados de exemplo
└── queries/
    ├── 01_custos_receitas.sql # custos por receita
    ├── 02_vendas.sql          # vendas pagas por cliente
    └── 03_estoque_perdas.sql  # valor das perdas de estoque
backend/
├── api.py                     # API e primeiros CRUDs
├── conexao.py                 # conexão com PostgreSQL
└── requirements.txt           # bibliotecas Python
frontend/
├── src/App.tsx                # telas e integração com a API
├── src/styles.css             # identidade visual do KitchenOS
└── package.json               # dependências React
```

## Como executar pelo pgAdmin

1. Instale o PostgreSQL com o pgAdmin.
2. Abra o pgAdmin.
3. Crie um banco chamado `restaurante`.
4. Clique com o botão direito no banco e abra **Query Tool**.
5. Abra `database/ddl/01_create_tables.sql` e clique em **Execute**.
6. Depois, abra `database/seeds/02_insert_data.sql` e clique em **Execute**.
7. Para usar as telas de IA, execute também `database/ddl/02_create_embeddings.sql`
   e `database/ddl/03_create_chat.sql`, nessa ordem.

Para confirmar que os dados foram inseridos, execute:

```sql
SELECT * FROM produto;
SELECT * FROM receita;
SELECT * FROM pedido;
```

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

## Executar a aplicação

### Início rápido (recomendado)

No Windows, abra o PowerShell na pasta raiz do projeto e execute:

```powershell
.\iniciar.ps1
```

Esse único comando inicia o PostgreSQL do projeto, o backend e o frontend em
terminais separados. Mantenha os terminais abertos enquanto estiver usando o
sistema.

Depois, acesse no navegador:

```text
http://127.0.0.1:5173
```

Se o PowerShell bloquear a execução de scripts, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\iniciar.ps1
```

Para encerrar a aplicação, pressione `Ctrl + C` nos terminais do backend e do
frontend.

Forma manual:

Abra dois terminais no VS Code.

Terminal do backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.api:app --reload
```

Terminal do frontend:

```powershell
cd frontend
npm run dev
```

Depois abra:

- aplicação: `http://127.0.0.1:5173`;
- documentação da API: `http://127.0.0.1:8000/docs`.

O frontend apresenta somente dados reais do PostgreSQL. Se o banco não estiver
configurado, as telas mostram o erro de conexão e permitem tentar novamente.

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
