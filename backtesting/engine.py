from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import pandas as pd
from .leakage import assert_no_lookahead

class BacktestError(ValueError):
    pass

@dataclass(frozen=True)
class BacktestConfig:
    start_gw: int = 1
    end_gw: int | None = None
    gw_column: str = "GW"
    player_id_column: str = "player_id"
    target_column: str = "total_points"

Predictor = Callable[[pd.DataFrame, int], pd.DataFrame]

class BacktestEngine:
    def __init__(self, config: BacktestConfig | None = None):
        self.config = config or BacktestConfig()

    def run(self, historical: pd.DataFrame, predictor: Predictor, *, actuals=None) -> pd.DataFrame:
        required = {self.config.gw_column, self.config.player_id_column}
        missing = required - set(historical.columns)
        if missing:
            raise BacktestError("historical frame missing columns: " + ", ".join(sorted(missing)))
        if historical.empty:
            raise BacktestError("historical frame is empty")

        data = historical.copy()
        data[self.config.gw_column] = pd.to_numeric(data[self.config.gw_column], errors="coerce")
        data = data.dropna(subset=[self.config.gw_column]).copy()
        data[self.config.gw_column] = data[self.config.gw_column].astype(int)
        last_gw = int(data[self.config.gw_column].max())
        end_gw = self.config.end_gw if self.config.end_gw is not None else last_gw - 1

        if actuals is None:
            if self.config.target_column not in data.columns:
                raise BacktestError(f"historical frame missing target column: {self.config.target_column}")
            actuals = data[[self.config.gw_column, self.config.player_id_column, self.config.target_column]].rename(
                columns={self.config.gw_column:"target_gw", self.config.target_column:"actual_points"}
            )
        else:
            actuals = actuals.copy()

        missing = {"target_gw", self.config.player_id_column, "actual_points"} - set(actuals.columns)
        if missing:
            raise BacktestError("actuals missing columns: " + ", ".join(sorted(missing)))

        actuals["target_gw"] = pd.to_numeric(actuals["target_gw"], errors="coerce")
        actuals = actuals.dropna(subset=["target_gw"]).copy()
        actuals["target_gw"] = actuals["target_gw"].astype(int)

        outputs = []
        for decision_gw in range(self.config.start_gw, end_gw + 1):
            history = data[data[self.config.gw_column] <= decision_gw].copy()
            if history.empty:
                continue
            assert_no_lookahead(history, decision_gw, gw_column=self.config.gw_column)

            pred = predictor(history.copy(), decision_gw)
            required_pred = {self.config.player_id_column, "predicted_points"}
            missing_pred = required_pred - set(pred.columns)
            if missing_pred:
                raise BacktestError("predictor missing columns: " + ", ".join(sorted(missing_pred)))

            pred = pred[[self.config.player_id_column, "predicted_points"]].copy()
            pred["target_gw"] = decision_gw + 1

            # Predictions may be fixture-level (DGW). Aggregate them to the
            # player/Gameweek level before joining the realised player/GW total.
            pred = (
                pred.groupby(
                    ["target_gw", self.config.player_id_column],
                    as_index=False,
                )["predicted_points"]
                .sum()
            )

            target = actuals[actuals["target_gw"] == decision_gw + 1][
                [self.config.player_id_column, "actual_points"]
            ].copy()

            # Historical source is fixture-level, so realised DGW points must
            # also be summed to player/GW before a one-to-one comparison.
            target = (
                target.groupby(self.config.player_id_column, as_index=False)[
                    "actual_points"
                ]
                .sum()
            )

            merged = pred.merge(
                target,
                on=self.config.player_id_column,
                how="inner",
                validate="one_to_one",
            )
            merged.insert(0, "GW", decision_gw)
            outputs.append(merged)

        if not outputs:
            return pd.DataFrame(columns=["GW",self.config.player_id_column,"predicted_points","target_gw","actual_points"])
        return pd.concat(outputs, ignore_index=True)
