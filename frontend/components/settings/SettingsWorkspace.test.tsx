import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { TeamProvider } from "@/app/providers/TeamProvider";
import { SettingsWorkspace } from "./SettingsWorkspace";


beforeEach(() => localStorage.setItem("fpl-ai-team-id", "123"));
afterEach(() => { localStorage.clear(); vi.restoreAllMocks(); });


test("shows the active public Team ID and can disconnect locally", async () => {
  const user = userEvent.setup();
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
    data: { team: { team_id: 123, name: "Test XI", picks: [] }, live: null, history: null, fixtures: null, players: null, decision: null },
    meta: { event: 2, generated_at: "2026-08-31T18:00:00Z", degraded: true, prediction_version: "gw3_predictions_v11.csv" },
    errors: [],
  }), { status: 200 }));
  render(<TeamProvider><SettingsWorkspace /></TeamProvider>);

  expect(await screen.findByText("123")).toBeInTheDocument();
  expect(screen.getByText("gw3_predictions_v11.csv")).toBeInTheDocument();
  expect(screen.getByText(/independent beta/i)).toHaveTextContent(/not affiliated with or endorsed by the Premier League/i);
  await user.click(screen.getByRole("button", { name: /disconnect team/i }));
  expect(screen.getByText("No team connected")).toBeInTheDocument();
});


test("stores a season goal locally with mini-league success as the default", async () => {
  const user = userEvent.setup();
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
    data: { team: { team_id: 123, name: "Test XI", picks: [] }, live: null, history: null, fixtures: null, players: null, decision: null },
    meta: { event: 2, generated_at: "2026-08-31T18:00:00Z", degraded: true },
    errors: [],
  }), { status: 200 }));
  render(<TeamProvider><SettingsWorkspace /></TeamProvider>);

  const goal = await screen.findByLabelText("Season goal");
  expect(goal).toHaveValue("mini_league");
  await user.selectOptions(goal, "overall_rank");

  expect(goal).toHaveValue("overall_rank");
  expect(localStorage.getItem("fpl-ai-season-goal")).toBe("overall_rank");
  expect(screen.getByText(/preferences personalize the product locally/i)).toBeInTheDocument();
});
