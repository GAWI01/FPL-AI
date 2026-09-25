import { act } from "@testing-library/react";
import axe, { type AxeResults } from "axe-core";
import { expect } from "vitest";


function describeViolations(results: AxeResults) {
  return results.violations.map((violation) => ({
    id: violation.id,
    impact: violation.impact,
    targets: violation.nodes.map((node) => node.target),
  }));
}

export async function expectNoA11yViolations(container: HTMLElement) {
  let results: AxeResults | undefined;
  await act(async () => {
    results = await axe.run(container, {
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] },
      rules: { "color-contrast": { enabled: false } },
    });
  });
  expect(describeViolations(results!)).toEqual([]);
}
