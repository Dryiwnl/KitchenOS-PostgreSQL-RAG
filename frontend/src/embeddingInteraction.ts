export type InicioClique<T> = {
  x: number;
  y: number;
  ponto: T | undefined;
  arrastou: boolean;
};

export const LIMITE_CLIQUE_PX = 7;

export function iniciarClique<T>(x: number, y: number, ponto: T | undefined): InicioClique<T> {
  return { x, y, ponto, arrastou: false };
}

export function acompanharPonteiro<T>(inicio: InicioClique<T>, x: number, y: number): InicioClique<T> {
  if (inicio.arrastou) return inicio;
  const distancia = Math.hypot(x - inicio.x, y - inicio.y);
  return distancia > LIMITE_CLIQUE_PX ? { ...inicio, arrastou: true } : inicio;
}

export function concluirClique<T>(inicio: InicioClique<T> | undefined): T | undefined {
  return inicio && !inicio.arrastou ? inicio.ponto : undefined;
}

export function alternarSelecao<T extends { id: string }>(atuais: T[], ponto: T): T[] {
  if (atuais.some(item => item.id === ponto.id)) {
    return atuais.filter(item => item.id !== ponto.id);
  }
  return atuais.length < 2 ? [...atuais, ponto] : [ponto];
}
