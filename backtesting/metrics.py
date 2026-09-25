from __future__ import annotations
import numpy as np
import pandas as pd

def calculate_metrics(results: pd.DataFrame, *, prediction_column="predicted_points",
                      actual_column="actual_points") -> dict[str,float]:
    if results.empty:
        return {"rows":0.0,"mae":0.0,"rmse":0.0,"bias":0.0,"directional_accuracy":0.0}
    pred=pd.to_numeric(results[prediction_column],errors="coerce")
    actual=pd.to_numeric(results[actual_column],errors="coerce")
    mask=pred.notna() & actual.notna()
    pred=pred[mask].to_numpy(float); actual=actual[mask].to_numpy(float)
    if len(pred)==0:
        return {"rows":0.0,"mae":0.0,"rmse":0.0,"bias":0.0,"directional_accuracy":0.0}
    err=pred-actual
    return {"rows":float(len(pred)),"mae":float(np.mean(np.abs(err))),
            "rmse":float(np.sqrt(np.mean(err**2))),"bias":float(np.mean(err)),
            "directional_accuracy":float(np.mean((pred>=np.median(pred))==(actual>=np.median(actual))))}

def evaluate_decisions(decisions: pd.DataFrame, *, predicted_gain_column="predicted_gain",
                       actual_gain_column="actual_gain") -> dict[str,float]:
    if decisions.empty:
        return {"decisions":0.0,"decision_accuracy":0.0,"predicted_gain_mean":0.0,
                "actual_gain_mean":0.0,"positive_decision_rate":0.0}
    pred=pd.to_numeric(decisions[predicted_gain_column],errors="coerce")
    actual=pd.to_numeric(decisions[actual_gain_column],errors="coerce")
    mask=pred.notna() & actual.notna()
    pred=pred[mask]; actual=actual[mask]
    if len(pred)==0:
        return {"decisions":0.0,"decision_accuracy":0.0,"predicted_gain_mean":0.0,
                "actual_gain_mean":0.0,"positive_decision_rate":0.0}
    return {"decisions":float(len(pred)),"decision_accuracy":float(np.mean((pred>0)==(actual>0))),
            "predicted_gain_mean":float(pred.mean()),"actual_gain_mean":float(actual.mean()),
            "positive_decision_rate":float(np.mean(pred>0))}
