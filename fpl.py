import requests
import sqlite3
import time

API_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
PLAYER_URL = "https://fantasy.premierleague.com/api/element-summary/{}/"

print("Henter FPL-data...")

response = requests.get(API_URL)

if response.status_code != 200:
    print("Kunne ikke hente FPL-data.")
    exit()

data = response.json()
players = data["elements"]

print(f"Fant {len(players)} spillere.")
print("Starter historikk...")

# Database
connection = sqlite3.connect("fpl.db")
cursor = connection.cursor()

# Historiske GW-data
cursor.execute("""
CREATE TABLE IF NOT EXISTS player_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER,
    gameweek INTEGER,
    minutes INTEGER,
    points INTEGER,
    goals INTEGER,
    assists INTEGER,
    clean_sheets INTEGER,
    goals_conceded INTEGER,
    bonus INTEGER,
    bps INTEGER,
    influence REAL,
    creativity REAL,
    threat REAL,
    ict_index REAL,
    value REAL,
    transfers_balance INTEGER,
    selected INTEGER
)
""")

# Fjern gammel historikk hvis vi kjører programmet på nytt
cursor.execute("DELETE FROM player_history")

successful = 0
failed = 0

for index, player in enumerate(players, start=1):

    player_id = player["id"]
    name = f'{player["first_name"]} {player["second_name"]}'

    try:
        response = requests.get(PLAYER_URL.format(player_id), timeout=10)

        if response.status_code != 200:
            failed += 1
            continue

        history = response.json()["history"]

        for gw in history:
            cursor.execute("""
            INSERT INTO player_history (
                player_id,
                gameweek,
                minutes,
                points,
                goals,
                assists,
                clean_sheets,
                goals_conceded,
                bonus,
                bps,
                influence,
                creativity,
                threat,
                ict_index,
                value,
                transfers_balance,
                selected
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player_id,
                gw["round"],
                gw["minutes"],
                gw["total_points"],
                gw["goals_scored"],
                gw["assists"],
                gw["clean_sheets"],
                gw["goals_conceded"],
                gw["bonus"],
                gw["bps"],
                float(gw["influence"]),
                float(gw["creativity"]),
                float(gw["threat"]),
                float(gw["ict_index"]),
                gw["value"] / 10,
                gw["transfers_balance"],
                gw["selected"]
            ))

        successful += 1

        if index % 25 == 0:
            print(f"Prosessert {index}/{len(players)} spillere...")

        # Litt pause mellom API-kall
        time.sleep(0.05)

    except Exception as e:
        failed += 1
        print(f"Feil med {name}: {e}")

connection.commit()

# Tell antall historiske rader
cursor.execute("SELECT COUNT(*) FROM player_history")
history_count = cursor.fetchone()[0]

connection.close()

print()
print("================================")
print("HISTORIKK FERDIG")
print("================================")
print(f"Spillere behandlet: {successful}")
print(f"Feilet: {failed}")
print(f"Historiske GW-rader: {history_count}")
print("Database oppdatert!")