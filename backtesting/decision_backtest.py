from __future__ import annotations
from typing import Callable
import pandas as pd
from .leakage import assert_no_lookahead
from .metrics import evaluate_decisions

class DecisionBacktestError(ValueError):
    pass

def run_decision_backtest(
    historical: pd.DataFrame,
    decision_fn: Callable[[pd.DataFrame,int], dict],
    *,
    gw_column: str="GW",
    player_id_column: str="player_id",
    actual_column: str="total_points",
    start_gw: int=1,
    end_gw: int|None=None,
) -> tuple[pd.DataFrame,dict[str,float]]:
    required={gw_column,player_id_column,actual_column}
    missing=required-set(historical.columns)
    if missing: raise DecisionBacktestError("historical frame missing columns: "+", ".join(sorted(missing)))
    data=historical.copy()
    data[gw_column]=pd.to_numeric(data[gw_column],errors="coerce")
    data=data.dropna(subset=[gw_column]).copy()
    data[gw_column]=data[gw_column].astype(int)
    last=int(data[gw_column].max())
    end=end_gw if end_gw is not None else last-1
    rows=[]
    for gw in range(start_gw,end+1):
        history=data[data[gw_column]<=gw].copy()
        assert_no_lookahead(history,gw,gw_column=gw_column)
        decision=decision_fn(history.copy(),gw)
        pred=float(decision.get("predicted_gain",0.0))
        out_id=decision.get("player_out_id")
        in_id=decision.get("player_in_id")
        target=data[data[gw_column]==gw+1]
        if out_id is None or in_id is None:
            actual_gain=0.0
        else:
            actual=target.groupby(player_id_column)[actual_column].sum()
            actual_gain=float(actual.get(int(in_id),0.0)-actual.get(int(out_id),0.0))
        rows.append({"GW":gw,"target_gw":gw+1,"player_out_id":out_id,"player_in_id":in_id,
                     "predicted_gain":pred,"actual_gain":actual_gain})
    result=pd.DataFrame(rows)
    return result,evaluate_decisions(result)
