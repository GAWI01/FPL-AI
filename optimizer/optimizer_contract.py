from __future__ import annotations
import pandas as pd

OPTIMIZER_REQUIRED_COLUMNS = frozenset({"name","position","team","price","predicted_points"})
OPTIMIZER_OUTPUT_COLUMNS = ("name","position","team","price","predicted_points")

def validate_optimizer_input(players: pd.DataFrame) -> None:
    if not isinstance(players, pd.DataFrame):
        raise ValueError("players must be a pandas DataFrame")
    missing = OPTIMIZER_REQUIRED_COLUMNS - set(players.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
    if players.empty:
        raise ValueError("players must not be empty")
    for col in ("price","predicted_points"):
        values = pd.to_numeric(players[col], errors="coerce")
        if values.isna().any():
            raise ValueError(f"{col} contains invalid values")
    if players["name"].isna().any() or players["position"].isna().any() or players["team"].isna().any():
        raise ValueError("name, position and team must not contain missing values")

def normalize_optimizer_input(players: pd.DataFrame) -> pd.DataFrame:
    validate_optimizer_input(players)
    out=players.copy()
    if "player_id" in out.columns:
        out["player_id"]=pd.to_numeric(out["player_id"],errors="raise").astype(int)
    out["position"]=out["position"].astype(str).str.strip().str.upper().replace({"GKP":"GK"})
    out["price"]=pd.to_numeric(out["price"],errors="raise").astype(float)
    out["predicted_points"]=pd.to_numeric(out["predicted_points"],errors="raise").astype(float)
    return out
