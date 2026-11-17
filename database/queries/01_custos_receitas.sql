-- Consulta 1: custo estimado dos ingredientes por receita.
-- Tabelas: receita, utiliza, produto e item_compra.
-- Agregacao: media dos precos historicos de compra.
SELECT p.cod_produto,
       r.nome AS receita,
       p.nome AS ingrediente,
       u.quantidade,
       ROUND(AVG(ic.preco_unitario), 4) AS preco_medio,
       ROUND(u.quantidade * AVG(ic.preco_unitario), 4) AS custo_estimado
  FROM receita AS r
  JOIN utiliza AS u
    ON u.cod_receita = r.cod_receita
  JOIN produto AS p
    ON p.cod_produto = u.cod_produto
  JOIN item_compra AS ic
    ON ic.cod_produto = p.cod_produto
 GROUP BY p.cod_produto, r.cod_receita, r.nome, p.nome, u.quantidade
 ORDER BY r.nome, custo_estimado DESC;
