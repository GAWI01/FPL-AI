import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { StatsGrid } from "./StatsGrid";


test("uses honest empty-state labels instead of production placeholders", () => {
  render(<StatsGrid
    projectedPoints={null}
    teamEvent={null}
    loading={false}
    squadValue={null}
    teamValue={null}
    bank={null}
    overallRank={null}
    eventRank={null}
    transfers={null}
  />);

  expect(screen.queryByText("???")).not.toBeInTheDocument();
  expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(0);
  expect(screen.getByText("Bank unavailable")).toBeInTheDocument();
});
