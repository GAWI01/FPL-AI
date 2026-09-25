import pandas as pd
from backtesting.decision_backtest import run_decision_backtest

def test_decision_backtest_aligns_target_gw_and_evaluates_gain():
    df=pd.DataFrame([
        {"GW":1,"player_id":1,"total_points":2},{"GW":1,"player_id":2,"total_points":5},
        {"GW":2,"player_id":1,"total_points":3},{"GW":2,"player_id":2,"total_points":8},
        {"GW":3,"player_id":1,"total_points":4},{"GW":3,"player_id":2,"total_points":2},
    ])
    def decide(history, gw):
        return {"player_out_id":1,"player_in_id":2,"predicted_gain":2.0}
    result,metrics=run_decision_backtest(df,decide)
    assert result["target_gw"].tolist()==[2,3]
    assert result["actual_gain"].tolist()==[5.0,-2.0]
    assert metrics["decisions"]==2.0
