"use client";

import { ArrowDownRight, ArrowRight, ArrowUpRight, BrainCircuit, Crown, History, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { DataState } from "@/components/states/DataState";
import { fetchReview } from "@/lib/api";
import type { ReviewEnvelope } from "@/lib/contracts";


function signed(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(1)}`;
}


function outcomeLabel(outcome: string) {
  return {
    ABOVE_EXPECTATION: "Above expectation",
    IN_LINE: "In line",
    BELOW_EXPECTATION: "Below expectation",
  }[outcome] ?? outcome.replaceAll("_", " ").toLowerCase();
}


function outcomeClass(outcome: string) {
  if (outcome === "ABOVE_EXPECTATION") return "review-positive";
  if (outcome === "BELOW_EXPECTATION") return "review-negative";
  return "review-neutral";
}


function decisionQualityLabel(label: string) {
  return {
    SOUND: "Sound process",
    MARGINAL: "Marginal process",
    QUESTIONABLE: "Review process",
  }[label] ?? "Review process";
}


function decisionSigned(value: number) {
  return value >= 0 ? `+${value.toFixed(1)}` : `−${Math.abs(value).toFixed(1)}`;
}


export function PostGameweekReview({ teamId, event }: { teamId: string; event?: number }) {
  const [review, setReview] = useState<ReviewEnvelope | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    queueMicrotask(() => {
      if (controller.signal.aborted) return;
      setLoading(true);
      setError(null);
      void fetchReview(teamId, event, controller.signal)
        .then(setReview)
        .catch((caught) => {
          if (!controller.signal.aborted) {
            setError(caught instanceof Error ? caught.message : "Could not load the review");
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    });
    return () => controller.abort();
  }, [event, teamId]);

  if (loading) {
    return <DataState title="Building your GW review" loading>Matching official outcomes with the stored pre-deadline model artifact…</DataState>;
  }
  if (error) {
    return <DataState title="Review could not be loaded" tone="error">{error}</DataState>;
  }
  if (!review) return null;
  const staleNotice = review.meta.stale
    ? <DataState title="Review uses cached official data" tone="warning">The stored model artifact is unchanged, but official outcome data may be older than the latest FPL response.</DataState>
    : null;
  if (!review.data.available) {
    return (
      <div className="review-workspace">
        {staleNotice}
        <section className="premium-card review-unavailable">
          <History aria-hidden="true" />
          <div><h2>GW{review.data.event} review is unavailable</h2><p>{review.data.reason}</p><small>FPL AI never reconstructs a model opinion that was not saved before the Gameweek.</small></div>
        </section>
      </div>
    );
  }

  const data = review.data;
  const deltaIcon = data.summary.actual_vs_projected >= 0
    ? <ArrowUpRight aria-hidden="true" />
    : <ArrowDownRight aria-hidden="true" />;

  return (
    <div className="review-workspace">
      {staleNotice}
      <section id="statistics" className="premium-card review-hero">
        <header>
          <div><span className="source-pill source-derived">Derived</span><h2>GW{data.event} review</h2></div>
          <span className={`review-outcome ${outcomeClass(data.summary.outcome)}`}>{outcomeLabel(data.summary.outcome)}</span>
        </header>
        <div className="review-scoreline">
          <div><small>MODEL PROJECTED</small><strong>{data.summary.projected_points.toFixed(1)}</strong></div>
          <ArrowRight aria-hidden="true" />
          <div><small>OFFICIAL POINTS</small><strong>{data.summary.official_points}</strong></div>
          <div className={outcomeClass(data.summary.outcome)}>{deltaIcon}<span><small>VERSUS MODEL</small><strong>{signed(data.summary.actual_vs_projected)}</strong></span></div>
        </div>
        <footer><span>Transfer cost: {data.summary.hit_cost} pts</span><span>Net after hits: {data.summary.net_points_after_hits} pts</span></footer>
      </section>

      <section className="review-detail-grid">
        <article className="premium-card review-detail">
          <header><div><Crown aria-hidden="true" /><h3>Captain outcome</h3></div><span className="source-pill source-official">Official</span></header>
          {data.captain ? <div className="review-player-call"><strong>{data.captain.name}</strong><span>{data.captain.multiplier}× multiplier</span><dl><div><dt>Projected contribution</dt><dd>{data.captain.projected_contribution.toFixed(1)}</dd></div><div><dt>Actual contribution</dt><dd>{data.captain.actual_contribution}</dd></div><div><dt>Delta</dt><dd>{signed(data.captain.contribution_delta)}</dd></div></dl></div> : <p className="review-empty">Captain history was not available.</p>}
        </article>

        <article className="premium-card review-detail">
          <header><div><ArrowRight aria-hidden="true" /><h3>Transfer outcome</h3></div><span className="source-pill source-derived">Derived</span></header>
          {data.transfers.length ? <div className="review-transfer-list">{data.transfers.map((transfer) => <div key={`${transfer.player_out.player_id}-${transfer.player_in.player_id}`}><strong>{transfer.player_out.name} → {transfer.player_in.name}</strong><span>Model delta <b>{signed(transfer.projected_delta)}</b></span><span>Actual delta <b>{signed(transfer.actual_delta)}</b></span></div>)}</div> : <p className="review-empty">No transfers were made in this Gameweek.</p>}
        </article>

        <article className="premium-card review-detail">
          <header><div><BrainCircuit aria-hidden="true" /><h3>Largest overprediction</h3></div><span className="source-pill source-model">Model</span></header>
          <div className="review-player-call"><strong>{data.largest_model_miss.name}</strong><span>The player whose actual points fell furthest below the model projection.</span><dl><div><dt>Projected</dt><dd>{data.largest_model_miss.predicted_points.toFixed(1)}</dd></div><div><dt>Actual</dt><dd>{data.largest_model_miss.actual_points}</dd></div><div><dt>Residual</dt><dd>{signed(data.largest_model_miss.residual)}</dd></div></dl></div>
        </article>

        <article className="premium-card review-detail">
          <header><div><ShieldCheck aria-hidden="true" /><h3>Bench audit</h3></div><span className="source-pill source-official">Official</span></header>
          <div className="review-player-call"><strong>{data.bench.official_points} points benched</strong><span>{data.bench.player_count} bench players · {data.bench.projected_points.toFixed(1)} model xPts</span><p>Bench points are reported from the official manager history, with the model figure kept separate.</p></div>
        </article>

        <article className="premium-card review-detail">
          <header><div><ShieldCheck aria-hidden="true" /><h3>Decision quality</h3></div><span className="source-pill source-model">Pre-deadline</span></header>
          <div className="review-player-call review-decision-quality">
            <strong>{decisionQualityLabel(data.decision_quality.label)}</strong>
            <span>{decisionSigned(data.decision_quality.projected_decision_value)} projected decision EV</span>
            <p>This process rating uses only the certified pre-deadline projection and official transfer cost. Actual points do not change this rating.</p>
            <dl><div><dt>Transfer EV</dt><dd>{decisionSigned(data.decision_quality.projected_transfer_value)}</dd></div><div><dt>Captain cost</dt><dd>{decisionSigned(-data.decision_quality.captain_opportunity_cost)}</dd></div><div><dt>Evidence</dt><dd>Pre-GW</dd></div></dl>
          </div>
        </article>

        <article className="premium-card review-detail">
          <header><div><History aria-hidden="true" /><h3>Largest xMins miss</h3></div><span className="source-pill source-derived">Model vs official</span></header>
          {data.largest_xmins_miss ? <div className="review-player-call"><strong>{data.largest_xmins_miss.name}</strong><span>Largest absolute difference between the certified minutes forecast and official minutes played.</span><dl><div><dt>Forecast</dt><dd>{data.largest_xmins_miss.predicted_xmins.toFixed(0)} xMins</dd></div><div><dt>Played</dt><dd>{data.largest_xmins_miss.actual_minutes} official minutes</dd></div><div><dt>Residual</dt><dd>{decisionSigned(data.largest_xmins_miss.residual)}</dd></div></dl></div> : <div className="review-player-call"><strong>xMins unavailable</strong><span>This certified artifact predates the minutes field, so FPL AI will not reconstruct an xMins opinion after the deadline.</span></div>}
        </article>
      </section>

      <section className="premium-card review-next" aria-label="Next Gameweek signals">
        <header><div><BrainCircuit aria-hidden="true" /><h3>Next Gameweek signals</h3></div><span className="source-pill source-derived">Evidence-backed</span></header>
        <div>{data.next_signals.length ? data.next_signals.map((signal) => <article key={signal.type}><span>{signal.severity}</span><strong>{signal.title}</strong><p>{signal.message}</p></article>) : <p className="review-empty">No material process signal cleared the evidence threshold. Refresh the live plan before the next deadline.</p>}</div>
        <footer><Link href="/plan">Open the next Gameweek plan<ArrowRight size={14} aria-hidden="true" /></Link></footer>
      </section>

      <aside className="review-methodology"><ShieldCheck aria-hidden="true" /><p><strong>Evidence, not hindsight.</strong> Official picks and points are compared with <b>{data.prediction_version}</b>. No retrospective narrative or regenerated prediction is used.</p></aside>
    </div>
  );
}
