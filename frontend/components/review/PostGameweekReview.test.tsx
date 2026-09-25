import { render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { expectNoA11yViolations } from "@/test-utils/accessibility";
import { PostGameweekReview } from "./PostGameweekReview";


const completeEnvelope = {
  data: {
    available: true,
    team_id: 123,
    event: 2,
    prediction_version: "gw2_predictions_v5.csv",
    summary: {
      projected_points: 17,
      official_points: 20,
      hit_cost: 4,
      net_points_after_hits: 16,
      actual_vs_projected: 3,
      outcome: "IN_LINE",
    },
    captain: {
      player_id: 1,
      name: "Alpha",
      multiplier: 2,
      projected_points: 6,
      actual_points: 4,
      projected_contribution: 12,
      actual_contribution: 8,
      contribution_delta: -4,
    },
    bench: { official_points: 8, projected_points: 4, player_count: 4 },
    transfers: [{
      player_in: { player_id: 2, name: "Beta" },
      player_out: { player_id: 4, name: "Delta" },
      projected_delta: -2,
      actual_delta: 10,
    }],
    picks: [],
    largest_model_miss: {
      player_id: 1,
      name: "Alpha",
      predicted_points: 6,
      actual_points: 4,
      residual: -2,
    },
    largest_xmins_miss: {
      player_id: 3,
      name: "Gamma",
      predicted_xmins: 60,
      actual_minutes: 0,
      residual: -60,
    },
    decision_quality: {
      label: "QUESTIONABLE",
      projected_decision_value: -6,
      projected_transfer_value: -6,
      captain_opportunity_cost: 0,
      basis: "pre_deadline_projection",
    },
    next_signals: [
      {
        type: "MINUTES_REVIEW",
        severity: "WATCH",
        title: "Recheck Gamma's minutes",
        message: "The largest xMins miss should be reassessed before the next deadline.",
        evidence: { predicted_xmins: 60, actual_minutes: 0 },
      },
      {
        type: "TRANSFER_DISCIPLINE",
        severity: "ACTION",
        title: "Raise the transfer threshold",
        message: "The move was negative expected value after its official points cost.",
        evidence: { projected_transfer_value: -6 },
      },
    ],
  },
  meta: {
    source: "derived",
    fetched_at: "2026-09-01T10:00:00+00:00",
    stale: false,
    version: "gw2_predictions_v5.csv",
    event: 2,
  },
  errors: [],
};


afterEach(() => {
  vi.restoreAllMocks();
});


test("shows a loading state while the historical review is fetched", () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(() => undefined));

  render(<PostGameweekReview teamId="123" />);

  expect(screen.getByText("Building your GW review")).toBeInTheDocument();
});


test("renders the complete evidence-based gameweek review", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(completeEnvelope), { status: 200 }),
  );

  render(<PostGameweekReview teamId="123" />);

  expect(await screen.findByRole("heading", { name: "GW2 review" })).toBeInTheDocument();
  expect(screen.getByText("In line")).toBeInTheDocument();
  expect(screen.getByText("20")).toBeInTheDocument();
  expect(screen.getByText("+3.0")).toBeInTheDocument();
  expect(screen.getByText("Delta → Beta")).toBeInTheDocument();
  expect(screen.getAllByText("Alpha").length).toBeGreaterThan(0);
  expect(screen.getByText("gw2_predictions_v5.csv")).toBeInTheDocument();
  expect(screen.getByText(/no retrospective narrative/i)).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Decision quality" })).toBeInTheDocument();
  expect(screen.getByText("Review process")).toBeInTheDocument();
  expect(screen.getByText("−6.0 projected decision EV")).toBeInTheDocument();
  expect(screen.getByText(/actual points do not change this rating/i)).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Largest xMins miss" })).toBeInTheDocument();
  expect(screen.getByText("60 xMins")).toBeInTheDocument();
  expect(screen.getByText("0 official minutes")).toBeInTheDocument();
  expect(screen.getByRole("region", { name: "Next Gameweek signals" })).toHaveTextContent("Recheck Gamma's minutes");
  expect(screen.getByRole("region", { name: "Next Gameweek signals" })).toHaveTextContent("Raise the transfer threshold");
});


test("post-gameweek review has no automated WCAG A/AA violations", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(completeEnvelope), { status: 200 }),
  );

  const { container } = render(<PostGameweekReview teamId="123" />);

  await screen.findByRole("heading", { name: "GW2 review" });
  await expectNoA11yViolations(container);
});


test("labels xMins audit unavailable for a legacy certified artifact", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({
      ...completeEnvelope,
      data: { ...completeEnvelope.data, largest_xmins_miss: null, next_signals: [] },
    }), { status: 200 }),
  );

  render(<PostGameweekReview teamId="123" />);

  expect(await screen.findByText("xMins unavailable")).toBeInTheDocument();
  expect(screen.getByText(/certified artifact predates the minutes field/i)).toBeInTheDocument();
});


test("warns when the official outcome feed came from cache", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({
      ...completeEnvelope,
      meta: { ...completeEnvelope.meta, stale: true },
    }), { status: 200 }),
  );

  render(<PostGameweekReview teamId="123" />);

  expect(await screen.findByText("Review uses cached official data")).toBeInTheDocument();
  expect(screen.getByText(/model artifact is unchanged/i)).toBeInTheDocument();
});


test("renders an honest unavailable state when no historical artifact exists", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({
      data: {
        available: false,
        team_id: 123,
        event: 1,
        reason: "No prediction artifact found for GW1",
      },
      meta: {
        source: "derived",
        fetched_at: "2026-09-01T10:00:00+00:00",
        stale: false,
        version: null,
        event: 1,
      },
      errors: [{ area: "model", message: "No prediction artifact found for GW1" }],
    }), { status: 200 }),
  );

  render(<PostGameweekReview teamId="123" />);

  expect(await screen.findByText("GW1 review is unavailable")).toBeInTheDocument();
  expect(screen.getByText("No prediction artifact found for GW1")).toBeInTheDocument();
});
