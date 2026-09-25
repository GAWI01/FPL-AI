import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { TeamProvider } from "@/app/providers/TeamProvider";
import TeamPage from "./page";


beforeEach(() => {
  localStorage.setItem("fpl-ai-team-id", "123");
});


afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});


test("shows squad loading while a saved Team ID is restored", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(() => undefined));

  render(<TeamProvider><TeamPage /></TeamProvider>);

  expect(await screen.findByText("Loading your squad…")).toBeInTheDocument();
  expect(screen.queryByText("Connect a team first")).not.toBeInTheDocument();
});


test("shows the dashboard error when a saved Team ID cannot be restored", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ detail: "This Team ID could not be found" }), { status: 404 }),
  );

  render(<TeamProvider><TeamPage /></TeamProvider>);

  const alert = await screen.findByRole("alert");
  expect(alert).toHaveTextContent("Your squad could not be loaded");
  expect(alert).toHaveTextContent("This Team ID could not be found");
  expect(screen.queryByText("Connect a team first")).not.toBeInTheDocument();
});
