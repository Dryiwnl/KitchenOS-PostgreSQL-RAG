"""Geração e busca de embeddings reais das receitas do KitchenOS."""

from functools import lru_cache

import numpy as np
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA

from backend.conexao import conectar


MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
PESO_NOME = 0.30
PESO_FICHA = 0.35
PESO_RELACOES = 0.35


@lru_cache(maxsize=1)
def carregar_modelo():
    return SentenceTransformer(MODELO, local_files_only=True)

#Função que coleta todos os textos de receitas para futuramente gerar os embeddings
def documentos_das_receitas():
    """Monta facetas curtas e inclui relações indiretas entre receitas."""
    with conectar() as conexao:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            #Consulta as receitas, colocando na lista receitas
            cursor.execute(
                """
                SELECT r.cod_receita, r.nome, c.nome AS categoria, r.modo_preparo
                  FROM receita r
                  JOIN categoria c ON c.cod_categoria = r.cod_categoria
                 ORDER BY r.cod_receita;
                """
            )
            receitas = {int(r["cod_receita"]): dict(r) for r in cursor.fetchall()}

            #Consulta os ingredientes em cada receita, colocando na lista ingredientes_diretos
            cursor.execute(
                """
                SELECT u.cod_receita, p.nome
                  FROM utiliza u
                  JOIN produto p ON p.cod_produto = u.cod_produto
                 ORDER BY u.cod_receita, p.nome;
                """
            )
            ingredientes_diretos = {codigo: [] for codigo in receitas}
            for registro in cursor.fetchall():
                ingredientes_diretos[int(registro["cod_receita"])].append(registro["nome"])
            #Consulta as sub-receitas, colocando na lista subreceitas_diretas
            cursor.execute(
                """
                SELECT cod_receita, cod_subreceita
                  FROM inclui
                 ORDER BY cod_receita, cod_subreceita;
                """
            )
            subreceitas_diretas = {codigo: [] for codigo in receitas}
            for registro in cursor.fetchall():
                subreceitas_diretas[int(registro["cod_receita"])].append(
                    int(registro["cod_subreceita"])
                )

    def expandir(codigo, caminho=()):
        if codigo in caminho:
            return set(), set()
        ingredientes = set(ingredientes_diretos[codigo])
        descendentes = set(subreceitas_diretas[codigo])
        for subcodigo in subreceitas_diretas[codigo]:
            subingredientes, subdescendentes = expandir(subcodigo, caminho + (codigo,))
            ingredientes.update(subingredientes)
            descendentes.update(subdescendentes)
        return ingredientes, descendentes

    resultado = []
    for codigo, receita in receitas.items():
        ingredientes, descendentes = expandir(codigo)
        nomes_subreceitas = [receitas[subcodigo]["nome"] for subcodigo in sorted(descendentes)]
        diretos = ingredientes_diretos[codigo]
        nome = receita["nome"]
        ficha = (
            f"Receita {nome}. Categoria: {receita['categoria']}. "
            f"Ingredientes diretos: {', '.join(diretos) if diretos else 'nenhum'}. "
            f"Preparo: {receita['modo_preparo'] or 'não informado'}."
        )
        relacoes = (
            f"A receita {nome} possui as sub-receitas "
            f"{', '.join(nomes_subreceitas) if nomes_subreceitas else 'nenhuma'}. "
            f"Considerando todos os níveis, usa os ingredientes "
            f"{', '.join(sorted(ingredientes)) if ingredientes else 'nenhum'}."
        )
        resultado.append(
            {
                "cod_receita": codigo,
                "nome_semantico": f"Receita: {nome}.",
                "ficha": ficha,
                "relacoes": relacoes,
                "texto": f"{ficha} {relacoes}",
            }
        )
    return resultado


def textos_das_receitas():
    return [(r["cod_receita"], r["texto"]) for r in documentos_das_receitas()]


def gerar_embeddings():
    receitas = documentos_das_receitas()
    modelo = carregar_modelo()
    vetores_nome = modelo.encode(
        [r["nome_semantico"] for r in receitas], normalize_embeddings=True
    )
    vetores_ficha = modelo.encode([r["ficha"] for r in receitas], normalize_embeddings=True)
    vetores_relacoes = modelo.encode(
        [r["relacoes"] for r in receitas], normalize_embeddings=True
    )
    vetores = (
        PESO_NOME * vetores_nome
        + PESO_FICHA * vetores_ficha
        + PESO_RELACOES * vetores_relacoes
    )
    vetores /= np.linalg.norm(vetores, axis=1, keepdims=True)

    with conectar() as conexao:
        with conexao.cursor() as cursor:
            for receita, vetor in zip(receitas, vetores):
                cursor.execute(
                    """
                    INSERT INTO receita_embedding
                        (cod_receita, texto, embedding, modelo, dimensao,
                         data_atualizacao)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (cod_receita) DO UPDATE
                       SET texto = EXCLUDED.texto,
                           embedding = EXCLUDED.embedding,
                           modelo = EXCLUDED.modelo,
                           dimensao = EXCLUDED.dimensao,
                           data_atualizacao = CURRENT_TIMESTAMP;
                    """,
                    (
                        receita["cod_receita"],
                        receita["texto"],
                        vetor.astype(float).tolist(),
                        MODELO,
                        len(vetor),
                    ),
                )
        conexao.commit()
    return {"quantidade": len(receitas), "modelo": MODELO, "dimensao": len(vetores[0])}


def buscar_receitas(pergunta, limite=5):
    modelo = carregar_modelo()
    vetor_pergunta = modelo.encode([pergunta], normalize_embeddings=True)[0]

    with conectar() as conexao:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT e.cod_receita, r.nome, c.nome AS categoria,
                       r.preco_de_venda, e.texto, e.embedding
                  FROM receita_embedding e
                  JOIN receita r ON r.cod_receita = e.cod_receita
                  JOIN categoria c ON c.cod_categoria = r.cod_categoria;
                """
            )
            registros = cursor.fetchall()

    resultados = []
    for registro in registros:
        vetor = np.asarray(registro.pop("embedding"), dtype=float)
        denominador = np.linalg.norm(vetor_pergunta) * np.linalg.norm(vetor)
        similaridade = float(np.dot(vetor_pergunta, vetor) / denominador)
        registro["similaridade"] = round(similaridade, 4)
        resultados.append(dict(registro))

    return sorted(resultados, key=lambda item: item["similaridade"], reverse=True)[:limite]


def dados_explorer():
    """Mostra somente consultas realizadas no Chat IA e receitas recuperadas."""
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT e.cod_receita, r.nome, c.nome AS categoria,
                       e.texto, e.modelo, e.dimensao, e.embedding
                  FROM receita_embedding e
                  JOIN receita r ON r.cod_receita = e.cod_receita
                  JOIN categoria c ON c.cod_categoria = r.cod_categoria
                 ORDER BY e.cod_receita;
                """
            )
            receitas = [dict(registro) for registro in cursor.fetchall()]
            cursor.execute(
                """
                SELECT cod_interacao, pergunta, embedding, receitas_recuperadas,
                       modelo_llm, data_interacao
                  FROM chat_interacao ORDER BY cod_interacao;
                """
            )
            interacoes = [dict(registro) for registro in cursor.fetchall()]
    finally:
        conexao.close()

    if not interacoes or len(receitas) < 2:
        return {"metodo": "PCA", "pontos": [], "variancia_explicada": []}

    codigos_visiveis = {
        int(codigo)
        for interacao in interacoes
        for codigo in (interacao["receitas_recuperadas"] or [])
    }
    receitas_visiveis = [
        receita for receita in receitas if int(receita["cod_receita"]) in codigos_visiveis
    ]
    registros_visiveis = [
        ("receita", receita, np.asarray(receita["embedding"], dtype=float))
        for receita in receitas_visiveis
    ] + [
        ("consulta", interacao, np.asarray(interacao["embedding"], dtype=float))
        for interacao in interacoes
    ]
    matriz = np.asarray([registro[2] for registro in registros_visiveis], dtype=float)
    matriz /= np.linalg.norm(matriz, axis=1, keepdims=True)
    if len(registros_visiveis) < 3:
        return {"metodo": "PCA", "pontos": [], "variancia_explicada": []}
    pca = PCA(n_components=3).fit(matriz)
    coordenadas = pca.transform(matriz)
    pontos = []

    for (tipo, registro, _), coordenada in zip(registros_visiveis, coordenadas):
        if tipo == "receita":
            codigo = int(registro["cod_receita"])
            ponto = {
                "id": f"receita-{codigo}", "tipo": "receita",
                "nome": registro["nome"], "categoria": registro["categoria"],
                "texto": registro["texto"], "modelo": registro["modelo"],
                "dimensao": registro["dimensao"],
            }
        else:
            ponto = {
                "id": f"consulta-{registro['cod_interacao']}", "tipo": "consulta",
                "nome": registro["pergunta"], "categoria": "Pergunta ao Chat IA",
                "texto": registro["pergunta"], "modelo": MODELO,
                "dimensao": len(registro["embedding"]),
            }
        ponto.update(
            {
                "x": round(float(coordenada[0]), 6),
                "y": round(float(coordenada[1]), 6),
                "z": round(float(coordenada[2]), 6),
            }
        )
        pontos.append(ponto)

    return {
        "metodo": "PCA",
        "variancia_explicada": [round(float(v), 4) for v in pca.explained_variance_ratio_],
        "pontos": pontos,
    }


def _vetor_do_ponto(identificador):
    tipo, codigo_texto = identificador.split("-", 1)
    codigo = int(codigo_texto)
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            if tipo == "receita":
                cursor.execute(
                    "SELECT embedding FROM receita_embedding WHERE cod_receita = %s", (codigo,)
                )
            elif tipo == "consulta":
                cursor.execute(
                    "SELECT embedding FROM chat_interacao WHERE cod_interacao = %s", (codigo,)
                )
            else:
                raise ValueError("Tipo de ponto inválido.")
            registro = cursor.fetchone()
    finally:
        conexao.close()
    if not registro:
        raise ValueError("Ponto não encontrado.")
    return np.asarray(registro[0], dtype=float)


def comparar_pontos(primeiro, segundo):
    vetor_a = _vetor_do_ponto(primeiro)
    vetor_b = _vetor_do_ponto(segundo)
    similaridade = float(np.dot(vetor_a, vetor_b) / (np.linalg.norm(vetor_a) * np.linalg.norm(vetor_b)))
    similaridade = float(np.clip(similaridade, -1.0, 1.0))
    angulo = float(np.degrees(np.arccos(similaridade)))
    return {
        "primeiro": primeiro,
        "segundo": segundo,
        "similaridade_cosseno": round(similaridade, 6),
        "angulo_graus": round(angulo, 4),
        "distancia_cosseno": round(1.0 - similaridade, 6),
        "distancia_euclidiana": round(float(np.linalg.norm(vetor_a - vetor_b)), 6),
        "dimensoes": int(vetor_a.size),
    }
