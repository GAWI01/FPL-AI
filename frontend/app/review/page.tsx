"use client";

import { useTeam } from "@/app/providers/TeamProvider";
import { PostGameweekReview } from "@/components/review/PostGameweekReview";
import { DataState } from "@/components/states/DataState";


export default function ReviewPage() {
  const { teamId, loading, error } = useTeam();
  if (!teamId && loading) {
    return <div className="workspace-page"><DataState title="Loading your team…" loading>Fetching the official squad before building the review.</DataState></div>;
  }
  if (!teamId && error) {
    return <div className="workspace-page"><DataState title="Your team could not be loaded" tone="error">{error}</DataState></div>;
  }
  if (!teamId) {
    return <div className="workspace-page"><DataState title="Connect a team first">Use Overview to connect your public FPL Team ID.</DataState></div>;
  }
  return (
    <div className="workspace-page">
      <header className="workspace-heading"><div><span className="eyebrow">DECISION ACCOUNTABILITY</span><h1>Post-Gameweek review</h1><p>See what worked, what missed and whether your decisions beat the saved model expectation.</p></div></header>
      <PostGameweekReview teamId={teamId} />
    </div>
  );
}
