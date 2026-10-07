import { describe, expect, it } from "vitest";
import { craLearningEdges, craLearningNodes, craSources, validateCraLearningGraph } from "@/content/cra-learning";
import { craQuestions, validateCraQuestions } from "@/content/cra-questions";
import { findCraAnswerPath, layoutCraEdge, layoutCraGraph, rankCraFacts, rankCraQuestions } from "@/utils/cra-graph-layout";

describe("CRA learning graph", () => {
  it("contains only source-linked, internally valid content", () => {
    expect(validateCraLearningGraph()).toEqual([]);
    expect(craLearningNodes.length).toBeGreaterThan(75);
    const positions = layoutCraGraph(craLearningNodes.slice(0, 11).map(node => node.id), craLearningNodes[0].id);
    expect(positions).toHaveLength(11);
    for (const x of [185, 815]) {
      const ys = positions.filter(position => position.x === x).map(position => position.y).sort((a, b) => a - b);
      expect(ys.every((y, index) => index === 0 || y - ys[index - 1] > 64)).toBe(true);
    }
    expect(craSources.law.authority).toContain("Binding");
    expect(craSources.guidance.authority).toContain("Non-binding");
    expect(craSources.faq.authority).toContain("Non-authoritative");
  });

  it("finds useful source facts from a plain-language question", () => {
    expect(rankCraFacts(craLearningNodes, "support period security updates").slice(0, 5).map(node => node.id)).toContain("support");
    expect(rankCraFacts(craLearningNodes, "actively exploited vulnerability report").slice(0, 5).map(node => node.id)).toContain("active_vulnerability");
    expect(rankCraFacts(craLearningNodes, "Who must report a vulnerability?").slice(0, 4).map(node => node.id)).toContain("reporting");
    expect(rankCraFacts(craLearningNodes, "Which conformity assessment route applies?").slice(0, 4).map(node => node.id)).toContain("conformity");
    expect(rankCraFacts(craLearningNodes, "the and what")).toEqual([]);
  });

  it("answers the 100-question challenge through sourced graph paths", () => {
    expect(validateCraQuestions(craLearningNodes, craLearningEdges)).toEqual([]);
    expect(craQuestions).toHaveLength(100);
    let answered = 0;
    for (const item of craQuestions) {
      const path = findCraAnswerPath(item.concepts, craLearningEdges);
      const ranked = rankCraQuestions(craQuestions, item.question).slice(0, 5);
      const hasTargets = item.concepts.every(id => path.includes(id));
      const hasSources = path.every(id => craLearningNodes.find(node => node.id === id)?.references.length);
      const hasRelations = path.slice(1).every((id, index) => craLearningEdges.some(edge => (edge.from === path[index] && edge.to === id) || (edge.to === path[index] && edge.from === id)));
      if (hasTargets && hasSources && hasRelations && ranked.includes(item)) answered += 1;
    }
    expect(answered).toBe(100);
  });

  it("places directional edges outside nodes and labels away from their lines", () => {
    const horizontal = layoutCraEdge({ x: 185, y: 310 }, { x: 500, y: 310 });
    expect(horizontal.x1).toBeGreaterThan(185);
    expect(horizontal.x2).toBeLessThan(500);
    expect(horizontal.labelY).toBeLessThan(310);
    const vertical = layoutCraEdge({ x: 185, y: 76 }, { x: 185, y: 193 });
    expect(vertical.y1).toBeGreaterThan(76);
    expect(vertical.y2).toBeLessThan(193);
    expect(vertical.labelX).toBeGreaterThan(185);
  });
});
