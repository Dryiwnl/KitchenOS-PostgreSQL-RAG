# Banco de dados

Execute os arquivos nesta ordem:

1. `ddl/01_create_tables.sql` — cria as 14 tabelas acadêmicas;
2. `seeds/02_insert_data.sql` — insere os dados;
3. `ddl/02_create_embeddings.sql` — cria o armazenamento dos vetores;
4. `ddl/03_create_chat.sql` — cria o histórico do Chat IA.

Os arquivos da pasta `queries` contêm as três consultas obrigatórias do
trabalho: custos das receitas, vendas por cliente e perdas de estoque. Todas
envolvem pelo menos três tabelas e usam funções de agregação.

Se o arquivo de criação for executado duas vezes no mesmo banco, o PostgreSQL
informará que as tabelas já existem. Para recomeçar, a maneira mais simples no
pgAdmin é excluir o banco `restaurante`, criá-lo novamente e executar os quatro
arquivos na ordem acima.
