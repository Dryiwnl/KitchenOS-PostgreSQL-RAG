"""Chat generativo fundamentado nos dados PostgreSQL do KitchenOS."""

import json
import os
from pathlib import Path

from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import requests

from backend.conexao import carregar_configuracao, conectar
from backend.embeddings import buscar_receitas, carregar_modelo


MODELOS_FALLBACK = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
]
MODELO_LLM = MODELOS_FALLBACK[0]
TABELAS_CONTEXTO = (
    "categoria", "fornecedor", "produto", "compra", "item_compra",
    "nota_fiscal", "receita", "utiliza", "inclui", "cliente",
    "forma_pagamento", "pedido", "contem_receita", "perda_estoque",
)


def chave_configurada():
    carregar_configuracao()
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


def salvar_chave(api_key):
    """Salva a chave apenas no .env local, que é ignorado pelo Git."""
    api_key = api_key.strip()
    if len(api_key) < 20:
        raise ValueError("A chave informada parece inválida.")

    arquivo = Path(__file__).resolve().parent.parent / ".env"
    linhas = arquivo.read_text(encoding="utf-8").splitlines() if arquivo.exists() else []
    novas_linhas = [linha for linha in linhas if not linha.startswith("GEMINI_API_KEY=")]
    novas_linhas.append(f"GEMINI_API_KEY={api_key}")
    arquivo.write_text("\n".join(novas_linhas) + "\n", encoding="utf-8")
    os.environ["GEMINI_API_KEY"] = api_key
    return {"configurado": True, "modelo": MODELO_LLM}


def contexto_do_banco():
    """Lê apenas tabelas permitidas; o LLM nunca escreve nem cria SQL."""
    contexto = {}
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            for tabela in TABELAS_CONTEXTO:
                cursor.execute(
                    sql.SQL("SELECT * FROM {} LIMIT 200").format(sql.Identifier(tabela))
                )
                contexto[tabela] = [dict(registro) for registro in cursor.fetchall()]
    finally:
        conexao.close()
    return contexto


def gerar_texto_gemini(api_key, prompt):
    """Usa a API REST oficial com fallback automático entre modelos e timeout."""
    corpo = {
        "systemInstruction": {
            "parts": [{
                "text": (
                    "Você é o Chat IA do KitchenOS, especialista em gestão de restaurantes. "
                    "Responda em português brasileiro usando exclusivamente os dados fornecidos. "
                    "Nunca invente preços, estoques, custos, vendas, clientes ou receitas. "
                    "Quando a informação não estiver nos dados, diga isso claramente. "
                    "Você não executa SQL. Seja útil, direto e cite os nomes dos registros usados."
                )
            }]
        },
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 1200},
    }

    ultimo_erro = "Nenhum modelo disponível."
    for modelo in MODELOS_FALLBACK:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{modelo}:generateContent"
        )
        try:
            resposta = requests.post(
                url,
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=corpo,
                timeout=(10, 60),
            )
        except requests.Timeout:
            ultimo_erro = "O Gemini demorou mais de 60 segundos para responder."
            continue
        except requests.RequestException:
            ultimo_erro = "Não foi possível conectar à API do Gemini."
            continue

        if not resposta.ok:
            try:
                detalhe = resposta.json().get("error", {}).get("message", "")
            except ValueError:
                detalhe = ""
            ultimo_erro = detalhe or f"erro HTTP {resposta.status_code}"
            if (
                resposta.status_code in (404, 429, 503)
                or "high demand" in ultimo_erro.lower()
                or "no longer available" in ultimo_erro.lower()
            ):
                continue
            raise RuntimeError(f"O Gemini recusou a solicitação: {ultimo_erro}")

        dados = resposta.json()
        try:
            partes = dados["candidates"][0]["content"]["parts"]
            texto = "".join(parte.get("text", "") for parte in partes).strip()
        except (KeyError, IndexError, TypeError):
            ultimo_erro = "O Gemini respondeu sem conteúdo de texto."
            continue

        if texto:
            return texto
        ultimo_erro = "O Gemini respondeu sem conteúdo de texto."

    raise RuntimeError(f"O Gemini recusou a solicitação: {ultimo_erro}")


def responder(pergunta):
    carregar_configuracao()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Configure uma chave gratuita do Gemini antes de conversar.")

    referencias = buscar_receitas(pergunta, limite=5)
    contexto = contexto_do_banco()
    prompt = (
        "PERGUNTA DO USUÁRIO:\n" + pergunta + "\n\n"
        "RECEITAS RECUPERADAS POR SIMILARIDADE:\n"
        + json.dumps(referencias, ensure_ascii=False, default=str)
        + "\n\nDADOS ATUAIS DO POSTGRESQL:\n"
        + json.dumps(contexto, ensure_ascii=False, default=str)
    )

    texto_resposta = gerar_texto_gemini(api_key, prompt)
    vetor = carregar_modelo().encode([pergunta], normalize_embeddings=True)[0]
    codigos = [int(item["cod_receita"]) for item in referencias]

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO chat_interacao
                    (pergunta, resposta, embedding, receitas_recuperadas, modelo_llm)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING cod_interacao, data_interacao;
                """,
                (pergunta, texto_resposta, vetor.astype(float).tolist(), codigos, MODELO_LLM),
            )
            interacao = dict(cursor.fetchone())
        conexao.commit()
    finally:
        conexao.close()

    return {
        "interacao": interacao,
        "resposta": texto_resposta,
        "fontes": referencias,
        "modelo": MODELO_LLM,
    }


def historico():
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT cod_interacao, pergunta, resposta, modelo_llm, data_interacao
                  FROM chat_interacao ORDER BY cod_interacao;
                """
            )
            return [dict(registro) for registro in cursor.fetchall()]
    finally:
        conexao.close()
