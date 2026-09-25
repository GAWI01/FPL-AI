import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { TeamProvider } from "@/app/providers/TeamProvider";
import { expectNoA11yViolations } from "@/test-utils/accessibility";
import { PlanWorkspace } from "./PlanWorkspace";


function dashboard(netGain = 2.8, liveStatus: string | null = null, actionsLocked = false) {
  return {
    data: {
      team: { team_id: 123, name: "Friends League XI", bank: 12, event: 2, transfers: 0, picks: [{ player_id: 1 }, { player_id: 2 }, { player_id: 4 }] },
      live: liveStatus ? { current_event: 2, status: liveStatus, picks: [] } : null,
      history: null,
      fixtures: null,
      players: null,
      decision: {
        captain: { player_id: 1, name: "Palmer", team: "Chelsea", predicted_points: 8.4 },
        vice_captain: { player_id: 2, name: "Salah", team: "Liverpool", predicted_points: 7.8 },
        transfers: {
          recommended_transfers: [{
            player_out_id: 3,
            player_out: "Saka",
            player_in_id: 1,
            player_in: "Palmer",
            gain: 6.8,
          }],
          transfers_used: 2,
          free_transfers: 1,
          hit_cost: 4,
          gross_gain: 6.8,
          net_gain: netGain,
        },
        intelligence: {
          action: "TRANSFER",
          confidence: {
            score: 0.62,
            label: "MEDIUM",
            components: { decision_margin: 0.5, minutes_certainty: 0.8, fixture_certainty: 0.7, signal_agreement: 0.5 },
          },
          captain_decision: {
            captain: { player_id: 1, name: "Palmer", team: "Chelsea", predicted_points: 8.4, xmins: 88, start_probability: 0.96 },
            vice_captain: { player_id: 2, name: "Salah", team: "Liverpool", predicted_points: 7.8, xmins: 90, start_probability: 1 },
            alternatives: [
              { player_id: 4, name: "Haaland", team: "Man City", predicted_points: 7.5, xmins: 90, start_probability: 1 },
              { player_id: 99, name: "Unowned", team: "Arsenal", predicted_points: 9.9, xmins: 90, start_probability: 1 },
            ],
          },
          transfer_strategy: {
            action: "TRANSFER",
            current_net_gain: netGain,
            horizon_gain: 5.7,
            combined_score: 8.5,
            coverage: 1,
            selected_transfers: [{ player_out_id: 3, player_out: "Saka", player_in_id: 1, player_in: "Palmer" }],
            alternatives: [{
              transfers: [{ player_out_id: 3, player_out: "Saka", player_in_id: 4, player_in: "Haaland" }],
              current_net_gain: 1.2,
              horizon_gain: 3,
              combined_score: 4.2,
              coverage: 1,
            }],
          },
          horizon: {
            horizon: 5,
            coverage: 1,
            team_projected_points: 278.4,
            team_player_projections: [{
              player_id: 1,
              predicted_points: 36,
              gameweeks: [3, 4, 5, 6, 7].map((gameweek, index) => ({
                gameweek,
                horizon_index: index + 1,
                predicted_points: 8.4 - index * 0.6,
                uncertainty: 1.5 + index * 0.3,
                opponent: ["ARS", "MCI", "BRE", "EVE", "LEE"][index],
                projection_method: index === 0 ? "native_model" : "fixture_scaled_v1",
                fixture_count: 1,
              })),
            }],
          },
          chip_advisor: { recommended_chip: null, score: 0, alternatives: [] },
          chip_state: {
            known: true,
            period: 1,
            period_events: [1, 19],
            used_in_period: [{ chip: "BENCH_BOOST", event: 2 }],
            wildcard_available: true,
            free_hit_available: true,
            bench_boost_available: false,
            triple_captain_available: true,
          },
          squad_health: { status: "WARNING", unavailable_count: 1, high_risk_count: 2, average_xmins: 77, players: [] },
          risk_summary: { average_risk: 0.24, high_risk_players: 2, players: [] },
          insights: [
            { type: "TRANSFER", severity: "ACTION", reason: "Best combined current and horizon value.", evidence: {} },
            { type: "SQUAD_HEALTH", severity: "WARNING", reason: "One player is unavailable.", evidence: {} },
          ],
        },
      },
    },
    meta: {
      event: 2,
      current_event: 2,
      prediction_event: 3,
      target_deadline_time: "2026-09-04T17:30:00Z",
      actions_locked: actionsLocked,
      generated_at: "2026-08-31T18:00:00Z",
      degraded: false,
    },
    errors: [],
  };
}


beforeEach(() => localStorage.setItem("fpl-ai-team-id", "123"));
afterEach(() => { localStorage.clear(); vi.restoreAllMocks(); });


test("explains the transfer, hit and captain recommendation", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(dashboard()), { status: 200 }),
  );
  render(<TeamProvider><PlanWorkspace /></TeamProvider>);

  expect(await screen.findByText("Saka → Palmer")).toBeInTheDocument();
  expect(screen.getByText("+2.8 net xPts")).toBeInTheDocument();
  expect(screen.getByText("−4 hit")).toBeInTheDocument();
  expect(screen.getAllByText("Palmer").length).toBeGreaterThan(0);
  expect(screen.getByText(/chip recommendations need/i)).toBeInTheDocument();
  await waitFor(() => expect(screen.getByRole("region", { name: "Local plan history" })).toHaveTextContent("Saka → Palmer"));
  expect(screen.getByRole("region", { name: "Local plan history" })).toHaveTextContent("GW3");
});


test("decision room has no automated WCAG A/AA violations", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(dashboard()), { status: 200 }),
  );
  const { container } = render(<TeamProvider><PlanWorkspace /></TeamProvider>);

  await screen.findByText("Saka → Palmer");
  await expectNoA11yViolations(container);
});


test("recommends holding when the net gain is not positive", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(dashboard(-0.6)), { status: 200 }),
  );
  render(<TeamProvider><PlanWorkspace /></TeamProvider>);

  expect(await screen.findByText("Hold the transfer")).toBeInTheDocument();
});


test("keeps next-gameweek transfer advice actionable while the current gameweek is live", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(dashboard(2.8, "LIVE")), { status: 200 }),
  );
  render(<TeamProvider><PlanWorkspace /></TeamProvider>);

  expect(await screen.findByText("Saka → Palmer")).toBeInTheDocument();
  expect(screen.getByText("GAMEWEEK 3 DECISION ROOM")).toBeInTheDocument();
  expect(screen.queryByText("Gameweek locked")).not.toBeInTheDocument();
});


test("locks transfer advice only when the prediction target deadline has passed", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(dashboard(2.8, "LIVE", true)), { status: 200 }),
  );
  render(<TeamProvider><PlanWorkspace /></TeamProvider>);

  expect(await screen.findByRole("heading", { name: "Gameweek locked" })).toBeInTheDocument();
  expect(screen.queryByText("Saka → Palmer")).not.toBeInTheDocument();
  expect(screen.queryByText("+2.8 net xPts")).not.toBeInTheDocument();
  expect(screen.getByText(/transfer calculations are hidden/i)).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Chip decision" })).toBeInTheDocument();
  expect(screen.getByText(/chip actions are locked/i)).toBeInTheDocument();
});


test("shows five-gameweek confidence, chip hold and what-if alternatives", async () => {
  const user = userEvent.setup();
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(dashboard()), { status: 200 }),
  );
  render(<TeamProvider><PlanWorkspace /></TeamProvider>);

  expect(await screen.findByText("5-GW outlook")).toBeInTheDocument();
  expect(screen.getByText("Medium confidence")).toBeInTheDocument();
  expect(screen.getByText("Hold chips")).toBeInTheDocument();
  expect(screen.getAllByText("GW3").length).toBeGreaterThan(0);
  expect(screen.getByText("GW7")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Compare roll transfer" }));
  expect(screen.getByText("Roll transfer selected")).toBeInTheDocument();
  expect(screen.getByText("Scenario: Hold the transfer")).toBeInTheDocument();
  expect(screen.getByText("No hit")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Try Haaland as captain" }));
  expect(screen.getByText("Haaland selected locally")).toBeInTheDocument();
  expect(screen.getByText("−0.9 captain xPts")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Try Unowned as captain" })).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: /open lineup and bench simulator/i })).toHaveAttribute("href", "/team");
  await user.click(screen.getByRole("button", { name: "Compare alternative 1" }));
  expect(screen.getByText("Alternative 1 selected")).toBeInTheDocument();
  expect(screen.getByText("+4.2 combined")).toBeInTheDocument();
});


test("explains the latest meaningful plan change without alarming on every refresh", async () => {
  localStorage.setItem("fpl-ai-plan-history", JSON.stringify([{
    event: 3,
    action: "Hold the transfer",
    captain: "Salah",
    netGain: 0.1,
    confidenceScore: 0.51,
    confidenceLabel: "LOW",
    modelVersion: "gw2_predictions_v10.csv",
    recordedAt: "2026-08-31T17:00:00Z",
  }]));
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(dashboard()), { status: 200 }),
  );

  render(<TeamProvider><PlanWorkspace /></TeamProvider>);

  const change = await screen.findByRole("status", { name: /plan changed/i });
  expect(change).toHaveTextContent("Hold the transfer");
  expect(change).toHaveTextContent("Saka → Palmer");
  expect(change).toHaveTextContent(/captaincy recommendation changed/i);
  expect(change).toHaveTextContent(/62% medium/i);
});
