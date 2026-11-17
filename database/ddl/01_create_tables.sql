
CREATE TABLE categoria (
    cod_categoria INTEGER,
    nome VARCHAR(100) NOT NULL,
    PRIMARY KEY (cod_categoria),
    UNIQUE (nome)
);

CREATE TABLE fornecedor (
    cod_fornecedor INTEGER,
    nome VARCHAR(100) NOT NULL,
    contato VARCHAR(100),
    PRIMARY KEY (cod_fornecedor)
);

CREATE TABLE produto (
    cod_produto INTEGER,
    nome VARCHAR(100) NOT NULL,
    estoque NUMERIC(12,3) NOT NULL,
    unidade_medida VARCHAR(10) NOT NULL,
    estoque_minimo NUMERIC(12,3) NOT NULL,
    fator_correcao NUMERIC(8,4) NOT NULL,
    PRIMARY KEY (cod_produto),
    UNIQUE (nome),
    CHECK (estoque >= 0),
    CHECK (estoque_minimo >= 0),
    CHECK (fator_correcao >= 1)
);

CREATE TABLE compra (
    cod_compra INTEGER,
    cod_fornecedor INTEGER NOT NULL,
    data_compra DATE NOT NULL,
    PRIMARY KEY (cod_compra),
    FOREIGN KEY (cod_fornecedor) REFERENCES fornecedor (cod_fornecedor)
);

CREATE TABLE item_compra (
    cod_compra INTEGER,
    cod_produto INTEGER,
    quantidade NUMERIC(12,3) NOT NULL,
    preco_unitario NUMERIC(12,4) NOT NULL,
    PRIMARY KEY (cod_compra, cod_produto),
    FOREIGN KEY (cod_compra) REFERENCES compra (cod_compra),
    FOREIGN KEY (cod_produto) REFERENCES produto (cod_produto),
    CHECK (quantidade > 0),
    CHECK (preco_unitario >= 0)
);

CREATE TABLE nota_fiscal (
    cod_nota_fiscal INTEGER,
    numero VARCHAR(20) NOT NULL,
    serie VARCHAR(10) NOT NULL,
    data_emissao DATE NOT NULL,
    cod_compra INTEGER NOT NULL,
    PRIMARY KEY (cod_nota_fiscal),
    UNIQUE (numero, serie),
    FOREIGN KEY (cod_compra) REFERENCES compra (cod_compra)
);

CREATE TABLE receita (
    cod_receita INTEGER,
    cod_categoria INTEGER NOT NULL,
    nome VARCHAR(100) NOT NULL,
    rendimento NUMERIC(12,3) NOT NULL,
    unidade_de_rendimento VARCHAR(10) NOT NULL,
    preco_de_venda NUMERIC(12,2) NOT NULL,
    modo_preparo TEXT,
    PRIMARY KEY (cod_receita),
    UNIQUE (nome),
    FOREIGN KEY (cod_categoria) REFERENCES categoria (cod_categoria),
    CHECK (rendimento > 0),
    CHECK (preco_de_venda >= 0)
);

CREATE TABLE utiliza (
    cod_receita INTEGER,
    cod_produto INTEGER,
    quantidade NUMERIC(12,3) NOT NULL,
    PRIMARY KEY (cod_receita, cod_produto),
    FOREIGN KEY (cod_receita) REFERENCES receita (cod_receita),
    FOREIGN KEY (cod_produto) REFERENCES produto (cod_produto),
    CHECK (quantidade > 0)
);

CREATE TABLE inclui (
    cod_receita INTEGER,
    cod_subreceita INTEGER,
    quantidade NUMERIC(12,3) NOT NULL,
    PRIMARY KEY (cod_receita, cod_subreceita),
    FOREIGN KEY (cod_receita) REFERENCES receita (cod_receita),
    FOREIGN KEY (cod_subreceita) REFERENCES receita (cod_receita),
    CHECK (cod_receita <> cod_subreceita),
    CHECK (quantidade > 0)
);

CREATE TABLE cliente (
    cod_cliente INTEGER,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(20),
    PRIMARY KEY (cod_cliente)
);

CREATE TABLE forma_pagamento (
    cod_forma_pagamento INTEGER,
    descricao VARCHAR(100) NOT NULL,
    PRIMARY KEY (cod_forma_pagamento),
    UNIQUE (descricao)
);

CREATE TABLE pedido (
    cod_pedido INTEGER,
    cod_cliente INTEGER NOT NULL,
    cod_forma_pagamento INTEGER NOT NULL,
    data_pedido TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL,
    PRIMARY KEY (cod_pedido),
    FOREIGN KEY (cod_cliente) REFERENCES cliente (cod_cliente),
    FOREIGN KEY (cod_forma_pagamento)
        REFERENCES forma_pagamento (cod_forma_pagamento),
    CHECK (status IN ('ABERTO', 'PAGO', 'CANCELADO'))
);

CREATE TABLE contem_receita (
    cod_pedido INTEGER,
    cod_receita INTEGER,
    quantidade INTEGER NOT NULL,
    preco_unitario NUMERIC(12,2) NOT NULL,
    custo_unitario_venda NUMERIC(12,4) NOT NULL,
    PRIMARY KEY (cod_pedido, cod_receita),
    FOREIGN KEY (cod_pedido) REFERENCES pedido (cod_pedido),
    FOREIGN KEY (cod_receita) REFERENCES receita (cod_receita),
    CHECK (quantidade > 0),
    CHECK (preco_unitario >= 0),
    CHECK (custo_unitario_venda >= 0)
);

CREATE TABLE perda_estoque (
    cod_perda INTEGER,
    cod_produto INTEGER NOT NULL,
    data DATE NOT NULL,
    quantidade NUMERIC(12,3) NOT NULL,
    motivo VARCHAR(100) NOT NULL,
    PRIMARY KEY (cod_perda),
    FOREIGN KEY (cod_produto) REFERENCES produto (cod_produto),
    CHECK (quantidade > 0)
);
