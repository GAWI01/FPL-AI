export type StartingXIPlayer = {
  player_id: number;
  position_name: string;
  team?: string;
};

export function isValidStartingXI(players: StartingXIPlayer[]): boolean {
  if (players.length !== 11) return false;

  const counts = {
    GKP: 0,
    DEF: 0,
    MID: 0,
    FWD: 0,
  };

  for (const player of players) {
    const position = String(player.position_name).toUpperCase();

    if (!(position in counts)) return false;

    counts[position as keyof typeof counts] += 1;
  }

  // FPL starting XI rules:
  // 1 goalkeeper, 3–5 defenders, 2–5 midfielders, 1–3 forwards.
  if (counts.GKP !== 1) return false;
  if (counts.DEF < 3 || counts.DEF > 5) return false;
  if (counts.MID < 2 || counts.MID > 5) return false;
  if (counts.FWD < 1 || counts.FWD > 3) return false;

  // A maximum of three players from one Premier League club.
  const clubCounts = new Map<string, number>();
  for (const player of players) {
    if (!player.team) continue;
    const count = (clubCounts.get(player.team) ?? 0) + 1;
    if (count > 3) return false;
    clubCounts.set(player.team, count);
  }

  return true;
}
