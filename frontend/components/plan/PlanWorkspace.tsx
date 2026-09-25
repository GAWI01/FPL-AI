"use client";

import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Crown,
  Gauge,
  GitCompareArrows,
  Lightbulb,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { useTeam } from "@/app/providers/TeamProvider";
import { DataState } from "@/components/states/DataState";
import { PlanHistoryPanel } from "@/components/plan/PlanHistoryPanel";
import type { DecisionPlayer, RecommendedTransfer, TransferScenario } from "@/lib/contracts";


type ScenarioOption = {
  id: string;
  label: string;
  ariaLabel: string;
  selectionLabel: string;
  scenario: TransferScenario;
  hitCost: number | null;
};


const number = (value?: number | null, digits = 1) =>
  typeof value === "number" ? value.toFixed(digits) : "—";

const signed = (value?: number | null) =>
  typeof value === "number" ? `${value > 0 ? "+" : ""}${value.toFixed(1)}` : "—";

const sentenceCase = (value?: string | null) => value
  ? value.charAt(0).toUpperCase() + value.slice(1).toLowerCase().replaceAll("_", " ")
  : "Unavailable";

const transferLabel = (transfers?: RecommendedTransfer[]) => {
  if (!transfers?.length) return "Hold the transfer";
  return transfers.map((item) => `${item.player_out ?? `Player ${item.player_out_id}`} → ${item.player_in ?? `Player ${item.player_in_id}`}`).join(" · ");
};

const chipName = (value?: string | null) => value ? sentenceCase(value) : "Hold chips";


export function PlanWorkspace() {
  const { dashboard, loading, error } = useTeam();
  const [selectedScenario, setSelectedScenario] = useState(0);
  const [selectedCaptainId, setSelectedCaptainId] = useState<number | null>(null);

  if (!dashboard) {
    return (
      <DataState title={loading ? "Loading your plan…" : "Connect your team to build a plan"} tone={error ? "error" : "neutral"} loading={loading}>
        {error}
      </DataState>
    );
  }

  const decision = dashboard.data.decision;
  const transfer = decision?.transfers?.recommended_transfers?.[0]
    ?? decision?.transfers?.recommended
    ?? null;
  const netGain = decision?.transfers?.net_gain ?? null;
  const hitCost = decision?.transfers?.hit_cost ?? 0;
  const shouldHold = typeof netGain === "number" && netGain <= 0;
  const gameweekLocked = dashboard.meta.actions_locked ?? true;
  const predictionEvent = dashboard.meta.prediction_event
    ?? dashboard.data.team.prediction_event
    ?? dashboard.meta.event;
  const intelligence = decision?.intelligence;
  const confidence = intelligence?.confidence;
  const strategy = intelligence?.transfer_strategy;
  const recommendedScenario: TransferScenario = {
    transfers: strategy?.selected_transfers?.length
      ? strategy.selected_transfers
      : transfer ? [transfer] : [],
    current_net_gain: strategy?.current_net_gain ?? netGain ?? 0,
    horizon_gain: strategy?.horizon_gain ?? 0,
    combined_score: strategy?.combined_score ?? netGain ?? 0,
    coverage: strategy?.coverage ?? 0,
  };
  const freeTransfers = decision?.transfers?.free_transfers;
  const rollScenario: TransferScenario = {
    transfers: [],
    current_net_gain: 0,
    horizon_gain: 0,
    combined_score: 0,
    coverage: strategy?.coverage ?? 0,
  };
  const scenarioOptions: ScenarioOption[] = [
    {
      id: "recommended",
      label: recommendedScenario.transfers.length ? "Recommended" : "Recommended HOLD",
      ariaLabel: "Compare recommended plan",
      selectionLabel: "Recommended plan selected",
      scenario: recommendedScenario,
      hitCost: decision?.transfers?.hit_cost ?? null,
    },
    ...(recommendedScenario.transfers.length ? [{
      id: "roll",
      label: "Roll / HOLD",
      ariaLabel: "Compare roll transfer",
      selectionLabel: "Roll transfer selected",
      scenario: rollScenario,
      hitCost: 0,
    }] : []),
    ...(strategy?.alternatives ?? []).map((scenario, index) => ({
      id: `alternative-${index + 1}`,
      label: `Alternative ${index + 1}`,
      ariaLabel: `Compare alternative ${index + 1}`,
      selectionLabel: `Alternative ${index + 1} selected`,
      scenario,
      hitCost: typeof freeTransfers === "number"
        ? Math.max(0, scenario.transfers.length - freeTransfers) * 4
        : null,
    })),
  ];
  const activeOption = scenarioOptions[Math.min(selectedScenario, Math.max(0, scenarioOptions.length - 1))];
  const activeScenario = activeOption?.scenario;
  const ownedIds = new Set(dashboard.data.team.picks.map((pick) => pick.player_id));
  const captainById = new Map<number, DecisionPlayer>();
  for (const candidate of [
    decision?.captain,
    decision?.vice_captain,
    ...(intelligence?.captain_decision.alternatives ?? []),
  ]) {
    if (candidate?.player_id != null && ownedIds.has(candidate.player_id)) {
      captainById.set(candidate.player_id, candidate);
    }
  }
  const captainCandidates = [...captainById.values()];
  const activeCaptain = captainCandidates.find((candidate) => candidate.player_id === selectedCaptainId)
    ?? captainCandidates.find((candidate) => candidate.player_id === decision?.captain?.player_id)
    ?? captainCandidates[0];
  const captainDelta = typeof activeCaptain?.predicted_points === "number"
    && typeof decision?.captain?.predicted_points === "number"
    ? activeCaptain.predicted_points - decision.captain.predicted_points
    : null;
  const captainHorizon = (
    activeCaptain?.player_id === decision?.captain?.player_id
      ? intelligence?.horizon.captain_projection
      : undefined
  ) ?? intelligence?.horizon.team_player_projections.find(
    (player) => player.player_id === activeCaptain?.player_id,
  ) ?? intelligence?.horizon.captain_projection;
  const chipState = intelligence?.chip_state;
  const health = intelligence?.squad_health;

  return (
    <section className="workspace-page">
      <div className="workspace-heading">
        <div>
          <span className="eyebrow">GAMEWEEK {predictionEvent ?? "—"} DECISION ROOM</span>
          <h1>Plan the move, not just the squad.</h1>
          <p>One clear recommendation, with the points math and uncertainty exposed.</p>
        </div>
        <div className="heading-pills"><span className="source-pill source-model">Model</span>{confidence ? <span className={`confidence-pill confidence-${confidence.label.toLowerCase()}`}>{sentenceCase(confidence.label)} confidence</span> : null}</div>
      </div>

      {decision ? (
        <div className="plan-grid">
          <article id="transfer-center" className="premium-card plan-primary">
            <header><div><Sparkles size={16} aria-hidden="true" /><h2>Gameweek call</h2></div><span className="source-pill source-derived">Derived</span></header>
            <div className="plan-call">
              <span className={shouldHold || gameweekLocked ? "plan-icon hold" : "plan-icon"}><ArrowRight aria-hidden="true" /></span>
              <div>
                <small>{gameweekLocked ? "LIVE MODE" : "RECOMMENDATION"}</small>
                <h3>{gameweekLocked ? "Gameweek locked" : shouldHold ? "Hold the transfer" : transfer ? `${transfer.player_out} → ${transfer.player_in}` : "Hold the transfer"}</h3>
                <p>{gameweekLocked
                  ? "The deadline has passed. Transfers are no longer actionable, so FPL AI is monitoring live performance instead."
                  : shouldHold
                  ? "The projected gain does not cover the cost. Preserve flexibility for the next deadline."
                  : "The model expects this move to improve your starting XI after transfer costs."}</p>
              </div>
            </div>
            {gameweekLocked ? <div className="plan-locked-note"><ShieldCheck size={16} aria-hidden="true" /><p><strong>Read-only target.</strong> Transfer calculations are hidden until a new actionable deadline plan is available.</p></div> : <div className="plan-math">
              <div><span>Gross gain</span><strong>+{number(decision.transfers?.gross_gain ?? transfer?.gain)} xPts</strong></div>
              <div><span>Transfer cost</span><strong>{hitCost ? `−${hitCost} hit` : "Free"}</strong></div>
              <div><span>Net decision</span><strong className={shouldHold ? "negative" : "positive"}>{typeof netGain === "number" && netGain > 0 ? "+" : ""}{number(netGain)} net xPts</strong></div>
            </div>}
          </article>

          <article id="ai-recommendations" className="premium-card captain-card">
            <header><div><Crown size={16} aria-hidden="true" /><h2>Armband</h2></div><span className="source-pill source-model">Model</span></header>
            <div className="captain-choice"><span>C</span><div><strong>{decision.captain?.name ?? "Unavailable"}</strong><small>{decision.captain?.team ?? "Captain model"}</small></div><b>{number(decision.captain?.predicted_points)} xPts</b></div>
            <div className="captain-choice vice"><span>VC</span><div><strong>{decision.vice_captain?.name ?? "Unavailable"}</strong><small>{decision.vice_captain?.team ?? "Vice-captain model"}</small></div><b>{number(decision.vice_captain?.predicted_points)} xPts</b></div>
          </article>

          <article className="premium-card honesty-card">
            <header><div><Gauge size={16} aria-hidden="true" /><h2>{intelligence ? "Decision confidence" : "Decision limits"}</h2></div><span className="source-pill source-official">Transparent</span></header>
            <div className="honesty-note"><AlertTriangle size={18} aria-hidden="true" /><p>{intelligence ? <><strong>{Math.round((intelligence.horizon.coverage ?? 0) * 100)}% horizon coverage.</strong> GW+2 to GW+5 use fixture-scaled model estimates with wider uncertainty than the native next-GW prediction. Chip recommendations need clear multi-week evidence before FPL AI advises using one.</> : <><strong>One-gameweek horizon.</strong> Chip recommendations need multi-week projections and are intentionally unavailable until that model is live.</>}</p></div>
            <div className="confidence-row"><span>Free transfers supplied</span><b>{decision.transfers?.free_transfers ?? "—"}</b></div>
            <div className="confidence-row"><span>Transfers in plan</span><b>{decision.transfers?.transfers_used ?? (transfer ? 1 : 0)}</b></div>
            {confidence ? <div className="confidence-row"><span>Model confidence</span><b>{Math.round(confidence.score * 100)}% · {sentenceCase(confidence.label)}</b></div> : null}
          </article>

          {!gameweekLocked && intelligence && activeScenario ? <article className="premium-card plan-wide scenario-lab">
            <header><div><GitCompareArrows size={16} aria-hidden="true" /><h2>What-if simulator</h2></div><span className="source-pill source-derived">Local only</span></header>
            <div className="scenario-tabs" role="group" aria-label="Transfer scenarios">
              {scenarioOptions.map((option, index) => <button type="button" key={option.id} aria-pressed={selectedScenario === index} aria-label={option.ariaLabel} onClick={() => setSelectedScenario(index)}>{option.label}</button>)}
            </div>
            <div className="scenario-result">
              <div><small>{activeOption.selectionLabel}</small><strong>Scenario: {transferLabel(activeScenario.transfers)}</strong><p>Compare current-Gameweek value and the fixture-scaled five-Gameweek effect. Nothing here changes your official FPL team.</p></div>
              <div className="scenario-metrics"><span><small>Next GW</small><b>{signed(activeScenario.current_net_gain)} xPts</b></span><span><small>Future horizon</small><b>{signed(activeScenario.horizon_gain)} xPts</b></span><span><small>Hit cost</small><b>{activeOption.hitCost == null ? "Unknown" : activeOption.hitCost > 0 ? `−${activeOption.hitCost} pts` : "No hit"}</b></span><span><small>Decision score</small><b>{signed(activeScenario.combined_score)} combined</b></span><span><small>Coverage</small><b>{Math.round(activeScenario.coverage * 100)}%</b></span></div>
            </div>
            {captainCandidates.length ? <div className="captain-simulator"><div><span>CAPTAIN WHAT-IF</span><strong>{activeCaptain?.player_id === decision.captain?.player_id ? "Model captain selected" : `${activeCaptain?.name} selected locally`}</strong><small>{captainDelta == null ? "Captain delta unavailable" : `${captainDelta < 0 ? "−" : captainDelta > 0 ? "+" : ""}${Math.abs(captainDelta).toFixed(1)} captain xPts`}</small></div><div role="group" aria-label="Captain scenarios">{captainCandidates.map((candidate) => <button type="button" key={candidate.player_id} aria-pressed={candidate.player_id === activeCaptain?.player_id} aria-label={`Try ${candidate.name} as captain`} onClick={() => setSelectedCaptainId(candidate.player_id)}>{candidate.name}<small>{number(candidate.predicted_points)} xPts</small></button>)}</div><Link href="/team">Open lineup and bench simulator <ArrowRight size={12} aria-hidden="true" /></Link></div> : null}
          </article> : null}

          {intelligence ? <article className="premium-card plan-wide horizon-card">
            <header><div><Activity size={16} aria-hidden="true" /><h2>{intelligence.horizon.horizon}-GW outlook</h2></div><span className="source-pill source-model">Model + fixtures</span></header>
            <div className="horizon-summary"><div><span>Squad horizon</span><strong>{number(intelligence.horizon.team_projected_points)} xPts</strong></div><p>First week is the native model. Later weeks are scaled by official home/away fixtures and FDR; uncertainty expands with distance.</p></div>
            <div className="horizon-strip">{captainHorizon?.gameweeks.map((gameweek) => <div key={`${gameweek.gameweek}-${gameweek.opponent}`}><span>GW{gameweek.gameweek}</span><strong>{number(gameweek.predicted_points)}<small> ±{number(gameweek.uncertainty)}</small></strong><b>{gameweek.opponent ?? "TBC"}</b><em>{gameweek.projection_method === "native_model" ? "Native" : gameweek.fixture_count === 0 ? "Blank" : "Scaled"}</em></div>) ?? <p>Player-level horizon unavailable.</p>}</div>
          </article> : null}

          {intelligence ? <article id="chip-advisor" className="premium-card chip-card">
            <header><div><Zap size={16} aria-hidden="true" /><h2>Chip decision</h2></div><span className="source-pill source-official">Official state</span></header>
            <div className="chip-call"><span>{gameweekLocked ? "LOCKED" : intelligence.chip_advisor.recommended_chip ? "OPPORTUNITY" : "CONSERVATIVE"}</span><strong>{gameweekLocked ? "Gameweek locked" : chipName(intelligence.chip_advisor.recommended_chip)}</strong><p>{gameweekLocked ? "Chip actions are locked for this target Gameweek. Availability remains visible for planning the next deadline." : intelligence.chip_advisor.recommended_chip ? `The ${chipName(intelligence.chip_advisor.recommended_chip)} scenario clears the current decision threshold.` : "No available chip clears the evidence threshold. Preserve optionality."}</p></div>
            <div className="chip-grid">{[
              ["Wildcard", chipState?.wildcard_available],
              ["Free Hit", chipState?.free_hit_available],
              ["Bench Boost", chipState?.bench_boost_available],
              ["Triple Captain", chipState?.triple_captain_available],
            ].map(([label, available]) => <span key={String(label)} className={available ? "available" : "used"}><ShieldCheck size={13} />{label}<b>{chipState?.known ? available ? "Ready" : "Used" : "Unknown"}</b></span>)}</div>
          </article> : null}

          {intelligence ? <article className="premium-card health-card">
            <header><div><ShieldCheck size={16} aria-hidden="true" /><h2>Squad health</h2></div><span className={`health-status health-${(health?.status ?? "unknown").toLowerCase()}`}>{sentenceCase(health?.status)}</span></header>
            <div className="health-score"><strong>{number(health?.average_xmins, 0)}<small>avg xMins</small></strong><div><span><b>{health?.unavailable_count ?? 0}</b> unavailable</span><span><b>{health?.high_risk_count ?? 0}</b> high risk</span></div></div>
          </article> : null}

          {intelligence?.insights?.length ? <article className="premium-card plan-wide insights-card">
            <header><div><Lightbulb size={16} aria-hidden="true" /><h2>Why this plan</h2></div><span className="source-pill source-derived">Evidence-backed</span></header>
            <div>{intelligence.insights.slice(0, 3).map((insight) => <section key={`${insight.type}-${insight.reason}`}><span>{sentenceCase(insight.type)}</span><p>{insight.reason}</p><b>{sentenceCase(insight.severity)}</b></section>)}</div>
          </article> : null}

          {!gameweekLocked ? <PlanHistoryPanel snapshot={{
            event: predictionEvent ?? 0,
            action: shouldHold ? "Hold the transfer" : transfer ? `${transfer.player_out} → ${transfer.player_in}` : "Hold the transfer",
            captain: decision.captain?.name ?? "Unavailable",
            netGain,
            confidenceScore: confidence?.score ?? null,
            confidenceLabel: confidence?.label ?? null,
            modelVersion: dashboard.meta.prediction_version ?? dashboard.data.team.prediction_file ?? null,
            recordedAt: dashboard.meta.generated_at,
          }} /> : null}
        </div>
      ) : <DataState title="Plan unavailable" tone="warning">Model analysis is unavailable. Official team data remains safe.</DataState>}
    </section>
  );
}
