import { render, screen, within } from "@testing-library/react";
import { expect, test } from "vitest";

import type { DecisionPlayer, TeamPick } from "@/lib/contracts";
import { ModelXIComparison } from "./ModelXIComparison";


const currentPicks: TeamPick[] = Array.from({ length: 11 }, (_, index) => ({
  player_id: index + 1,
  position: index + 1,
  name: `Current ${index + 1}`,
  position_name: index === 0 ? "GKP" : index < 5 ? "DEF" : index < 9 ? "MID" : "FWD",
  team: `Club ${index + 1}`,
  price: 5,
  status: "a",
  prediction: { predicted_points: 4 },
}));

const modelPlayers: DecisionPlayer[] = [
  ...currentPicks.slice(0, 9).map((pick) => ({
    player_id: pick.player_id,
    name: pick.name,
    position: pick.position_name,
    team: pick.team,
    predicted_points: 5,
  })),
  { player_id: 20, name: "Model Forward", position: "FWD", team: "Arsenal", predicted_points: 8.2 },
  { player_id: 21, name: "Model Mid", position: "MID", team: "Chelsea", predicted_points: 7.4 },
];


test("separates retained players, model additions and displaced current slots", () => {
  render(
    <ModelXIComparison
      currentPicks={currentPicks}
      modelPlayers={modelPlayers}
      formation="3-5-2"
      projectedPoints={69.8}
    />,
  );

  const comparison = screen.getByRole("region", { name: "Current XI versus model XI" });
  expect(within(comparison).getByText("9/11 retained")).toBeInTheDocument();
  expect(within(comparison).getByText("2 model changes")).toBeInTheDocument();
  expect(within(comparison).getByText("Model Forward")).toBeInTheDocument();
  expect(within(comparison).getByText("Model Mid")).toBeInTheDocument();
  expect(within(comparison).getByText("Current 10")).toBeInTheDocument();
  expect(within(comparison).getByText("Current 11")).toBeInTheDocument();
  expect(within(comparison).getByText("69.8 xPts")).toBeInTheDocument();
  expect(within(comparison).getByText(/not an immediate transfer instruction/i)).toBeInTheDocument();
});
