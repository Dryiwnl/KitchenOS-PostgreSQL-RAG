-- Consulta 2: vendas pagas consolidadas por cliente.
-- Tabelas: cliente, pedido, forma_pagamento e contem_receita.
-- Agregacoes: quantidade de pedidos, quantidade de itens e valor vendido.
SELECT c.nome AS cliente,
       COUNT(DISTINCT p.cod_pedido) AS pedidos_pagos,
       SUM(cr.quantidade) AS itens_comprados,
       ROUND(SUM(cr.quantidade * cr.preco_unitario), 2) AS valor_total
  FROM cliente AS c
  JOIN pedido AS p
    ON p.cod_cliente = c.cod_cliente
  JOIN forma_pagamento AS fp
    ON fp.cod_forma_pagamento = p.cod_forma_pagamento
  JOIN contem_receita AS cr
    ON cr.cod_pedido = p.cod_pedido
 WHERE p.status = 'PAGO'
 GROUP BY c.cod_cliente, c.nome
 ORDER BY valor_total DESC, c.nome;
