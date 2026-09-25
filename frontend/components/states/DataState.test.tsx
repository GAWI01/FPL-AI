import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { DataState } from "./DataState";


test("keeps loading copy accessible while reserving layout with a decorative skeleton", () => {
  const { container } = render(
    <DataState title="Loading your FPL cockpit" loading>
      Fetching official team and live data…
    </DataState>,
  );

  expect(screen.getByRole("status")).toHaveTextContent("Loading your FPL cockpit");
  expect(screen.getByRole("status")).toHaveTextContent("Fetching official team and live data");
  const skeleton = container.querySelector(".data-state-skeleton");
  expect(skeleton).toBeInTheDocument();
  expect(skeleton).toHaveAttribute("aria-hidden", "true");
  expect(skeleton?.children).toHaveLength(3);
});
