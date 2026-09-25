import pandas as pd
from optimizer.objective import OptimizerObjectiveConfig, score_predictions, build_objective_column

def test_default_objective_preserves_predictions():
    df=pd.DataFrame({"predicted_points":[1.0,2.5]})
    assert score_predictions(df, OptimizerObjectiveConfig()).tolist()==[1.0,2.5]

def test_risk_adjustment_is_bounded_and_explicit():
    df=pd.DataFrame({"predicted_points":[10.0],"risk":[1.0],"minutes_certainty":[1.0]})
    cfg=OptimizerObjectiveConfig(risk_weight=0.2, minutes_certainty_weight=0.3)
    assert score_predictions(df,cfg).iloc[0] == 8.0

def test_missing_optional_signals_do_not_change_score():
    df=pd.DataFrame({"predicted_points":[7.0]})
    cfg=OptimizerObjectiveConfig(risk_weight=0.2, minutes_certainty_weight=0.3)
    assert score_predictions(df,cfg).iloc[0] == 7.0

def test_build_objective_column_does_not_overwrite_prediction():
    df=pd.DataFrame({"predicted_points":[7.0]})
    out=build_objective_column(df, OptimizerObjectiveConfig())
    assert out["predicted_points"].iloc[0] == 7.0
    assert out["optimization_score"].iloc[0] == 7.0
