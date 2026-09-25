import pandas as pd
import pytest
from backtesting.engine import BacktestConfig, BacktestEngine, BacktestError
from backtesting.metrics import calculate_metrics, evaluate_decisions

def history():
    return pd.DataFrame({"GW":[1,1,2,2,3,3],"player_id":[1,2,1,2,1,2],"total_points":[5,2,8,4,6,7]})

def predictor(h,g):
    return h.groupby("player_id").tail(1)[["player_id"]].assign(predicted_points=5.0)

def test_only_past_rows_are_seen():
    seen=[]
    def p(h,g):
        seen.append((g,int(h.GW.max())))
        return predictor(h,g)
    BacktestEngine(BacktestConfig(start_gw=1,end_gw=2)).run(history(),p)
    assert seen==[(1,1),(2,2)]

def test_targets_are_next_gw():
    r=BacktestEngine(BacktestConfig(start_gw=1,end_gw=2)).run(history(),predictor)
    assert r.loc[r.GW==1,"target_gw"].eq(2).all()
    assert r.loc[r.GW==2,"target_gw"].eq(3).all()

def test_missing_prediction_column_fails():
    with pytest.raises(BacktestError):
        BacktestEngine(BacktestConfig(start_gw=1,end_gw=1)).run(history(),lambda h,g: pd.DataFrame({"player_id":[1]}))

def test_metrics():
    r=calculate_metrics(pd.DataFrame({"predicted_points":[2,4,8],"actual_points":[1,5,7]}))
    assert r["rows"]==3 and r["mae"]==pytest.approx(1.0) and r["rmse"]==pytest.approx(1.0)

def test_decision_metrics():
    r=evaluate_decisions(pd.DataFrame({"predicted_gain":[2,-1,3,-2],"actual_gain":[1,2,4,-1]}))
    assert r["decision_accuracy"]==pytest.approx(.75)

def test_duplicate_fixture_predictions_are_aggregated():
    def dup(h, g):
        return pd.DataFrame({"player_id": [1, 1], "predicted_points": [5, 6]})
    r = BacktestEngine(BacktestConfig(start_gw=1, end_gw=1)).run(history(), dup)
    assert r.loc[r.GW == 1, "predicted_points"].tolist() == [11.0]
