from playwright.async_api import async_playwright
import asyncio

async def fetch_draftkings_props(event_group_id: int, stat_category: str, sport: str):
    url = f"https://sportsbook.draftkings.com/sites/US-SB/api/v5/eventgroups/{event_group_id}?category={stat_category}&format=json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Visit a real page first to make Playwright fully simulate a user
        await page.goto(f"https://sportsbook.draftkings.com/leagues", timeout=30000)

        # Fetch the raw JSON
        data = await page.evaluate(f"""() => 
            fetch("{url}")
            .then(res => res.json())
        """)

        await browser.close()

        print("DATA HERE:", data)

        # Extract structured props
        props = []
        event_group = data.get("eventGroup", {})
        categories = event_group.get("offerCategories", [])

        for category in categories:
            category_name = category.get("name", "").lower()
            if "player" not in category_name:
                continue


            for subcat in category.get("offerSubcategoryDescriptors", []):
                offers = subcat.get("offerSubcategory", {}).get("offers", [])
                for market in offers:
                    for offer in market:
                        stat = category["name"].replace("Player ", "").strip()
                        for outcome in offer.get("outcomes", []):
                            player = outcome.get("participant") or outcome.get("label")
                            line = outcome.get("line")
                            odds_str = outcome.get("oddsAmerican")

                            if player and line is not None and odds_str:
                                try:
                                    odds = int(odds_str)
                                except ValueError:
                                    odds = None

                                props.append({
                                    "player": player,
                                    "stat": stat,
                                    "line": line,
                                    "odds": odds,
                                    "sportsbook": "DraftKings",
                                    "sport": sport
                                })

        print("PROPS:", props)
        return props
