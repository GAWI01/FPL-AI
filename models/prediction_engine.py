import sqlite3

DATABASE = "fpl.db"

RECENT_GWS = 5
FUTURE_GWS = 5


def get_players():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            first_name,
            second_name,
            position,
            team_id,
            price,
            total_points,
            form,
            points_per_game,
            selected_by_percent
        FROM players
    """)

    players = cursor.fetchall()
    connection.close()

    return players


def get_history(player_id):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            gameweek,
            minutes,
            points,
            goals,
            assists,
            clean_sheets,
            bonus,
            bps,
            influence,
            creativity,
            threat,
            ict_index
        FROM player_history
        WHERE player_id = ?
        ORDER BY gameweek DESC
        LIMIT ?
    """, (player_id, RECENT_GWS))

    history = cursor.fetchall()
    connection.close()

    return history


def get_fixtures(team_id):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            gameweek,
            home_team,
            away_team,
            home_difficulty,
            away_difficulty
        FROM fixtures
        WHERE
            (home_team = ? OR away_team = ?)
            AND gameweek IS NOT NULL
        ORDER BY gameweek ASC
    """, (team_id, team_id))

    fixtures = cursor.fetchall()
    connection.close()

    return fixtures


def weighted_average(values):
    if not values:
        return 0

    weights = list(range(len(values), 0, -1))

    total = sum(
        value * weight
        for value, weight in zip(values, weights)
    )

    weight_sum = sum(weights)

    return total / weight_sum


def calculate_fixture_score(team_id):
    """
    Beregner hvor gode de neste kampene er.

    FPL difficulty:
    1 = lett
    5 = vanskelig

    Vi konverterer dette til en score hvor
    høyere = bedre fixture.
    """

    fixtures = get_fixtures(team_id)

    if not fixtures:
        return {
            "fixture_score": 1.0,
            "average_difficulty": 3.0,
            "fixtures_used": 0
        }

    # Kun fremtidige / nærmeste fixtures
    upcoming = fixtures[:FUTURE_GWS]

    scores = []

    for fixture in upcoming:

        (
            gameweek,
            home_team,
            away_team,
            home_difficulty,
            away_difficulty
        ) = fixture

        if home_team == team_id:
            difficulty = home_difficulty
        else:
            difficulty = away_difficulty

        # Difficulty 1 → 1.30
        # Difficulty 3 → 1.00
        # Difficulty 5 → 0.70

        fixture_multiplier = 1.30 - (
            (difficulty - 1) * 0.15
        )

        scores.append(fixture_multiplier)

    average_multiplier = sum(scores) / len(scores)

    average_difficulty = sum(
        (
            fixture[3]
            if fixture[1] == team_id
            else fixture[4]
        )
        for fixture in upcoming
    ) / len(upcoming)

    return {
        "fixture_score": average_multiplier,
        "average_difficulty": average_difficulty,
        "fixtures_used": len(upcoming)
    }


def calculate_player_score(player, history):
    (
        player_id,
        first_name,
        second_name,
        position,
        team_id,
        price,
        total_points,
        form,
        points_per_game,
        ownership
    ) = player

    if not history:
        return None

    # =========================
    # RECENT PERFORMANCE
    # =========================

    minutes = weighted_average([
        row[1] for row in history
    ])

    points = weighted_average([
        row[2] for row in history
    ])

    goals = weighted_average([
        row[3] for row in history
    ])

    assists = weighted_average([
        row[4] for row in history
    ])

    bonus = weighted_average([
        row[6] for row in history
    ])

    bps = weighted_average([
        row[7] for row in history
    ])

    influence = weighted_average([
        row[8] for row in history
    ])

    creativity = weighted_average([
        row[9] for row in history
    ])

    threat = weighted_average([
        row[10] for row in history
    ])

    ict = weighted_average([
        row[11] for row in history
    ])

    # =========================
    # MINUTES
    # =========================

    minutes_factor = min(minutes / 90, 1)

    # =========================
    # ATTACKING PERFORMANCE
    # =========================

    attacking_score = (
        goals * 2.0
        + assists * 1.5
        + threat * 0.015
        + creativity * 0.01
    )

    # =========================
    # GENERAL PERFORMANCE
    # =========================

    performance_score = (
        points * 0.8
        + bonus * 0.8
        + bps * 0.01
        + influence * 0.01
        + ict * 0.01
    )

    # =========================
    # VALUE
    # =========================

    value_score = 0

    if price > 0:
        value_score = points_per_game / price

    # =========================
    # BASE SCORE
    # =========================

    base_score = (
        points * 0.9
        + attacking_score
        + performance_score
        + float(form) * 0.4
        + value_score * 2
    )

    # =========================
    # FIXTURES
    # =========================

    fixture_data = calculate_fixture_score(team_id)

    fixture_multiplier = fixture_data["fixture_score"]

    # Fixtures påvirker forventet output
    adjusted_score = base_score * fixture_multiplier

    # =========================
    # MINUTES
    # =========================

    adjusted_score *= (
        0.5 + minutes_factor * 0.5
    )

    return {
        "id": player_id,
        "name": f"{first_name} {second_name}",
        "position": position,
        "team_id": team_id,
        "price": price,
        "form": form,
        "ppg": points_per_game,
        "minutes": minutes,
        "goals": goals,
        "assists": assists,
        "fixture_score": fixture_multiplier,
        "average_difficulty": fixture_data["average_difficulty"],
        "fixtures_used": fixture_data["fixtures_used"],
        "base_score": base_score,
        "score": adjusted_score
    }


def main():

    print("=" * 75)
    print("FPL AI — PREDICTION ENGINE V2")
    print("=" * 75)

    players = get_players()

    predictions = []

    for player in players:

        history = get_history(player[0])

        result = calculate_player_score(
            player,
            history
        )

        if result:
            predictions.append(result)

    predictions.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    print()
    print("TOP 30 — FIXTURE ADJUSTED")
    print("-" * 75)

    for i, player in enumerate(
        predictions[:30],
        start=1
    ):

        print(
            f"{i:2}. "
            f"{player['name']:<28} "
            f"£{player['price']:<4} "
            f"Form {player['form']:>4} "
            f"FDR {player['average_difficulty']:.1f} "
            f"xP {player['score']:>6.2f}"
        )

    print()
    print("=" * 75)
    print(f"Spillere analysert: {len(predictions)}")
    print("=" * 75)


if __name__ == "__main__":
    main()