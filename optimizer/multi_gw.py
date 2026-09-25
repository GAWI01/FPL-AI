from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from .squad_optimizer import optimize_squad

@dataclass(frozen=True)
class MultiGWConfig:
    horizon: int = 3
    gw_weights: tuple[float,...] | None = None
    def __post_init__(self):
        if self.horizon < 1: raise ValueError("horizon must be >= 1")
        if self.gw_weights is not None and len(self.gw_weights) != self.horizon:
            raise ValueError("gw_weights length must equal horizon")

def aggregate_multi_gw_value(predictions: pd.DataFrame, config: MultiGWConfig) -> pd.DataFrame:
    required={"player_id","GW","predicted_points"}
    missing=required-set(predictions.columns)
    if missing: raise ValueError("predictions missing columns: "+", ".join(sorted(missing)))
    df=predictions.copy()
    df["GW"]=pd.to_numeric(df["GW"],errors="coerce")
    if df["GW"].isna().any(): raise ValueError("GW contains invalid values")
    start=int(df["GW"].min())
    end=start+config.horizon-1
    df=df[(df["GW"]>=start)&(df["GW"]<=end)].copy()
    weights=config.gw_weights or tuple(1.0 for _ in range(config.horizon))
    weight_map={start+i:w for i,w in enumerate(weights)}
    df["_weighted"]=pd.to_numeric(df["predicted_points"],errors="coerce")*df["GW"].map(weight_map)
    grouped=df.groupby("player_id",as_index=False)["_weighted"].sum().rename(columns={"_weighted":"optimization_score"})
    meta=[c for c in ["name","position","team","price"] if c in df.columns]
    if meta:
        grouped=grouped.merge(df.sort_values("GW").drop_duplicates("player_id")[["player_id"]+meta],on="player_id",how="left")
    return grouped

def optimize_multi_gw(predictions: pd.DataFrame,budget: float=100.0,config: MultiGWConfig|None=None)->pd.DataFrame:
    config=config or MultiGWConfig()
    aggregated=aggregate_multi_gw_value(predictions,config)
    out=aggregated.rename(columns={"optimization_score":"predicted_points"})
    return optimize_squad(out,budget=budget)
