import aiohttp

BASE_URL = "https://api.prizepicks.com/projections"
LEAGUE_ID = 7  # NBA

async def fetch_prizepicks_props(league_id=LEAGUE_ID):
    url = f"{BASE_URL}?league_id={league_id}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            # if resp.status != 200:
            #     raise Exception(f"PrizePicks API returned status {resp.status}")

            try:
                data = await resp.json()
            except Exception as e:
                raise Exception(f"Failed to parse JSON: {e}")

            projections = data.get("data", [])
            included = data.get("included", [])

            # Step 1: Build a map of player_id → display_name
            player_map = {
                item["id"]: item["attributes"]["display_name"]
                for item in included
                if item["type"] == "new_player"
            }

            picks = []

            for item in projections:
                if item.get("type") == "projection":
                    attr = item.get("attributes", {})
                    relationships = item.get("relationships", {})

                    stat = attr.get("stat_display_name")
                    line = attr.get("line_score")
                    player_id = relationships.get("new_player", {}).get("data", {}).get("id")

                    if stat and line is not None and player_id:
                        player_name = player_map.get(player_id, "Unknown Player")
                        picks.append((player_name, stat, line))

            return picks
