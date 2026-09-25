const LEGACY_MODULE_TARGETS: Readonly<Record<string, string>> = {
  "my-team": "/team",
  "transfer-center": "/plan#transfer-center",
  "ai-recommendations": "/plan#ai-recommendations",
  players: "/explore#player-market",
  fixtures: "/explore#fixture-matrix",
  chips: "/plan#chip-advisor",
  statistics: "/review#statistics",
  "team-history": "/review",
  settings: "/settings",
};


export function legacyModuleTarget(module: string): string | null {
  return LEGACY_MODULE_TARGETS[module] ?? null;
}
