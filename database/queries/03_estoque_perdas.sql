-- Consulta 3: quantidade total perdida e prejuízo estimado por produto.
-- Tabelas: perda_estoque, produto e item_compra.
-- Agregação: soma das quantidades perdidas e média do preço unitário de compra.
SELECT
    p.nome AS produto,
    SUM(pe.quantidade) AS quantidade_perdida,
    ROUND(
        SUM(pe.quantidade) * (
            SELECT AVG(ic.preco_unitario)
            FROM item_compra AS ic
            WHERE ic.cod_produto = p.cod_produto
        ), 2
    ) AS prejuizo_estimado

FROM perda_estoque AS pe
INNER JOIN produto AS p
    ON p.cod_produto = pe.cod_produto

GROUP BY p.cod_produto, p.nome
ORDER BY quantidade_perdida DESC;
