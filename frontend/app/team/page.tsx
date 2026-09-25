"use client";

import { useTeam } from "@/app/providers/TeamProvider";
import { DataState } from "@/components/states/DataState";
import { ModelXIComparison } from "@/components/team/ModelXIComparison";
import { TeamPitch } from "@/components/team/TeamPitch";

export default function TeamPage() {
  const { dashboard, loading, error } = useTeam();
  if (!dashboard && loading) return <DataState title="Loading your squad…" loading>Fetching your official FPL picks and current model projections.</DataState>;
  if (!dashboard && error) return <DataState title="Your squad could not be loaded" tone="error">{error}</DataState>;
  if (!dashboard) return <DataState title="Connect a team first">Use Overview to connect your public FPL Team ID.</DataState>;
  const decision = dashboard.data.decision;
  const intelligence = dashboard.data.decision?.intelligence;
  const preferredMode = dashboard.data.live?.status === "LIVE" && dashboard.data.live.finished !== true
    ? "live"
    : "projected";
  return <div className="workspace-page"><header><span className="eyebrow">OFFICIAL SQUAD · LIVE AND PROJECTED</span><h1>My Team</h1><p>Inspect the starting XI, compare live and projected output, and test legal bench swaps.</p></header><TeamPitch picks={dashboard.data.team.picks} preferredMode={preferredMode} livePicks={dashboard.data.live?.picks} healthPlayers={intelligence?.squad_health.players} horizons={intelligence?.horizon.team_player_projections} /><ModelXIComparison currentPicks={dashboard.data.team.picks} modelPlayers={decision?.starting_xi?.players} formation={decision?.starting_xi?.formation} projectedPoints={decision?.starting_xi?.projected_points} /></div>;
}
