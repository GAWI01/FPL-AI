import { render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { TeamProvider } from "@/app/providers/TeamProvider";
import type { DashboardLive } from "@/lib/contracts";
import { expectNoA11yViolations } from "@/test-utils/accessibility";
import { OverviewDashboard } from "./OverviewDashboard";


function envelope(decision: object | null = {
  current_team: { players: [{ player_id: 1, predicted_points: 85 }] },
  optimal_squad: { players: [], projected_points: 100 },
  starting_xi: { formation: "3-5-2", players: [], projected_points: 68.4 },
  captain: { player_id: 1, name: "Palmer", team: "Chelsea", predicted_points: 8.1 },
  vice_captain: { player_id: 2, name: "Salah", team: "Liverpool", predicted_points: 7.9 },
  transfers: {
    recommended_transfers: [{
      player_out_id: 3,
      player_out: "Saka",
      player_in_id: 1,
      player_in: "Palmer",
      gain: 3.1,
    }],
    net_gain: 3.1,
    hit_cost: 0,
    free_transfers: 2,
  },
  intelligence: {
    squad_health: {
      status: "HEALTHY",
      unavailable_count: 0,
      high_risk_count: 1,
      average_xmins: 84,
      players: [],
    },
    insights: [{
      type: "CAPTAIN_OPPORTUNITY",
      severity: "MEDIUM",
      reason: "Palmer has the strongest captaincy evidence this week.",
      evidence: {},
    }],
  },
}, liveStatus: string | null = "LIVE", actionsLocked = false) {
  return {
    data: {
      team: {
        team_id: 123,
        name: "Friends League XI",
        manager_name: "Gabri Manager",
        bank: 10,
        event: 2,
        transfers: 0,
        overall_rank: 612345,
        value: 1005,
        picks: [{
          player_id: 1,
          position: 1,
          name: "Palmer",
          position_name: "MID",
          team: "Chelsea",
          price: 10.5,
          status: "a",
          prediction: { predicted_points: 8.1 },
        }],
      },
      live: liveStatus ? {
        current_event: 2,
        status: liveStatus,
        finished: liveStatus === "FINISHED",
        picks: [{
          player_id: 1,
          position: 1,
          name: "Palmer",
          position_name: "MID",
          team: "Chelsea",
          price: 10.5,
          status: "a",
         event_points: 9 as number | null | undefined,
         multiplied_points: 18 as number | null | undefined,
       }],
        summary: undefined as DashboardLive["summary"],
        fixtures: undefined as DashboardLive["fixtures"],
        events: undefined as DashboardLive["events"],
      } : null,
      history: { history: [{ event: 1, points: 70, overall_rank: 800000 }] },
      fixtures: { fixtures: [{ fixture_id: 1, event: 3, home_team: "Chelsea", away_team: "Arsenal", kickoff_time: "2026-09-04T17:30:00Z" }] },
      players: { players: [
        { player_id: 1, name: "Palmer", team: "Chelsea", team_short: "CHE", position: "MID", price: 10.5, form: 7.2, ownership: 42.1, event_points: 9, minutes: 90 },
        { player_id: 2, name: "Haaland", team: "Man City", team_short: "MCI", position: "FWD", price: 14, form: 6.4, ownership: 55.2, event_points: 6, minutes: 72 },
      ] },
      decision,
    },
    meta: {
      event: 2,
      current_event: 2,
      prediction_event: 3,
      target_deadline_time: "2026-09-04T17:30:00Z",
      actions_locked: actionsLocked,
      generated_at: "2026-08-31T18:00:00+00:00",
      degraded: decision === null,
    },
    errors: decision === null ? [{ area: "decision", message: "Decision data is unavailable" }] : [],
  };
}


beforeEach(() => {
  localStorage.setItem("fpl-ai-team-id", "123");
});


afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});


test("shows live score and keeps the future plan actionable during the gameweek", async () => {
  const payload = envelope();
  payload.data.live = {
    ...payload.data.live!,
    summary: {
      live_points: 18,
      captain_contribution: 18,
      players_finished: 0,
      players_live: 1,
      players_remaining: 10,
    },
    fixtures: [{
      fixture_id: 30,
      home_team_id: 1,
      away_team_id: 2,
      home_team: "Chelsea",
      away_team: "Arsenal",
      home_score: 1,
      away_score: 0,
      started: true,
      finished: false,
      minutes: 32,
    }],
    events: [
      { player_id: 1, player_name: "Palmer", team_short: "CHE", event_type: "GOAL", count: 1, active: true, provisional: false },
      { player_id: 1, player_name: "Palmer", team_short: "CHE", event_type: "BONUS", count: 2, active: true, provisional: true },
    ],
  };
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(payload), { status: 200 }),
  );
  render(<TeamProvider><OverviewDashboard /></TeamProvider>);

  expect(await screen.findByText("Friends League XI")).toBeInTheDocument();
  expect(screen.getByText("Managed by Gabri Manager")).toBeInTheDocument();
  expect(screen.getByText("18")).toBeInTheDocument();
  expect(screen.getByText("Saka → Palmer")).toBeInTheDocument();
  expect(screen.queryByText("Gameweek locked")).not.toBeInTheDocument();
  expect(screen.getByText("LIVE MODE")).toBeInTheDocument();
  expect(screen.getByText("Next deadline plan")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /follow live team/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Live fixtures" })).toBeInTheDocument();
  expect(screen.getAllByText("Live").length).toBeGreaterThan(0);
  expect(screen.getAllByText("Model").length).toBeGreaterThan(0);
  const events = screen.getByRole("region", { name: "Owned team events" });
  expect(events).toHaveTextContent("Palmer");
  expect(events).toHaveTextContent("1 goal");
  expect(events).toHaveTextContent("2 bonus");
  expect(events).toHaveTextContent("Provisional");
  expect(events).toHaveTextContent(/official aggregate, not an event timeline/i);
});


test("switches Current XI to live player data during an active Gameweek", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(envelope()), { status: 200 }),
  );
  render(<TeamProvider><OverviewDashboard /></TeamProvider>);

  await screen.findByText("Friends League XI");
  const currentXi = screen.getByRole("heading", { name: "Current XI" }).closest("article");
  expect(currentXi).not.toBeNull();
  expect(within(currentXi as HTMLElement).getByText("Live", { selector: ".source-pill" })).toBeInTheDocument();
  expect(within(currentXi as HTMLElement).getByText("9 pts")).toBeInTheDocument();
  expect(within(currentXi as HTMLElement).queryByText("8.1 xPts")).not.toBeInTheDocument();
});


test("does not present a partial live pick feed as a complete team total", async () => {
  const payload = envelope();
  const livePick = payload.data.live!.picks[0];
  payload.data.live = {
    ...payload.data.live!,
    picks: [
      { ...livePick, event_points: undefined, multiplied_points: undefined },
      { ...livePick, player_id: 2, name: "Salah", event_points: 4, multiplied_points: 4 },
    ],
  };
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(payload), { status: 200 }),
  );
  render(<TeamProvider><OverviewDashboard /></TeamProvider>);

  await screen.findByText("Friends League XI");
  const pointsKpi = screen.getByText("Gameweek points", { exact: false }).closest("article");
  expect(pointsKpi).not.toBeNull();
  expect(within(pointsKpi as HTMLElement).getByText("—", { selector: "strong" })).toBeInTheDocument();
  expect(within(pointsKpi as HTMLElement).queryByText("0", { selector: "strong" })).not.toBeInTheDocument();
});


test("overview cockpit has no automated WCAG A/AA violations", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(envelope(undefined, null)), { status: 200 }),
  );
  const { container } = render(<TeamProvider><OverviewDashboard /></TeamProvider>);

  await screen.findByText("Friends League XI");
  await expectNoA11yViolations(container);
});


test("hides the recommendation when the prediction target is locked", async () => {
  const payload = envelope(undefined, "LIVE", true);
  payload.data.live = {
    ...payload.data.live!,
    summary: {
      live_points: 51,
      captain_contribution: 16,
      players_finished: 1,
      players_live: 2,
      players_remaining: 8,
    },
    fixtures: [{
      fixture_id: 31,
      home_team_id: 1,
      away_team_id: 2,
      home_team: "Chelsea",
      away_team: "Arsenal",
      home_score: 2,
      away_score: 1,
      started: true,
      finished: false,
      minutes: 67,
    }],
  };
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(payload), { status: 200 }),
  );
  render(<TeamProvider><OverviewDashboard /></TeamProvider>);

  expect(await screen.findByText("Gameweek locked")).toBeInTheDocument();
  expect(screen.queryByText("Saka → Palmer")).not.toBeInTheDocument();
  expect(screen.getByText("1 finished · 2 live · 8 to play")).toBeInTheDocument();
  expect(screen.getByText("Chelsea 2")).toBeInTheDocument();
  expect(screen.getByText("Arsenal 1")).toBeInTheDocument();
  expect(screen.getByText("67′ · LIVE")).toBeInTheDocument();
});


test("shows the primary model recommendation before the deadline", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(envelope(undefined, null)), { status: 200 }),
  );
  render(<TeamProvider><OverviewDashboard /></TeamProvider>);

  expect(await screen.findByText("Saka → Palmer")).toBeInTheDocument();
});


test("labels finished Gameweek points as official instead of live", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(envelope(undefined, "FINISHED", true)), { status: 200 }),
  );
  render(<TeamProvider><OverviewDashboard /></TeamProvider>);

  await screen.findByText("Friends League XI");
  const pointsKpi = screen.getByText("Gameweek points", { exact: false }).closest("article");
  expect(pointsKpi).not.toBeNull();
  expect(within(pointsKpi as HTMLElement).getByText("Official", { selector: ".source-pill" })).toBeInTheDocument();
  expect(within(pointsKpi as HTMLElement).queryByText("Live", { selector: ".source-pill" })).not.toBeInTheDocument();
});


test("labels every official live surface as cached when the dashboard snapshot is stale", async () => {
  const payload = envelope();
  const stalePayload = { ...payload, meta: { ...payload.meta, stale: true, degraded: true } };
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(stalePayload), { status: 200 }),
  );
  const { container } = render(<TeamProvider><OverviewDashboard /></TeamProvider>);

  await screen.findByText("Friends League XI");
  const pointsKpi = screen.getByText("Gameweek points", { exact: false }).closest("article");
  expect(pointsKpi).not.toBeNull();
  expect(within(pointsKpi as HTMLElement).getByText("Cached", { selector: ".source-pill" })).toBeInTheDocument();
  const teamSummary = screen.getByRole("region", { name: "Team summary" });
  for (const label of ["Overall rank", "Free transfers"]) {
    const card = within(teamSummary).getByText(label).closest("article");
    expect(card).not.toBeNull();
    expect(within(card as HTMLElement).getByText("Cached", { selector: ".source-pill" })).toBeInTheDocument();
  }
  for (const heading of ["Gameweek status", "Current XI", "Next fixtures", "Owned team events"]) {
    const card = screen.getByRole("heading", { name: heading }).closest("article");
    expect(card).not.toBeNull();
    expect(within(card as HTMLElement).getByText("Cached", { selector: ".source-pill" })).toBeInTheDocument();
  }
  const watch = screen.getByRole("region", { name: "Form and action watch" });
  expect(within(watch).getByText("Cached GW", { selector: ".source-pill" })).toBeInTheDocument();
  expect(within(watch).getByText("Cached form", { selector: ".source-pill" })).toBeInTheDocument();
  expect(container.querySelectorAll(".source-pill.source-live, .source-pill.source-official")).toHaveLength(0);
});


test("keeps official team data visible when decision analysis fails", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(envelope(null, null)), { status: 200 }),
  );
  render(<TeamProvider><OverviewDashboard /></TeamProvider>);

  expect(await screen.findByText("Friends League XI")).toBeInTheDocument();
  expect(screen.getByText(/model analysis is unavailable/i)).toBeInTheDocument();
  expect(screen.getAllByText("Palmer").length).toBeGreaterThan(0);
});


test("shows rank momentum and compact squad readiness", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(envelope()), { status: 200 }),
  );
  render(<TeamProvider><OverviewDashboard /></TeamProvider>);

  expect(await screen.findByRole("img", { name: "Overall rank trend" })).toBeInTheDocument();
  expect(screen.getByText("612,345")).toBeInTheDocument();
  expect(screen.getByText("Healthy")).toBeInTheDocument();
  expect(screen.getByText("84 avg xMins")).toBeInTheDocument();
  expect(screen.getByText("Squad rating")).toBeInTheDocument();
  expect(screen.getByText("85")).toBeInTheDocument();
  expect(screen.getByText("Free transfers")).toBeInTheDocument();
  expect(screen.getByText("2")).toBeInTheDocument();
});


test("surfaces live leaders, official form and actionable plan evidence", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(envelope()), { status: 200 }),
  );
  render(<TeamProvider><OverviewDashboard /></TeamProvider>);

  const radar = await screen.findByRole("region", { name: "Form and action watch" });
  expect(radar).toHaveTextContent("Palmer");
  expect(radar).toHaveTextContent("7.2 form");
  expect(radar).toHaveTextContent("Palmer has the strongest captaincy evidence this week.");
  expect(radar).toHaveTextContent("Official form");
  expect(radar).toHaveTextContent("LIVE LEADERS");
  expect(radar).toHaveTextContent("9 pts");
  expect(radar).toHaveTextContent("90 min");
});


test("frames the strategic edge around the locally selected season goal", async () => {
  localStorage.setItem("fpl-ai-season-goal", "overall_rank");
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(envelope()), { status: 200 }),
  );
  render(<TeamProvider><OverviewDashboard /></TeamProvider>);

  expect(await screen.findByText("Overall-rank edge")).toBeInTheDocument();
  expect(screen.getByText(/climb through repeatable expected value/i)).toBeInTheDocument();
});
