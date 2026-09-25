import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { TeamProvider } from "@/app/providers/TeamProvider";
import { expectNoA11yViolations } from "@/test-utils/accessibility";
import { ExploreWorkspace } from "./ExploreWorkspace";


const envelope = {
  data: {
    team: { team_id: 123, name: "Test XI", bank: 0, event: 2, transfers: 0, picks: [] },
    live: null,
    history: null,
    fixtures: { fixtures: [{ fixture_id: 4, event: 3, home_team: "Chelsea", away_team: "Arsenal", difficulty: 4 }] },
    players: { players: [
      { player_id: 1, name: "Palmer", team: "Chelsea", team_short: "CHE", position: "MID", price: 10.5, ownership: 42.1, event_points: 12, minutes: 90, goals: 1, assists: 1, bonus: 3, bps: 42, clean_sheets: 1, form: 7.2, expected_goals: 1.4, expected_assists: 1.1, expected_goal_involvements: 2.5, ict_index: 21.7, predicted_points: 8.4, xmins: 82, start_probability: 0.92, status: "d", chance_of_playing_next_round: 75, news: "Knock - 75% chance of playing", news_added: "2026-09-01T08:00:00Z" },
      { player_id: 2, name: "Haaland", team: "Man City", team_short: "MCI", position: "FWD", price: 14.0, ownership: 55.2, event_points: 9, minutes: 90, goals: 1, assists: 0, bonus: 2, bps: 35, clean_sheets: 0, form: 6.4, expected_goals: 2.2, expected_assists: 0.2, expected_goal_involvements: 2.4, ict_index: 19.8, predicted_points: 7.9, xmins: 90, start_probability: 1, status: "a", news: "" },
    ] },
    decision: null,
  },
  meta: { event: 2, generated_at: "2026-08-31T18:00:00Z", degraded: false },
  errors: [],
};

const matrixEnvelope = {
  data: {
    current_event: 2,
    next_event: 3,
    start_event: 3,
    horizon: 2,
    gameweeks: [3, 4],
    teams: [
      {
        team_id: 1,
        team: "Arsenal",
        team_short: "ARS",
        fixtures: [
          { event: 3, opponents: ["CHE (H)"], difficulty: 2, fixture_count: 1 },
          { event: 4, opponents: [], difficulty: null, fixture_count: 0 },
        ],
      },
      {
        team_id: 2,
        team: "Chelsea",
        team_short: "CHE",
        fixtures: [
          { event: 3, opponents: ["ARS (A)", "LIV (H)"], difficulty: 3.5, fixture_count: 2 },
          { event: 4, opponents: ["MCI (A)"], difficulty: 5, fixture_count: 1 },
        ],
      },
    ],
  },
  meta: { source: "official", fetched_at: "2026-09-01T10:00:00Z", stale: false, version: null },
  errors: [],
};

function mockExploreApis() {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    const payload = url.includes("/fixture-matrix")
      ? matrixEnvelope
      : url.includes("/api/v1/players")
      ? {
          data: { ...envelope.data.players, current_event: 2, gameweek_name: "Gameweek 2", status: "LIVE", finished: false, next_event: 3, next_deadline_time: "2026-09-12T10:00:00Z" },
          meta: { source: "live", fetched_at: "2026-09-01T10:00:00Z", stale: false, version: null },
          errors: [],
        }
      : envelope;
    return new Response(
      JSON.stringify(payload),
      { status: 200 },
    );
  });
}


beforeEach(() => {
  localStorage.setItem("fpl-ai-team-id", "123");
  window.history.replaceState({}, "", "/explore");
});
afterEach(() => { localStorage.clear(); window.history.replaceState({}, "", "/"); vi.restoreAllMocks(); });


test("filters live players and builds a local comparison tray", async () => {
  const user = userEvent.setup();
  mockExploreApis();
  render(<TeamProvider><ExploreWorkspace /></TeamProvider>);

  expect(await screen.findByText("Palmer")).toBeInTheDocument();
  expect(screen.getByText("GW points")).toBeInTheDocument();
  expect(screen.getByText("Palmer").closest(".explorer-row")).toHaveTextContent("12");
  await user.click(screen.getByRole("button", { name: "MID" }));
  expect(screen.getByText("Palmer")).toBeInTheDocument();
  expect(screen.queryByText("Haaland")).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: /compare palmer/i }));
  expect(screen.getByText("1 of 4 selected")).toBeInTheDocument();
  expect(screen.getAllByText("Live").length).toBeGreaterThan(0);
});


test("player and fixture explorer has no automated WCAG A/AA violations", async () => {
  mockExploreApis();
  const { container } = render(<TeamProvider><ExploreWorkspace /></TeamProvider>);

  await screen.findByText("Palmer");
  await screen.findByRole("region", { name: "Fixture planning matrix" });
  await expectNoA11yViolations(container);
});


test("loads the full searchable player universe even when a team is connected", async () => {
  const fetchSpy = mockExploreApis();
  render(<TeamProvider><ExploreWorkspace /></TeamProvider>);

  await screen.findByText("Palmer");
  await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith(
    expect.stringContaining("/api/v1/players?limit=700"),
    expect.any(Object),
  ));
});


test("keeps loading the full market when the connected dashboard resolves first", async () => {
  let resolvePlayers: ((response: Response) => void) | undefined;
  vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
    const url = String(input);
    if (url.includes("/fixture-matrix")) {
      return Promise.resolve(new Response(JSON.stringify(matrixEnvelope), { status: 200 }));
    }
    if (url.includes("/api/v1/players")) {
      return new Promise<Response>((resolve, reject) => {
        resolvePlayers = resolve;
        init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
      });
    }
    return Promise.resolve(new Response(JSON.stringify(envelope), { status: 200 }));
  });
  render(<TeamProvider><ExploreWorkspace /></TeamProvider>);

  expect(await screen.findByText("Palmer")).toBeInTheDocument();
  await waitFor(() => expect(resolvePlayers).toBeTypeOf("function"));
  resolvePlayers!(new Response(JSON.stringify({
    data: { players: [
      ...envelope.data.players.players,
      { player_id: 99, name: "Full Market Player", team: "Leeds", team_short: "LEE", position: "MID", price: 5.5, event_points: 4, predicted_points: 5.1 },
    ] },
    meta: { source: "live", fetched_at: "2026-09-01T10:00:00Z", stale: false, version: null },
    errors: [],
  }), { status: 200 }));

  expect(await screen.findByText("Full Market Player")).toBeInTheDocument();
});


test("labels cached public player and fixture data instead of presenting it as fresh", async () => {
  localStorage.removeItem("fpl-ai-team-id");
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const isMatrix = String(input).includes("/fixture-matrix");
    const payload = isMatrix
      ? { ...matrixEnvelope, meta: { ...matrixEnvelope.meta, stale: true } }
      : { data: envelope.data.players, meta: { source: "live", fetched_at: "2026-09-01T09:00:00Z", stale: true, version: null }, errors: [] };
    return new Response(JSON.stringify(payload), { status: 200 });
  });

  render(<TeamProvider><ExploreWorkspace /></TeamProvider>);

  expect(await screen.findByText("Showing cached FPL data")).toBeInTheDocument();
  expect(screen.getByText(/official service is temporarily unavailable/i)).toBeInTheDocument();
});


test("labels a finished official player market as official instead of live", async () => {
  localStorage.removeItem("fpl-ai-team-id");
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const payload = String(input).includes("/fixture-matrix")
      ? matrixEnvelope
      : {
          data: {
            ...envelope.data.players,
            current_event: 2,
            gameweek_name: "Gameweek 2",
            status: "FINISHED",
            finished: true,
            next_event: 3,
            next_deadline_time: "2026-09-12T10:00:00Z",
          },
          meta: { source: "official", fetched_at: "2026-09-02T09:00:00Z", stale: false, version: null },
          errors: [],
        };
    return new Response(JSON.stringify(payload), { status: 200 });
  });

  render(<TeamProvider><ExploreWorkspace /></TeamProvider>);

  await screen.findByText("Palmer");
  const heading = screen.getByRole("heading", { name: "Explore the player pool." }).closest(".workspace-heading");
  expect(heading).not.toBeNull();
  expect(within(heading as HTMLElement).getByText("Official")).toBeInTheDocument();
  expect(within(heading as HTMLElement).queryByText("Live")).not.toBeInTheDocument();
});


test("compares shortlisted players with projected edge and value", async () => {
  const user = userEvent.setup();
  mockExploreApis();
  render(<TeamProvider><ExploreWorkspace /></TeamProvider>);

  await screen.findByText("Palmer");
  await user.click(screen.getByRole("button", { name: /compare palmer/i }));
  await user.click(screen.getByRole("button", { name: /compare haaland/i }));

  const comparison = screen.getByRole("region", { name: "Detailed player comparison" });
  expect(comparison).toHaveTextContent("Palmer leads by +0.5 xPts");
  expect(comparison).toHaveTextContent("0.8 xPts/£m");
  expect(comparison).toHaveTextContent("0.6 xPts/£m");
  expect(comparison).toHaveTextContent("82 xMins");
  expect(comparison).toHaveTextContent("1 goal · 1 assist");
  expect(comparison).toHaveTextContent("3 bonus · 42 BPS");
  expect(comparison).toHaveTextContent("Season underlying");
  expect(comparison).toHaveTextContent("1.4 xG · 1.1 xA");
  expect(comparison).toHaveTextContent("2.5 xGI · 21.7 ICT");
  expect(comparison).toHaveTextContent("Official · season");
  expect(comparison).toHaveTextContent("Knock - 75% chance of playing");
  expect(comparison).toHaveTextContent("Official FPL status");
});


test("restores shareable filters and shortlist from the URL", async () => {
  window.history.replaceState({}, "", "/explore?position=MID&q=palmer&compare=1,2");
  const user = userEvent.setup();
  mockExploreApis();

  render(<TeamProvider><ExploreWorkspace /></TeamProvider>);

  expect(await screen.findByText("2 of 4 selected")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "MID" })).toHaveClass("active");
  expect(screen.getByPlaceholderText("Search players")).toHaveValue("palmer");

  await user.clear(screen.getByPlaceholderText("Search players"));
  await user.type(screen.getByPlaceholderText("Search players"), "haal");
  await user.click(screen.getByRole("button", { name: "FWD" }));

  await waitFor(() => {
    expect(window.location.search).toContain("position=FWD");
    expect(window.location.search).toContain("q=haal");
    expect(window.location.search).toContain("compare=1%2C2");
  });
});


test("shows a five-gameweek fixture difficulty matrix for every club", async () => {
  mockExploreApis();

  render(<TeamProvider><ExploreWorkspace /></TeamProvider>);

  const matrix = await screen.findByRole("region", { name: "Fixture planning matrix" });
  expect(matrix).toHaveTextContent("GW3");
  expect(matrix).toHaveTextContent("GW4");
  expect(matrix).toHaveTextContent("CHE (H)");
  expect(matrix).toHaveTextContent("Blank");
  expect(matrix).toHaveTextContent("Double GW");
  expect(matrix).toHaveTextContent("FDR 5");
});


test("keeps the public player and fixture explorer useful before team connection", async () => {
  localStorage.removeItem("fpl-ai-team-id");
  mockExploreApis();

  render(<TeamProvider><ExploreWorkspace /></TeamProvider>);

  expect(await screen.findByText("Palmer")).toBeInTheDocument();
  expect(screen.getByText(/connect a team for personalized/i)).toBeInTheDocument();
  expect(screen.getByRole("region", { name: "Fixture planning matrix" })).toBeInTheDocument();
});
