"use client";

import type { FormEvent } from "react";
import { Sparkles, ArrowRight } from "lucide-react";

type ConnectTeamProps = {
  teamIdInput: string;
  connecting: boolean;
  error: string | null;
  onTeamIdChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function ConnectTeam({
  teamIdInput,
  connecting,
  error,
  onTeamIdChange,
  onSubmit,
}: ConnectTeamProps) {
  return (

  <main
    className="shell"
    style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "32px",
    }}
  >
    <section
      className="card"
      style={{
        width: "100%",
        maxWidth: "520px",
        padding: "42px",
        textAlign: "center",
      }}
    >
      <div
        className="brand-icon"
        style={{
          width: "52px",
          height: "52px",
          margin: "0 auto 20px",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Sparkles size={24} />
      </div>

      <small
        style={{
          color: "#8B8B96",
          letterSpacing: "0.12em",
          fontWeight: 700,
        }}
      >
        FANTASY ANALYTICS
      </small>

      <h1 style={{ margin: "10px 0", fontSize: "32px" }}>
        Connect your FPL team
      </h1>

      <p style={{ color: "#8B8B96", lineHeight: 1.6, margin: "0 auto 28px" }}>
        Enter your Fantasy Premier League Team ID to unlock your
        personalized AI dashboard, predictions and fixture analysis.
      </p>

      <form onSubmit={onSubmit}>
        <label
          htmlFor="team-id"
          style={{
            display: "block",
            textAlign: "left",
            fontSize: "12px",
            fontWeight: 700,
            marginBottom: "8px",
          }}
        >
          FPL TEAM ID
        </label>

        <input
          id="team-id"
          inputMode="numeric"
          pattern="[0-9]*"
          autoFocus
          value={teamIdInput}
          onChange={(event) => onTeamIdChange(event.target.value)}
          placeholder="e.g. 6658075"
          disabled={connecting}
          style={{
            width: "100%",
            boxSizing: "border-box",
            padding: "14px 16px",
            borderRadius: "10px",
            border: "1px solid rgba(255,255,255,0.12)",
            background: "rgba(255,255,255,0.04)",
            color: "inherit",
            fontSize: "16px",
            outline: "none",
            marginBottom: "12px",
          }}
        />

        {error && (
          <div
            style={{
              textAlign: "left",
              color: "#FCA5A5",
              fontSize: "13px",
              marginBottom: "14px",
            }}
          >
            {error}
          </div>
        )}

        <button
          type="submit"
          className="primary"
          disabled={connecting || !teamIdInput.trim()}
          style={{
            width: "100%",
            justifyContent: "center",
            opacity: connecting || !teamIdInput.trim() ? 0.65 : 1,
          }}
        >
          {connecting ? "Connecting..." : "Connect Team"}
          {!connecting && <ArrowRight size={15} />}
        </button>
      </form>

      <p style={{ color: "#70707B", fontSize: "12px", lineHeight: 1.5, margin: "20px 0 0" }}>
        Your Team ID is the number in your FPL team page URL.
        <br />
        Example: <b style={{ color: "#9B9BA5" }}>fantasy.premierleague.com/entry/6658075</b>
      </p>
    </section>
  </main>
  );
}
