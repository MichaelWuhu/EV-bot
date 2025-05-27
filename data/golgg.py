import aiohttp
from bs4 import BeautifulSoup
import re
from collections import defaultdict

async def get_player_id_from_name(player_name: str, season="S15", split="Spring", tournament="ALL"):
    url = f"https://gol.gg/players/list/season-{season}/split-{split}/tournament-{tournament}/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception("Failed to fetch player list page")
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")
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


async def fetch_player_last10_avg_from_golgg(player_id: int, season="S15", split="Spring", tournament="ALL"):
    url = f"https://gol.gg/players/player-matchlist/{player_id}/season-{season}/split-{split}/tournament-{tournament}/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch page: {url}")
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="table_list")
    if not table:
        raise Exception("Match table not found.")

    rows = table.find_all("tr")[1:]

    raw_matches = defaultdict(list)
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 7:
            continue

        try:
            kda = cols[2].text.strip()
            opponent = cols[6].text.strip()
            kills, deaths, assists = map(int, kda.split("/"))
        except Exception:
            continue

        raw_matches[opponent].append({
            "kills": kills,
            "assists": assists
        })

    matches = defaultdict(lambda: defaultdict(dict))
    for opponent, maps in raw_matches.items():
        ordered_maps = maps[::-1]
        for i, map_stats in enumerate(ordered_maps, start=1):
            matches[opponent][f"match{i}"] = map_stats

    limited_matches = dict(list(matches.items())[:10])
    games = [match for series in limited_matches.values() for match in series.values()]

    if not games:
        raise Exception("No valid game data found.")

    avg_kills = round(sum(g["kills"] for g in games) / len(games), 2)
    avg_assists = round(sum(g["assists"] for g in games) / len(games), 2)

    return {
        "player_id": player_id,
        "avg_kills": avg_kills,
        "avg_assists": avg_assists,
        "matches": limited_matches
    }
