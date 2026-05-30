import httpx
from tools.search_cache import cache_get, cache_set
from tools.keyvault_tool import get_secret

def search_flights(intent: dict) -> list:
    o  = intent["origin"]
    d  = intent["destination"]
    dt = intent["date"]
    tp = intent.get("time_pref", "any")

    cached = cache_get(o, d, dt, tp)
    if cached:
        print("Cache hit")
        return cached

    api_key = get_secret("serpapi-key")
    params = {
        "engine":        "google_flights",
        "departure_id":  o,
        "arrival_id":    d,
        "outbound_date": dt,
        "currency":      "USD",
        "hl":            "en",
        "api_key":       api_key,
        "type":          "2",
        "adults":        intent.get("passengers", 1)
    }

    resp = httpx.get("https://serpapi.com/search", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    flights = []
    for f in data.get("best_flights", []) + data.get("other_flights", []):
        legs = f.get("flights", [])
        if not legs:
            continue
        first = legs[0]
        flights.append({
            "airline":    first.get("airline", "Unknown"),
            "flight_no":  first.get("flight_number", "N/A"),
            "departure":  first.get("departure_airport", {}).get("time", ""),
            "arrival":    legs[-1].get("arrival_airport", {}).get("time", ""),
            "duration":   str(f.get("total_duration", "")),
            "stops":      len(legs) - 1,
            "price_usd":  float(f.get("price", 0)),
            "booking_token": f.get("booking_token", "")
        })

    if tp and tp != "any":
        flights = _filter_by_time(flights, tp)

    cache_set(o, d, dt, tp, flights)
    return flights

def _filter_by_time(flights, pref):
    bands = {
        "early":     [0,  8],
        "morning":   [8,  12],
        "afternoon": [12, 18],
        "evening":   [18, 24]
    }
    lo, hi = bands.get(pref, [0, 24])
    filtered = []
    for f in flights:
        try:
            hour = int(f["departure"][11:13])
            if lo <= hour < hi:
                filtered.append(f)
        except:
            filtered.append(f)
    return filtered if filtered else flights