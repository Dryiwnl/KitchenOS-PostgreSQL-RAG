-- Histórico do Chat IA e pontos de consulta usados no mapa de embeddings.

CREATE TABLE chat_interacao (
    cod_interacao SERIAL,
    pergunta TEXT NOT NULL,
    resposta TEXT NOT NULL,
    embedding DOUBLE PRECISION[] NOT NULL,
    receitas_recuperadas INTEGER[] NOT NULL,
    modelo_llm VARCHAR(100) NOT NULL,
    data_interacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cod_interacao)
);
