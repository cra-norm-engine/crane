export interface CraGraphPosition { id: string; x: number; y: number }

export interface CraSearchableFact { id: string; title: string; shortLabel: string; summary: string; detail: string }

/** Places one focus node centrally and up to five neighbours in each side column. */
export function layoutCraGraph(ids: string[], selectedId: string): CraGraphPosition[] {
  if (!ids.length) return [];
  const focus = ids.includes(selectedId) ? selectedId : ids[0];
  const rest = ids.filter(id => id !== focus).slice(0, 10);
  const left = rest.filter((_, index) => index % 2 === 0);
  const right = rest.filter((_, index) => index % 2 === 1);
  const y = (index: number, count: number) => count === 1 ? 310 : 76 + index * (468 / (count - 1));
  return [
    { id: focus, x: 500, y: 310 },
    ...left.map((id, index) => ({ id, x: 185, y: y(index, left.length) })),
    ...right.map((id, index) => ({ id, x: 815, y: y(index, right.length) })),
  ];
}


/** Deterministic keyword ranking: it returns source facts, never generated legal advice. */
export function rankCraFacts<T extends CraSearchableFact>(nodes: T[], question: string): T[] {
  const stopWords = new Set(["a", "an", "and", "are", "do", "does", "for", "how", "i", "in", "is", "my", "of", "on", "or", "the", "to", "what", "which", "who"]);
  const tokens = question.toLocaleLowerCase().normalize("NFKD").replace(/[^\p{L}\p{N}\s]/gu, " ").split(/\s+/).filter(token => token.length > 1 && !stopWords.has(token));
  if (!tokens.length) return [];
  return nodes.map(node => {
    const title = `${node.title} ${node.shortLabel}`.toLocaleLowerCase();
    const summary = node.summary.toLocaleLowerCase();
    const detail = node.detail.toLocaleLowerCase();
    const score = tokens.reduce((total, token) => total + (title.includes(token) ? 5 : 0) + (summary.includes(token) ? 3 : 0) + (detail.includes(token) ? 1 : 0), 0);
    return { node, score };
  }).filter(result => result.score > 0).sort((a, b) => b.score - a.score || a.node.title.localeCompare(b.node.title)).map(result => result.node);
}


export interface CraGraphEdgeLike { from: string; to: string }
export interface CraSearchableQuestion { question: string }

/** Joins requested concepts using shortest undirected paths through explicit graph relations. */
export function findCraAnswerPath(conceptIds: string[], edges: CraGraphEdgeLike[]): string[] {
  if (!conceptIds.length) return [];
  const neighbours = new Map<string, string[]>();
  for (const edge of edges) {
    neighbours.set(edge.from, [...(neighbours.get(edge.from) ?? []), edge.to]);
    neighbours.set(edge.to, [...(neighbours.get(edge.to) ?? []), edge.from]);
  }
  const answer = [conceptIds[0]];
  for (const target of conceptIds.slice(1)) {
    const start = answer[answer.length - 1];
    if (start === target) continue;
    const queue: string[][] = [[start]];
    const seen = new Set([start]);
    let path: string[] = [];
    while (queue.length && !path.length) {
      const current = queue.shift()!;
      for (const next of neighbours.get(current[current.length - 1]) ?? []) {
        if (seen.has(next)) continue;
        const candidate = [...current, next];
        if (next === target) { path = candidate; break; }
        seen.add(next); queue.push(candidate);
      }
    }
    answer.push(...(path.length ? path.slice(1) : [target]));
  }
  return answer.filter((id, index) => index === 0 || id !== answer[index - 1]);
}

/** Ranks the curated question library; answers still come only from mapped graph evidence. */
export function rankCraQuestions<T extends CraSearchableQuestion>(questions: T[], input: string): T[] {
  const stopWords = new Set(["a", "an", "and", "are", "can", "do", "does", "for", "how", "i", "in", "is", "my", "of", "on", "or", "the", "to", "what", "when", "which", "who", "why"]);
  const tokens = input.toLocaleLowerCase().normalize("NFKD").replace(/[^\p{L}\p{N}\s]/gu, " ").split(/\s+/).filter(token => token.length > 1 && !stopWords.has(token));
  if (!tokens.length) return [];
  return questions.map(item => {
    const text = item.question.toLocaleLowerCase();
    return { item, score: tokens.reduce((total, token) => total + (text.includes(token) ? 1 : 0), 0) };
  }).filter(result => result.score > 0).sort((a, b) => b.score - a.score || a.item.question.localeCompare(b.item.question)).map(result => result.item);
}


export interface CraPoint { x: number; y: number }

/** Trims a directed edge at node borders and offsets its label from the line midpoint. */
export function layoutCraEdge(from: CraPoint, to: CraPoint): { x1: number; y1: number; x2: number; y2: number; labelX: number; labelY: number } {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const length = Math.hypot(dx, dy) || 1;
  const ux = dx / length;
  const uy = dy / length;
  const borderDistance = 1 / Math.max(Math.abs(ux) / 88, Math.abs(uy) / 32);
  let nx = -uy;
  let ny = ux;
  if (ny > 0 || (Math.abs(ny) < .001 && nx < 0)) { nx *= -1; ny *= -1; }
  return {
    x1: from.x + ux * borderDistance,
    y1: from.y + uy * borderDistance,
    x2: to.x - ux * (borderDistance + 5),
    y2: to.y - uy * (borderDistance + 5),
    labelX: (from.x + to.x) / 2 + nx * 15,
    labelY: (from.y + to.y) / 2 + ny * 15,
  };
}
