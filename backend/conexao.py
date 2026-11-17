"""Conexão inicial do KitchenOS com o PostgreSQL."""

import getpass
import os
from pathlib import Path

try:
    import psycopg2
except ImportError:
    print("A biblioteca psycopg2 ainda não está instalada.")
    print("Execute: pip install -r backend/requirements.txt")
    raise SystemExit(1)


def carregar_configuracao():
    """Lê a configuração local do arquivo .env, quando ele existir."""
    arquivo_env = Path(__file__).resolve().parent.parent / ".env"

    if arquivo_env.exists():
        for linha in arquivo_env.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                chave, valor = linha.split("=", 1)
                os.environ.setdefault(chave, valor)


def conectar(senha=None):
    """Abre e retorna uma conexão com o banco restaurante."""
    carregar_configuracao()

    if senha is None:
        senha = os.getenv("DB_PASSWORD")

    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "restaurante"),
        user=os.getenv("DB_USER", "kitchenos"),
        password=senha,
    )


def testar_conexao():
    """Conecta ao banco e mostra informações básicas da conexão."""
    carregar_configuracao()
    senha = os.getenv("DB_PASSWORD")

    if not senha:
        senha = getpass.getpass("Digite a senha do banco: ")

    conexao = None

    try:
        conexao = conectar(senha)
        cursor = conexao.cursor()

        cursor.execute("SELECT current_database(), version();")
        banco, versao = cursor.fetchone()

        print("Conexão realizada com sucesso!")
        print("Banco conectado:", banco)
        print("Versão:", versao)

        cursor.close()
    except psycopg2.Error as erro:
        print("Não foi possível conectar ao PostgreSQL.")
        print("Detalhes:", erro)
    finally:
        if conexao is not None:
            conexao.close()
            print("Conexão encerrada.")


if __name__ == "__main__":
    testar_conexao()
