import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


RAIN_KEYWORDS = (
    "rain",
    "shower",
    "drizzle",
    "thunder",
    "storm",
    "雨",
    "雷",
)


def classify_weather(temperature_c, description, precipitation_mm=0):
    description_text = str(description or "").lower()
    try:
        precipitation = float(precipitation_mm or 0)
    except (TypeError, ValueError):
        precipitation = 0

    if precipitation >= 0.2:
        return "雨天"
    if "nearby" not in description_text and "可能" not in description_text:
        if any(keyword in description_text for keyword in RAIN_KEYWORDS):
            return "雨天"
    if temperature_c is not None and temperature_c >= 29:
        return "熱"
    if temperature_c is not None and temperature_c <= 18:
        return "冷"
    return "普通"


def fetch_current_weather(location="Xitun District, Taichung, Taiwan", timeout=8):
    city = str(location or "Xitun District, Taichung, Taiwan").strip() or "Xitun District, Taichung, Taiwan"
    url = f"https://wttr.in/{quote(city)}?format=j1"
    request = Request(url, headers={"User-Agent": "restaurant-recommender/1.0"})

    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
        return {
            "ok": False,
            "location": city,
            "weather": "普通",
            "temperature_c": None,
            "precipitation_mm": 0,
            "description": "",
            "source": "wttr.in",
            "error": str(error),
        }

    current = (payload.get("current_condition") or [{}])[0]
    nearest_area = (payload.get("nearest_area") or [{}])[0]
    area_name = (nearest_area.get("areaName") or [{}])[0].get("value", city)
    country = (nearest_area.get("country") or [{}])[0].get("value", "")
    description = (current.get("weatherDesc") or [{}])[0].get("value", "")

    try:
        temperature_c = float(current.get("temp_C"))
    except (TypeError, ValueError):
        temperature_c = None
    try:
        precipitation_mm = float(current.get("precipMM") or 0)
    except (TypeError, ValueError):
        precipitation_mm = 0

    return {
        "ok": True,
        "location": f"{area_name}, {country}".strip(", "),
        "weather": classify_weather(temperature_c, description, precipitation_mm),
        "temperature_c": temperature_c,
        "precipitation_mm": precipitation_mm,
        "description": description,
        "source": "wttr.in",
        "error": "",
    }
