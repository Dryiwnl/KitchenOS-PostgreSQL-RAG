INSERT INTO categoria (cod_categoria, nome) VALUES
    (1, 'Bases e molhos'),
    (2, 'Pratos principais'),
    (3, 'Lanches'),
    (4, 'Sobremesas');

INSERT INTO fornecedor (cod_fornecedor, nome, contato) VALUES
    (1, 'Distribuidora Ilha', 'compras@ilha.test'),
    (2, 'Hortifruti Santa Catarina', '(48) 3000-1000'),
    (3, 'Laticínios do Sul', '(48) 3000-2000');

-- O estoque foi informado diretamente, pois o projeto não usa triggers.
INSERT INTO produto
    (cod_produto, nome, estoque, unidade_medida, estoque_minimo, fator_correcao)
VALUES
    (1, 'Farinha de trigo', 50.000, 'kg', 5, 1.0200),
    (2, 'Ovo', 174.000, 'un', 24, 1.0000),
    (3, 'Leite integral', 29.200, 'l', 5, 1.0000),
    (4, 'Manteiga', 10.000, 'kg', 2, 1.0500),
    (5, 'Tomate', 42.600, 'kg', 4, 1.1000),
    (6, 'Queijo muçarela', 24.650, 'kg', 3, 1.0000),
    (7, 'Carne bovina moída', 34.500, 'kg', 5, 1.1500),
    (8, 'Sal', 10.000, 'kg', 1, 1.0000),
    (9, 'Ervas frescas', 0, 'kg', 0.5, 1.2000);

INSERT INTO compra (cod_compra, cod_fornecedor, data_compra) VALUES
    (1, 1, DATE '2026-01-10'),
    (2, 2, DATE '2026-01-18'),
    (3, 3, DATE '2026-01-18'),
    (4, 1, DATE '2026-02-05'),
    (5, 2, DATE '2026-02-05');

INSERT INTO item_compra (cod_compra, cod_produto, quantidade, preco_unitario) VALUES
    (1, 1, 30.000, 4.5000),
    (1, 2, 120.000, 0.8500),
    (1, 8, 10.000, 2.0000),
    (2, 5, 25.000, 5.2000),
    (2, 7, 20.000, 27.0000),
    (3, 3, 30.000, 4.7000),
    (3, 4, 10.000, 19.0000),
    (3, 6, 15.000, 28.0000),
    (4, 1, 20.000, 4.8000),
    (4, 2, 60.000, 0.9000),
    (5, 5, 20.000, 6.0000),
    (5, 7, 15.000, 29.0000),
    (5, 6, 10.000, 30.0000);

INSERT INTO nota_fiscal
    (cod_nota_fiscal, numero, serie, data_emissao, cod_compra)
VALUES
    (1, '000101', 'A1', DATE '2026-01-10', 1),
    (2, '000245', 'H1', DATE '2026-01-18', 2),
    (3, '000088', 'L1', DATE '2026-01-18', 3),
    (4, '000119', 'A1', DATE '2026-02-05', 4),
    (5, '000263', 'H1', DATE '2026-02-05', 5);

INSERT INTO receita
    (cod_receita, cod_categoria, nome, rendimento, unidade_de_rendimento,
     preco_de_venda, modo_preparo)
VALUES
    (1, 1, 'Molho de tomate', 10.000, 'porcao', 3.50,
     'Cozinhar os tomates e ajustar o sal.'),
    (2, 1, 'Massa de pizza', 4.000, 'un', 4.00,
     'Misturar, sovar e fermentar a massa.'),
    (3, 2, 'Pizza marguerita', 1.000, 'un', 42.00,
     'Abrir a massa, adicionar molho e queijo e assar.'),
    (4, 3, 'Hambúrguer artesanal', 1.000, 'un', 29.00,
     'Modelar e grelhar a carne; finalizar com queijo.'),
    (5, 2, 'Combo da casa', 1.000, 'combo', 65.00,
     'Preparar uma pizza e um hambúrguer.'),
    (6, 1, 'Molho de ervas', 5.000, 'porcao', 4.50,
     'Picar as ervas e misturar os ingredientes.');

INSERT INTO utiliza (cod_receita, cod_produto, quantidade) VALUES
    (1, 5, 2.000),
    (1, 8, 0.050),
    (2, 1, 0.800),
    (2, 3, 0.300),
    (2, 4, 0.050),
    (2, 8, 0.010),
    (3, 6, 0.250),
    (4, 7, 0.180),
    (4, 6, 0.050),
    (4, 8, 0.005),
    (6, 9, 0.200),
    (6, 8, 0.010);

INSERT INTO inclui (cod_receita, cod_subreceita, quantidade) VALUES
    (3, 2, 1.000),
    (3, 1, 1.000),
    (5, 3, 1.000),
    (5, 4, 1.000);

INSERT INTO cliente (cod_cliente, nome, telefone) VALUES
    (1, 'Ana Souza', '(48) 99999-1001'),
    (2, 'Bruno Lima', '(48) 99999-1002'),
    (3, 'Carla Mendes', '(48) 99999-1003'),
    (4, 'Diego Alves', NULL);

INSERT INTO forma_pagamento (cod_forma_pagamento, descricao) VALUES
    (1, 'Cartão de crédito'),
    (2, 'PIX'),
    (3, 'Dinheiro');

INSERT INTO pedido
    (cod_pedido, cod_cliente, cod_forma_pagamento, data_pedido, status)
VALUES
    (1, 1, 2, TIMESTAMP '2026-01-20 12:10:00', 'PAGO'),
    (2, 2, 1, TIMESTAMP '2026-01-25 20:30:00', 'PAGO'),
    (3, 3, 3, TIMESTAMP '2026-02-07 13:00:00', 'PAGO'),
    (4, 1, 1, TIMESTAMP '2026-02-12 19:45:00', 'PAGO'),
    (5, 4, 2, TIMESTAMP '2026-02-14 21:15:00', 'CANCELADO'),
    (6, 2, 2, TIMESTAMP '2026-03-02 12:20:00', 'PAGO');

-- custo_unitario_venda é um snapshot histórico e não muda com novas compras.
INSERT INTO contem_receita
    (cod_pedido, cod_receita, quantidade, preco_unitario, custo_unitario_venda)
VALUES
    (1, 3, 2, 40.00, 9.8000),
    (1, 4, 1, 28.00, 7.0000),
    (2, 5, 1, 63.00, 17.5000),
    (3, 3, 1, 42.00, 10.4517),
    (3, 4, 2, 29.00, 7.5130),
    (4, 5, 2, 65.00, 17.9647),
    (5, 3, 3, 42.00, 10.4517),
    (6, 4, 3, 29.00, 7.5130),
    (6, 3, 1, 42.00, 10.4517);

INSERT INTO perda_estoque (cod_perda, cod_produto, data, quantidade, motivo) VALUES
    (1, 5, DATE '2026-01-22', 1.500, 'Amassados no transporte'),
    (2, 3, DATE '2026-01-27', 0.800, 'Validade expirada'),
    (3, 6, DATE '2026-02-08', 0.350, 'Falha de refrigeração'),
    (4, 5, DATE '2026-02-15', 0.900, 'Deterioração'),
    (5, 7, DATE '2026-02-18', 0.500, 'Erro de manipulação'),
    (6, 2, DATE '2026-03-01', 6.000, 'Quebra');

