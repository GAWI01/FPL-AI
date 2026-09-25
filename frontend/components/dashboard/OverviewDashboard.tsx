"use client";

import { ArrowRight, CalendarDays, Crown, Lightbulb, RefreshCw, ShieldAlert, Sparkles, TrendingUp, Trophy } from "lucide-react";
import Link from "next/link";
import { useMemo, useState, type FormEvent } from "react";

import { useTeam } from "@/app/providers/TeamProvider";
import { RankTrend } from "@/components/dashboard/RankTrend";
import { DataState } from "@/components/states/DataState";
import { TeamShirt } from "@/components/team/TeamShirt";
import type { LiveEvent, LivePick, TeamPick } from "@/lib/contracts";
import { seasonGoalCopy, useSeasonGoal } from "@/lib/preferences";

function compactNumber(value: number | null | undefined) {
  if (value == null) return "—";
  return new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

function points(value: number | null | undefined) {
  return value == null ? "—" : value.toFixed(1);
}

const eventCopy: Record<LiveEvent["event_type"], [string, string]> = {
  GOAL: ["goal", "goals"],
  ASSIST: ["assist", "assists"],
  PENALTY_SAVE: ["penalty saved", "penalties saved"],
  SAVE: ["save", "saves"],
  BONUS: ["bonus", "bonus"],
  YELLOW_CARD: ["yellow card", "yellow cards"],
  RED_CARD: ["red card", "red cards"],
  OWN_GOAL: ["own goal", "own goals"],
  PENALTY_MISS: ["penalty missed", "penalties missed"],
};

function eventLabel(event: LiveEvent) {
  const [singular, plural] = eventCopy[event.event_type];
  return `${event.count} ${event.count === 1 ? singular : plural}`;
}

function CompactSquad({ picks, livePicks = [], liveMode }: { picks: TeamPick[]; livePicks?: LivePick[]; liveMode: boolean }) {
  const liveById = new Map(livePicks.map((pick) => [pick.player_id, pick]));
  return (
    <div className="cockpit-squad" aria-label="Current starting eleven">
      {picks.filter((pick) => pick.position <= 11).map((pick) => {
        const livePoints = liveById.get(pick.player_id)?.event_points ?? pick.event_points;
        const displayPoints = liveMode
          ? livePoints == null ? "—" : `${livePoints} pts`
          : pick.prediction?.predicted_points == null ? "—" : `${pick.prediction.predicted_points.toFixed(1)} xPts`;
        return (
          <div className="cockpit-player" key={pick.player_id}>
            <TeamShirt className="cockpit-shirt" team={pick.team} teamShort={pick.team_short} />
            <strong>{pick.name}</strong>
            <small>{displayPoints}</small>
            {pick.is_captain ? <b aria-label="Captain">C</b> : null}
          </div>
        );
      })}
    </div>
  );
}

function ConnectPanel() {
  const { connect, loading, error } = useTeam();
  const [value, setValue] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    try { await connect(value); } catch { /* Provider renders the API error. */ }
  }
  return (
    <section className="connect-premium">
      <span className="connect-mark"><Sparkles aria-hidden="true" /></span>
      <span className="eyebrow">YOUR FPL COMMAND CENTER</span>
      <h1>Make the move your mini-league rivals miss.</h1>
      <p>Connect your public FPL Team ID for live points, projected decisions and a five-gameweek planning edge.</p>
      <form onSubmit={submit}>
        <label htmlFor="overview-team-id">FPL Team ID</label>
        <div>
          <input id="overview-team-id" inputMode="numeric" pattern="[0-9]+" value={value} onChange={(event) => setValue(event.target.value)} placeholder="e.g. 1234567" required />
          <button className="primary" disabled={loading}>{loading ? "Connecting…" : "Open my dashboard"}<ArrowRight size={16} aria-hidden="true" /></button>
        </div>
      </form>
      {error ? <p className="connect-error" role="alert">{error}</p> : null}
      <small>No FPL password. Public team data only.</small>
    </section>
  );
}

export function OverviewDashboard() {
  const { dashboard, loading, error, refresh } = useTeam();
  const seasonGoal = useSeasonGoal();
  const liveScore = useMemo(() => {
    const picks = dashboard?.data.live?.picks;
    if (!picks?.length) return null;
    const contributions = picks.map((pick) => pick.multiplied_points
      ?? (pick.event_points != null && pick.multiplier != null
        ? pick.event_points * pick.multiplier
        : null));
    let total = 0;
    for (const value of contributions) {
      if (value == null) return null;
      total += value;
    }
    return total;
  }, [dashboard]);

  if (!dashboard) {
    if (loading) return <DataState title="Loading your FPL cockpit" loading>Fetching official team and live data…</DataState>;
    return <ConnectPanel />;
  }

  const { team, decision } = dashboard.data;
  const transfer = decision?.transfers?.recommended_transfers?.[0] ?? decision?.transfers?.recommended ?? null;
  const netGain = decision?.transfers?.net_gain;
  const actionsLocked = dashboard.meta.actions_locked ?? true;
  const liveMode = dashboard.data.live?.status === "LIVE" && dashboard.data.live?.finished !== true;
  const stale = dashboard.meta.stale ?? dashboard.meta.official?.stale ?? false;
  const liveSourceLabel = stale ? "Cached" : liveMode ? "Live" : "Official";
  const liveSourceClass = stale ? "source-derived" : liveMode ? "source-live" : "source-official";
  const officialSourceLabel = stale ? "Cached" : "Official";
  const officialSourceClass = stale ? "source-derived" : "source-official";
  const planTitle = transfer ? `${transfer.player_out} → ${transfer.player_in}` : decision ? "Hold the transfer" : null;
  const recommendationTitle = actionsLocked ? "Gameweek locked" : planTitle;
  const fixtures = dashboard.data.fixtures?.fixtures ?? [];
  const liveSummary = dashboard.data.live?.summary;
  const liveFixtures = dashboard.data.live?.fixtures ?? [];
  const liveEvents = dashboard.data.live?.events ?? [];
  const captains = [decision?.captain, decision?.vice_captain].filter(Boolean);
  const health = decision?.intelligence?.squad_health;
  const formWatch = [...(dashboard.data.players?.players ?? [])]
    .filter((player) => typeof player.form === "number")
    .sort((left, right) => (right.form ?? 0) - (left.form ?? 0))
    .slice(0, 3);
  const liveLeaders = [...(dashboard.data.players?.players ?? [])]
    .filter((player) => typeof player.event_points === "number")
    .sort((left, right) => (right.event_points ?? 0) - (left.event_points ?? 0))
    .slice(0, 3);
  const actionInsights = decision?.intelligence?.insights?.slice(0, 2) ?? [];
  const currentSquadProjection = decision?.current_team?.players.reduce(
    (total, player) => total + (player.predicted_points ?? 0),
    0,
  );
  const optimalSquadProjection = decision?.optimal_squad?.projected_points;
  const squadRating = typeof currentSquadProjection === "number"
    && typeof optimalSquadProjection === "number"
    && optimalSquadProjection > 0
    ? Math.max(0, Math.min(100, Math.round((currentSquadProjection / optimalSquadProjection) * 100)))
    : null;
  const freeTransfers = decision?.transfers?.free_transfers;
  const readiness = health?.status
    ? health.status.charAt(0) + health.status.slice(1).toLowerCase()
    : "Analysis pending";
  const goalCopy = seasonGoalCopy(seasonGoal);

  return (
    <div className="cockpit">
      <header className="cockpit-heading">
        <div><span className="eyebrow">GAMEWEEK {team.event ?? "—"} INTELLIGENCE</span><h1>{team.name}</h1>{team.manager_name ? <span className="cockpit-manager">Managed by {team.manager_name}</span> : null}<p>One clear view of what is happening now and what gives you the best edge next.</p></div>
        <button className="refresh-button" type="button" onClick={() => void refresh()} disabled={loading}><RefreshCw size={15} aria-hidden="true" />{loading ? "Refreshing" : "Refresh data"}</button>
      </header>

      {error ? <DataState title="Latest refresh failed" tone="warning">Showing the last successful dashboard. {error}</DataState> : null}

      <section className="cockpit-kpis" aria-label="Team summary">
        <article><span><i className={`source-pill ${liveSourceClass}`}>{liveSourceLabel}</i>Gameweek points</span><strong>{liveSummary?.live_points ?? liveScore ?? team.event_points ?? "—"}</strong><small>{liveSummary ? `${liveSummary.players_finished} finished · ${liveSummary.players_live} live · ${liveSummary.players_remaining} to play` : dashboard.data.live?.status ?? "Official FPL"}</small></article>
        <article><span><i className="source-pill source-model">Model</i>Next projection</span><strong>{points(decision?.starting_xi?.projected_points)}</strong><small>{decision?.starting_xi?.formation ?? "Model unavailable"}</small></article>
        <article><span><i className="source-pill source-derived">Derived</i>Squad rating</span><strong>{squadRating ?? "—"}</strong><small>Current 15 vs model-optimal 15</small></article>
        <article><span><i className={`source-pill ${officialSourceClass}`}>{officialSourceLabel}</i>Overall rank</span><strong>{compactNumber(team.overall_rank)}</strong><small>{team.total_points == null ? "Current season" : `${team.total_points} total points`}</small></article>
        <article><span><i className="source-pill source-derived">Derived</i>Squad value</span><strong>{team.value == null ? "—" : `£${team.value.toFixed(1)}m`}</strong><small>{team.bank == null ? "Bank unavailable" : `£${team.bank.toFixed(1)}m in bank`}</small></article>
        <article><span><i className={`source-pill ${officialSourceClass}`}>{officialSourceLabel}</i>Free transfers</span><strong>{freeTransfers ?? "—"}</strong><small>{freeTransfers == null ? "Transfer state unavailable" : `${freeTransfers} available for the target GW`}</small></article>
      </section>

      <section className="rank-trend-wrap" aria-label="Season momentum">
        <RankTrend history={dashboard.data.history?.history ?? []} currentRank={team.overall_rank} />
        <article className="live-kpi readiness-kpi">
          <span><i className="source-pill source-model">Model</i> SQUAD READINESS</span>
          <strong>{readiness}</strong>
          <small>{health ? `${Math.round(health.average_xmins)} avg xMins` : "Risk model unavailable"}</small>
          {health ? <small>{health.unavailable_count} unavailable · {health.high_risk_count} high risk</small> : null}
          <Link href="/team">Inspect player evidence <ArrowRight size={12} /></Link>
        </article>
      </section>

      <section className="cockpit-primary-grid">
        <article className="premium-card decision-card">
          <header><div><span className={`source-pill ${liveMode ? liveSourceClass : "source-model"}`}>{liveMode ? liveSourceLabel : "Model"}</span><h2>{liveMode ? "Gameweek status" : "Best next move"}</h2></div><Sparkles aria-hidden="true" /></header>
          {liveMode ? <div className="decision-body">
            <span className="decision-kicker">LIVE MODE</span>
            <strong>{actionsLocked ? "Gameweek locked" : `${liveSummary?.live_points ?? liveScore ?? team.event_points ?? "—"} live points`}</strong>
            <p>{liveSummary ? `${liveSummary.players_finished} players finished, ${liveSummary.players_live} currently live and ${liveSummary.players_remaining} still to play. Captain contribution: ${liveSummary.captain_contribution} points.` : "Follow the official score and individual player output while matches are active."}</p>
            {!actionsLocked && planTitle ? <div className="decision-next-plan"><span>Next deadline plan</span><strong>{planTitle}</strong><Link href="/plan">Review plan <ArrowRight size={13} aria-hidden="true" /></Link></div> : null}
            <Link className="primary" href="/team">Follow live team<ArrowRight size={15} aria-hidden="true" /></Link>
          </div> : recommendationTitle ? <div className="decision-body"><span className="decision-kicker">FPL AI RECOMMENDATION</span><strong>{recommendationTitle}</strong><p>{actionsLocked ? "The target deadline has passed, so transfer actions are hidden." : transfer ? "The strongest available transfer after budget, hit cost and expected points." : "The current squad projects better than forcing a marginal move."}</p>{!actionsLocked ? <div className="decision-gain"><span>Net expected gain</span><b>{netGain == null ? "—" : `${netGain >= 0 ? "+" : ""}${netGain.toFixed(1)} pts`}</b></div> : null}<Link className="primary" href="/plan">Review the full plan<ArrowRight size={15} aria-hidden="true" /></Link></div> : <DataState title="Model analysis is unavailable" tone="warning">Official team and live data remain current. Try refreshing before the deadline.</DataState>}
        </article>
        <article className="premium-card squad-card"><header><div><span className={`source-pill ${liveMode ? liveSourceClass : "source-model"}`}>{liveMode ? liveSourceLabel : "Model"}</span><h2>Current XI</h2></div><Link href="/team">Open team</Link></header><CompactSquad picks={team.picks} livePicks={dashboard.data.live?.picks} liveMode={liveMode} /></article>
      </section>

      <section className="cockpit-secondary-grid">
        <article className="premium-card"><header><div><CalendarDays size={16} aria-hidden="true" /><h2>{liveMode && liveFixtures.length ? "Live fixtures" : "Next fixtures"}</h2></div><span className={`source-pill ${liveMode && liveFixtures.length ? liveSourceClass : officialSourceClass}`}>{liveMode && liveFixtures.length ? liveSourceLabel : officialSourceLabel}</span></header>{liveMode && liveFixtures.length ? <div className="fixture-stack">{liveFixtures.slice(0, 5).map((fixture) => <div key={fixture.fixture_id}><b>GW{dashboard.data.live?.current_event}</b><strong><b>{fixture.home_team} {fixture.home_score ?? "–"}</b><span>vs</span><b>{fixture.away_team} {fixture.away_score ?? "–"}</b></strong><small>{fixture.finished ? "FT" : fixture.started ? `${fixture.minutes}′ · LIVE` : fixture.kickoff_time ? new Date(fixture.kickoff_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "TBC"}</small></div>)}</div> : <div className="fixture-stack">{fixtures.slice(0, 5).map((fixture) => <div key={fixture.fixture_id}><b>GW{fixture.event}</b><strong>{fixture.home_team ?? fixture.team} <span>vs</span> {fixture.away_team ?? fixture.opponent}</strong><small>{fixture.kickoff_time ? new Date(fixture.kickoff_time).toLocaleDateString([], { day: "numeric", month: "short" }) : "TBC"}</small></div>)}{fixtures.length === 0 ? <p>Fixture data is unavailable.</p> : null}</div>}</article>
        <article className="premium-card"><header><div><Crown size={16} aria-hidden="true" /><h2>Captain shortlist</h2></div><span className="source-pill source-model">Model</span></header><div className="captain-stack">{captains.map((captain, index) => captain ? <div key={captain.player_id}><span>{index === 0 ? "C" : "VC"}</span><strong>{captain.name}<small>{captain.team ?? "—"}</small></strong><b>{points(captain.predicted_points)}</b></div> : null)}{captains.length === 0 ? <p>Captain model unavailable.</p> : null}</div></article>
        <article className="premium-card edge-card"><header><div><Trophy size={16} aria-hidden="true" /><h2>{goalCopy.title}</h2></div></header><div><ShieldAlert aria-hidden="true" /><strong>{goalCopy.headline}</strong><p>{goalCopy.description}</p><Link href="/review">Open post-GW review <ArrowRight size={12} /></Link></div></article>
      </section>
      {liveMode ? <article className="premium-card team-events-card" role="region" aria-label="Owned team events">
        <header><div><Trophy size={16} aria-hidden="true" /><h2>Owned team events</h2></div><span className={`source-pill ${liveSourceClass}`}>{liveSourceLabel}</span></header>
        <p className="team-events-note">Official aggregate, not an event timeline.</p>
        <div className="team-event-list">
          {liveEvents.length ? liveEvents.slice(0, 8).map((event) => <div className={`team-event team-event-${event.event_type.toLowerCase()}`} key={`${event.player_id}-${event.event_type}`}>
            <span>{event.active ? "XI" : "Bench"}</span>
            <strong>{event.player_name}<small>{event.team_short}</small></strong>
            <b>{eventLabel(event)}</b>
            {event.provisional ? <em>Provisional</em> : null}
          </div>) : <p>No official owned-player returns yet.</p>}
        </div>
      </article> : null}
      <article className="premium-card market-watch-card" role="region" aria-label="Form and action watch">
        <header><div><TrendingUp size={16} aria-hidden="true" /><h2>Form and action watch</h2></div><div><span className={`source-pill ${stale ? "source-derived" : liveMode ? "source-live" : "source-official"}`}>{stale ? "Cached GW" : "Actual GW"}</span><span className={`source-pill ${officialSourceClass}`}>{stale ? "Cached form" : "Official form"}</span><span className="source-pill source-derived">Plan evidence</span></div></header>
        <div className="market-watch-body">
          <section><span>{liveMode ? "LIVE LEADERS" : "GW LEADERS"}</span>{liveLeaders.length ? liveLeaders.map((player) => <div key={player.player_id}><strong>{player.name}<small>{player.team_short} · {player.position}</small></strong><b>{player.event_points} pts</b><em>{player.minutes == null ? "Minutes —" : `${player.minutes} min`}</em></div>) : <p>Actual Gameweek output is unavailable.</p>}</section>
          <section><span>FORM WATCH</span>{formWatch.length ? formWatch.map((player) => <div key={player.player_id}><strong>{player.name}<small>{player.team_short}</small></strong><b>{player.form?.toFixed(1)} form</b><em>{player.ownership == null ? "Ownership —" : `${player.ownership.toFixed(1)}% owned`}</em></div>) : <p>Official form data is unavailable.</p>}</section>
          <section><span><Lightbulb size={12} aria-hidden="true" /> ACTION RADAR</span>{actionInsights.length ? actionInsights.map((insight) => <div key={`${insight.type}-${insight.reason}`}><strong>{insight.type.replaceAll("_", " ").toLowerCase()}</strong><p>{insight.reason}</p><em>{insight.severity.toLowerCase()}</em></div>) : <p>No model action signal is available. Official data remains current.</p>}<Link href="/plan">Open full evidence <ArrowRight size={12} /></Link></section>
        </div>
      </article>
    </div>
  );
}
