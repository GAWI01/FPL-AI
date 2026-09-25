from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from transfer_analysis import optimize_transfer_plan
from .multi_gw import MultiGWConfig, aggregate_multi_gw_value

@dataclass(frozen=True)
class TransferOptimizationConfig:
    max_transfers: int = 1
    free_transfers: int = 1
    bank: float | None = None
    hit_cost: float = 4.0
    def __post_init__(self):
        if self.max_transfers < 0 or self.free_transfers < 0: raise ValueError("transfer counts cannot be negative")
        if self.hit_cost < 0: raise ValueError("hit_cost cannot be negative")

def calculate_transfer_value(current_squad: pd.DataFrame,candidate_squad: pd.DataFrame,*,hit_cost: float=0.0)->float:
    current=float(pd.to_numeric(current_squad["predicted_points"],errors="raise").sum())
    candidate=float(pd.to_numeric(candidate_squad["predicted_points"],errors="raise").sum())
    return candidate-current-float(hit_cost)

def optimize_transfers(
    current_squad: dict,
    predictions: pd.DataFrame,
    config: TransferOptimizationConfig | None = None,
    *,
    horizon_predictions: pd.DataFrame | None = None,
    horizon_config: MultiGWConfig | None = None,
) -> dict:
    config = config or TransferOptimizationConfig()
    data = predictions.copy()
    if horizon_predictions is not None:
        aggregated = aggregate_multi_gw_value(
            horizon_predictions,
            horizon_config or MultiGWConfig(),
        )
        score = aggregated[["player_id", "optimization_score"]].rename(
            columns={"optimization_score": "predicted_points"}
        )
        data = data.drop(columns=["predicted_points"], errors="ignore").merge(
            score, on="player_id", how="left", validate="one_to_one"
        )
        data["predicted_points"] = data["predicted_points"].fillna(0.0)
    return optimize_transfer_plan(
        current_squad,
        data,
        free_transfers=config.free_transfers,
        max_transfers=config.max_transfers,
        bank=config.bank,
        hit_cost=config.hit_cost,
    )
