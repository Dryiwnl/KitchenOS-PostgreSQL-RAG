"""API inicial do KitchenOS.

Esta etapa implementa CRUD de categorias, fornecedores e produtos usando
FastAPI e comandos SQL escritos diretamente, como no material da disciplina.
"""

from decimal import Decimal

import psycopg2
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field

from backend.conexao import conectar
from backend.chat_ai import chave_configurada, historico, responder, salvar_chave, MODELO_LLM
from backend.embeddings import (
    MODELO, buscar_receitas, comparar_pontos, dados_explorer, gerar_embeddings,
)
from backend.administracao import router as administracao_router


app = FastAPI(
    title="KitchenOS API",
    description="API para gerenciamento de dados do restaurante.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(administracao_router)


class Categoria(BaseModel):
    cod_categoria: int
    nome: str = Field(min_length=1, max_length=100)


class Fornecedor(BaseModel):
    cod_fornecedor: int
    nome: str = Field(min_length=1, max_length=100)
    contato: str | None = Field(default=None, max_length=100)


class Produto(BaseModel):
    cod_produto: int
    nome: str = Field(min_length=1, max_length=100)
    estoque: Decimal = Field(ge=0)
    unidade_medida: str = Field(min_length=1, max_length=10)
    estoque_minimo: Decimal = Field(ge=0)
    fator_correcao: Decimal = Field(ge=1)


class BuscaSemantica(BaseModel):
    pergunta: str = Field(min_length=3, max_length=500)
    limite: int = Field(default=5, ge=1, le=10)


class PerguntaChat(BaseModel):
    pergunta: str = Field(min_length=3, max_length=1000)


class ConfiguracaoChat(BaseModel):
    api_key: str = Field(min_length=20, max_length=300)


class ComparacaoPontos(BaseModel):
    primeiro: str = Field(pattern=r"^(receita|consulta)-\d+$")
    segundo: str = Field(pattern=r"^(receita|consulta)-\d+$")

def consultar(sql, parametros=(), apenas_um=False):
    """Executa um SELECT e devolve registros no formato de dicionário."""
    conexao = None
    try:
        conexao = conectar()
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, parametros)
            if apenas_um:
                registro = cursor.fetchone()
                if registro is not None:
                    return dict(registro)
                else:
                    return None
            registros = []
            for registro in cursor.fetchall():
                registros.append(dict(registro))
            return registros
    except psycopg2.Error as erro:
        raise HTTPException(status_code=500, detail=str(erro)) from erro
    finally:
        if conexao is not None:
            conexao.close()


def modificar(sql, parametros=(), retornar=False):
    """Executa INSERT, UPDATE ou DELETE em uma transação."""
    conexao = None
    try:
        conexao = conectar()
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, parametros)
            registro = cursor.fetchone() if retornar else None
            quantidade = cursor.rowcount
        conexao.commit()
        if retornar:
            return dict(registro) if registro else None
        return quantidade
    except psycopg2.IntegrityError as erro:
        raise HTTPException(
            status_code=400,
            detail="A operação viola uma restrição do banco de dados.",
        ) from erro
    except psycopg2.Error as erro:
        raise HTTPException(status_code=500, detail=str(erro)) from erro
    finally:
        if conexao is not None:
            conexao.close()


@app.get("/")
def inicio():
    return {
        "sistema": "KitchenOS",
        "mensagem": "API em funcionamento",
        "documentacao": "/docs",
    }


@app.get("/saude")
def saude():
    resultado = consultar("SELECT current_database() AS banco;", apenas_um=True)
    return {"api": "online", "banco": resultado["banco"]}


@app.get("/receitas")
def listar_receitas():
    return consultar(
        """
        SELECT r.cod_receita, r.nome, c.nome AS categoria,
               r.rendimento, r.unidade_de_rendimento, r.preco_de_venda,
               COUNT(DISTINCT u.cod_produto) AS ingredientes,
               COUNT(DISTINCT i.cod_subreceita) AS subreceitas
          FROM receita r
          JOIN categoria c ON c.cod_categoria = r.cod_categoria
          LEFT JOIN utiliza u ON u.cod_receita = r.cod_receita
          LEFT JOIN inclui i ON i.cod_receita = r.cod_receita
         GROUP BY r.cod_receita, r.nome, c.nome, r.rendimento,
                  r.unidade_de_rendimento, r.preco_de_venda
         ORDER BY r.nome;
        """
    )


@app.get("/receitas/{codigo}/ficha")
def obter_ficha_tecnica(codigo: int):
    receita = consultar(
        """
        SELECT r.*, c.nome AS categoria
          FROM receita r
          JOIN categoria c ON c.cod_categoria = r.cod_categoria
         WHERE r.cod_receita = %s;
        """,
        (codigo,),
        apenas_um=True,
    )
    if receita is None:
        raise HTTPException(status_code=404, detail="Receita não encontrada.")

    ingredientes = consultar(
        """
        SELECT p.cod_produto, p.nome, u.quantidade, p.unidade_medida,
               p.fator_correcao, preco.preco_unitario,
               CASE WHEN preco.preco_unitario IS NOT NULL
                    THEN u.quantidade * p.fator_correcao * preco.preco_unitario
               END AS custo
          FROM utiliza u
          JOIN produto p ON p.cod_produto = u.cod_produto
          LEFT JOIN LATERAL (
              SELECT ic.preco_unitario
                FROM item_compra ic
                JOIN compra c ON c.cod_compra = ic.cod_compra
               WHERE ic.cod_produto = p.cod_produto
               ORDER BY c.data_compra DESC, c.cod_compra DESC
               LIMIT 1
          ) preco ON TRUE
         WHERE u.cod_receita = %s
         ORDER BY p.nome;
        """,
        (codigo,),
    )
    subreceitas = consultar(
        """
        SELECT r.cod_receita, r.nome, i.quantidade,
               r.unidade_de_rendimento
          FROM inclui i
          JOIN receita r ON r.cod_receita = i.cod_subreceita
         WHERE i.cod_receita = %s
         ORDER BY r.nome;
        """,
        (codigo,),
    )
    expandidos = consultar(
        """
        WITH RECURSIVE arvore AS (
            SELECT r.cod_receita, 1::NUMERIC AS multiplicador,
                   ARRAY[r.cod_receita] AS caminho
              FROM receita r WHERE r.cod_receita = %s
            UNION ALL
            SELECT sub.cod_receita,
                   a.multiplicador * i.quantidade / sub.rendimento,
                   a.caminho || sub.cod_receita
              FROM arvore a
              JOIN inclui i ON i.cod_receita = a.cod_receita
              JOIN receita sub ON sub.cod_receita = i.cod_subreceita
             WHERE NOT sub.cod_receita = ANY(a.caminho)
        ), quantidades AS (
            SELECT u.cod_produto,
                   SUM(a.multiplicador * u.quantidade) AS quantidade
              FROM arvore a
              JOIN utiliza u ON u.cod_receita = a.cod_receita
             GROUP BY u.cod_produto
        )
        SELECT p.nome, q.quantidade, p.unidade_medida, p.fator_correcao,
               preco.preco_unitario,
               CASE WHEN preco.preco_unitario IS NOT NULL
                    THEN q.quantidade * p.fator_correcao * preco.preco_unitario
               END AS custo
          FROM quantidades q
          JOIN produto p ON p.cod_produto = q.cod_produto
          LEFT JOIN LATERAL (
              SELECT ic.preco_unitario
                FROM item_compra ic
                JOIN compra c ON c.cod_compra = ic.cod_compra
               WHERE ic.cod_produto = p.cod_produto
               ORDER BY c.data_compra DESC, c.cod_compra DESC
               LIMIT 1
          ) preco ON TRUE
         ORDER BY p.nome;
        """,
        (codigo,),
    )
    custos = [Decimal(str(item["custo"])) for item in expandidos if item["custo"] is not None]
    sem_preco = sum(1 for item in expandidos if item["custo"] is None)
    custo_total = sum(custos, Decimal("0")) if sem_preco == 0 else None
    custo_unitario = custo_total / Decimal(str(receita["rendimento"])) if custo_total is not None else None
    margem = Decimal(str(receita["preco_de_venda"])) - custo_unitario if custo_unitario is not None else None
    return {
        "receita": receita,
        "ingredientes_diretos": ingredientes,
        "subreceitas": subreceitas,
        "ingredientes_expandidos": expandidos,
        "custo_total": custo_total,
        "custo_unitario": custo_unitario,
        "margem_unitaria": margem,
        "ingredientes_sem_preco": sem_preco,
    }


@app.get("/embeddings")
def status_embeddings():
    registros = consultar(
        """
        SELECT COUNT(*) AS quantidade, MAX(modelo) AS modelo,
               MAX(dimensao) AS dimensao,
               MAX(data_atualizacao) AS ultima_atualizacao
          FROM receita_embedding;
        """,
        apenas_um=True,
    )
    registros["modelo_configurado"] = MODELO
    return registros


@app.post("/embeddings/gerar")
def gerar_embeddings_das_receitas():
    return gerar_embeddings()


@app.post("/embeddings/buscar")
def busca_semantica(busca: BuscaSemantica):
    return {
        "pergunta": busca.pergunta,
        "resultados": buscar_receitas(busca.pergunta, busca.limite),
    }


@app.get("/embeddings/explorer")
def embedding_explorer():
    return dados_explorer()


@app.post("/embeddings/comparar")
def comparar_embeddings(pontos: ComparacaoPontos):
    try:
        return comparar_pontos(pontos.primeiro, pontos.segundo)
    except ValueError as erro:
        raise HTTPException(status_code=404, detail=str(erro)) from erro


@app.get("/chat/status")
def status_chat():
    return {"configurado": chave_configurada(), "modelo": MODELO_LLM}


@app.post("/chat/configurar")
def configurar_chat(configuracao: ConfiguracaoChat):
    try:
        return salvar_chave(configuracao.api_key)
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro


@app.get("/chat/historico")
def historico_chat():
    return historico()


@app.post("/chat")
def conversar_chat(pergunta: PerguntaChat):
    try:
        return responder(pergunta.pergunta)
    except RuntimeError as erro:
        raise HTTPException(status_code=503, detail=str(erro)) from erro
    except Exception as erro:
        raise HTTPException(
            status_code=502,
            detail="O Gemini não conseguiu gerar a resposta. Verifique a chave e tente novamente.",
        ) from erro


@app.get("/pedidos")
def listar_pedidos():
    return consultar(
        """
        SELECT p.cod_pedido, c.nome AS cliente, fp.descricao AS forma_pagamento,
               p.data_pedido, p.status,
               COALESCE(SUM(cr.quantidade * cr.preco_unitario), 0) AS total
          FROM pedido p
          JOIN cliente c ON c.cod_cliente = p.cod_cliente
          JOIN forma_pagamento fp
            ON fp.cod_forma_pagamento = p.cod_forma_pagamento
          LEFT JOIN contem_receita cr ON cr.cod_pedido = p.cod_pedido
         GROUP BY p.cod_pedido, c.nome, fp.descricao, p.data_pedido, p.status
         ORDER BY p.data_pedido DESC;
        """
    )


@app.get("/perdas")
def listar_perdas():
    return consultar(
        """
        SELECT pe.cod_perda, p.nome AS produto, pe.data,
               pe.quantidade, p.unidade_medida, pe.motivo
          FROM perda_estoque pe
          JOIN produto p ON p.cod_produto = pe.cod_produto
         ORDER BY pe.data DESC, pe.cod_perda DESC;
        """
    )


# ---------------------------------------------------------------------------
# Categorias
# ---------------------------------------------------------------------------


@app.get("/categorias", response_model=list[Categoria])
def listar_categorias():
    return consultar("SELECT * FROM categoria ORDER BY cod_categoria;")


@app.get("/categorias/{codigo}", response_model=Categoria)
def obter_categoria(codigo: int):
    categoria = consultar(
        "SELECT * FROM categoria WHERE cod_categoria = %s;",
        (codigo,),
        apenas_um=True,
    )
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    return categoria


@app.post("/categorias", response_model=Categoria, status_code=status.HTTP_201_CREATED)
def criar_categoria(categoria: Categoria):
    return modificar(
        """
        INSERT INTO categoria (cod_categoria, nome)
        VALUES (%s, %s)
        RETURNING *;
        """,
        (categoria.cod_categoria, categoria.nome),
        retornar=True,
    )


@app.put("/categorias/{codigo}", response_model=Categoria)
def atualizar_categoria(codigo: int, categoria: Categoria):
    atualizada = modificar(
        """
        UPDATE categoria
           SET cod_categoria = %s, nome = %s
         WHERE cod_categoria = %s
        RETURNING *;
        """,
        (categoria.cod_categoria, categoria.nome, codigo),
        retornar=True,
    )
    if atualizada is None:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    return atualizada


@app.delete("/categorias/{codigo}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_categoria(codigo: int):
    quantidade = modificar(
        "DELETE FROM categoria WHERE cod_categoria = %s;", (codigo,)
    )
    if quantidade == 0:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Fornecedores
# ---------------------------------------------------------------------------


@app.get("/fornecedores", response_model=list[Fornecedor])
def listar_fornecedores():
    return consultar("SELECT * FROM fornecedor ORDER BY cod_fornecedor;")


@app.get("/fornecedores/{codigo}", response_model=Fornecedor)
def obter_fornecedor(codigo: int):
    fornecedor = consultar(
        "SELECT * FROM fornecedor WHERE cod_fornecedor = %s;",
        (codigo,),
        apenas_um=True,
    )
    if fornecedor is None:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado.")
    return fornecedor


@app.post(
    "/fornecedores", response_model=Fornecedor, status_code=status.HTTP_201_CREATED
)
def criar_fornecedor(fornecedor: Fornecedor):
    return modificar(
        """
        INSERT INTO fornecedor (cod_fornecedor, nome, contato)
        VALUES (%s, %s, %s)
        RETURNING *;
        """,
        (fornecedor.cod_fornecedor, fornecedor.nome, fornecedor.contato),
        retornar=True,
    )


@app.put("/fornecedores/{codigo}", response_model=Fornecedor)
def atualizar_fornecedor(codigo: int, fornecedor: Fornecedor):
    atualizado = modificar(
        """
        UPDATE fornecedor
           SET cod_fornecedor = %s, nome = %s, contato = %s
         WHERE cod_fornecedor = %s
        RETURNING *;
        """,
        (
            fornecedor.cod_fornecedor,
            fornecedor.nome,
            fornecedor.contato,
            codigo,
        ),
        retornar=True,
    )
    if atualizado is None:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado.")
    return atualizado


@app.delete("/fornecedores/{codigo}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_fornecedor(codigo: int):
    quantidade = modificar(
        "DELETE FROM fornecedor WHERE cod_fornecedor = %s;", (codigo,)
    )
    if quantidade == 0:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Produtos
# ---------------------------------------------------------------------------


@app.get("/produtos", response_model=list[Produto])
def listar_produtos():
    return consultar("SELECT * FROM produto ORDER BY cod_produto;")


@app.get("/produtos/{codigo}", response_model=Produto)
def obter_produto(codigo: int):
    produto = consultar(
        "SELECT * FROM produto WHERE cod_produto = %s;",
        (codigo,),
        apenas_um=True,
    )
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto


@app.post("/produtos", response_model=Produto, status_code=status.HTTP_201_CREATED)
def criar_produto(produto: Produto):
    return modificar(
        """
        INSERT INTO produto
            (cod_produto, nome, estoque, unidade_medida,
             estoque_minimo, fator_correcao)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING *;
        """,
        (
            produto.cod_produto,
            produto.nome,
            produto.estoque,
            produto.unidade_medida,
            produto.estoque_minimo,
            produto.fator_correcao,
        ),
        retornar=True,
    )


@app.put("/produtos/{codigo}", response_model=Produto)
def atualizar_produto(codigo: int, produto: Produto):
    atualizado = modificar(
        """
        UPDATE produto
           SET cod_produto = %s,
               nome = %s,
               estoque = %s,
               unidade_medida = %s,
               estoque_minimo = %s,
               fator_correcao = %s
         WHERE cod_produto = %s
        RETURNING *;
        """,
        (
            produto.cod_produto,
            produto.nome,
            produto.estoque,
            produto.unidade_medida,
            produto.estoque_minimo,
            produto.fator_correcao,
            codigo,
        ),
        retornar=True,
    )
    if atualizado is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return atualizado


@app.delete("/produtos/{codigo}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_produto(codigo: int):
    quantidade = modificar("DELETE FROM produto WHERE cod_produto = %s;", (codigo,))
    if quantidade == 0:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
