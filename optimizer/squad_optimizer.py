import pandas as pd
import numpy as np

from scipy.optimize import milp, LinearConstraint, Bounds
from .optimizer_contract import normalize_optimizer_input
from .objective import OptimizerObjectiveConfig, build_objective_column


REQUIRED_COLUMNS = {
    "name",
    "position",
    "team",
    "price",
    "predicted_points",
}

POSITION_LIMITS = {
    "GK": 2,
    "DEF": 5,
    "MID": 5,
    "FWD": 3,
}

MAX_PLAYERS_PER_TEAM = 3


def _validate_players(players):
    """Validate the player data required by the optimizer."""

    if not isinstance(players, pd.DataFrame):
        raise ValueError(
            "players must be a pandas DataFrame"
        )

    missing = REQUIRED_COLUMNS - set(players.columns)

    if missing:
        missing_columns = ", ".join(
            sorted(missing)
        )

        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )


def _normalize_positions(players):
    """
    Normalize FPL position names.

    Test data may use GK.
    Real FPL data uses GKP.

    Internally the optimizer uses GK.
    """

    players = players.copy()

    players["position"] = (
        players["position"]
        .astype(str)
        .str.strip()
        .str.upper()
        .replace(
            {
                "GKP": "GK",
            }
        )
    )

    return players


def _prepare_players(players):
    """Prepare and validate optimizer input data."""

    players = _normalize_positions(
        players
    )

    players["price"] = pd.to_numeric(
        players["price"],
        errors="coerce",
    )

    players["predicted_points"] = pd.to_numeric(
        players["predicted_points"],
        errors="coerce",
    )

    if players["price"].isna().any():
        raise ValueError(
            "price contains invalid values"
        )

    if players["predicted_points"].isna().any():
        raise ValueError(
            "predicted_points contains invalid values"
        )

    return players


def _build_constraints(players, budget):
    """
    Build all constraints for the FPL squad.

    Every player is represented by one binary variable:
        1 = selected
        0 = not selected
    """

    n = len(players)

    constraints = []

    # ------------------------------------------------------------
    # Squad size
    # ------------------------------------------------------------

    constraints.append(
        LinearConstraint(
            np.ones(n),
            15,
            15,
        )
    )

    # ------------------------------------------------------------
    # Position requirements
    # ------------------------------------------------------------

    for position, required in POSITION_LIMITS.items():

        mask = (
            players["position"] == position
        ).astype(float).to_numpy()

        constraints.append(
            LinearConstraint(
                mask,
                required,
                required,
            )
        )

    # ------------------------------------------------------------
    # Maximum three players per club
    # ------------------------------------------------------------

    for team in players["team"].dropna().unique():

        mask = (
            players["team"] == team
        ).astype(float).to_numpy()

        constraints.append(
            LinearConstraint(
                mask,
                0,
                MAX_PLAYERS_PER_TEAM,
            )
        )

    # ------------------------------------------------------------
    # Budget
    # ------------------------------------------------------------

    prices = players["price"].to_numpy(
        dtype=float
    )

    constraints.append(
        LinearConstraint(
            prices,
            0,
            budget,
        )
    )

    return constraints


def optimize_squad(
    players,
    budget=100.0,
    *,
    objective_config=None,
):
    """
    Select the optimal valid 15-player FPL squad.

    Constraints:
    - 15 players
    - 2 goalkeepers
    - 5 defenders
    - 5 midfielders
    - 3 forwards
    - Maximum 3 players per club
    - Total cost <= budget

    Objective:
    Maximize predicted_points.
    """

    if budget <= 0:
        raise ValueError(
            "budget must be greater than 0"
        )

    players = normalize_optimizer_input(players)

    if budget <= 0:
        raise ValueError(
            "budget must be greater than 0"
        )

    # ------------------------------------------------------------
    # Check position availability
    # ------------------------------------------------------------

    for position, required in POSITION_LIMITS.items():

        available = (
            players["position"] == position
        ).sum()

        if available < required:
            raise ValueError(
                f"Not enough valid players for position {position}"
            )

    # ------------------------------------------------------------
    # Build optimization problem
    # ------------------------------------------------------------

    n = len(players)

    players = build_objective_column(
        players,
        objective_config or OptimizerObjectiveConfig(),
    )

    predicted_points = players[
        "optimization_score"
    ].to_numpy(
        dtype=float
    )

    # scipy.optimize.milp minimizes.
    # Negating points converts maximization
    # into minimization.
    objective = -predicted_points

    integrality = np.ones(n)

    lower_bounds = np.zeros(n)

    upper_bounds = np.ones(n)

    constraints = _build_constraints(
        players,
        budget,
    )

    # ------------------------------------------------------------
    # Solve
    # ------------------------------------------------------------

    result = milp(
        c=objective,
        integrality=integrality,
        bounds=Bounds(
            lower_bounds,
            upper_bounds,
        ),
        constraints=constraints,
        options={
            "disp": False,
        },
    )

    # ------------------------------------------------------------
    # Handle solver failure
    # ------------------------------------------------------------

    if not result.success:

        message = (
            result.message
            if result.message
            else "No feasible squad found"
        )

        raise ValueError(
            "Optimizer could not find a valid squad: "
            f"{message}"
        )

    # ------------------------------------------------------------
    # Extract selected players
    # ------------------------------------------------------------

    selected_mask = (
        result.x >= 0.5
    )

    selected = players.loc[
        selected_mask
    ].copy()

    selected = selected.reset_index(
        drop=True
    )

    # ------------------------------------------------------------
    # Final validation
    # ------------------------------------------------------------

    if len(selected) != 15:
        raise ValueError(
            "Optimizer did not produce exactly 15 players"
        )

    expected_positions = {
        "GK": 2,
        "DEF": 5,
        "MID": 5,
        "FWD": 3,
    }

    position_counts = (
        selected["position"]
        .value_counts()
        .to_dict()
    )

    if position_counts != expected_positions:
        raise ValueError(
            "Optimizer produced an invalid position structure"
        )

    team_counts = (
        selected["team"]
        .value_counts()
    )

    if (
        team_counts
        > MAX_PLAYERS_PER_TEAM
    ).any():

        raise ValueError(
            "Squad exceeds maximum three players from one team"
        )

    total_cost = selected[
        "price"
    ].sum()

    if total_cost > budget + 1e-9:
        raise ValueError(
            f"Squad exceeds budget: "
            f"{total_cost:.1f} > {budget:.1f}"
        )

    return selected.drop(columns=["optimization_score"], errors="ignore")


def optimize_from_predictions(
    csv_path,
    budget=100.0,
):
    """
    Load predictions from a CSV file
    and optimize the squad.
    """

    players = pd.read_csv(
        csv_path
    )

    return optimize_squad(
        players,
        budget=budget,
    )