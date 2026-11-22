"""CRUD genérico das 14 tabelas, consultas acadêmicas e administração do banco."""

from pathlib import Path

import psycopg2
from fastapi import APIRouter, Body, HTTPException
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from backend.conexao import conectar
from backend.embeddings import gerar_embeddings
from backend.conexao import conectar


router = APIRouter()
RAIZ = Path(__file__).resolve().parent.parent

TABELAS = (
    "categoria", "fornecedor", "produto", "compra", "item_compra",
    "nota_fiscal", "receita", "utiliza", "inclui", "cliente",
    "forma_pagamento", "pedido", "contem_receita", "perda_estoque",
)

ROTULOS = {
    "categoria": "Categorias", "fornecedor": "Fornecedores", "produto": "Produtos",
    "compra": "Compras", "item_compra": "Itens de compra", "nota_fiscal": "Notas fiscais",
    "receita": "Receitas", "utiliza": "Ingredientes das receitas", "inclui": "Sub-receitas",
    "cliente": "Clientes", "forma_pagamento": "Formas de pagamento", "pedido": "Pedidos",
    "contem_receita": "Itens dos pedidos", "perda_estoque": "Perdas de estoque",
}

CONSULTAS = {
    "custos-receitas": ("Custos e rentabilidade", RAIZ / "database/queries/01_custos_receitas.sql"),
    "vendas": ("Vendas", RAIZ / "database/queries/02_vendas.sql"),
    "estoque-perdas": ("Estoque e perdas", RAIZ / "database/queries/03_estoque_perdas.sql"),
}


class Alteracao(BaseModel):
    chave: dict
    dados: dict


class Confirmacao(BaseModel):
    confirmacao: str


def _validar_tabela(tabela):
    if tabela not in TABELAS:
        raise HTTPException(status_code=404, detail="Tabela não permitida.")


def _erro_banco(erro):
    detalhe = getattr(erro.diag, "message_primary", None) or str(erro)
    raise HTTPException(status_code=400, detail=detalhe) from erro


def _metadados_tabela(cursor, tabela):
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
    colunas = [dict(item) for item in cursor.fetchall()]
    cursor.execute(
        """
        SELECT a.attname AS coluna
          FROM pg_index i
          JOIN pg_attribute a ON a.attrelid = i.indrelid
                             AND a.attnum = ANY(i.indkey)
         WHERE i.indrelid = %s::regclass AND i.indisprimary
         ORDER BY array_position(i.indkey, a.attnum);
        """,
        (tabela,),
    )
    primarias = [item["coluna"] for item in cursor.fetchall()]
    cursor.execute(
        """
        SELECT kcu.column_name AS coluna, ccu.table_name AS tabela_referenciada,
               ccu.column_name AS coluna_referenciada
          FROM information_schema.table_constraints tc
          JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
          JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
         WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s;
        """,
        (tabela,),
    )
    estrangeiras = {item["coluna"]: dict(item) for item in cursor.fetchall()}
    for coluna in colunas:
        coluna["primary_key"] = coluna["column_name"] in primarias
        coluna["foreign_key"] = estrangeiras.get(coluna["column_name"])
    return {"nome": tabela, "rotulo": ROTULOS[tabela], "primary_key": primarias, "colunas": colunas}


@router.get("/dados/metadados")
def metadados():
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            return [_metadados_tabela(cursor, tabela) for tabela in TABELAS]
    finally:
        conexao.close()


@router.get("/dados/{tabela}")
def listar_tabela(tabela: str):
    _validar_tabela(tabela)
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            meta = _metadados_tabela(cursor, tabela)
            ordem = sql.SQL(", ").join(map(sql.Identifier, meta["primary_key"]))
            comando = sql.SQL("SELECT * FROM {} ").format(sql.Identifier(tabela))
            if meta["primary_key"]:
                comando += sql.SQL("ORDER BY {} ").format(ordem)
            comando += sql.SQL("LIMIT 500")
            cursor.execute(comando)
            return [dict(item) for item in cursor.fetchall()]
    finally:
        conexao.close()


@router.post("/dados/{tabela}")
def inserir_registro(tabela: str, dados: dict = Body(...)):
    _validar_tabela(tabela)
    if not dados:
        raise HTTPException(status_code=400, detail="Informe os dados do registro.")
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            meta = _metadados_tabela(cursor, tabela)
            permitidas = {item["column_name"] for item in meta["colunas"]}
            campos = [campo for campo in dados if campo in permitidas]
            if not campos:
                raise HTTPException(status_code=400, detail="Nenhuma coluna válida foi informada.")
            comando = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
                sql.Identifier(tabela),
                sql.SQL(", ").join(map(sql.Identifier, campos)),
                sql.SQL(", ").join(sql.Placeholder() for _ in campos),
            )
            cursor.execute(comando, [dados[campo] for campo in campos])
            registro = dict(cursor.fetchone())
        conexao.commit()
        return registro
    except psycopg2.Error as erro:
        conexao.rollback()
        _erro_banco(erro)
    finally:
        conexao.close()


@router.put("/dados/{tabela}")
def atualizar_registro(tabela: str, alteracao: Alteracao):
    _validar_tabela(tabela)
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            meta = _metadados_tabela(cursor, tabela)
            if set(alteracao.chave) != set(meta["primary_key"]):
                raise HTTPException(status_code=400, detail="Chave primária incompleta.")
            permitidas = {item["column_name"] for item in meta["colunas"]}
            campos = [campo for campo in alteracao.dados if campo in permitidas]
            if not campos:
                raise HTTPException(status_code=400, detail="Nenhum dado para atualizar.")
            sets = sql.SQL(", ").join(
                sql.SQL("{} = {}").format(sql.Identifier(campo), sql.Placeholder()) for campo in campos
            )
            filtros = sql.SQL(" AND ").join(
                sql.SQL("{} = {}").format(sql.Identifier(campo), sql.Placeholder())
                for campo in meta["primary_key"]
            )
            comando = sql.SQL("UPDATE {} SET {} WHERE {} RETURNING *").format(
                sql.Identifier(tabela), sets, filtros
            )
            valores = [alteracao.dados[campo] for campo in campos]
            valores += [alteracao.chave[campo] for campo in meta["primary_key"]]
            cursor.execute(comando, valores)
            registro = cursor.fetchone()
            if not registro:
                raise HTTPException(status_code=404, detail="Registro não encontrado.")
        conexao.commit()
        return dict(registro)
    except psycopg2.Error as erro:
        conexao.rollback()
        _erro_banco(erro)
    finally:
        conexao.close()


@router.delete("/dados/{tabela}")
def excluir_registro(tabela: str, chave: dict = Body(...)):
    _validar_tabela(tabela)
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            meta = _metadados_tabela(cursor, tabela)
            if set(chave) != set(meta["primary_key"]):
                raise HTTPException(status_code=400, detail="Chave primária incompleta.")
            filtros = sql.SQL(" AND ").join(
                sql.SQL("{} = {}").format(sql.Identifier(campo), sql.Placeholder())
                for campo in meta["primary_key"]
            )
            cursor.execute(
                sql.SQL("DELETE FROM {} WHERE {}").format(sql.Identifier(tabela), filtros),
                [chave[campo] for campo in meta["primary_key"]],
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Registro não encontrado.")
        conexao.commit()
        return {"excluido": True}
    except psycopg2.Error as erro:
        conexao.rollback()
        _erro_banco(erro)
    finally:
        conexao.close()


@router.get("/analytics")
def listar_consultas():
    return [{"id": codigo, "titulo": titulo} for codigo, (titulo, _) in CONSULTAS.items()]


@router.post("/analytics/{codigo}")
def executar_consulta(codigo: str):
    if codigo not in CONSULTAS:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")
    titulo, arquivo = CONSULTAS[codigo]
    texto = arquivo.read_text(encoding="utf-8")
    comando = "\n".join(linha for linha in texto.splitlines() if not linha.strip().startswith("--")).strip()
    if not comando:
        raise HTTPException(status_code=409, detail=f"Preencha o arquivo {arquivo.name} com a consulta SQL.")
    sem_ponto = comando.rstrip().rstrip(";")
    if ";" in sem_ponto or not sem_ponto.lstrip().upper().startswith(("SELECT", "WITH")):
        raise HTTPException(status_code=400, detail="O arquivo deve conter uma única consulta SELECT.")
    conexao = conectar()
    try:
        conexao.set_session(readonly=True, autocommit=False)
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sem_ponto)
            linhas = [dict(item) for item in cursor.fetchall()]
            colunas = [item.name for item in cursor.description]
        conexao.rollback()
        return {"id": codigo, "titulo": titulo, "colunas": colunas, "linhas": linhas}
    except psycopg2.Error as erro:
        conexao.rollback()
        _erro_banco(erro)
    finally:
        conexao.close()


@router.post("/administracao/inicializar")
def inicializar_banco(confirmacao: Confirmacao):
    if confirmacao.confirmacao != "CRIAR":
        raise HTTPException(status_code=400, detail='Digite "CRIAR" para confirmar.')
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.categoria')")
            if cursor.fetchone()[0] is not None:
                raise HTTPException(status_code=409, detail="As tabelas já existem. Elimine-as antes de criar novamente.")
            for caminho in (
                "database/ddl/01_create_tables.sql", "database/seeds/02_insert_data.sql",
                "database/ddl/02_create_embeddings.sql", "database/ddl/03_create_chat.sql",
            ):
                cursor.execute((RAIZ / caminho).read_text(encoding="utf-8"))
        conexao.commit()
        gerar_embeddings()
        return {"criado": True, "mensagem": "Tabelas criadas, dados iniciais carregados e embeddings gerados."}
    except psycopg2.Error as erro:
        conexao.rollback()
        _erro_banco(erro)
    finally:
        conexao.close()


@router.post("/administracao/eliminar")
def eliminar_banco(confirmacao: Confirmacao):
    if confirmacao.confirmacao != "ELIMINAR":
        raise HTTPException(status_code=400, detail='Digite "ELIMINAR" para confirmar.')
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            nomes = ("chat_interacao", "receita_embedding") + TABELAS
            cursor.execute(
                sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                    sql.SQL(", ").join(map(sql.Identifier, nomes))
                )
            )
        conexao.commit()
        return {"eliminado": True, "mensagem": "Todas as tabelas foram eliminadas."}
    except psycopg2.Error as erro:
        conexao.rollback()
        _erro_banco(erro)
    finally:
        conexao.close()
