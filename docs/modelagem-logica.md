# Modelagem lógica

O modelo lógico abaixo é a tradução relacional da modelagem conceitual. As
chaves compostas das tabelas associativas impedem a repetição do mesmo item
dentro de uma compra, receita ou pedido.

```mermaid
erDiagram
    CATEGORIA {
        INTEGER cod_categoria PK
        VARCHAR_100 nome UK
    }
    FORNECEDOR {
        INTEGER cod_fornecedor PK
        VARCHAR_100 nome
        VARCHAR_100 contato
    }
    PRODUTO {
        INTEGER cod_produto PK
        VARCHAR_100 nome UK
        NUMERIC_12_3 estoque
        VARCHAR_10 unidade_medida
        NUMERIC_12_3 estoque_minimo
        NUMERIC_8_4 fator_correcao
    }
    COMPRA {
        INTEGER cod_compra PK
        INTEGER cod_fornecedor FK
        DATE data_compra
    }
    ITEM_COMPRA {
        INTEGER cod_compra PK,FK
        INTEGER cod_produto PK,FK
        NUMERIC_12_3 quantidade
        NUMERIC_12_4 preco_unitario
    }
    NOTA_FISCAL {
        INTEGER cod_nota_fiscal PK
        VARCHAR_20 numero
        VARCHAR_10 serie
        DATE data_emissao
        INTEGER cod_compra FK
    }
    RECEITA {
        INTEGER cod_receita PK
        INTEGER cod_categoria FK
        VARCHAR_100 nome UK
        NUMERIC_12_3 rendimento
        VARCHAR_10 unidade_de_rendimento
        NUMERIC_12_2 preco_de_venda
        TEXT modo_preparo
    }
    UTILIZA {
        INTEGER cod_receita PK,FK
        INTEGER cod_produto PK,FK
        NUMERIC_12_3 quantidade
    }
    INCLUI {
        INTEGER cod_receita PK,FK
        INTEGER cod_subreceita PK,FK
        NUMERIC_12_3 quantidade
    }
    CLIENTE {
        INTEGER cod_cliente PK
        VARCHAR_100 nome
        VARCHAR_20 telefone
    }
    FORMA_PAGAMENTO {
        INTEGER cod_forma_pagamento PK
        VARCHAR_100 descricao UK
    }
    PEDIDO {
        INTEGER cod_pedido PK
        INTEGER cod_cliente FK
        INTEGER cod_forma_pagamento FK
        TIMESTAMP data_pedido
        VARCHAR_20 status
    }
    CONTEM_RECEITA {
        INTEGER cod_pedido PK,FK
        INTEGER cod_receita PK,FK
        INTEGER quantidade
        NUMERIC_12_2 preco_unitario
        NUMERIC_12_4 custo_unitario_venda
    }
    PERDA_ESTOQUE {
        INTEGER cod_perda PK
        INTEGER cod_produto FK
        DATE data
        NUMERIC_12_3 quantidade
        VARCHAR_100 motivo
    }

    FORNECEDOR ||--o{ COMPRA : cod_fornecedor
    COMPRA ||--|{ ITEM_COMPRA : cod_compra
    PRODUTO ||--o{ ITEM_COMPRA : cod_produto
    COMPRA ||--o| NOTA_FISCAL : cod_compra
    PRODUTO ||--o{ PERDA_ESTOQUE : cod_produto
    CATEGORIA ||--o{ RECEITA : cod_categoria
    RECEITA ||--o{ UTILIZA : cod_receita
    PRODUTO ||--o{ UTILIZA : cod_produto
    RECEITA ||--o{ INCLUI : cod_receita
    RECEITA ||--o{ INCLUI : cod_subreceita
    CLIENTE ||--o{ PEDIDO : cod_cliente
    FORMA_PAGAMENTO ||--o{ PEDIDO : cod_forma_pagamento
    PEDIDO ||--|{ CONTEM_RECEITA : cod_pedido
    RECEITA ||--o{ CONTEM_RECEITA : cod_receita
```

O DDL correspondente está em
[`database/ddl/01_create_tables.sql`](../database/ddl/01_create_tables.sql).
