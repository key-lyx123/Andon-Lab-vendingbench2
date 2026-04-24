"""
VendingBench2 - Weather Simulation
Generates realistic weather progressions with seasonal patterns.
Weather affects customer foot traffic (and thus sales).
"""
import random
from typing import Dict


# ── season helpers ─────────────────────────────────────────────────────────────

def get_season(month: int) -> str:
    if month in (12, 1, 2):
        return "winter"
    elif month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    return "fall"


def get_weather_probabilities(season: str, previous_weather: str) -> Dict[str, float]:
    """
    Markov-chain weather model: next state probabilities conditioned on season and
    the previous day's weather (persistence bonus of 0.30).
    """
    seasonal_base: Dict[str, Dict[str, float]] = {
        "winter": {"sunny": 0.20, "cloudy": 0.40, "rainy": 0.20, "snowy": 0.20},
        "spring": {"sunny": 0.40, "cloudy": 0.30, "rainy": 0.30, "snowy": 0.00},
        "summer": {"sunny": 0.60, "cloudy": 0.20, "rainy": 0.20, "snowy": 0.00},
        "fall":   {"sunny": 0.30, "cloudy": 0.40, "rainy": 0.30, "snowy": 0.00},
    }
    persistence = 0.30
    probs = seasonal_base[season].copy()
    if previous_weather in probs:
        for k in probs:
            probs[k] *= (1.0 - persistence)
        probs[previous_weather] += persistence
    total = sum(probs.values())
    return {k: v / total for k, v in probs.items()}


def generate_next_weather(month: int, previous_weather: str = "sunny") -> str:
    """Sample next day's weather given the month and previous weather."""
    season = get_season(month)
    probs = get_weather_probabilities(season, previous_weather)
    return random.choices(list(probs.keys()), weights=list(probs.values()))[0]


def get_weather_sales_multiplier(weather: str) -> float:
    """Sales multiplier based on weather (foot-traffic proxy)."""
    return {"sunny": 1.10, "cloudy": 1.00, "rainy": 0.85, "snowy": 0.75}.get(weather, 1.00)
