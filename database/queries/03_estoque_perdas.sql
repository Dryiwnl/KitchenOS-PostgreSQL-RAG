-- Consulta 3: valor estimado das perdas de estoque por produto.
-- Tabelas: perda_estoque, produto e item_compra.
-- Agregacoes: quantidade perdida, preco medio e valor estimado da perda.
WITH preco_produto AS (
    SELECT cod_produto,
           AVG(preco_unitario) AS preco_medio
      FROM item_compra
     GROUP BY cod_produto
)
SELECT p.nome AS produto,
       SUM(pe.quantidade) AS quantidade_perdida,
       ROUND(MAX(pp.preco_medio), 4) AS preco_medio,
       ROUND(SUM(pe.quantidade) * MAX(pp.preco_medio), 2) AS valor_estimado
  FROM perda_estoque AS pe
  JOIN produto AS p
    ON p.cod_produto = pe.cod_produto
  JOIN preco_produto AS pp
    ON pp.cod_produto = p.cod_produto
 GROUP BY p.cod_produto, p.nome
 ORDER BY valor_estimado DESC, p.nome;
