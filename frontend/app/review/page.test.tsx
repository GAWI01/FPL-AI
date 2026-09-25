import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { TeamProvider } from "@/app/providers/TeamProvider";
import ReviewPage from "./page";


beforeEach(() => {
  localStorage.setItem("fpl-ai-team-id", "123");
});


afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});


test("shows team loading while a saved Team ID is restored for review", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(() => undefined));

  render(<TeamProvider><ReviewPage /></TeamProvider>);

  expect(await screen.findByText("Loading your team…")).toBeInTheDocument();
  expect(screen.queryByText("Connect a team first")).not.toBeInTheDocument();
});


test("shows the dashboard error when a saved Team ID cannot be restored for review", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ detail: "FPL is temporarily unavailable" }), { status: 503 }),
  );

  render(<TeamProvider><ReviewPage /></TeamProvider>);

  const alert = await screen.findByRole("alert");
  expect(alert).toHaveTextContent("Your team could not be loaded");
  expect(alert).toHaveTextContent("FPL is temporarily unavailable");
});
