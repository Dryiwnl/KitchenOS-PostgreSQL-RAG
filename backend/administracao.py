"""CRUD genérico das 14 tabelas, consultas acadêmicas e administração do banco."""

from fastapi import APIRouter

from backend.consultas import executar_consulta, select_consultas
from backend.crud import delete, insert, select, update
from backend.gerenciar_banco import eliminar_banco, inicializar_banco
from backend.metadados import select_metadados


router = APIRouter()


@router.get("/dados/metadados")
def rota_metadados():
    return select_metadados()


@router.get("/dados/{tabela}")
def rota_select(tabela: str):
    return select(tabela)


@router.post("/dados/{tabela}")
def rota_insert(tabela: str, dados: dict):
    return insert(tabela, dados)


@router.put("/dados/{tabela}")
def rota_update(tabela: str, alteracao: dict):
    return update(tabela, alteracao.get("chave", {}), alteracao.get("dados", {}))


@router.delete("/dados/{tabela}")
def rota_delete(tabela: str, chave: dict):
    return delete(tabela, chave)

#Ao entrar na aba de analytics, a rota /analytics é chamada, que chama a
#  função select_consultas, que retorna uma lista com as 3 consultas SQL obrigatórias.
@router.get("/analytics")
def rota_select_consultas():
    return select_consultas()

#Como o select_consultas já foi chamado assim que entramos na aba
#ao clicarmos no botão executar sql, já temos as três consultas,
#basta passar o código como parâmetro para retornar apenas a consulta
#Selecionada
@router.post("/analytics/{codigo}")
def rota_executar_consulta(codigo: str):
    return executar_consulta(codigo)


@router.post("/administracao/inicializar")
def rota_inicializar_banco(dados: dict):
    return inicializar_banco(dados.get("confirmacao", ""))


@router.post("/administracao/eliminar")
def rota_eliminar_banco(dados: dict):
    return eliminar_banco(dados.get("confirmacao", ""))
