
"""Operações SELECT, INSERT, UPDATE e DELETE das 14 tabelas."""

import psycopg2
from fastapi import HTTPException
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from backend.conexao import conectar
from backend.metadados import select_metadados_tabela, validar_tabela


# Trata os erros retornados pelo PostgreSQL.
def erro_banco(erro):
    mensagem = str(erro)

    if erro.diag.message_primary:
        mensagem = erro.diag.message_primary

    raise HTTPException(status_code=400, detail=mensagem)


#Constroi o comando Select * from {tabela} order by {coluna_pk} limit 500
def select(tabela):
    #Verifica se a tabela é uma das 14 do banco.
    validar_tabela(tabela)
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            #todos os metadados são armazenados em estrutura
            estrutura = select_metadados_tabela(cursor, tabela)
            #na variável estrutura, a chave "primary_key" contém uma lista com o nome das colunas que compõem a PK da tabela.
            primarias = estrutura["primary_key"]
            #como a parametrização %s não funciona para nomes de tabelas e colunas
            #passamos o nome da tabela para {}
            consulta_sql = sql.SQL("SELECT * FROM {}").format(
                sql.Identifier(tabela)
            )

            if primarias:
                colunas_ordem = []
                #faz um for nas chaves primárias da tabela, fazendo um append 
                #da coluna na lista colunas_ordem
                for coluna in primarias:
                    colunas_ordem.append(sql.Identifier(coluna))
                #ordem armazena todas as pk da tabela, onde o comando sql.SQL(", ").join(colunas_ordem) 
                # junta todas as pk da tabela separadas por vírgula.
                #logo teremos todas as pk separadas do mesmo jeito que deve ser em sql.
                ordem = sql.SQL(", ").join(colunas_ordem)
                #consulta_sql que até agora só tinha o select, agora é concatenado com o ORDER BY
                #com todas as pk e o LIMIT 500, para não retornar mais do que 500 registros.
                consulta_sql += sql.SQL(" ORDER BY {}").format(ordem)
            consulta_sql += sql.SQL(" LIMIT 500")
            #Executa o comando e rotorna todas as linhas retornadas, que são armazenadas na lista registros, onde cada registro é um dicionário.
            cursor.execute(consulta_sql)
            registros = []
            for registro in cursor.fetchall():
                registros.append(dict(registro))
            return registros
    finally:
        conexao.close()


#constroi o comando:
#INSERT INTO {tabela} ({colunas}) 
# VALUES ({valores})
#  RETURNING *
#Os parametros da função é o nome da tabela  e um dicionário dados, contendo
#como chave o nome da coluna e como valor o valor a ser inserido na coluna.
def insert(tabela, dados):
    validar_tabela(tabela)
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            #todos os metadados são armazenados em estrutura
            estrutura = select_metadados_tabela(cursor, tabela)
            #cria a lista de colunas permitidas, para fazer a verificação do comando
            colunas_permitidas = []
            #for em estrutura na chave "colunas", onde cada nome de coluna é 
            #feito um append para a lista colunas_permitidas
            for coluna in estrutura["colunas"]:
                colunas_permitidas.append(coluna["column_name"])
            #nova lista. 
            colunas = []
            #itera sobre cada chave em dados atribuindo para coluna, 
            # se a coluna estiver na lista de colunas_permitidas, 
            # é feito um append na lista colunas.
            for coluna in dados:
                if coluna in colunas_permitidas:
                    colunas.append(coluna)
            if not colunas:
                raise HTTPException(
                    status_code=400,
                    detail="Nenhuma coluna válida foi informada."
                )
            nomes_colunas = []
            marcadores = []
            valores = []
            #A cada iteração do for, coluna recebe o nome da coluna do dicionário colunas
            #nome_colunas sofre um append com o nome passado para coluna
            #como estamos fazendo um insert, para cada coluna teremos um valor,
            #o place holder adiciona um %s para parametizar o valor do insert.
            #já o valor sofre um append do valor em dados onde a chave é o nome da coluna
            for coluna in colunas:
                nomes_colunas.append(sql.Identifier(coluna))
                marcadores.append(sql.Placeholder())
                valores.append(dados[coluna])
            #cria o comando e executa
            consulta_sql = sql.SQL(
                "INSERT INTO {} ({}) VALUES ({}) RETURNING *"
            ).format(
                sql.Identifier(tabela),
                sql.SQL(", ").join(nomes_colunas),
                sql.SQL(", ").join(marcadores)
            )
            cursor.execute(consulta_sql, valores)
            registro = dict(cursor.fetchone())
        conexao.commit()
        return registro

    except psycopg2.Error as erro:
        conexao.rollback()
        erro_banco(erro)

    finally:
        conexao.close()


#constroi o comando:
#UPDATE tabela
#SET atribitos = x
#WHERE chave
#RETURNING *
#Os parametros da função são: nome da tabela, qual a chave que queremos alterar (vai no where) e dados que é u
#dicionário
def update(tabela, chave, dados):
    validar_tabela(tabela)
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            #todos os metadados são armazenados em estrutura
            estrutura = select_metadados_tabela(cursor, tabela)
            #na variável estrutura, a chave "primary_key" contém uma lista com o nome das colunas que compõem a PK da tabela.
            primarias = estrutura["primary_key"]
            #se todas as chaves do parâmetro chave for diferente do conjunto de PKs da tabela, retorna um erro
            if set(chave) != set(primarias):
                raise HTTPException(
                    status_code=400,
                    detail="Chave primária incompleta."
                )
            #itera sobre cada chave em dados atribuindo para coluna, 
            # se a coluna estiver na lista de colunas_permitidas, 
            # é feito um append na lista colunas.
            colunas_permitidas = []
            for coluna in estrutura["colunas"]:
                colunas_permitidas.append(coluna["column_name"])
            colunas = []
            for coluna in dados:
                if coluna in colunas_permitidas:
                    colunas.append(coluna)
            if not colunas:
                raise HTTPException(
                    status_code=400,
                    detail="Nenhum dado para atualizar."
                )
            alteracoes = []
            filtros = []
            valores = []
            for coluna in colunas:
                #itera sobre as colunas construindo o SET:
                #nome_coluna = %s
                alteracao = sql.SQL("{} = {}").format(
                    sql.Identifier(coluna),
                    sql.Placeholder()
                )
                alteracoes.append(alteracao)
                #preenche o %s
                valores.append(dados[coluna])
            #itera sobre as PK constuindo o where
            #pk = %s
            for coluna in primarias:
                filtro = sql.SQL("{} = {}").format(
                    sql.Identifier(coluna),
                    sql.Placeholder()
                )
                filtros.append(filtro)
                #preenche o %s
                valores.append(chave[coluna])
            #constroi o comando completo e executa
            consulta_sql = sql.SQL(
                "UPDATE {} SET {} WHERE {} RETURNING *"
            ).format(
                sql.Identifier(tabela),
                sql.SQL(", ").join(alteracoes),
                sql.SQL(" AND ").join(filtros)
            )
            cursor.execute(consulta_sql, valores)
            registro = cursor.fetchone()
            if registro is None:
                raise HTTPException(
                    status_code=404,
                    detail="Registro não encontrado."
                )
        conexao.commit()
        return dict(registro)
    except psycopg2.Error as erro:
        conexao.rollback()
        erro_banco(erro)
    finally:
        conexao.close()

# Exclui um registro de uma tabela.
def delete(tabela, chave):
    validar_tabela(tabela)
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            #todos os metadados são armazenados em estrutura
            estrutura = select_metadados_tabela(cursor, tabela)
            #na variável estrutura, a chave "primary_key" contém uma lista com o nome das colunas que compõem a PK da tabela.
            primarias = estrutura["primary_key"]
            #se todas as chaves do parâmetro chave for diferente do conjunto de PKs da tabela, retorna um erro
            if set(chave) != set(primarias):
                raise HTTPException(
                    status_code=400,
                    detail="Chave primária incompleta."
                )
            filtros = []
            valores = []
            #itera sobre as PK constuindo o where
            #pk = %s
            for coluna in primarias:
                filtro = sql.SQL("{} = {}").format(
                    sql.Identifier(coluna),
                    sql.Placeholder()
                )
                filtros.append(filtro)
                valores.append(chave[coluna])
            #cnstroi o comando completo e executa com o cursor
            consulta_sql = sql.SQL(
                "DELETE FROM {} WHERE {}"
            ).format(
                sql.Identifier(tabela),
                sql.SQL(" AND ").join(filtros)
            )

            cursor.execute(consulta_sql, valores)
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Registro não encontrado."
                )
        conexao.commit()
        return {"excluido": True}
    except psycopg2.Error as erro:
        conexao.rollback()
        erro_banco(erro)

    finally:
        conexao.close()