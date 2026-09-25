from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

@dataclass(frozen=True)
class OptimizerObjectiveConfig:
    risk_weight: float = 0.0
    minutes_certainty_weight: float = 0.0
    def __post_init__(self):
        if not 0 <= self.risk_weight <= 1 or not 0 <= self.minutes_certainty_weight <= 1:
            raise ValueError("objective weights must be between 0 and 1")

def score_predictions(df: pd.DataFrame, config: OptimizerObjectiveConfig) -> pd.Series:
    points=pd.to_numeric(df["predicted_points"],errors="coerce")
    if points.isna().any(): raise ValueError("predicted_points contains invalid values")
    score=points.astype(float).copy()
    if config.risk_weight and "risk" in df:
        risk=pd.to_numeric(df["risk"],errors="coerce").fillna(0.0).clip(0,1)
        score *= (1.0-config.risk_weight*risk)
    if config.minutes_certainty_weight and "minutes_certainty" in df:
        certainty=pd.to_numeric(df["minutes_certainty"],errors="coerce").fillna(1.0).clip(0,1)
        score *= (1.0-config.minutes_certainty_weight*(1.0-certainty))
    return score

def build_objective_column(df: pd.DataFrame, config: OptimizerObjectiveConfig) -> pd.DataFrame:
    out=df.copy()
    out["optimization_score"]=score_predictions(out,config)
    return out
