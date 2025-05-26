import statistics

def score_lol_chance(avg_stat, line, hit_rate):
    print("📊 EV Scoring Stats:")
    print(f"  avg_stat: {avg_stat}")
    print(f"  line: {line}")
    print(f"  hit_rate: {hit_rate}%")

    score = 0

    # ✅ Check if the average performance is above the line
    if avg_stat > line:
        score += 1

    # ✅ Check if historical hit rate is ≥ 70%
    if hit_rate >= 70:
        score += 1

    return score



def calculate_lol_hit_rate(matches, stat: str, line: float):
    total = 0
    hits = 0

    for series in matches.values():
        map1 = series.get("match1", {})
        map2 = series.get("match2", {})

        if stat not in map1 or stat not in map2:
            continue  # skip incomplete series

        total += 1
        stat_sum = map1[stat] + map2[stat]
        if stat_sum > line:
            hits += 1

    if total == 0:
        return 0.0

    return round(hits / total * 100, 1)


# def calculate_std_dev(matches, stat, maps=2):
#     series_totals = []

#     for series in matches.values():
#         stat_sum = 0
#         map_count = 0

#         for i, match_key in enumerate(["match1", "match2"][:maps]):
#             match_data = series.get(match_key, {})
#             if stat in match_data:
#                 stat_sum += match_data[stat]
#                 map_count += 1

#         if map_count == maps:  # Only use complete series
#             series_totals.append(stat_sum)

#     if len(series_totals) < 2:
#         return 0.0

#     return round(statistics.stdev(series_totals), 2)
