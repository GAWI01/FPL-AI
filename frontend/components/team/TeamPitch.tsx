"use client";

import { Activity, ChevronLeft, ChevronRight, Gauge, ShieldAlert, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState, type DragEvent } from "react";

import { isValidStartingXI } from "@/app/teamSelection";
import { TeamShirt } from "@/components/team/TeamShirt";
import type { HorizonPlayer, LivePick, SquadHealthPlayer, TeamPick } from "@/lib/contracts";

type Mode = "live" | "projected";

function valueFor(pick: TeamPick, mode: Mode) {
  if (mode === "projected") return pick.prediction?.predicted_points == null ? "—" : `${pick.prediction.predicted_points.toFixed(1)} xPts`;
  return pick.event_points == null ? "—" : `${pick.event_points} pts`;
}

function percent(value?: number | null) {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "—";
}

function playerReason(pick: TeamPick, health?: SquadHealthPlayer) {
  const availability = String(health?.availability ?? pick.prediction?.availability ?? pick.status).toUpperCase();
  const xmins = health?.xmins ?? pick.prediction?.xmins ?? pick.prediction?.minutes;
  const difficulty = pick.prediction?.difficulty;
  if (["UNAVAILABLE", "D", "I", "S", "U"].includes(availability)) return "Availability is the dominant concern. Keep a playable bench route until official team news improves.";
  if (health?.score != null && health.score >= 0.45) return "Minutes and availability signals create material downside. Treat the headline projection as fragile.";
  if (typeof xmins === "number" && xmins < 60) return "Expected minutes are below a full appearance, so upside depends on an uncertain start or early return.";
  if (typeof difficulty === "number" && difficulty >= 4) return "The immediate fixture is difficult. The multi-Gameweek view matters more than the single-week score here.";
  return "Minutes, availability and fixture signals are aligned. This is a stable squad slot unless a higher-upside move clears the transfer threshold.";
}

type TeamPitchProps = {
  picks: TeamPick[];
  preferredMode: Mode;
  livePicks?: LivePick[];
  healthPlayers?: SquadHealthPlayer[];
  horizons?: HorizonPlayer[];
};

export function TeamPitch({ picks, preferredMode, livePicks = [], healthPlayers = [], horizons = [] }: TeamPitchProps) {
  const displayPicks = useMemo(() => {
    const liveById = new Map(livePicks.map((pick) => [pick.player_id, pick]));
    return picks.map((pick) => {
      const live = liveById.get(pick.player_id);
      if (!live) return pick;
      return {
        ...pick,
        event_points: live.event_points ?? pick.event_points,
        live_minutes: live.live_minutes ?? pick.live_minutes,
        live_bps: live.live_bps ?? pick.live_bps,
      };
    });
  }, [livePicks, picks]);
  const officialSelectionSignature = picks
    .map((pick) => `${pick.player_id}:${pick.position}`)
    .join("|");
  const lastOfficialSelection = useRef(officialSelectionSignature);
  const lastPreferredMode = useRef(preferredMode);
  const [mode, setMode] = useState<Mode>(preferredMode);
  const [startingIds, setStartingIds] = useState(() => new Set(picks.filter((pick) => pick.position <= 11).map((pick) => pick.player_id)));
  const [benchOrder, setBenchOrder] = useState(() => picks.filter((pick) => pick.position > 11).sort((a, b) => a.position - b.position).map((pick) => pick.player_id));
  const [selected, setSelected] = useState<number | null>(null);
  const [draggedId, setDraggedId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const byId = useMemo(() => new Map(displayPicks.map((pick) => [pick.player_id, pick])), [displayPicks]);
  const healthById = useMemo(() => new Map(healthPlayers.map((player) => [player.player_id, player])), [healthPlayers]);
  const horizonById = useMemo(() => new Map(horizons.map((player) => [player.player_id, player])), [horizons]);
  const starters = displayPicks.filter((pick) => startingIds.has(pick.player_id));
  const benchIds = new Set(displayPicks.filter((pick) => !startingIds.has(pick.player_id)).map((pick) => pick.player_id));
  const orderedBenchIds = [...benchOrder.filter((id) => benchIds.has(id)), ...[...benchIds].filter((id) => !benchOrder.includes(id))];
  const bench = orderedBenchIds.map((id) => byId.get(id)).filter((pick): pick is TeamPick => Boolean(pick));
  const selectedPick = selected == null ? null : byId.get(selected) ?? null;
  const selectedHealth = selected == null ? undefined : healthById.get(selected);
  const selectedHorizon = selected == null ? undefined : horizonById.get(selected);
  const selectedXmins = selectedHealth?.xmins ?? selectedPick?.prediction?.xmins ?? selectedPick?.prediction?.minutes;
  const selectedStartProbability = selectedHealth?.start_probability ?? selectedPick?.prediction?.start_probability;

  useEffect(() => {
    if (lastPreferredMode.current === preferredMode) return;
    lastPreferredMode.current = preferredMode;
    let active = true;
    queueMicrotask(() => {
      if (active) setMode(preferredMode);
    });
    return () => { active = false; };
  }, [preferredMode]);

  useEffect(() => {
    if (lastOfficialSelection.current === officialSelectionSignature) return;
    lastOfficialSelection.current = officialSelectionSignature;
    let active = true;
    queueMicrotask(() => {
      if (!active) return;
      setStartingIds(new Set(
        picks.filter((pick) => pick.position <= 11).map((pick) => pick.player_id),
      ));
      setBenchOrder(
        picks
          .filter((pick) => pick.position > 11)
          .sort((left, right) => left.position - right.position)
          .map((pick) => pick.player_id),
      );
      setSelected(null);
      setMessage(null);
    });
    return () => { active = false; };
  }, [officialSelectionSignature, picks]);

  function swapPlayers(firstId: number, secondId: number) {
    const firstStarts = startingIds.has(firstId);
    const secondStarts = startingIds.has(secondId);
    if (firstStarts === secondStarts) return;
    const next = new Set(startingIds);
    next.delete(firstStarts ? firstId : secondId);
    next.add(firstStarts ? secondId : firstId);
    const nextPlayers = [...next].map((id) => byId.get(id)).filter((pick): pick is TeamPick => Boolean(pick));
    if (!isValidStartingXI(nextPlayers)) {
      setMessage("Invalid formation. Keep one goalkeeper and the required outfield positions.");
      setSelected(null);
      return;
    }
    const outgoingId = firstStarts ? firstId : secondId;
    const incomingId = firstStarts ? secondId : firstId;
    setBenchOrder((current) => current.map((id) => id === incomingId ? outgoingId : id));
    setStartingIds(next);
    setSelected(null);
    setMessage("Starting XI updated locally.");
  }

  function choose(playerId: number) {
    setMessage(null);
    if (selected == null) { setSelected(playerId); return; }
    if (selected === playerId) { setSelected(null); return; }
    if (startingIds.has(selected) === startingIds.has(playerId)) { setSelected(playerId); return; }
    swapPlayers(selected, playerId);
  }

  function startDrag(event: DragEvent<HTMLButtonElement>, playerId: number) {
    setMessage(null);
    setSelected(null);
    setDraggedId(playerId);
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", String(playerId));
  }

  function dropPlayer(event: DragEvent<HTMLButtonElement>, targetId: number) {
    event.preventDefault();
    const transferredId = Number(event.dataTransfer.getData("text/plain"));
    const sourceId = Number.isInteger(transferredId) && transferredId > 0 ? transferredId : draggedId;
    if (sourceId != null && sourceId !== targetId) swapPlayers(sourceId, targetId);
    setDraggedId(null);
  }

  function moveBench(index: number, offset: -1 | 1) {
    const target = index + offset;
    if (target < 0 || target >= bench.length) return;
    const next = bench.map((pick) => pick.player_id);
    [next[index], next[target]] = [next[target], next[index]];
    setBenchOrder(next);
    setSelected(null);
    setMessage("Bench order updated locally.");
  }

  function playerButton(pick: TeamPick) {
    const captainLabel = pick.is_captain ? "Captain" : pick.is_vice_captain ? "Vice captain" : null;
    const priceLabel = pick.price == null ? "Price unavailable" : `£${pick.price.toFixed(1)}m`;
    const compatibleDrop = draggedId != null && startingIds.has(draggedId) !== startingIds.has(pick.player_id);
    return (
      <button key={pick.player_id} type="button" draggable className={`team-player${draggedId === pick.player_id ? " team-player-dragging" : ""}${compatibleDrop ? " drop-active" : ""}`} aria-pressed={selected === pick.player_id} aria-label={`${pick.name}, ${pick.position_name}, ${valueFor(pick, mode)}, ${priceLabel}`} onClick={() => choose(pick.player_id)} onDragStart={(event) => startDrag(event, pick.player_id)} onDragOver={(event) => { if (compatibleDrop) event.preventDefault(); }} onDrop={(event) => dropPlayer(event, pick.player_id)} onDragEnd={() => setDraggedId(null)}>
        <TeamShirt team={pick.team} teamShort={pick.team_short} />
        <strong>{pick.name}</strong>
        <span className="team-player-price">{priceLabel}</span>
        <small>{valueFor(pick, mode)}</small>
        {captainLabel ? <em>{captainLabel}</em> : null}
      </button>
    );
  }

  return (
    <section className="team-workspace">
      <div className="team-toolbar" aria-label="Point display">
        <button type="button" aria-pressed={mode === "live"} onClick={() => setMode("live")}>Live</button>
        <button type="button" aria-pressed={mode === "projected"} onClick={() => setMode("projected")}>Projected</button>
      </div>
      {message ? <p className="team-message" role={message.startsWith("Invalid") ? "alert" : "status"}>{message}</p> : null}
      {selectedPick ? <aside className="player-inspector" role="region" aria-label="Player decision profile">
        <header>
          <div><TeamShirt team={selectedPick.team} teamShort={selectedPick.team_short} /><div><small>{selectedPick.position_name} · {selectedPick.team}</small><h2>{selectedPick.name}</h2><span className={`player-risk risk-${(selectedHealth?.label ?? "unknown").toLowerCase()}`}><ShieldAlert size={12} />{selectedHealth ? `${selectedHealth.label.charAt(0)}${selectedHealth.label.slice(1).toLowerCase()} risk` : "Risk pending"}</span></div></div>
          <button type="button" aria-label="Close player profile" onClick={() => setSelected(null)}><X size={17} /></button>
        </header>
        <div className="player-inspector-body">
          <div className="player-evidence">
            <div><span>Next GW</span><strong>{selectedPick.prediction?.predicted_points?.toFixed(1) ?? "—"} xPts</strong><small className="source-pill source-model">Model</small></div>
            <div><span>Minutes</span><strong>{selectedXmins == null ? "—" : `${Math.round(selectedXmins)} xMins`}</strong><small className="source-pill source-model">Model</small></div>
            <div><span>Starting</span><strong>{percent(selectedStartProbability)} start</strong><small className="source-pill source-derived">Derived</small></div>
            <div><span>Price</span><strong>{selectedPick.price == null ? "—" : `£${selectedPick.price.toFixed(1)}m`}</strong><small className="source-pill source-official">Official</small></div>
          </div>
          <div className="player-season-stats" role="group" aria-label="Official season evidence">
            <span><small>Form</small><strong>{selectedPick.form == null ? "—" : `${selectedPick.form.toFixed(1)} form`}</strong></span>
            <span><small>Ownership</small><strong>{selectedPick.ownership == null ? "—" : `${selectedPick.ownership.toFixed(1)}% owned`}</strong></span>
            <span><small>Points</small><strong>{selectedPick.season_points == null ? "—" : `${selectedPick.season_points} points`}</strong></span>
            <span><small>Starts</small><strong>{selectedPick.starts == null ? "—" : `${selectedPick.starts} starts`}</strong></span>
            <span><small>Returns</small><strong>{selectedPick.season_goals ?? "—"} goal · {selectedPick.season_assists ?? "—"} assists</strong></span>
            <span><small>Expected</small><strong>{selectedPick.expected_goals == null ? "—" : selectedPick.expected_goals.toFixed(1)} xG · {selectedPick.expected_assists == null ? "—" : selectedPick.expected_assists.toFixed(1)} xA</strong></span>
            <span><small>ICT</small><strong>{selectedPick.ict_index == null ? "—" : `${selectedPick.ict_index.toFixed(1)} ICT`}</strong></span>
          </div>
          <div className="player-rationale"><Gauge size={17} /><div><span>Decision read</span><p>{playerReason(selectedPick, selectedHealth)}</p></div></div>
          <div className="player-fixture"><Activity size={16} /><div><span>Immediate fixture</span><strong>{selectedPick.prediction?.opponent ?? "To be confirmed"} {selectedPick.prediction?.home == null ? "" : selectedPick.prediction.home ? "(H)" : "(A)"}</strong></div><b>FDR {selectedPick.prediction?.difficulty ?? "—"}</b></div>
          {selectedHorizon?.gameweeks.length ? <div className="player-horizon"><div>{selectedHorizon.gameweeks.map((gameweek) => <span key={`${gameweek.gameweek}-${gameweek.opponent}`}><small>GW{gameweek.gameweek}</small><strong>{gameweek.predicted_points.toFixed(1)}</strong><b>{gameweek.opponent ?? "TBC"}</b><em>{gameweek.projection_method === "native_model" ? "Native" : "Scaled"}</em></span>)}</div><p>The first available week uses native model output; later weeks are a fixture-scaled estimate with increasing uncertainty.</p></div> : null}
        </div>
      </aside> : null}
      <div className="team-pitch" role="region" aria-label="Starting eleven">
        {(["GKP", "DEF", "MID", "FWD"] as const).map((position) => (
          <div className="team-position-row" key={position} data-position={position}>
            {starters.filter((pick) => pick.position_name.toUpperCase() === position).map((pick) => playerButton(pick))}
          </div>
        ))}
      </div>
      <div className="team-bench" role="region" aria-label="Bench order"><span>Bench order</span><div>{bench.map((pick, index) => <div className="bench-slot" key={pick.player_id}>{playerButton(pick)}<div className="bench-controls"><button type="button" aria-label={`Move ${pick.name} earlier`} disabled={index === 0} onClick={() => moveBench(index, -1)}><ChevronLeft size={13} /></button><b>{index + 1}</b><button type="button" aria-label={`Move ${pick.name} later`} disabled={index === bench.length - 1} onClick={() => moveBench(index, 1)}><ChevronRight size={13} /></button></div></div>)}</div></div>
    </section>
  );
}
