from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
import pandas as pd

from .squad_optimizer import optimize_squad
from .starting_xi import select_starting_xi

CHIPS=("WILDCARD","FREE_HIT","BENCH_BOOST","TRIPLE_CAPTAIN")

@dataclass(frozen=True)
class ChipOptimizationConfig:
    horizon: int = 3
    bench_boost_weight: float = 1.0
    triple_captain_weight: float = 1.0
    wildcard_weight: float = 1.0
    free_hit_weight: float = 1.0
    def __post_init__(self):
        if self.horizon < 1: raise ValueError("horizon must be >= 1")

def _prepared(df: pd.DataFrame) -> pd.DataFrame:
    required={"player_id","predicted_points"}
    missing=required-set(df.columns)
    if missing: raise ValueError("predictions missing columns: "+", ".join(sorted(missing)))
    out=df.copy()
    out["player_id"]=pd.to_numeric(out["player_id"],errors="raise").astype(int)
    out["predicted_points"]=pd.to_numeric(out["predicted_points"],errors="raise").astype(float)
    return out

def _legal_optimal_squad(pool: pd.DataFrame) -> pd.DataFrame | None:
    required={"name","position","team","price"}
    if not required.issubset(pool.columns):
        return None
    return optimize_squad(pool.copy(), budget=float(pool["price"].sum()))

def evaluate_chip_scenarios(
    current_squad: pd.DataFrame,
    predictions: pd.DataFrame,
    *,
    available_chips: Mapping[str,bool] | None=None,
    config: ChipOptimizationConfig|None=None,
    double_gameweek: bool=False,
    blank_gameweek: bool=False,
) -> dict[str,Any]:
    cfg=config or ChipOptimizationConfig()
    squad=_prepared(current_squad)
    pool=_prepared(predictions)
    available={c: bool((available_chips or {}).get(c, True)) for c in CHIPS}
    current_ids=set(squad["player_id"])
    current_points=float(squad["predicted_points"].sum())
    if not any(available.values()):
        return {
            "recommended_chip": None,
            "score": 0.0,
            "scenarios": [],
            "baseline_value": round(current_points, 3),
        }
    pool_by_id=pool.groupby("player_id",as_index=False)["predicted_points"].sum()
    scenarios=[]

    legal_squad=_legal_optimal_squad(pool)
    if available["WILDCARD"] and legal_squad is not None:
        best=float(legal_squad["predicted_points"].sum())
        scenarios.append(("WILDCARD",max(0.0,best-current_points)*cfg.wildcard_weight,
                          "Rebuild the squad using the legal FPL squad optimizer."))

    if available["FREE_HIT"] and blank_gameweek and legal_squad is not None:
        xi=select_starting_xi(legal_squad)
        best=float(xi["starting_xi_base_points"])
        current_xi=select_starting_xi(squad) if {"name","position","team","price"}.issubset(squad.columns) and len(squad)>=11 else None
        baseline=float(current_xi["starting_xi_base_points"]) if current_xi else 0.0
        scenarios.append(("FREE_HIT",max(0.0,best-baseline)*cfg.free_hit_weight,
                          "Compare a legal one-week optimized XI against the current XI."))

    if available["BENCH_BOOST"] and double_gameweek:
        if legal_squad is not None:
            xi=select_starting_xi(legal_squad)
            xi_ids={int(p["player_id"]) for p in xi["starting_xi"]}
            bench=legal_squad[~legal_squad["player_id"].isin(xi_ids)]
            bench_value=float(bench["predicted_points"].sum())
        else:
            bench=pool_by_id[~pool_by_id.player_id.isin(current_ids)].nlargest(4,"predicted_points")
            bench_value=float(bench["predicted_points"].sum())
        scenarios.append(("BENCH_BOOST",max(0.0,bench_value)*cfg.bench_boost_weight,
                           "Double Gameweek raises the expected contribution of the four bench players."))

    if available["TRIPLE_CAPTAIN"] and double_gameweek and not pool_by_id.empty:
        best=float(pool_by_id["predicted_points"].max())
        scenarios.append(("TRIPLE_CAPTAIN",max(0.0,best*2.0)*cfg.triple_captain_weight,
                          "Triple Captain adds two extra captain multiples relative to a normal captain."))

    scenarios.sort(key=lambda x:(-x[1],x[0]))
    output=[{"chip":c,"score":round(max(0.0,s),3),"reason":r} for c,s,r in scenarios]
    recommendation=output[0] if output and output[0]["score"]>0 else None
    return {
        "recommended_chip":recommendation["chip"] if recommendation else None,
        "score":recommendation["score"] if recommendation else 0.0,
        "scenarios":output,
        "baseline_value":round(current_points,3),
    }

def chip_advisor_upgrade(current_squad: pd.DataFrame,predictions: pd.DataFrame,**kwargs: Any)->dict[str,Any]:
    return evaluate_chip_scenarios(current_squad,predictions,**kwargs)
