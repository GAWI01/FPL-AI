import pandas as pd
import pytest
from optimizer.optimizer_contract import OPTIMIZER_REQUIRED_COLUMNS, normalize_optimizer_input, validate_optimizer_input

def base():
    return pd.DataFrame([
        {"player_id": 1, "name": "A", "position": "GKP", "team": "X", "price": 5, "predicted_points": 4},
        {"player_id": 2, "name": "B", "position": "MID", "team": "Y", "price": 6, "predicted_points": 5},
    ])

def test_required_columns_are_explicit():
    assert {"name","position","team","price","predicted_points"} <= OPTIMIZER_REQUIRED_COLUMNS

def test_contract_rejects_missing_columns():
    with pytest.raises(ValueError, match="predicted_points"):
        validate_optimizer_input(base().drop(columns=["predicted_points"]))

def test_normalize_positions_and_numeric_fields():
    df=base(); df["player_id"]=df["player_id"].astype(str)
    out=normalize_optimizer_input(df)
    assert out["position"].tolist()==["GK","MID"]
    assert out["price"].dtype.kind in "fi"
    assert out["predicted_points"].dtype.kind in "fi"
