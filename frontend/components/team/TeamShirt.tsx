import type { CSSProperties } from "react";

type KitPalette = {
  primary: string;
  secondary: string;
  accent: string;
  text: string;
};

const palettes: Record<string, KitPalette> = {
  ARS: { primary: "#ef0107", secondary: "#ffffff", accent: "#063672", text: "#ffffff" },
  AVL: { primary: "#670e36", secondary: "#95bfe5", accent: "#f9d34a", text: "#ffffff" },
  BHA: { primary: "#0057b8", secondary: "#ffffff", accent: "#ffcd00", text: "#ffffff" },
  BOU: { primary: "#da291c", secondary: "#111111", accent: "#ffffff", text: "#ffffff" },
  BRE: { primary: "#e30613", secondary: "#ffffff", accent: "#111111", text: "#ffffff" },
  BUR: { primary: "#6c1d45", secondary: "#99d6ea", accent: "#f8e71c", text: "#ffffff" },
  CHE: { primary: "#034694", secondary: "#ffffff", accent: "#dba111", text: "#ffffff" },
  COV: { primary: "#69b3e7", secondary: "#ffffff", accent: "#12355b", text: "#10253e" },
  CRY: { primary: "#1b458f", secondary: "#c4122e", accent: "#ffffff", text: "#ffffff" },
  EVE: { primary: "#003399", secondary: "#ffffff", accent: "#1e7d34", text: "#ffffff" },
  FUL: { primary: "#ffffff", secondary: "#111111", accent: "#cc0000", text: "#111111" },
  HUL: { primary: "#f5a12d", secondary: "#111111", accent: "#ffffff", text: "#111111" },
  IPS: { primary: "#0044aa", secondary: "#ffffff", accent: "#d81920", text: "#ffffff" },
  LEE: { primary: "#ffffff", secondary: "#1d428a", accent: "#ffcd00", text: "#1d428a" },
  LEI: { primary: "#003090", secondary: "#ffffff", accent: "#fdbe11", text: "#ffffff" },
  LIV: { primary: "#c8102e", secondary: "#ffffff", accent: "#00b2a9", text: "#ffffff" },
  MCI: { primary: "#6cabdd", secondary: "#ffffff", accent: "#1c2c5b", text: "#10253e" },
  MUN: { primary: "#da291c", secondary: "#ffffff", accent: "#fbe122", text: "#ffffff" },
  NEW: { primary: "#111111", secondary: "#ffffff", accent: "#41b6e6", text: "#ffffff" },
  NFO: { primary: "#dd0000", secondary: "#ffffff", accent: "#111111", text: "#ffffff" },
  NOR: { primary: "#fff200", secondary: "#00a650", accent: "#111111", text: "#123524" },
  SHU: { primary: "#ee2737", secondary: "#ffffff", accent: "#111111", text: "#ffffff" },
  SOU: { primary: "#d71920", secondary: "#ffffff", accent: "#111111", text: "#ffffff" },
  SUN: { primary: "#eb172b", secondary: "#ffffff", accent: "#111111", text: "#ffffff" },
  TOT: { primary: "#ffffff", secondary: "#132257", accent: "#7c8798", text: "#132257" },
  WAT: { primary: "#fbec21", secondary: "#111111", accent: "#ed2127", text: "#111111" },
  WHU: { primary: "#7a263a", secondary: "#1bb1e7", accent: "#f3d459", text: "#ffffff" },
  WOL: { primary: "#fdb913", secondary: "#231f20", accent: "#ffffff", text: "#231f20" },
};

const aliases: Record<string, string> = {
  arsenal: "ARS",
  astonvilla: "AVL",
  bournemouth: "BOU",
  brentford: "BRE",
  brighton: "BHA",
  brightonandhovealbion: "BHA",
  burnley: "BUR",
  chelsea: "CHE",
  coventrycity: "COV",
  crystalpalace: "CRY",
  everton: "EVE",
  fulham: "FUL",
  hullcity: "HUL",
  ipswichtown: "IPS",
  leeds: "LEE",
  leedsunited: "LEE",
  leicestercity: "LEI",
  liverpool: "LIV",
  mancity: "MCI",
  manchestercity: "MCI",
  manutd: "MUN",
  manchesterunited: "MUN",
  newcastle: "NEW",
  newcastleunited: "NEW",
  norwichcity: "NOR",
  nottmforest: "NFO",
  nottinghamforest: "NFO",
  sheffieldunited: "SHU",
  southampton: "SOU",
  spurs: "TOT",
  sunderland: "SUN",
  tottenhamhotspur: "TOT",
  watford: "WAT",
  westham: "WHU",
  westhamunited: "WHU",
  wolves: "WOL",
  wolverhamptonwanderers: "WOL",
};

const fallbackPalette: KitPalette = {
  primary: "#6842b8",
  secondary: "#a78bfa",
  accent: "#ffffff",
  text: "#ffffff",
};

type KitStyle = CSSProperties & Record<`--kit-${string}`, string>;

function normalizedTeam(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

export function teamKit(team: string, teamShort?: string | null) {
  const suppliedCode = teamShort?.trim().toUpperCase() ?? "";
  const code = palettes[suppliedCode] ? suppliedCode : aliases[normalizedTeam(team)] ?? suppliedCode;
  const palette = palettes[code] ?? fallbackPalette;
  const label = code || team.replace(/[^a-z0-9]/gi, "").slice(0, 3).toUpperCase() || "FPL";
  const style: KitStyle = {
    "--kit-primary": palette.primary,
    "--kit-secondary": palette.secondary,
    "--kit-accent": palette.accent,
    "--kit-text": palette.text,
  };
  return { label, style };
}

export function TeamShirt({
  team,
  teamShort,
  className = "team-shirt",
}: {
  team: string;
  teamShort?: string | null;
  className?: string;
}) {
  const kit = teamKit(team, teamShort);
  return <span className={`${className} club-kit`} style={kit.style} aria-hidden="true">{kit.label}</span>;
}
