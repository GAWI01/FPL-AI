import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { TeamProvider } from "@/app/providers/TeamProvider";
import { expectNoA11yViolations } from "@/test-utils/accessibility";
import { AppShell } from "./AppShell";


vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

beforeEach(() => localStorage.clear());
afterEach(() => { localStorage.clear(); vi.restoreAllMocks(); });


test("shell exposes the full PRD navigation on desktop and a compact mobile bar", () => {
  render(
    <TeamProvider>
      <AppShell><div>Page content</div></AppShell>
    </TeamProvider>,
  );

  const navigation = screen.getByRole("navigation", { name: /^primary$/i });
  for (const name of [
    "Overview",
    "My Team",
    "Transfer Center",
    "AI Recommendations",
    "Players",
    "Fixtures",
    "Chips",
    "Statistics",
    "Team History",
    "Settings",
  ]) {
    expect(navigation).toContainElement(screen.getAllByRole("link", { name })[0]);
  }
  const mobileNavigation = screen.getByRole("navigation", { name: /mobile primary/i });
  for (const name of ["Overview", "My Team", "Plan", "Explore"]) {
    expect(within(mobileNavigation).getByRole("link", { name })).toBeInTheDocument();
  }
  expect(within(mobileNavigation).getByRole("button", { name: "More" })).toBeInTheDocument();
  expect(navigation).toBeInTheDocument();
  expect(screen.getByText(/team not connected/i)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /skip to content/i })).toHaveAttribute(
    "href",
    "#main-content",
  );
});


test("does not claim live data before a team is connected", () => {
  render(
    <TeamProvider>
      <AppShell><div>Page content</div></AppShell>
    </TeamProvider>,
  );

  expect(screen.getByText("Setup", { selector: ".source-pill" })).toBeInTheDocument();
  expect(screen.queryByText("Live", { selector: ".source-pill" })).not.toBeInTheDocument();
});


test("opens every remaining PRD destination from the mobile More sheet", async () => {
  const user = userEvent.setup();
  const { container } = render(
    <TeamProvider>
      <AppShell><div>Page content</div></AppShell>
    </TeamProvider>,
  );
  const mobileNavigation = screen.getByRole("navigation", { name: /mobile primary/i });
  const more = within(mobileNavigation).getByRole("button", { name: "More" });

  await user.click(more);

  const sheet = screen.getByRole("dialog", { name: "More FPL AI tools" });
  for (const name of [
    "Transfer Center",
    "AI Recommendations",
    "Players",
    "Fixtures",
    "Chips",
    "Statistics",
    "Team History",
    "Settings",
  ]) {
    expect(within(sheet).getByRole("link", { name })).toBeInTheDocument();
  }
  const close = within(sheet).getByRole("button", { name: "Close more tools" });
  const settings = within(sheet).getByRole("link", { name: "Settings" });
  expect(close).toHaveFocus();
  await expectNoA11yViolations(container);
  await user.keyboard("{Shift>}{Tab}{/Shift}");
  expect(settings).toHaveFocus();
  await user.tab();
  expect(close).toHaveFocus();

  await user.keyboard("{Escape}");

  expect(screen.queryByRole("dialog", { name: "More FPL AI tools" })).not.toBeInTheDocument();
  expect(more).toHaveFocus();
});


test("labels cached official data globally when the dashboard is stale", async () => {
  localStorage.setItem("fpl-ai-team-id", "123");
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
    data: {
      team: { team_id: 123, name: "Cached XI", picks: [] },
      live: null,
      history: null,
      fixtures: null,
      players: null,
      decision: null,
    },
    meta: {
      event: 2,
      generated_at: "2026-09-01T10:00:00Z",
      degraded: true,
      stale: true,
      official: { source: "official", fetched_at: "2026-09-01T09:45:00Z", stale: true, version: null },
    },
    errors: [{ area: "official", message: "Showing cached official FPL data" }],
  }), { status: 200 }));

  render(<TeamProvider><AppShell><div>Page content</div></AppShell></TeamProvider>);

  expect(await screen.findByText("Cached FPL data")).toBeInTheDocument();
  expect(screen.getByText("Cached", { selector: ".source-pill" })).toBeInTheDocument();
  expect(screen.getByRole("status")).toHaveTextContent(/showing the last cached data/i);
  expect(screen.getByText(/^Cached \d{2}:\d{2}$/)).toBeInTheDocument();
});
