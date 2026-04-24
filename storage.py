"""
VendingBench2 - Backroom Storage System
Manages inventory held in the back room before stocking the vending machine.
Also tracks pending deliveries from suppliers.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

from vending_machine import Item


class StorageSystem:
    """
    Back-room inventory for the vending machine operator.

    Items arrive via scheduled deliveries; the operator then moves them
    from storage into the physical vending machine.
    """

    def __init__(self):
        # {item_name: {"item": Item, "quantity": int, "avg_unit_cost": float}}
        self.items: Dict[str, Dict] = {}
        # List of scheduled incoming deliveries
        self.pending_deliveries: List[Dict] = []

    # ── storage mutations ──────────────────────────────────────────────────────

    def add_items(self, name: str, size: str, quantity: int,
                  unit_cost: float, price: float = 0.0) -> float:
        """
        Add items to storage, updating weighted-average cost.
        Returns total cost of this batch (unit_cost * quantity).
        """
        if name not in self.items:
            self.items[name] = {
                "item": Item(name, size, price, unit_cost),
                "quantity": 0,
                "avg_unit_cost": 0.0,
            }
        record = self.items[name]
        new_qty = record["quantity"] + quantity
        if new_qty > 0:
            total_cost = record["avg_unit_cost"] * record["quantity"] + unit_cost * quantity
            record["avg_unit_cost"] = total_cost / new_qty
        record["quantity"] = new_qty
        record["item"].cost = record["avg_unit_cost"]
        return float(unit_cost) * int(quantity)

    def remove_items(self, name: str, quantity: int) -> bool:
        """Remove items when stocking the machine. Returns False if insufficient."""
        if name not in self.items or self.items[name]["quantity"] < quantity:
            return False
        self.items[name]["quantity"] -= quantity
        if self.items[name]["quantity"] == 0:
            del self.items[name]
        return True

    def update_price(self, name: str, new_price: float) -> bool:
        if name not in self.items:
            return False
        self.items[name]["item"].price = new_price
        return True

    # ── delivery scheduling ────────────────────────────────────────────────────

    def schedule_delivery(self, current_time: datetime, items: List[Dict],
                          days_until_delivery: int, supplier: str = "Unknown Supplier",
                          reference: Optional[str] = None) -> datetime:
        """Schedule a delivery to arrive at 06:00 on day+N."""
        arrival = (current_time.replace(hour=6, minute=0, second=0, microsecond=0)
                   + timedelta(days=int(days_until_delivery)))
        self.pending_deliveries.append({
            "arrival_time": arrival,
            "supplier": supplier,
            "items": items,
            "reference": reference,
        })
        return arrival

    def process_arrivals(self, current_time: datetime,
                         on_arrival: Optional[Callable[[str, Optional[str], str], None]] = None) -> float:
        """
        Process all deliveries due by *current_time*.
        Calls *on_arrival(supplier, reference, notice_body)* for each processed delivery.
        Returns total monetary cost of processed deliveries.
        """
        if not self.pending_deliveries:
            return 0.0
        total_cost = 0.0
        remaining = []
        for delivery in self.pending_deliveries:
            if delivery["arrival_time"] <= current_time:
                supplier = delivery.get("supplier", "Supplier")
                ref = delivery.get("reference")
                lines: List[str] = []
                delivery_cost = 0.0
                for it in delivery.get("items", []):
                    name = it.get("name", "")
                    size = it.get("size", "small")
                    qty = int(it.get("quantity", 0))
                    uc = float(it.get("unit_cost", 0.0))
                    if qty <= 0 or not name:
                        continue
                    delivery_cost += self.add_items(name, size, qty, uc)
                    lines.append(f"- {name} ({size}) x{qty} @ ${uc:.2f}")
                total_cost += delivery_cost
                if on_arrival:
                    body_parts = [
                        f"Delivery arrived from {supplier}.",
                        f"Reference: {ref}" if ref else None,
                        f"Arrival: {delivery['arrival_time'].strftime('%Y-%m-%d %H:%M UTC')}",
                        "",
                        "Items received:",
                        *lines,
                        "",
                        f"Total charged: ${delivery_cost:.2f}",
                    ]
                    body = "\n".join(p for p in body_parts if p is not None)
                    on_arrival(supplier, ref, body)
            else:
                remaining.append(delivery)
        self.pending_deliveries = remaining
        return total_cost

    # ── queries ────────────────────────────────────────────────────────────────

    def get_quantity(self, name: str) -> int:
        return self.items.get(name, {}).get("quantity", 0)

    def get_item(self, name: str) -> Optional[Item]:
        return self.items.get(name, {}).get("item")

    def list_all_items(self) -> List[str]:
        return list(self.items.keys())

    def get_total_value(self) -> float:
        return sum(r["quantity"] * r["avg_unit_cost"] for r in self.items.values())

    def is_empty(self) -> bool:
        return not bool(self.items)

    def get_storage_report(self) -> str:
        if self.is_empty():
            return "Storage is currently empty. No items in backroom inventory."
        lines = ["STORAGE INVENTORY REPORT", "=" * 50]
        for name, rec in sorted(self.items.items(),
                                 key=lambda x: (x[1]["item"].size == "small", x[0])):
            item = rec["item"]
            qty = rec["quantity"]
            ac = rec["avg_unit_cost"]
            lines.append(
                f"  [{item.size.upper():5}] {name:20} {qty:3} units @ ${ac:.2f}/unit  "
                f"(Value: ${qty * ac:.2f})"
            )
        lines += [
            "-" * 50,
            f"Total Product Types: {len(self.items)}",
            f"Total Inventory Value: ${self.get_total_value():.2f}",
        ]
        if self.pending_deliveries:
            lines.append(f"Pending Deliveries: {len(self.pending_deliveries)}")
        return "\n".join(lines)

    def __repr__(self):
        return (
            f"StorageSystem({len(self.items)} types, "
            f"${self.get_total_value():.2f} value, "
            f"{len(self.pending_deliveries)} pending deliveries)"
        )
