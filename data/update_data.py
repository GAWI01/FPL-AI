import requests
import sqlite3

BASE_URL = "https://fantasy.premierleague.com/api"
DATABASE = "fpl.db"


def get_data(endpoint):
    """Hent data fra FPL API."""
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        raise Exception(
            f"API-feil {response.status_code}: {url}"
        )

    return response.json()


def update_players(cursor, data):
    """Oppdater spillerdata."""

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY,
        first_name TEXT,
        second_name TEXT,
        position INTEGER,
        team_id INTEGER,
        price REAL,
        total_points INTEGER,
        form REAL,
        points_per_game REAL,
        selected_by_percent REAL
    )
    """)

    cursor.execute("DELETE FROM players")

    for player in data["elements"]:
        cursor.execute("""
        INSERT INTO players (
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
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            player["id"],
            player["first_name"],
            player["second_name"],
            player["element_type"],
            player["team"],
            player["now_cost"] / 10,
            player["total_points"],
            float(player["form"]),
            float(player["points_per_game"]),
            float(player["selected_by_percent"])
        ))

    print(f"✓ Spillere oppdatert: {len(data['elements'])}")


def update_fixtures(cursor, fixtures):
    """Oppdater fixtures."""

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fixtures (
        id INTEGER PRIMARY KEY,
        gameweek INTEGER,
        home_team INTEGER,
        away_team INTEGER,
        home_difficulty INTEGER,
        away_difficulty INTEGER
    )
    """)

    cursor.execute("DELETE FROM fixtures")

    for fixture in fixtures:
        cursor.execute("""
        INSERT INTO fixtures (
            id,
            gameweek,
            home_team,
            away_team,
            home_difficulty,
            away_difficulty
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            fixture["id"],
            fixture["event"],
            fixture["team_h"],
            fixture["team_a"],
            fixture["team_h_difficulty"],
            fixture["team_a_difficulty"]
        ))

    print(f"✓ Fixtures oppdatert: {len(fixtures)}")


def main():

    print("=" * 40)
    print("FPL AI — DATA UPDATE")
    print("=" * 40)

    print("\nHenter FPL-data...")

    data = get_data("bootstrap-static/")
    fixtures = get_data("fixtures/")

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    update_players(cursor, data)
    update_fixtures(cursor, fixtures)

    connection.commit()
    connection.close()

    print("\n✓ DATABASE OPPDATERT")
    print("=" * 40)


if __name__ == "__main__":
    main()