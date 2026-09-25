import { ArrowRightLeft, Check, Minus, Plus } from "lucide-react";

import type { DecisionPlayer, TeamPick } from "@/lib/contracts";


type ModelXIComparisonProps = {
  currentPicks: TeamPick[];
  modelPlayers?: DecisionPlayer[];
  formation?: string | null;
  projectedPoints?: number | null;
};

const points = (value?: number | null) => typeof value === "number" ? `${value.toFixed(1)} xPts` : "—";

function PlayerList({ title, players, direction }: { title: string; players: DecisionPlayer[]; direction: "in" | "out" }) {
  return (
    <section>
      <header><span className={direction === "in" ? "model-in" : "model-out"}>{direction === "in" ? <Plus size={13} /> : <Minus size={13} />}</span><h3>{title}</h3></header>
      <div>{players.length ? players.map((player) => <article key={player.player_id}><div><strong>{player.name}</strong><small>{player.position ?? "—"} · {player.team ?? "—"}</small></div><b>{points(player.predicted_points)}</b></article>) : <p>No differences in this group.</p>}</div>
    </section>
  );
}

export function ModelXIComparison({ currentPicks, modelPlayers, formation, projectedPoints }: ModelXIComparisonProps) {
  const currentStarters = currentPicks.filter((pick) => pick.position <= 11);
  const currentIds = new Set(currentStarters.map((pick) => pick.player_id));
  const modelIds = new Set((modelPlayers ?? []).map((player) => player.player_id));
  const retained = currentStarters.filter((pick) => modelIds.has(pick.player_id));
  const additions = (modelPlayers ?? []).filter((player) => !currentIds.has(player.player_id));
  const displaced: DecisionPlayer[] = currentStarters
    .filter((pick) => !modelIds.has(pick.player_id))
    .map((pick) => ({
      player_id: pick.player_id,
      name: pick.name,
      position: pick.position_name,
      team: pick.team,
      predicted_points: pick.prediction?.predicted_points,
    }));
  const changes = Math.max(additions.length, displaced.length);

  return (
    <article className="premium-card model-xi-comparison" role="region" aria-label="Current XI versus model XI">
      <header><div><ArrowRightLeft size={16} /><h2>Current XI vs model benchmark</h2></div><span className="source-pill source-model">Model</span></header>
      {!modelPlayers?.length ? <div className="model-xi-empty"><strong>Model XI unavailable</strong><p>Your official squad remains visible. Refresh the decision model before comparing lineups.</p></div> : <>
        <div className="model-xi-summary">
          <div><Check size={15} /><span><strong>{retained.length}/{currentStarters.length} retained</strong><small>Already aligned</small></span></div>
          <div><ArrowRightLeft size={15} /><span><strong>{changes} model {changes === 1 ? "change" : "changes"}</strong><small>Benchmark gap</small></span></div>
          <div><span><strong>{formation ?? "—"}</strong><small>Model formation</small></span></div>
          <div><span><strong>{points(projectedPoints)}</strong><small>Projected XI</small></span></div>
        </div>
        <div className="model-xi-differences">
          <PlayerList title="Model additions" players={additions} direction="in" />
          <PlayerList title="Current slots displaced" players={displaced} direction="out" />
        </div>
        <footer><strong>Benchmark, not a transfer order.</strong><p>This is not an immediate transfer instruction. Plan applies your bank, free transfers, hit cost and five-Gameweek horizon before recommending action.</p></footer>
      </>}
    </article>
  );
}
