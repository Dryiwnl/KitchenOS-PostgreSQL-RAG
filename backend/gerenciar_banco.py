"""Criação, carga inicial e eliminação das tabelas do projeto."""

from pathlib import Path

import psycopg2
from fastapi import HTTPException
from psycopg2 import sql

from backend.conexao import conectar
from backend.metadados import TABELAS


RAIZ = Path(__file__).resolve().parent.parent


def inicializar_banco(confirmacao):
    if confirmacao != "CRIAR":
        raise HTTPException(status_code=400, detail='Digite "CRIAR" para confirmar.')
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            #faz um select da primeira tabela do create_tableas.sql, ou seja
            #se retornar algo, as tabelas já foram inicializadas, se retornar
            #NULL vamos cria-las
            cursor.execute("SELECT to_regclass('public.categoria')")
            if cursor.fetchone()[0] is not None:
                raise HTTPException(status_code=409, detail="As tabelas já existem. Elimine-as antes de criar novamente.")
            #pega o cmainho de cada ddl do projeto e executa com o curtos
            for caminho in (
                "database/ddl/01_create_tables.sql", "database/seeds/02_insert_data.sql",
                "database/ddl/02_create_embeddings.sql", "database/ddl/03_create_chat.sql",
            ):
                cursor.execute((RAIZ / caminho).read_text(encoding="utf-8"))
        conexao.commit()
        return {"criado": True, "mensagem": "Tabelas criadas e dados iniciais carregados."}
    except psycopg2.Error as erro:
        conexao.rollback()
        detalhe = getattr(erro.diag, "message_primary", None) or str(erro)
        raise HTTPException(status_code=400, detail=detalhe) from erro
    finally:
        conexao.close()


def eliminar_banco(confirmacao):
    if confirmacao != "ELIMINAR":
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
        detalhe = getattr(erro.diag, "message_primary", None) or str(erro)
        raise HTTPException(status_code=400, detail=detalhe) from erro
    finally:
        conexao.close()
