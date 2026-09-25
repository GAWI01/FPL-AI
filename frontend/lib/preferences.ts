import { useSyncExternalStore } from "react";

export const SEASON_GOAL_KEY = "fpl-ai-season-goal";
const SEASON_GOAL_EVENT = "fpl-ai-season-goal-change";

export type SeasonGoal = "mini_league" | "overall_rank" | "decision_quality";

export const DEFAULT_SEASON_GOAL: SeasonGoal = "mini_league";

export const seasonGoalOptions: Array<{
  id: SeasonGoal;
  label: string;
  title: string;
  headline: string;
  description: string;
}> = [
  {
    id: "mini_league",
    label: "Win my mini-league",
    title: "Mini-league edge",
    headline: "Create separation through better decisions.",
    description: "Use expected value, captain reliability and selective upside without inventing rival data.",
  },
  {
    id: "overall_rank",
    label: "Improve overall rank",
    title: "Overall-rank edge",
    headline: "Climb through repeatable expected value.",
    description: "Keep transfer cost, squad structure and captain reliability ahead of short-term noise.",
  },
  {
    id: "decision_quality",
    label: "Improve my decisions",
    title: "Decision-quality edge",
    headline: "Build a repeatable FPL process.",
    description: "Focus on evidence, uncertainty and post-Gameweek learning instead of outcome bias.",
  },
];

export function readSeasonGoal(): SeasonGoal {
  if (typeof window === "undefined") return DEFAULT_SEASON_GOAL;
  const stored = window.localStorage.getItem(SEASON_GOAL_KEY);
  return seasonGoalOptions.some((option) => option.id === stored)
    ? stored as SeasonGoal
    : DEFAULT_SEASON_GOAL;
}

export function writeSeasonGoal(goal: SeasonGoal) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(SEASON_GOAL_KEY, goal);
  window.dispatchEvent(new Event(SEASON_GOAL_EVENT));
}

export function seasonGoalCopy(goal: SeasonGoal) {
  return seasonGoalOptions.find((option) => option.id === goal) ?? seasonGoalOptions[0];
}

function subscribeSeasonGoal(onStoreChange: () => void) {
  if (typeof window === "undefined") return () => undefined;
  const handleStorage = (event: StorageEvent) => {
    if (event.key === SEASON_GOAL_KEY) onStoreChange();
  };
  window.addEventListener("storage", handleStorage);
  window.addEventListener(SEASON_GOAL_EVENT, onStoreChange);
  return () => {
    window.removeEventListener("storage", handleStorage);
    window.removeEventListener(SEASON_GOAL_EVENT, onStoreChange);
  };
}

export function useSeasonGoal() {
  return useSyncExternalStore(
    subscribeSeasonGoal,
    readSeasonGoal,
    () => DEFAULT_SEASON_GOAL,
  );
}
