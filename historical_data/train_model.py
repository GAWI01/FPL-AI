import pandas as pd
import numpy as np
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib

from feature_contract import CATEGORICAL_COLUMNS, FEATURE_COLUMNS, NUMERIC_COLUMNS, build_feature_row


BASE_DIR = Path("historical_data")

TRAIN_SEASONS = [
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24",
]

TEST_SEASON = "2024-25"


FEATURES = list(FEATURE_COLUMNS)


def load_season(season):

    file = BASE_DIR / season / "features.csv"

    print(f"Leser {season}...")

    df = pd.read_csv(file)

    df["season"] = season

    return df


def prepare_data(df):

    # Sorter kronologisk per spiller
    df = df.sort_values(
        ["player_id", "GW"]
    ).copy()

    # Neste gameweek sine poeng
    df["target"] = (
        df.groupby("player_id")["total_points"]
        .shift(-1)
    )

    # Fjern siste GW for hver spiller
    df = df.dropna(
        subset=["target"]
    ).copy()

    # Numeriske features
    numeric_features = [
        "price",
        "was_home",
        "points_last_3",
        "points_last_5",
        "points_avg_5",
        "minutes_last_5",
        "starts_last_5",
        "goals_last_5",
        "assists_last_5",
        "bps_avg_5",
        "influence_avg_5",
        "creativity_avg_5",
        "threat_avg_5",
        "ict_index_avg_5",
        "form_5",
        "opponent_team",
    ]

    # Konverter numeriske kolonner
    for col in numeric_features:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    return df


def main():

    print("=" * 65)
    print("FPL AI — ML TRAINING V1")
    print("=" * 65)

    print()
    print("LASTER DATA")
    print("-" * 65)

    train_frames = []

    for season in TRAIN_SEASONS:

        df = load_season(season)

        df = prepare_data(df)

        train_frames.append(df)

        print(
            f"  {season}: {len(df)} rader"
        )

    train = pd.concat(
        train_frames,
        ignore_index=True
    )

    print()
    print(
        f"TRAIN TOTAL: {len(train)} rader"
    )

    # Test
    test = load_season(TEST_SEASON)

    test = prepare_data(test)

    print(
        f"TEST TOTAL:  {len(test)} rader"
    )

    # ---------------------------------------------------------
    # FEATURES
    # ---------------------------------------------------------

    X_train = pd.DataFrame(
        [build_feature_row(row) for _, row in train.iterrows()],
        columns=FEATURES,
    )
    y_train = train["target"].copy()

    X_test = pd.DataFrame(
        [build_feature_row(row) for _, row in test.iterrows()],
        columns=FEATURES,
    )
    y_test = test["target"].copy()

    categorical_features = list(CATEGORICAL_COLUMNS)
    numeric_features = list(NUMERIC_COLUMNS)

    # ---------------------------------------------------------
    # PREPROCESSING
    # ---------------------------------------------------------

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                categorical_features
            ),
            (
                "numeric",
                "passthrough",
                numeric_features
            )
        ]
    )

    # ---------------------------------------------------------
    # MODEL
    # ---------------------------------------------------------

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=10,
        random_state=42,
        n_jobs=-1
    )

    pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor
            ),
            (
                "model",
                model
            )
        ]
    )

    print()
    print("TRENER RANDOM FOREST...")
    print("-" * 65)

    pipeline.fit(
        X_train,
        y_train
    )

    print("✓ Modell trent")

    # ---------------------------------------------------------
    # EVALUATION
    # ---------------------------------------------------------

    predictions = pipeline.predict(
        X_test
    )

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions
        )
    )

    r2 = r2_score(
        y_test,
        predictions
    )

    print()
    print("=" * 65)
    print("MODEL EVALUERING")
    print("=" * 65)

    print(
        f"MAE:  {mae:.3f}"
    )

    print(
        f"RMSE: {rmse:.3f}"
    )

    print(
        f"R²:   {r2:.3f}"
    )

    # ---------------------------------------------------------
    # EKSEMPLER
    # ---------------------------------------------------------

    results = test[
        [
            "name",
            "position",
            "GW",
            "total_points"
        ]
    ].copy()

    results["predicted"] = predictions

    results["error"] = (
        results["predicted"]
        - results["total_points"]
    )

    results = results.sort_values(
        "predicted",
        ascending=False
    )

    print()
    print("=" * 65)
    print("TOP 20 PREDIKSJONER")
    print("=" * 65)

    for _, row in results.head(20).iterrows():

        print(
            f"{row['name']:<30} "
            f"GW {int(row['GW']):2d} "
            f"Actual {row['total_points']:4.1f} "
            f"Pred {row['predicted']:5.2f}"
        )

    # ---------------------------------------------------------
    # SAVE MODEL
    # ---------------------------------------------------------

    output = Path(
        "models/fpl_model_v1.pkl"
    )

    joblib.dump(
        pipeline,
        output
    )

    print()
    print(
        f"✓ Modell lagret: {output}"
    )

    print()
    print("=" * 65)
    print("ML TRAINING FERDIG")
    print("=" * 65)


if __name__ == "__main__":
    main()
