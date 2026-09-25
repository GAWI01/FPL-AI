import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { DeadlineCountdown, formatDeadlineRemaining } from "./DeadlineCountdown";


test("formats a deadline as a compact live countdown", () => {
  const now = Date.parse("2026-09-01T10:00:00Z");

  expect(formatDeadlineRemaining("2026-09-03T17:30:00Z", now)).toBe("2d 7h 30m");
  expect(formatDeadlineRemaining("2026-09-01T10:00:59Z", now)).toBe("59s");
  expect(formatDeadlineRemaining("2026-09-01T09:59:59Z", now)).toBe("Deadline passed");
});


test("labels the target gameweek and official deadline", () => {
  render(
    <DeadlineCountdown
      deadline="2026-09-03T17:30:00Z"
      event={3}
      now={Date.parse("2026-09-01T10:00:00Z")}
    />,
  );

  expect(screen.getByText("GW3 deadline")).toBeInTheDocument();
  expect(screen.getByText("2d 7h 30m")).toBeInTheDocument();
  expect(screen.getByRole("timer")).toHaveAttribute(
    "dateTime",
    "2026-09-03T17:30:00Z",
  );
});
