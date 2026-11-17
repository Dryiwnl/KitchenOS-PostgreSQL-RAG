-- Extensão do sistema para armazenar embeddings reais das receitas.
-- Não altera nenhuma das 14 tabelas acadêmicas.

CREATE TABLE receita_embedding (
    cod_receita INTEGER,
    texto TEXT NOT NULL,
    embedding DOUBLE PRECISION[] NOT NULL,
    modelo VARCHAR(150) NOT NULL,
    dimensao INTEGER NOT NULL,
    data_atualizacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cod_receita),
    FOREIGN KEY (cod_receita) REFERENCES receita (cod_receita)
);
