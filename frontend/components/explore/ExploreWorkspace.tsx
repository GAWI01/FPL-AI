"use client";

import { CalendarRange, Plus, Scale, Search, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { useTeam } from "@/app/providers/TeamProvider";
import { DataState } from "@/components/states/DataState";
import { fetchFixtureMatrix, fetchPlayers } from "@/lib/api";
import type { FixtureMatrixEnvelope, PlayerMarketEnvelope, PlayerSummary, SourceMeta } from "@/lib/contracts";


const filters = ["ALL", "GKP", "DEF", "MID", "FWD"] as const;
const metric = (value?: number | null) => typeof value === "number" ? value.toFixed(1) : "—";
type PositionFilter = (typeof filters)[number];

function readExploreUrl(): { position: PositionFilter; query: string; selectedIds: number[] } {
  if (typeof window === "undefined") return { position: "ALL", query: "", selectedIds: [] };
  const params = new URLSearchParams(window.location.search);
  const candidate = (params.get("position") ?? "ALL").toUpperCase();
  const position = filters.includes(candidate as PositionFilter)
    ? candidate as PositionFilter
    : "ALL";
  const selectedIds = (params.get("compare") ?? "")
    .split(",")
    .map((value) => Number(value))
    .filter((value, index, values) => Number.isInteger(value) && value > 0 && values.indexOf(value) === index)
    .slice(0, 4);
  return { position, query: params.get("q") ?? "", selectedIds };
}

function fdrClass(difficulty: number | null) {
  if (difficulty == null) return "fixture-blank";
  if (difficulty <= 2) return "fixture-easy";
  if (difficulty >= 4) return "fixture-hard";
  return "fixture-medium";
}

function availability(player: PlayerSummary) {
  if (player.status === "a") return "Available";
  if (typeof player.chance_of_playing_next_round === "number") return `${player.chance_of_playing_next_round}% chance`;
  return player.status ? player.status.toUpperCase() : "Unknown";
}


export function ExploreWorkspace() {
  const { dashboard, loading, error } = useTeam();
  const [initialFilters] = useState(readExploreUrl);
  const [position, setPosition] = useState<PositionFilter>(initialFilters.position);
  const [query, setQuery] = useState(initialFilters.query);
  const [selectedIds, setSelectedIds] = useState<number[]>(initialFilters.selectedIds);
  const [matrix, setMatrix] = useState<FixtureMatrixEnvelope["data"] | null>(null);
  const [matrixMeta, setMatrixMeta] = useState<SourceMeta | null>(null);
  const [matrixError, setMatrixError] = useState<string | null>(null);
  const [publicPlayers, setPublicPlayers] = useState<PlayerSummary[]>([]);
  const [marketMeta, setMarketMeta] = useState<SourceMeta | null>(null);
  const [marketPhase, setMarketPhase] = useState<Pick<PlayerMarketEnvelope["data"], "status" | "finished"> | null>(null);
  const [marketLoading, setMarketLoading] = useState(!dashboard);
  const [marketError, setMarketError] = useState<string | null>(null);
  const players = useMemo(
    () => publicPlayers.length ? publicPlayers : dashboard?.data.players?.players ?? [],
    [dashboard, publicPlayers],
  );
  const selected = useMemo(() => {
    const byId = new Map(players.map((player) => [player.player_id, player]));
    return selectedIds.map((playerId) => byId.get(playerId)).filter((player): player is PlayerSummary => Boolean(player));
  }, [players, selectedIds]);
  const visible = useMemo(() => players.filter((player) =>
    (position === "ALL" || player.position === position)
    && player.name.toLowerCase().includes(query.toLowerCase())), [players, position, query]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    if (position === "ALL") params.delete("position"); else params.set("position", position);
    if (query) params.set("q", query); else params.delete("q");
    if (selectedIds.length) params.set("compare", selectedIds.join(",")); else params.delete("compare");
    const next = `${window.location.pathname}${params.size ? `?${params.toString()}` : ""}${window.location.hash}`;
    window.history.replaceState(window.history.state, "", next);
  }, [position, query, selectedIds]);

  useEffect(() => {
    const controller = new AbortController();
    void fetchFixtureMatrix(5, controller.signal)
      .then((result) => {
        setMatrix(result.data);
        setMatrixMeta(result.meta);
      })
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setMatrixError(caught instanceof Error ? caught.message : "Fixture matrix unavailable");
        }
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    queueMicrotask(() => {
      if (controller.signal.aborted) return;
      setMarketLoading(true);
      setMarketError(null);
      void fetchPlayers(700, controller.signal)
        .then((result) => {
          setPublicPlayers(result.data.players);
          setMarketMeta(result.meta);
          setMarketPhase({ status: result.data.status, finished: result.data.finished });
        })
        .catch((caught) => {
          if (!controller.signal.aborted) {
            setMarketError(caught instanceof Error ? caught.message : "Player market unavailable");
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) setMarketLoading(false);
        });
    });
    return () => controller.abort();
  }, []);

  if (!dashboard && !publicPlayers.length && (loading || marketLoading)) {
    return <DataState title="Loading public player market…" loading>Fetching official FPL data and the latest model projections.</DataState>;
  }
  if (!dashboard && !publicPlayers.length && (marketError || error)) {
    return <DataState title="The public player market is temporarily unavailable" tone="error">{marketError || error}</DataState>;
  }

  const toggle = (player: PlayerSummary) => setSelectedIds((current) => {
    if (current.includes(player.player_id)) return current.filter((playerId) => playerId !== player.player_id);
    return current.length < 4 ? [...current, player.player_id] : current;
  });
  const rankedSelection = [...selected].sort((a, b) => (b.predicted_points ?? 0) - (a.predicted_points ?? 0));
  const leader = rankedSelection[0];
  const projectedEdge = leader && rankedSelection[1]
    ? (leader.predicted_points ?? 0) - (rankedSelection[1].predicted_points ?? 0)
    : 0;
  const cachedData = Boolean(marketMeta?.stale || matrixMeta?.stale);
  const marketLive = marketPhase?.status === "LIVE" && marketPhase.finished !== true;
  const marketLabel = cachedData ? "Cached" : marketLive ? "Live" : "Official";
  const marketSourceClass = cachedData ? "source-derived" : marketLive ? "source-live" : "source-official";

  return (
    <section className="workspace-page">
      <div className="workspace-heading"><div><span className="eyebrow">PLAYER MARKET</span><h1>Explore the player pool.</h1><p>Filter current FPL data, then compare a shortlist without changing your squad.</p></div><span className={`source-pill ${marketSourceClass}`}>{marketLabel}</span></div>
      {!dashboard ? <aside className="explore-public-banner"><div><strong>Connect a team for personalized projections.</strong><p>Public player data, model rankings and the fixture matrix remain available without a Team ID.</p></div><span>Public mode</span></aside> : null}
      {cachedData ? <DataState title="Showing cached FPL data" tone="warning">The official service is temporarily unavailable. Player and fixture timestamps remain visible in the API response.</DataState> : null}
      {dashboard && marketError ? <DataState title="The full player market is temporarily unavailable" tone="warning">Showing the connected dashboard subset. {marketError}</DataState> : null}
      <div className="explore-toolbar">
        <label><Search size={15} aria-hidden="true" /><span className="sr-only">Search players</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search players" /></label>
        <div className="position-filters" aria-label="Position filter">{filters.map((filter) => <button key={filter} className={position === filter ? "active" : ""} onClick={() => setPosition(filter)}>{filter}</button>)}</div>
      </div>
      {selected.length ? <aside className="compare-tray" aria-label="Player comparison"><div><Scale size={16} /><strong>{selected.length} of 4 selected</strong></div><div>{selected.map((player) => <button key={player.player_id} onClick={() => toggle(player)}>{player.name}<X size={12} aria-hidden="true" /></button>)}</div></aside> : null}
      {selected.length >= 2 ? <article className="premium-card compare-lab" role="region" aria-label="Detailed player comparison">
        <header><div><Scale size={16} /><h2>Shortlist intelligence</h2></div><div><span className={`source-pill ${marketSourceClass}`}>{marketLabel} market</span><span className="source-pill source-model">Model xPts</span></div></header>
        <div className="compare-lab-grid">{rankedSelection.map((player, index) => {
          const valueScore = player.price && player.predicted_points != null ? player.predicted_points / player.price : null;
          return <section key={player.player_id} className={index === 0 ? "compare-leader" : ""}><div><span>{player.position} · {player.team_short}</span><strong>{player.name}</strong>{index === 0 ? <b>Projected leader</b> : null}</div><dl><div><dt>Projected</dt><dd>{metric(player.predicted_points)} xPts</dd></div><div><dt>GW points</dt><dd>{player.event_points ?? "—"} actual</dd></div><div><dt>Returns</dt><dd>{player.goals ?? "—"} goal · {player.assists ?? "—"} assist</dd></div><div><dt>Bonus signal</dt><dd>{player.bonus ?? "—"} bonus · {player.bps ?? "—"} BPS</dd></div><div><dt>xMins</dt><dd>{player.xmins == null ? "—" : `${Math.round(player.xmins)} xMins`}</dd></div><div><dt>Form</dt><dd>{metric(player.form)}</dd></div><div><dt>Ownership</dt><dd>{metric(player.ownership)}%</dd></div><div><dt>Price</dt><dd>£{metric(player.price)}m</dd></div><div><dt>Value</dt><dd>{metric(valueScore)} xPts/£m</dd></div><div><dt>Season underlying</dt><dd>{metric(player.expected_goals)} xG · {metric(player.expected_assists)} xA</dd></div><div><dt>Involvement</dt><dd>{metric(player.expected_goal_involvements)} xGI · {metric(player.ict_index)} ICT</dd></div></dl><small className="compare-underlying-source">Official · season</small><p className="compare-news"><span className="source-pill source-official">Official FPL status</span><strong>{availability(player)}</strong><small>{player.news || "No current availability note."}</small></p></section>;
        })}</div>
        <footer><span>PROJECTED EDGE</span><strong>{leader?.name} leads by +{projectedEdge.toFixed(1)} xPts</strong><p>Compare the model edge with price and current form; this shortlist is local and never changes your official team.</p></footer>
      </article> : null}
      {matrix ? <article id="fixture-matrix" className="premium-card fixture-matrix" role="region" aria-label="Fixture planning matrix">
        <header><div><CalendarRange size={16} aria-hidden="true" /><h2>Five-Gameweek fixture matrix</h2></div><div><span className="source-pill source-official">Official</span><small>FDR 1 easy · 5 hard</small></div></header>
        <div className="fixture-matrix-scroll">
          <div className="fixture-matrix-row fixture-matrix-head" style={{ gridTemplateColumns: `120px repeat(${matrix.gameweeks.length}, minmax(118px, 1fr))` }}><strong>Club</strong>{matrix.gameweeks.map((gameweek) => <span key={gameweek}>GW{gameweek}</span>)}</div>
          {matrix.teams.map((team) => <div className="fixture-matrix-row" key={team.team_id} style={{ gridTemplateColumns: `120px repeat(${matrix.gameweeks.length}, minmax(118px, 1fr))` }}><strong>{team.team_short}<small>{team.team}</small></strong>{team.fixtures.map((fixture) => <span className={fdrClass(fixture.difficulty)} key={fixture.event}><b>{fixture.opponents.length ? fixture.opponents.join(" · ") : "Blank"}</b><small>{fixture.fixture_count > 1 ? "Double GW · " : ""}{fixture.difficulty == null ? "No fixture" : `FDR ${fixture.difficulty}`}</small></span>)}</div>)}
        </div>
      </article> : matrixError ? <DataState title="Fixture matrix is temporarily unavailable" tone="warning">{matrixError}</DataState> : <DataState title="Loading fixture matrix" loading>Building the official five-Gameweek schedule…</DataState>}
      <article id="player-market" className="premium-card explorer-card">
        <header className="explorer-head"><span>Player</span><span>Position</span><span>Price</span><span>Own.</span><span>Form</span><span>GW points</span><span>xPts</span><span>xMins</span><span>Status</span><span /></header>
        <div>{visible.map((player) => {
          const chosen = selected.some((item) => item.player_id === player.player_id);
          return <div className="explorer-row" key={player.player_id}><strong>{player.name}<small>{player.team}</small></strong><span>{player.position}</span><span>£{metric(player.price)}m</span><span>{metric(player.ownership)}%</span><span>{metric(player.form)}</span><span className="live-player-points">{player.event_points ?? "—"}</span><b>{metric(player.predicted_points)}</b><span>{player.xmins == null ? "—" : Math.round(player.xmins)}</span><span title={player.news || undefined}>{availability(player)}</span><button aria-label={`${chosen ? "Remove" : "Compare"} ${player.name}`} onClick={() => toggle(player)}>{chosen ? <X size={14} /> : <Plus size={14} />}</button></div>;
        })}{visible.length === 0 ? <DataState title="No players match this filter" /> : null}</div>
      </article>
    </section>
  );
}
