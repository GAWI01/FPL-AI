import { expect, test } from "vitest";

import { legacyModuleTarget } from "./navigation";


test.each([
  ["my-team", "/team"],
  ["transfer-center", "/plan#transfer-center"],
  ["ai-recommendations", "/plan#ai-recommendations"],
  ["players", "/explore#player-market"],
  ["fixtures", "/explore#fixture-matrix"],
  ["chips", "/plan#chip-advisor"],
  ["statistics", "/review#statistics"],
  ["team-history", "/review"],
  ["settings", "/settings"],
])("maps the legacy %s route to the canonical product surface", (module, target) => {
  expect(legacyModuleTarget(module)).toBe(target);
});


test("does not fabricate a destination for unknown modules", () => {
  expect(legacyModuleTarget("coming-soon")).toBeNull();
});
