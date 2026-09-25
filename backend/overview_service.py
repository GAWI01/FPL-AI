from __future__ import annotations
from typing import Any
import pandas as pd

def build_top_players(predictions: pd.DataFrame, players: pd.DataFrame, teams: pd.DataFrame, limit: int = 5, position: str | None = None) -> list[dict[str, Any]]:
    if limit < 1: raise ValueError("limit must be >= 1")
    required = {"player_id", "name", "position", "team", "price", "predicted_points"}
    missing = required - set(predictions.columns)
    if missing: raise ValueError("Prediction data is missing columns: " + ", ".join(sorted(missing)))
    result = predictions.copy()
    result["player_id"] = pd.to_numeric(result["player_id"], errors="coerce")
    result["predicted_points"] = pd.to_numeric(result["predicted_points"], errors="coerce")
    result = result.dropna(subset=["player_id", "predicted_points"])
    if position:
        result = result[result["position"].astype(str).str.upper() == position.upper()]
    result = result.sort_values(["predicted_points", "player_id"], ascending=[False, True]).head(limit)
    ownership_by_id = {}
    if "player_id" in players.columns and "selected_by_percent" in players.columns:
        for _, row in players.iterrows():
            pid = pd.to_numeric(row["player_id"], errors="coerce")
            if pd.isna(pid): continue
            ownership = pd.to_numeric(row["selected_by_percent"], errors="coerce")
            ownership_by_id[int(pid)] = None if pd.isna(ownership) else float(ownership)
    short_by_name = {}
    if "name" in teams.columns and "short_name" in teams.columns:
        short_by_name = {str(row["name"]): str(row["short_name"]) for _, row in teams.iterrows()}
    rows=[]
    for _, row in result.iterrows():
        pid=int(row["player_id"])
        rows.append({
            "player_id": pid, "name": str(row["name"]), "team": str(row["team"]),
            "team_short": short_by_name.get(str(row["team"]), "—"), "position": str(row["position"]),
            "price": float(row["price"]) if pd.notna(row["price"]) else None,
            "opponent": row.get("opponent"), "predicted_points": float(row["predicted_points"]),
            "form": float(row["form"]) if pd.notna(row.get("form")) else None,
            "value": float(row["value"]) if pd.notna(row.get("value")) else None,
            "ownership": ownership_by_id.get(pid),
        })
    return rows
