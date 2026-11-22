"""The statistics answers in the shape the page shows. No GTK."""
MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]


def years(stats):
    """[(year, km, [(month index 1–12, km)])], newest year first."""
    out = []
    for entry in (stats or {}).get("yearlyStats") or []:
        months = entry.get("monthlyDistanceKm") or {}
        out.append((int(entry.get("year")), entry.get("totalDistanceKm") or 0,
                    [(i + 1, months.get(name) or 0) for i, name in enumerate(MONTHS)]))
    return sorted(out, key=lambda item: item[0], reverse=True)


def totals(stats):
    stats = stats or {}
    return {"distance": stats.get("totalDistanceKm") or 0,
            "points": stats.get("totalPointsTracked") or 0,
            "countries": stats.get("totalCountriesVisited") or 0,
            "cities": stats.get("totalCitiesVisited") or 0}


def countries(body):
    return sorted(c.get("name") or c.get("iso_a3") or "?"
                  for c in (body or {}).get("countries") or [])


def cities(body):
    """[(country, [city names by points, most first])]."""
    out = []
    for entry in (body or {}).get("data") or []:
        names = [c.get("city") for c in sorted(entry.get("cities") or [],
                                               key=lambda c: -(c.get("points") or 0))
                 if c.get("city")]
        out.append((entry.get("country") or "?", names))
    return sorted(out)
