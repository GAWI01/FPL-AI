"use client";

import { Database, LogOut, Server, ShieldCheck, Target } from "lucide-react";

import { useTeam } from "@/app/providers/TeamProvider";
import { API_BASE_URL } from "@/lib/api";
import { seasonGoalOptions, useSeasonGoal, writeSeasonGoal, type SeasonGoal } from "@/lib/preferences";


export function SettingsWorkspace() {
  const { teamId, dashboard, disconnect } = useTeam();
  const seasonGoal = useSeasonGoal();

  const updateSeasonGoal = (value: SeasonGoal) => {
    writeSeasonGoal(value);
  };
  return (
    <section className="workspace-page">
      <div className="workspace-heading"><div><span className="eyebrow">LOCAL MVP PREFERENCES</span><h1>Settings & data trust.</h1><p>Your public Team ID is stored only in this browser. FPL AI never asks for an FPL password.</p></div><span className="source-pill source-official">Private by design</span></div>
      <div className="settings-grid">
        <article className="premium-card settings-card"><header><Database size={16} /><h2>Connected team</h2></header><div className="settings-value"><span>Public FPL Team ID</span><strong>{teamId ?? "No team connected"}</strong></div>{teamId ? <button className="danger-button" onClick={disconnect}><LogOut size={14} />Disconnect team</button> : null}</article>
        <article className="premium-card settings-card preference-card"><header><Target size={16} /><h2>Season preference</h2></header><div className="settings-control"><label htmlFor="season-goal">Season goal</label><select id="season-goal" value={seasonGoal} onChange={(event) => updateSeasonGoal(event.target.value as SeasonGoal)}>{seasonGoalOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}</select><p>Preferences personalize the product locally. Official facts and model projections remain unchanged.</p></div></article>
        <article className="premium-card settings-card"><header><Server size={16} /><h2>Data runtime</h2></header><div className="settings-value"><span>API origin</span><strong>{API_BASE_URL || "Same-origin gateway"}</strong></div><div className="settings-value"><span>Prediction version</span><strong>{dashboard?.meta.prediction_version ?? dashboard?.data.team.prediction_file ?? "Unavailable"}</strong></div><div className="settings-value"><span>Last generated</span><strong>{dashboard?.meta.generated_at ? new Date(dashboard.meta.generated_at).toLocaleString() : "Unavailable"}</strong></div></article>
        <article className="premium-card settings-card trust-card"><header><ShieldCheck size={16} /><h2>What FPL AI can do</h2></header><p>FPL AI reads public manager data and provides decision support. It cannot make transfers, activate chips or change your captain on the official FPL site.</p></article>
        <article className="premium-card settings-card trust-card"><header><ShieldCheck size={16} /><h2>Release integrity</h2></header><p>Independent beta. Not affiliated with or endorsed by the Premier League. A commercial launch remains gated on written data and trademark permissions.</p></article>
      </div>
    </section>
  );
}
