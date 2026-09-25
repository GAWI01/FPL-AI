import { render } from "@testing-library/react";
import { beforeEach, test, vi } from "vitest";

import { TeamProvider } from "@/app/providers/TeamProvider";
import type { TeamPick } from "@/lib/contracts";
import { expectNoA11yViolations } from "@/test-utils/accessibility";
import { SettingsWorkspace } from "./settings/SettingsWorkspace";
import { AppShell } from "./shell/AppShell";
import { TeamPitch } from "./team/TeamPitch";


vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

const positions = ["GKP", "DEF", "DEF", "DEF", "DEF", "MID", "MID", "MID", "MID", "FWD", "FWD", "GKP", "DEF", "MID", "FWD"];
const picks: TeamPick[] = positions.map((position_name, index) => ({
  player_id: index + 1,
  position: index + 1,
  name: `Player ${index + 1}`,
  position_name,
  team: `Club ${index + 1}`,
  price: 5 + index / 10,
  status: "a",
  event_points: index + 1,
  prediction: { predicted_points: 20 - index / 2 },
  is_captain: index === 5,
  is_vice_captain: index === 6,
}));

beforeEach(() => localStorage.clear());

test("application shell has no automated WCAG A/AA violations", async () => {
  const { container } = render(
    <TeamProvider>
      <AppShell><div>Page content</div></AppShell>
    </TeamProvider>,
  );

  await expectNoA11yViolations(container);
});

test("interactive squad has no automated WCAG A/AA violations", async () => {
  const { container } = render(<TeamPitch picks={picks} preferredMode="projected" />);

  await expectNoA11yViolations(container);
});

test("settings form has no automated WCAG A/AA violations", async () => {
  const { container } = render(
    <TeamProvider><SettingsWorkspace /></TeamProvider>,
  );

  await expectNoA11yViolations(container);
});
