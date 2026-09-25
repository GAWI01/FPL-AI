"use client";

import { History } from "lucide-react";
import { useEffect, useState } from "react";

import { recordPlanSnapshot, type PlanSnapshot } from "@/lib/planHistory";


export function PlanHistoryPanel({ snapshot }: { snapshot: PlanSnapshot }) {
  const [history, setHistory] = useState<PlanSnapshot[]>([]);

  useEffect(() => {
    let cancelled = false;
    queueMicrotask(() => {
      if (!cancelled) setHistory(recordPlanSnapshot(window.localStorage, snapshot));
    });
    return () => { cancelled = true; };
  }, [snapshot]);

  const current = history[0];
  const previous = history[1]?.event === current?.event ? history[1] : null;
  const reasons = previous && current ? [
    previous.action !== current.action ? "Transfer/HOLD recommendation changed" : null,
    previous.captain !== current.captain ? "Captaincy recommendation changed" : null,
    typeof previous.netGain === "number" && typeof current.netGain === "number" && Math.abs(previous.netGain - current.netGain) >= 0.5
      ? `Expected edge moved by ${Math.abs(previous.netGain - current.netGain).toFixed(1)} points`
      : null,
    previous.confidenceLabel !== current.confidenceLabel
      || (typeof previous.confidenceScore === "number" && typeof current.confidenceScore === "number" && Math.abs(previous.confidenceScore - current.confidenceScore) >= 0.05)
      ? "Decision uncertainty changed"
      : null,
  ].filter((reason): reason is string => Boolean(reason)) : [];

  return (
    <article className="premium-card plan-wide plan-history-card" role="region" aria-label="Local plan history">
      <header><div><History size={16} aria-hidden="true" /><h2>Plan history</h2></div><span className="source-pill source-derived">This browser</span></header>
      {previous && current && reasons.length ? <div className="plan-change-callout" role="status" aria-label="Plan changed">
        <div><span>PLAN CHANGED</span><time dateTime={current.recordedAt}>{new Date(current.recordedAt).toLocaleString([], { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</time></div>
        <strong>{previous.action}<b>→</b>{current.action}</strong>
        <p>{reasons.join(" · ")}</p>
        <small>Updated uncertainty: {typeof current.confidenceScore === "number" ? `${Math.round(current.confidenceScore * 100)}%` : "—"} {current.confidenceLabel?.toLowerCase() ?? "unavailable"}</small>
      </div> : null}
      <div className="plan-history-list">{history.map((item, index) => <div key={`${item.recordedAt}-${item.action}`}><span>GW{item.event}</span><strong>{item.action}<small>Captain {item.captain}</small></strong><b>{item.netGain == null ? "—" : `${item.netGain >= 0 ? "+" : ""}${item.netGain.toFixed(1)} xPts`}</b><em>{index === 0 ? "Current" : new Date(item.recordedAt).toLocaleDateString([], { day: "numeric", month: "short" })}</em></div>)}</div>
      <footer>Saved locally only when the recommended action, captain, points edge or uncertainty changes meaningfully.</footer>
    </article>
  );
}
