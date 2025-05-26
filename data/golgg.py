import requests
from bs4 import BeautifulSoup
import re
from collections import defaultdict


def get_player_id_from_name(player_name: str, season="S15", split="Spring", tournament="ALL"):
    url = f"https://gol.gg/players/list/season-{season}/split-{split}/tournament-{tournament}/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception("Failed to fetch player list page")

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="table_list")
    if not table:
        raise Exception("Player table not found")

    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if not cols:
            continue

        link = cols[0].find("a")
        if not link:
            continue
        
        name = link.text.strip()
        normalized_name = re.sub(r'[^a-zA-Z0-9]', '', name.lower().strip())
        normalized_player = re.sub(r'[^a-zA-Z0-9]', '', player_name.lower().strip())

        if normalized_name == normalized_player:
            href = link["href"]
            match = re.search(r"/player-stats/(\d+)", href)
            if match:
                return int(match.group(1))

    raise Exception(f"Player '{player_name}' not found")


def fetch_player_last10_avg_from_golgg(player_id: int, season="S15", split="Spring", tournament="ALL"):
    url = f"https://gol.gg/players/player-matchlist/{player_id}/season-{season}/split-{split}/tournament-{tournament}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch page: {url}")

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="table_list")
    if not table:
        raise Exception("Match table not found.")

    rows = table.find_all("tr")[1:]  # skip header
    rows = rows[:10][::-1]

    games = []
    matches = defaultdict(lambda: defaultdict(dict))
    match_counters = defaultdict(int)

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 7:
            continue

        try:
            result = cols[1].text.strip()
            kda = cols[2].text.strip()
            opponent = cols[6].text.strip()

            kills, deaths, assists = map(int, kda.split("/"))
        except Exception:
            continue

        games.append({
            "kills": kills,
            "assists": assists,
            "win": result == "Victory"
        })

        # print("matches:", matches)
        print("opponent:", opponent)

        match_number = match_counters[opponent] + 1
        matches[opponent][f"match{match_number}"] = {
            "kills": kills,
            "assists": assists
        }
        
        match_counters[opponent] += 1

        if len(games) >= 10:
            break

    if not games:
        raise Exception("No valid game data found.")

    avg_kills = round(sum(g["kills"] for g in games) / len(games), 2)
    avg_assists = round(sum(g["assists"] for g in games) / len(games), 2)
    winrate = round(sum(1 for g in games if g["win"]) / len(games) * 100, 1)

    return {
        "player_id": player_id,
        "avg_kills": avg_kills,
        "avg_assists": avg_assists,
        "winrate": winrate,
        "matches": matches
    }
