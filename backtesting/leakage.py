from __future__ import annotations
from typing import Iterable
import pandas as pd

class LookaheadError(ValueError):
    pass

def assert_no_lookahead(frame: pd.DataFrame, decision_gw: int, *, gw_column: str = "GW",
                        feature_gw_columns: Iterable[str] = ()) -> None:
    if gw_column in frame.columns:
        values = pd.to_numeric(frame[gw_column], errors="coerce")
        if (values.dropna() > decision_gw).any():
            raise LookaheadError(f"Input contains GW>{decision_gw}; future rows are not allowed.")
    for column in feature_gw_columns:
        if column in frame.columns:
            values = pd.to_numeric(frame[column], errors="coerce")
            if (values.dropna() > decision_gw).any():
                raise LookaheadError(f"Feature version column {column!r} contains future GW data.")
