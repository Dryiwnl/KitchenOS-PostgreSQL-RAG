
"""Execução das três consultas SQL obrigatórias."""

from pathlib import Path

import psycopg2
from fastapi import HTTPException
from psycopg2.extras import RealDictCursor

from backend.conexao import conectar

#Passa o caminho da raiz do projeto para a variável RAIZ.
RAIZ = Path(__file__).resolve().parent.parent

#Cria um dicionário com as 3 consultas SQL obrigatórias.
#Cada consulta possui uma chave e um valor. 
#O valor é uma tupla, onde o primeiro valor seria o nome da consulta
# e o segundo o caminho exato do arquivo onde o script SQL está localizado.
CONSULTAS = {
    #chave = custo-receitas.
    #valor = (Custos e rentabilidade, caminho do arquivo SQL)
    "custos-receitas": (
        "Custos e rentabilidade",
        RAIZ / "database/queries/01_custos_receitas.sql"
    ),

    "vendas": (
        "Vendas",
        RAIZ / "database/queries/02_vendas.sql"
    ),

    "estoque-perdas": (
        "Estoque e perdas",
        RAIZ / "database/queries/03_estoque_perdas.sql"
    )

}

#Função que seleciona todas as 3 consultas em uma lista.
def select_consultas():
    #Cria a lista vazia chamada resultado
    resultado = []
    #Para cada consulta no dicionário CONSULTAS, faz um append
    #na lista resultado do código e título de cada iteraçao.
    for codigo, valores in CONSULTAS.items():
        
        titulo = valores[0]

        resultado.append({
            "id": codigo,
            "titulo": titulo
        })
    #Retorna uma lista com todas as 3 consultas.
    return resultado

#Função que executa a consulta passada como parametro.
def executar_consulta(codigo):

    if codigo not in CONSULTAS:
        raise HTTPException(
            status_code=404,
            detail="Consulta não encontrada."
        )
    #O título e o caminho do arquivo do comando SQL
    #do item no dicionário que possui chave igual ao código passado, é armazenado
    #nas variáveis titulo e arquivo. Ou seja, o código passado como 
    #parametro é usado para buscar o item no dicionário CONSULTAS.
    titulo, arquivo = CONSULTAS[codigo]
    #O conteúdo do arquivo SQL é lido e armazenado na variável consulta_sql.
    consulta_sql = arquivo.read_text(encoding="utf-8")
    #Chama a função de se conectar ao banco. 
    conexao = conectar()

    try:
        conexao.set_session(readonly=True, autocommit=False)
        #Cri o cursor com a factory RealDictCursor, que retorna os resultados como dicionários.
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            #Executa a consulta SQL lida do arquivo.
            cursor.execute(consulta_sql)
            #Lisa vazia que armazenará todas as tuplas retornadas pela consulta SQL.
            registros = []
            #Para cada registro retornado pela consulta SQL, é feito um append na lista registros.
            #Ou seja, todas as tuplas retornadas são armazenadas na lista registros.
            for registro in cursor.fetchall():
                registros.append(dict(registro))
            #Lista vazia que armazenará o nome das colunas.
            colunas = []
            #Para cada coluna retornada pela consulta SQL, é feito um append na lista colunas.
            for coluna in cursor.description:
                colunas.append(coluna.name)

        conexao.rollback()

        return {
            "id": codigo,
            "titulo": titulo,
            "colunas": colunas,
            "linhas": registros
        }

    except psycopg2.Error as erro:

        conexao.rollback()

        detalhe = getattr(erro.diag, "message_primary", None) or str(erro)

        raise HTTPException(
            status_code=400,
            detail=detalhe
        ) from erro

    finally:
        conexao.close()
