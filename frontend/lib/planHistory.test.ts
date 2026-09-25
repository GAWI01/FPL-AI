import { afterEach, beforeEach, expect, test } from "vitest";

import { readPlanHistory, recordPlanSnapshot, type PlanSnapshot } from "./planHistory";


const base: PlanSnapshot = {
  event: 3,
  action: "Saka → Palmer",
  captain: "Palmer",
  netGain: 2.8,
  confidenceScore: 0.62,
  confidenceLabel: "MEDIUM",
  modelVersion: "gw3_predictions_v11.csv",
  recordedAt: "2026-09-01T10:00:00Z",
};


beforeEach(() => localStorage.clear());
afterEach(() => localStorage.clear());


test("records decision changes but deduplicates identical refreshes", () => {
  recordPlanSnapshot(localStorage, base);
  recordPlanSnapshot(localStorage, { ...base, recordedAt: "2026-09-01T10:05:00Z" });
  recordPlanSnapshot(localStorage, {
    ...base,
    action: "Hold the transfer",
    netGain: 0,
    recordedAt: "2026-09-01T12:00:00Z",
  });

  const history = readPlanHistory(localStorage);
  expect(history).toHaveLength(2);
  expect(history[0].action).toBe("Hold the transfer");
  expect(history[1].action).toBe("Saka → Palmer");
});


test("ignores tiny model refreshes but records a meaningful uncertainty change", () => {
  recordPlanSnapshot(localStorage, base);
  recordPlanSnapshot(localStorage, {
    ...base,
    netGain: 2.9,
    confidenceScore: 0.64,
    modelVersion: "gw3_predictions_v12.csv",
    recordedAt: "2026-09-01T10:05:00Z",
  });
  expect(readPlanHistory(localStorage)).toHaveLength(1);

  recordPlanSnapshot(localStorage, {
    ...base,
    confidenceScore: 0.78,
    confidenceLabel: "HIGH",
    modelVersion: "gw3_predictions_v13.csv",
    recordedAt: "2026-09-01T11:00:00Z",
  });

  expect(readPlanHistory(localStorage)).toHaveLength(2);
  expect(readPlanHistory(localStorage)[0].confidenceLabel).toBe("HIGH");
});


test("keeps only the six most recent local decision snapshots", () => {
  for (let index = 0; index < 8; index += 1) {
    recordPlanSnapshot(localStorage, {
      ...base,
      action: `Decision ${index}`,
      recordedAt: `2026-09-01T${String(index).padStart(2, "0")}:00:00Z`,
    });
  }

  const history = readPlanHistory(localStorage);
  expect(history).toHaveLength(6);
  expect(history[0].action).toBe("Decision 7");
  expect(history[5].action).toBe("Decision 2");
});


test("treats invalid local data as empty history", () => {
  localStorage.setItem("fpl-ai-plan-history", "not-json");

  expect(readPlanHistory(localStorage)).toEqual([]);
});
