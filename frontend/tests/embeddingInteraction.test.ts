import assert from "node:assert/strict";
import test from "node:test";

import {
  acompanharPonteiro,
  alternarSelecao,
  concluirClique,
  iniciarClique,
  LIMITE_CLIQUE_PX,
} from "../src/embeddingInteraction.ts";

type Ponto = { id: string };
const a: Ponto = { id: "receita-1" };
const b: Ponto = { id: "consulta-1" };
const c: Ponto = { id: "receita-2" };

test("mil ciclos de clicar e clicar novamente sempre selecionam e desselecionam", () => {
  for (let i = 0; i < 1000; i++) {
    let selecionados: Ponto[] = [];
    selecionados = alternarSelecao(selecionados, a);
    assert.deepEqual(selecionados, [a]);
    selecionados = alternarSelecao(selecionados, a);
    assert.deepEqual(selecionados, []);
  }
});

test("clique com pequeno tremor ainda conta como um único clique", () => {
  for (let i = 0; i < 1000; i++) {
    let gesto = iniciarClique(100, 100, a);
    gesto = acompanharPonteiro(gesto, 100 + LIMITE_CLIQUE_PX, 100);
    assert.equal(concluirClique(gesto), a);
  }
});

test("arrastar para girar nunca seleciona um ponto", () => {
  for (let i = 0; i < 1000; i++) {
    let gesto = iniciarClique(100, 100, a);
    gesto = acompanharPonteiro(gesto, 100 + LIMITE_CLIQUE_PX + 1, 100);
    assert.equal(concluirClique(gesto), undefined);
  }
});

test("segurar não alterna nada até soltar e alterna apenas uma vez", () => {
  const gesto = iniciarClique(100, 100, a);
  let selecionados: Ponto[] = [];
  assert.deepEqual(selecionados, []);
  const ponto = concluirClique(gesto);
  if (ponto) selecionados = alternarSelecao(selecionados, ponto);
  assert.deepEqual(selecionados, [a]);
});

test("dois pontos permanecem selecionados e o terceiro inicia nova comparação", () => {
  let selecionados: Ponto[] = [];
  selecionados = alternarSelecao(selecionados, a);
  selecionados = alternarSelecao(selecionados, b);
  assert.deepEqual(selecionados, [a, b]);
  selecionados = alternarSelecao(selecionados, c);
  assert.deepEqual(selecionados, [c]);
});
