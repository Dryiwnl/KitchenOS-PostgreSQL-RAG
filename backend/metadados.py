"""Leitura das colunas e chaves das 14 tabelas."""

from fastapi import HTTPException
from psycopg2.extras import RealDictCursor

from backend.conexao import conectar

#tupla com o nome das 14 tabelas do banco para validações.
TABELAS = (
    "categoria", "fornecedor", "produto", "compra", "item_compra",
    "nota_fiscal", "receita", "utiliza", "inclui", "cliente",
    "forma_pagamento", "pedido", "contem_receita", "perda_estoque",
)

#Dicionário com os nomes as tabelas, apenas utilizado para
#exibir os nomes das tabelas na aplicação.
ROTULOS = {
    "categoria": "Categorias", "fornecedor": "Fornecedores", "produto": "Produtos",
    "compra": "Compras", "item_compra": "Itens de compra", "nota_fiscal": "Notas fiscais",
    "receita": "Receitas", "utiliza": "Ingredientes das receitas", "inclui": "Sub-receitas",
    "cliente": "Clientes", "forma_pagamento": "Formas de pagamento", "pedido": "Pedidos",
    "contem_receita": "Itens dos pedidos", "perda_estoque": "Perdas de estoque",
}

#Dicionário que define para cada tabela, sua PK
CHAVES_PRIMARIAS = {
    "categoria": ["cod_categoria"],
    "fornecedor": ["cod_fornecedor"],
    "produto": ["cod_produto"],
    "compra": ["cod_compra"],
    "item_compra": ["cod_compra", "cod_produto"],
    "nota_fiscal": ["cod_nota_fiscal"],
    "receita": ["cod_receita"],
    "utiliza": ["cod_receita", "cod_produto"],
    "inclui": ["cod_receita", "cod_subreceita"],
    "cliente": ["cod_cliente"],
    "forma_pagamento": ["cod_forma_pagamento"],
    "pedido": ["cod_pedido"],
    "contem_receita": ["cod_pedido", "cod_receita"],
    "perda_estoque": ["cod_perda"],
}

#Dicionário que define para cada tabela sua FK (se tiver) e qual tabela 
#referenciada
CHAVES_ESTRANGEIRAS = {
    "categoria": {},
    "fornecedor": {},
    "produto": {},
    "compra": {
        "cod_fornecedor": {
            "tabela_referenciada": "fornecedor",
            "coluna_referenciada": "cod_fornecedor",
        },
    },
    "item_compra": {
        "cod_compra": {
            "tabela_referenciada": "compra",
            "coluna_referenciada": "cod_compra",
        },
        "cod_produto": {
            "tabela_referenciada": "produto",
            "coluna_referenciada": "cod_produto",
        },
    },
    "nota_fiscal": {
        "cod_compra": {
            "tabela_referenciada": "compra",
            "coluna_referenciada": "cod_compra",
        },
    },
    "receita": {
        "cod_categoria": {
            "tabela_referenciada": "categoria",
            "coluna_referenciada": "cod_categoria",
        },
    },
    "utiliza": {
        "cod_receita": {
            "tabela_referenciada": "receita",
            "coluna_referenciada": "cod_receita",
        },
        "cod_produto": {
            "tabela_referenciada": "produto",
            "coluna_referenciada": "cod_produto",
        },
    },
    "inclui": {
        "cod_receita": {
            "tabela_referenciada": "receita",
            "coluna_referenciada": "cod_receita",
        },
        "cod_subreceita": {
            "tabela_referenciada": "receita",
            "coluna_referenciada": "cod_receita",
        },
    },
    "cliente": {},
    "forma_pagamento": {},
    "pedido": {
        "cod_cliente": {
            "tabela_referenciada": "cliente",
            "coluna_referenciada": "cod_cliente",
        },
        "cod_forma_pagamento": {
            "tabela_referenciada": "forma_pagamento",
            "coluna_referenciada": "cod_forma_pagamento",
        },
    },
    "contem_receita": {
        "cod_pedido": {
            "tabela_referenciada": "pedido",
            "coluna_referenciada": "cod_pedido",
        },
        "cod_receita": {
            "tabela_referenciada": "receita",
            "coluna_referenciada": "cod_receita",
        },
    },
    "perda_estoque": {
        "cod_produto": {
            "tabela_referenciada": "produto",
            "coluna_referenciada": "cod_produto",
        },
    },
}

#Se o parametro passando para a função, não estiver na tupla TABELAS
#Retora um erro.
def validar_tabela(tabela):
    if tabela not in TABELAS:
        raise HTTPException(status_code=404, detail="Tabela não permitida.")

#Essa função recebe o cursos e o nome da tabela como parâmetro
#Basicamente, é com essa função que toda a aplicação consegue descobrir
#quais as informações das colunas, domínios e chaves do banco
def select_metadados_tabela(cursor, tabela):
    #Executa uma consulta em sql para retornar informações sobre as COLUNAS da 
    #tabela passada.
    #retorna o nome, o tipo, se pode aceitar null e utiliza a consulta parametrizada
    #com o %s
    cursor.execute(
        """
        SELECT column_name, data_type, udt_name, is_nullable = 'YES' AS nullable,
               column_default
          FROM information_schema.columns
         WHERE table_schema = 'public' AND table_name = %s
         ORDER BY ordinal_position;
        """,
        (tabela,),
    )
    #Recupera todas as linhas retornadas pelo cursosr, converte em um dicionário
    #e para cada linha, faz um append na lista colunas.
    colunas = []
    for item in cursor.fetchall():
        colunas.append(dict(item))


    primarias = CHAVES_PRIMARIAS[tabela]
    estrangeiras = CHAVES_ESTRANGEIRAS[tabela]

    for coluna in colunas:
        #da lista de colunas, pega o valor da chave column_name e 
        #nome_coluna recebe esse valor
        nome_coluna = coluna["column_name"]

        # Verifica se a coluna é chave primária
        if nome_coluna in primarias:
            coluna["primary_key"] = True
        else:
            coluna["primary_key"] = False

        # Verifica se a coluna é chave estrangeira
        chave_estrangeira = estrangeiras.get(nome_coluna)

        if chave_estrangeira is not None:
            coluna["foreign_key"] = {
                "coluna": nome_coluna,
                "tabela_referenciada": chave_estrangeira["tabela_referenciada"],
                "coluna_referenciada": chave_estrangeira["coluna_referenciada"]
            }
        else:
            coluna["foreign_key"] = None

    return {
        "nome": tabela,
        "rotulo": ROTULOS[tabela],
        "primary_key": primarias,
        "colunas": colunas
    }


def select_metadados():
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            return [select_metadados_tabela(cursor, tabela) for tabela in TABELAS]
    finally:
        conexao.close()
