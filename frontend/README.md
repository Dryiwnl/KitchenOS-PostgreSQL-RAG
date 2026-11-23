# Frontend do KitchenOS

Interface React + TypeScript com identidade editorial de restaurante.

Funcionalidades atuais:

- dashboard com indicadores e gráficos reais;
- estoque com cadastro, edição e exclusão de produtos;
- fichas técnicas completas com custos e sub-receitas;
- chat com IA (RAG) integrado ao Gemini com configuração local da chave;
- descoberta semântica com embeddings reais;
- mapa 3D interativo dos embeddings com Plotly e comparação vetorial em 384D;
- CRUD dinâmico das 14 tabelas acadêmicas com validação de chaves primárias e estrangeiras;
- analytics SQL com execução das 3 consultas prontas em tabela e gráfico;
- administração do banco com criação, carga inicial e eliminação protegida das tabelas;
- listagens de vendas e perdas;
- gestão de categorias e fornecedores;
- layout responsivo e estados de erro/carregamento.

## Executar

Na primeira vez, instale as dependências:

    cd frontend
    npm install

Depois, inicie o servidor de desenvolvimento:

    npm run dev

Abra `http://localhost:5173` (ou `http://127.0.0.1:5173`) com o backend executando na porta `8000`.