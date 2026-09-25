import { ArrowLeftRight, LineChart, Shield, Sparkles, Trophy } from "lucide-react";
import { Stat } from "../ui/DashboardPrimitives";

type StatsGridProps = {
  projectedPoints: number | null;
  teamEvent: number | null | undefined;
  loading: boolean;
  squadValue: number | null;
  teamValue: number | null | undefined;
  bank: number | null | undefined;
  overallRank: number | null | undefined;
  eventRank: number | null | undefined;
  transfers: number | null | undefined;
  teamRating?: number | null;
};

function formatProjectedPoints(points: number | null) {
  return points == null ? "Unavailable" : points.toFixed(1);
}

export function StatsGrid({
  projectedPoints,
  teamEvent,
  loading,
  squadValue,
  teamValue,
  bank,
  overallRank,
  eventRank,
  transfers,
  teamRating,
}: StatsGridProps) {
  return (
    <div className="stats">
      <Stat
        icon={Sparkles}
        label={`Projected Points (GW${(teamEvent ?? 2) + 1})`}
        value={formatProjectedPoints(projectedPoints)}
        sub="From current prediction data"
        tone="purple"
      />
      <Stat
        icon={Shield}
        label="Team Rating"
        value={teamRating == null ? "—" : `${teamRating.toFixed(1)}/10`}
        sub={loading ? "Loading team analysis" : "AI squad rating"}
        tone="green"
      />
      <Stat
        icon={Trophy}
        label="Team Value"
        value={
          teamValue == null
            ? (squadValue == null ? "Unavailable" : `${squadValue.toFixed(1)}m`)
            : `${(teamValue / 10).toFixed(1)}m`
        }
        sub={bank == null ? "Bank unavailable" : `ITB: ${bank.toFixed(1)}m`}
        tone="yellow"
      />
      <Stat
        icon={LineChart}
        label="Overall Rank"
        value={overallRank == null ? "Unavailable" : overallRank.toLocaleString("en-US")}
        sub={
          eventRank == null
            ? "From FPL team data"
            : `GW rank: ${eventRank.toLocaleString("en-US")}`
        }
        tone="orange"
      />
      <Stat
        icon={ArrowLeftRight}
        label="Transfers"
        value={transfers == null ? "Unavailable" : String(transfers)}
        sub="From FPL team data"
        tone="cyan"
      />
    </div>
  );
}
