import { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { TeamProvider, useTeam } from "./TeamProvider";


const dashboard = {
  data: {
    team: {
      team_id: 123,
      name: "Test XI",
      bank: 10,
      event: 2,
      transfers: 0,
      picks: [],
    },
    live: null,
    history: { history: [] },
    fixtures: { fixtures: [] },
    players: { players: [] },
    decision: null,
  },
  meta: {
    event: 2,
    generated_at: "2026-08-31T18:00:00+00:00",
    degraded: false,
  },
  errors: [],
};


function Probe() {
  const [value, setValue] = useState("");
  const { connect, dashboard: result, loading } = useTeam();
  return (
    <div>
      <label htmlFor="team-id">Team ID</label>
      <input id="team-id" value={value} onChange={(event) => setValue(event.target.value)} />
      <button type="button" onClick={() => void connect(value)}>Connect</button>
      {loading ? <span>Loading</span> : null}
      {result ? <span>{result.data.team.name}</span> : null}
    </div>
  );
}


beforeEach(() => {
  localStorage.clear();
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(dashboard), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
});


afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});


test("connect persists a valid Team ID and loads the dashboard", async () => {
  const user = userEvent.setup();
  render(<TeamProvider><Probe /></TeamProvider>);

  await user.type(screen.getByLabelText(/team id/i), "123");
  await user.click(screen.getByRole("button", { name: /connect/i }));

  expect(localStorage.getItem("fpl-ai-team-id")).toBe("123");
  expect(await screen.findByText("Test XI")).toBeInTheDocument();
});


test("disconnect clears the selected Team ID and dashboard", async () => {
  const user = userEvent.setup();
  localStorage.setItem("fpl-ai-team-id", "123");
  function DisconnectProbe() {
    const team = useTeam();
    return <><span>{team.dashboard?.data.team.name ?? "No team"}</span><button onClick={team.disconnect}>Disconnect</button></>;
  }
  render(<TeamProvider><DisconnectProbe /></TeamProvider>);
  expect(await screen.findByText("Test XI")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Disconnect" }));

  expect(localStorage.getItem("fpl-ai-team-id")).toBeNull();
  expect(screen.getByText("No team")).toBeInTheDocument();
});
