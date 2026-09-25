"use client";

import { Clock3 } from "lucide-react";
import { useEffect, useState } from "react";


export function formatDeadlineRemaining(deadline: string, now = Date.now()) {
  const target = Date.parse(deadline);
  if (!Number.isFinite(target)) return "Deadline unavailable";
  const seconds = Math.floor((target - now) / 1000);
  if (seconds <= 0) return "Deadline passed";
  const days = Math.floor(seconds / 86_400);
  const hours = Math.floor((seconds % 86_400) / 3_600);
  const minutes = Math.floor((seconds % 3_600) / 60);
  const remainingSeconds = seconds % 60;
  if (days > 0) return `${days}d ${hours}h ${minutes}m`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${remainingSeconds}s`;
  return `${remainingSeconds}s`;
}


export function DeadlineCountdown({
  deadline,
  event,
  now,
}: {
  deadline?: string | null;
  event?: number | null;
  now?: number;
}) {
  const [clock, setClock] = useState<number | null>(now ?? null);

  useEffect(() => {
    if (!deadline || now !== undefined) return;
    const initial = window.setTimeout(() => setClock(Date.now()), 0);
    const interval = window.setInterval(() => setClock(Date.now()), 1_000);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(interval);
    };
  }, [deadline, now]);

  if (!deadline) return null;
  return (
    <span className="deadline-countdown">
      <Clock3 size={13} aria-hidden="true" />
      <span><small>{event ? `GW${event} deadline` : "Next deadline"}</small><time role="timer" dateTime={deadline}>{clock == null ? "Calculating…" : formatDeadlineRemaining(deadline, clock)}</time></span>
    </span>
  );
}
