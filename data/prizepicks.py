import aiohttp

BASE_URL = "https://api.prizepicks.com/projections?per_page=250&state_code=CA"

async def fetch_prizepicks_props():
    url = f"{BASE_URL}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            try:
                data = await resp.json()
            except Exception as e:
                raise Exception(f"Failed to parse JSON: {e}")

            projections = data.get("data", [])
            included = data.get("included", [])

            # player_id → display_name
            player_map = {
                item["id"]: item["attributes"]["display_name"]
                for item in included
                if item["type"] == "new_player"
            }

            # league_id → league_name
            league_map = {
                item["id"]: item["attributes"]["name"]
                for item in included
                if item["type"] == "league"
            }

            picks = []

            for item in projections:
                if item.get("type") != "projection":
                    continue

                attr = item.get("attributes", {})
                relationships = item.get("relationships", {})

                stat = attr.get("stat_display_name")
                line = attr.get("line_score")
                description = attr.get("description", "").strip()
                if "maps 1-2" not in description.lower():
                    continue  # Skip non-Maps 1–2 props

                full_stat = f"{stat} ({description})" if description else stat

                player_id = relationships.get("new_player", {}).get("data", {}).get("id")
                league_id = relationships.get("league", {}).get("data", {}).get("id")
                league_name = league_map.get(league_id, "")

                if league_name != "LoL":
                    continue

                if stat and line is not None and player_id:
                    player_name = player_map.get(player_id, "Unknown Player")
                    picks.append({
                        "player": player_name,
                        "stat": full_stat,
                        "line": line,
                        "odds": None,
                        "sportsbook": "PrizePicks",
                        "sport": "LoL"
                    })

            return picks

def compareLoLChance():
    # CHECKS TODO:
    # 1. avg kills/assists are above line
    # 2. prop hit rate
    # 3. standard deviation
    # 4. winrate
    # 5. map count
    

    # 1. avg kills/assists are above line
    # code goes here
    
    # 2. prop hit rate
    # 3. standard deviation
    # 4. winrate
    # 5. map count
    
     
    pass
    return 