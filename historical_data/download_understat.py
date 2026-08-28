import requests
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data"

SEASONS = [
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24",
    "2024-25",
]

OUTPUT_DIR = Path("historical_data")


def download_file(url, destination):
    response = requests.get(url, timeout=120)

    if response.status_code != 200:
        print(f"  ✗ {response.status_code}: {url}")
        return False

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)

    print(f"  ✓ {destination}")
    return True


def main():

    print("=" * 65)
    print("FPL AI — UNDERSTAT DATA DOWNLOADER")
    print("=" * 65)

    for season in SEASONS:

        print()
        print(f"--- Sesong {season} ---")

        season_dir = OUTPUT_DIR / season
        understat_dir = season_dir / "understat"

        # Oversikt over Understat-spillere
        player_url = (
            f"{BASE_URL}/{season}/understat/understat_player.csv"
        )

        # Kobling mellom Understat-ID og FPL-ID
        id_url = (
            f"{BASE_URL}/{season}/understat/id_dict.csv"
        )

        download_file(
            player_url,
            understat_dir / "understat_player.csv"
        )

        download_file(
            id_url,
            understat_dir / "id_dict.csv"
        )

    print()
    print("=" * 65)
    print("UNDERSTAT-DATA FERDIG")
    print("=" * 65)


if __name__ == "__main__":
    main()