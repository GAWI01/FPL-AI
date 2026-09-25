"use client";

import type { LucideIcon } from "lucide-react";

export function Avatar({
  name,
  tone = "violet",
  badge,
}: {
  name: string;
  tone?: string;
  badge?: string;
}) {
  return (
    <div className="avatar-wrap">
      <div className={`avatar ${tone}`} aria-label={`${name} generic player shirt`}>
        <span className="jersey-collar" />
        <span className="jersey-initials">
          {name
            .split(" ")
            .map((x) => x[0])
            .join("")
            .slice(0, 2)}
        </span>
      </div>
      {badge && <b className="badge">{badge}</b>}
    </div>
  );
}

export function Card({
  title,
  icon: Icon,
  children,
  action,
}: {
  title: string;
  icon?: LucideIcon;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <section className="card">
      <header className="card-head">
        <div className="card-title">
          {Icon && (
            <span className="small-icon">
              <Icon size={15} />
            </span>
          )}
          <h2>{title}</h2>
        </div>
        {action}
      </header>
      {children}
    </section>
  );
}

export function Stat({
  icon: Icon,
  label,
  value,
  sub,
  tone,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  sub: React.ReactNode;
  tone: string;
}) {
  return (
    <div className="stat">
      <span className={`stat-icon ${tone}`}>
        <Icon size={16} />
      </span>
      <span className="label">{label}</span>
      <strong>{value}</strong>
      <small>{sub}</small>
    </div>
  );
}
