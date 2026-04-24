"""
VendingBench2 - Economic Environment
Simulates customer purchasing behavior using price-elasticity models with
seasonal, weather, and product-variety multipliers.
"""
from __future__ import annotations
import math
from functools import lru_cache
from typing import Dict, Tuple

from vending_machine import Item, VendingMachine
from weather import get_weather_sales_multiplier


# ── LLM-backed price-elasticity estimation ─────────────────────────────────────

def analyze_single_item(item_name: str, item_price: float, item_size: str,
                        quantity: int, context: str = "") -> Tuple[float, float, int]:
    """
    Ask the LLM to estimate price_elasticity, reference_price, and base_daily_sales
    for a single item. Falls back to sensible defaults on any parse error.
    """
    from model_client import call_model

    prompt = f"""You are an economics expert analyzing customer behavior for a vending machine item.

CONTEXT: {context or "Standard office-building vending machine, Chicago IL"}

ITEM:
  Name:            {item_name}
  Current price:   ${item_price:.2f}
  Size:            {item_size}
  Available qty:   {quantity} units

Return ONLY three comma-separated numbers:
  price_elasticity  (−2.0 … −0.1, more negative = more price-sensitive)
  reference_price   (USD, what customers expect to pay)
  base_daily_sales  (integer units/day at reference price; cannot exceed {quantity})

Example: -1.2,2.50,15
"""
    result = call_model(prompt)
    return _parse_elasticity_response(result.get("content", ""), item_price)


def _parse_elasticity_response(text: str, fallback_price: float) -> Tuple[float, float, int]:
    try:
        parts = text.strip().split(",")
        return float(parts[0]), float(parts[1]), int(parts[2])
    except Exception:
        return -1.0, fallback_price, 10


def generate_customer_behavior(vending_slots: Dict) -> Dict[str, Dict]:
    """
    Build a {item_name -> {price_elasticity, reference_price, base_sales}} map
    for all unique items currently in the machine.
    """
    behavior: Dict[str, Dict] = {}
    for slot in vending_slots.values():
        item = slot.get("item")
        if item is None or item.name in behavior:
            continue
        pe, rp, bs = analyze_single_item(item.name, item.price, item.size, slot["quantity"])
        behavior[item.name] = {"price_elasticity": pe, "reference_price": rp, "base_sales": bs}
    return behavior


# ── sales calculation ──────────────────────────────────────────────────────────

def calculate_item_sales(item_name: str, current_price: float, behavior: Dict) -> int:
    """Base sales adjusted for price vs. reference price."""
    if item_name not in behavior:
        return 0
    m = behavior[item_name]
    pct_diff = (current_price - m["reference_price"]) / m["reference_price"]
    adjusted = m["base_sales"] * (1 + m["price_elasticity"] * pct_diff)
    return max(0, int(round(adjusted)))


@lru_cache(maxsize=None)
def calculate_choice_multiplier(num_products: int) -> float:
    """
    Sigmoid-based variety multiplier (optimal at ~10 products).
    Floor: 0.50.
    """
    if num_products == 0:
        return 0.50
    x0, k = 10.0, 0.5
    sigmoid = 1.0 / (1.0 + math.exp(-k * (num_products - x0)))
    if num_products <= x0:
        multiplier = 0.5 + 0.5 * sigmoid
    else:
        multiplier = sigmoid * math.exp(-0.1 * (num_products - x0))
    return max(0.50, multiplier)


@lru_cache(maxsize=None)
def get_month_multiplier(month: int) -> float:
    return {
        1: 0.80, 2: 0.85, 3: 0.95, 4: 1.05, 5: 1.10,
        6: 1.15, 7: 1.20, 8: 1.20, 9: 1.10, 10: 1.00,
        11: 0.90, 12: 0.95,
    }.get(month, 1.00)


@lru_cache(maxsize=None)
def get_day_multiplier(day_of_week: int) -> float:
    """0=Monday … 6=Sunday."""
    return {0: 0.85, 1: 0.95, 2: 1.00, 3: 1.05,
            4: 1.15, 5: 1.25, 6: 1.20}.get(day_of_week, 1.00)


def calculate_item_final_sales(item: Item, behavior: Dict, unique_products: int,
                                weather: str = "cloudy", month: int = 6,
                                day_of_week: int = 2) -> int:
    """Final daily unit sales with all multipliers applied."""
    base = calculate_item_sales(item.name, item.price, behavior)
    return max(0, int(round(
        base
        * calculate_choice_multiplier(unique_products)
        * get_weather_sales_multiplier(weather)
        * get_month_multiplier(month)
        * get_day_multiplier(day_of_week)
    )))


def calculate_total_sales(vending_machine: VendingMachine, weather: str = "cloudy",
                           month: int = 6, day_of_week: int = 2
                           ) -> Tuple[float, float, str]:
    """
    Simulate one day of sales for *vending_machine*.

    Returns:
        (total_revenue, total_cogs, report_string)
    """
    slots = vending_machine.get_slots()
    unique = vending_machine.unique_products()
    behavior = generate_customer_behavior(slots)

    total_revenue = 0.0
    total_cogs = 0.0
    lines = ["DAILY SALES REPORT", "=" * 40]

    for sid, slot in slots.items():
        item = slot.get("item")
        if item is None:
            continue
        units = calculate_item_final_sales(item, behavior, unique, weather, month, day_of_week)
        result = vending_machine.sell_item(sid, units)
        if result is None:
            continue
        sold_item, actual_units = result
        revenue = actual_units * sold_item.price
        cogs = actual_units * sold_item.cost
        total_revenue += revenue
        total_cogs += cogs
        lines.append(
            f"  {sold_item.name:20} sold={actual_units:3}  rev=${revenue:.2f}  cogs=${cogs:.2f}"
        )

    gross_profit = total_revenue - total_cogs
    lines += [
        "=" * 40,
        f"Total Revenue: ${total_revenue:.2f}",
        f"Total COGS:    ${total_cogs:.2f}",
        f"Gross Profit:  ${gross_profit:.2f}",
    ]
    return total_revenue, total_cogs, "\n".join(lines)
