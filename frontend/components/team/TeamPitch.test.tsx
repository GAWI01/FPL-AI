import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";

import type { HorizonPlayer, SquadHealthPlayer, TeamPick } from "@/lib/contracts";
import { TeamPitch } from "./TeamPitch";


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


test("renders all picks and switches between live and projected points", async () => {
  const user = userEvent.setup();
  render(<TeamPitch picks={picks} preferredMode="projected" />);

  expect(screen.getAllByRole("button", { name: /^player \d+,/i })).toHaveLength(15);
  expect(screen.getByText("Captain")).toBeInTheDocument();
  expect(screen.getByText("£5.0m")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Live" }));
  expect(screen.getByRole("button", { name: /^player 1,/i })).toHaveAccessibleName(/1 pts/i);
  await user.click(screen.getByRole("button", { name: "Projected" }));
  expect(screen.getByText("20.0 xPts")).toBeInTheDocument();
});


test("follows the Gameweek context from projected before deadline to live after lock", async () => {
  const { rerender } = render(<TeamPitch picks={picks} preferredMode="projected" />);

  expect(screen.getByRole("button", { name: "Projected" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByRole("button", { name: /^player 1,/i })).toHaveAccessibleName(/20\.0 xPts/i);

  rerender(<TeamPitch picks={picks} preferredMode="live" />);

  await waitFor(() => expect(screen.getByRole("button", { name: "Live" })).toHaveAttribute("aria-pressed", "true"));
  expect(screen.getByRole("button", { name: /^player 1,/i })).toHaveAccessibleName(/1 pts/i);
});


test("renders legally safe club-colour kit abstractions instead of one generic shirt", () => {
  const clubPicks = picks.map((pick, index) => {
    if (index === 0) return { ...pick, team: "Arsenal", team_short: "ARS" };
    if (index === 1) return { ...pick, team: "Chelsea", team_short: "CHE" };
    return pick;
  });

  render(<TeamPitch picks={clubPicks} preferredMode="projected" />);

  const arsenalShirt = within(screen.getByRole("button", { name: /^player 1,/i })).getByText("ARS");
  const chelseaShirt = within(screen.getByRole("button", { name: /^player 2,/i })).getByText("CHE");
  expect(arsenalShirt.style.getPropertyValue("--kit-primary")).toBe("#ef0107");
  expect(chelseaShirt.style.getPropertyValue("--kit-primary")).toBe("#034694");
  expect(arsenalShirt.style.getPropertyValue("--kit-primary")).not.toBe(
    chelseaShirt.style.getPropertyValue("--kit-primary"),
  );
});


test("uses the live pick feed instead of stale official squad points", () => {
  render(<TeamPitch picks={picks} preferredMode="live" livePicks={[
    { ...picks[0], event_points: 12, live_minutes: 76 },
  ]} />);

  expect(screen.getByRole("button", { name: /^player 1,/i })).toHaveAccessibleName(/12 pts/i);
});


test("does not fabricate zero live points when a player's official value is missing", () => {
  const picksWithUnknownLivePoints = picks.map((pick, index) => index === 0
    ? { ...pick, event_points: undefined }
    : pick);

  render(<TeamPitch picks={picksWithUnknownLivePoints} preferredMode="live" />);

  const player = screen.getByRole("button", { name: /^player 1,/i });
  expect(player).toHaveTextContent("—");
  expect(player).not.toHaveTextContent("0 pts");
});


test("rejects a swap that would remove the starting goalkeeper", async () => {
  const user = userEvent.setup();
  render(<TeamPitch picks={picks} preferredMode="projected" />);

    await user.click(screen.getByRole("button", { name: /^player 1,/i }));
    await user.click(screen.getByRole("button", { name: /^player 14,/i }));

  expect(screen.getByRole("alert")).toHaveTextContent(/invalid formation/i);
});


test("drags a compatible bench player into the starting eleven without touching official FPL", () => {
  render(<TeamPitch picks={picks} preferredMode="projected" />);
  const pitch = screen.getByRole("region", { name: "Starting eleven" });
  const bench = screen.getByRole("region", { name: "Bench order" });
  const benchDefender = within(bench).getByRole("button", { name: /^player 13,/i });
  const startingDefender = within(pitch).getByRole("button", { name: /^player 2,/i });
  const values = new Map<string, string>();
  const dataTransfer = {
    setData: (type: string, value: string) => values.set(type, value),
    getData: (type: string) => values.get(type) ?? "",
    effectAllowed: "move",
    dropEffect: "move",
  };

  fireEvent.dragStart(benchDefender, { dataTransfer });
  expect(fireEvent.dragOver(startingDefender, { dataTransfer })).toBe(false);
  fireEvent.drop(startingDefender, { dataTransfer });

  expect(screen.getByRole("status")).toHaveTextContent("Starting XI updated locally");
  expect(within(pitch).getByRole("button", { name: /^player 13,/i })).toBeInTheDocument();
  expect(within(bench).getByRole("button", { name: /^player 2,/i })).toBeInTheDocument();
});


test("opens an evidence-backed player profile with horizon and risk", async () => {
  const user = userEvent.setup();
  const detailedPicks = picks.map((pick, index) => index === 0 ? {
    ...pick,
    prediction: {
      predicted_points: 6.4,
      xmins: 72,
      start_probability: 0.8,
      opponent: "Arsenal",
      home: true,
      difficulty: 4,
    },
    form: 7.2,
    ownership: 42.1,
    season_points: 32,
    starts: 2,
    season_goals: 1,
    season_assists: 2,
    season_bonus: 4,
    expected_goals: 1.4,
    expected_assists: 1.1,
    ict_index: 21.7,
  } : pick);
  const healthPlayers: SquadHealthPlayer[] = [{
    player_id: 1,
    name: "Player 1",
    score: 0.32,
    label: "MEDIUM",
    xmins: 72,
    start_probability: 0.8,
    availability: "AVAILABLE",
  }];
  const horizons: HorizonPlayer[] = [{
    player_id: 1,
    coverage: 1,
    predicted_points: 25,
    gameweeks: [
      { gameweek: 3, predicted_points: 6.4, opponent: "Arsenal", difficulty: 4, projection_method: "native_model" },
      { gameweek: 4, predicted_points: 4.8, opponent: "Everton", difficulty: 2, projection_method: "fixture_scaled_v1" },
    ],
  }];

  render(<TeamPitch picks={detailedPicks} preferredMode="projected" healthPlayers={healthPlayers} horizons={horizons} />);
  await user.click(screen.getByRole("button", { name: /^player 1,/i }));

  expect(screen.getByRole("region", { name: "Player decision profile" })).toBeInTheDocument();
  expect(screen.getByText("72 xMins")).toBeInTheDocument();
  expect(screen.getByText("80% start")).toBeInTheDocument();
  expect(screen.getByText("Medium risk")).toBeInTheDocument();
  expect(screen.getByText("7.2 form")).toBeInTheDocument();
  expect(screen.getByText("42.1% owned")).toBeInTheDocument();
  expect(screen.getByText("32 points")).toBeInTheDocument();
  expect(screen.getByText("2 starts")).toBeInTheDocument();
  expect(screen.getByText("1 goal · 2 assists")).toBeInTheDocument();
  expect(screen.getByText("1.4 xG · 1.1 xA")).toBeInTheDocument();
  expect(screen.getByText("21.7 ICT")).toBeInTheDocument();
  expect(screen.getByText("GW3")).toBeInTheDocument();
  expect(screen.getByText("GW4")).toBeInTheDocument();
  expect(screen.getByText(/fixture-scaled estimate/i)).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Close player profile" }));
  expect(screen.queryByRole("region", { name: "Player decision profile" })).not.toBeInTheDocument();
});


test("reorders the bench locally with accessible controls", async () => {
  const user = userEvent.setup();
  render(<TeamPitch picks={picks} preferredMode="projected" />);
  const bench = screen.getByRole("region", { name: "Bench order" });

  expect(within(bench).getAllByRole("button", { name: /^player \d+,/i })[0]).toHaveAccessibleName(/^Player 12,/);
  await user.click(within(bench).getByRole("button", { name: "Move Player 13 earlier" }));

  expect(within(bench).getAllByRole("button", { name: /^player \d+,/i })[0]).toHaveAccessibleName(/^Player 13,/);
  expect(screen.getByRole("status")).toHaveTextContent("Bench order updated locally");
});


test("resets local squad edits when refreshed official picks change", async () => {
  const user = userEvent.setup();
  const { rerender } = render(<TeamPitch picks={picks} preferredMode="projected" />);
  const bench = screen.getByRole("region", { name: "Bench order" });
  await user.click(within(bench).getByRole("button", { name: "Move Player 13 earlier" }));
  expect(within(bench).getAllByRole("button", { name: /^player \d+,/i })[0]).toHaveAccessibleName(/^Player 13,/);

  const refreshed = picks.map((pick) => {
    if (pick.player_id === 1) return { ...pick, position: 12 };
    if (pick.player_id === 12) return { ...pick, position: 1 };
    return pick;
  });
  rerender(<TeamPitch picks={refreshed} preferredMode="projected" />);

  await waitFor(() => expect(
    within(bench).getAllByRole("button", { name: /^player \d+,/i })[0],
  ).toHaveAccessibleName(/^Player 1,/));
  expect(screen.queryByText("Bench order updated locally")).not.toBeInTheDocument();
});
