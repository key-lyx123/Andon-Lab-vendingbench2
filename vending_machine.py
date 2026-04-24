"""
VendingBench2 - Vending Machine Physical Simulation
Models a 4-row x 3-slot vending machine with small/large item slots.
Rows 0-1: small items (max 10/slot), Rows 2-3: large items (max 6/slot)
"""


class Item:
    def __init__(self, name: str, size: str, price: float, cost: float):
        self.name = name
        self.size = size   # 'small' or 'large'
        self.price = price # selling price
        self.cost = cost   # purchase cost from supplier

    def __repr__(self):
        return f"Item({self.name}, {self.size}, price=${self.price:.2f}, cost=${self.cost:.2f})"


class VendingMachine:
    """
    Simulates a physical vending machine with 12 slots (4 rows x 3 columns).
    Rows 0-1 hold small items (capacity 10 each).
    Rows 2-3 hold large items (capacity 6 each).
    """
    def __init__(self):
        self.slots = {}
        for row in range(4):
            for col in range(3):
                slot_id = f"{row}-{col}"
                self.slots[slot_id] = {
                    'item': None,
                    'quantity': 0,
                    'max_capacity': 10 if row < 2 else 6,
                    'size_type': 'small' if row < 2 else 'large',
                }

    # ── query helpers ──────────────────────────────────────────────────────────

    def get_slots(self) -> dict:
        return self.slots

    def get_slot(self, slot_id: str) -> dict | None:
        return self.slots.get(slot_id)

    def get_available_slots(self, size_type: str) -> list[str]:
        """Return slot IDs that can accept more items of the given size."""
        return [
            sid for sid, s in self.slots.items()
            if s['size_type'] == size_type
            and s['quantity'] < s['max_capacity']
            and (s['item'] is None or True)  # allow stacking same item
        ]

    def total_items(self) -> int:
        return sum(s['quantity'] for s in self.slots.values())

    def unique_products(self) -> int:
        return len({s['item'].name for s in self.slots.values() if s['item']})

    # ── mutation helpers ───────────────────────────────────────────────────────

    def can_stock_item(self, slot_id: str, item: Item) -> bool:
        if slot_id not in self.slots:
            return False
        slot = self.slots[slot_id]
        if slot['size_type'] != item.size:
            return False
        if slot['item'] is not None and slot['item'].name != item.name:
            return False  # slot already has different item
        return slot['quantity'] < slot['max_capacity']

    def stock_item(self, slot_id: str, item: Item, quantity: int) -> bool:
        """Stock *quantity* units of *item* into *slot_id*. Returns True on success."""
        if not self.can_stock_item(slot_id, item):
            return False
        slot = self.slots[slot_id]
        actual = min(quantity, slot['max_capacity'] - slot['quantity'])
        slot['item'] = item
        slot['quantity'] += actual
        return True

    def sell_item(self, slot_id: str, quantity: int = 1) -> tuple[Item, int] | None:
        """
        Sell up to *quantity* items from *slot_id*.
        Returns (item, units_sold) or None if slot is empty.
        """
        if slot_id not in self.slots:
            return None
        slot = self.slots[slot_id]
        if slot['quantity'] <= 0 or slot['item'] is None:
            return None
        sold = min(quantity, slot['quantity'])
        slot['quantity'] -= sold
        item = slot['item']
        if slot['quantity'] == 0:
            slot['item'] = None
        return item, sold

    def update_price(self, item_name: str, new_price: float) -> bool:
        """Update the selling price for all slots holding *item_name*."""
        updated = False
        for slot in self.slots.values():
            if slot['item'] and slot['item'].name == item_name:
                slot['item'].price = new_price
                updated = True
        return updated

    # ── reporting ──────────────────────────────────────────────────────────────

    def get_inventory_report(self) -> str:
        lines = ["VENDING MACHINE INVENTORY", "=" * 50]
        for sid, slot in sorted(self.slots.items()):
            if slot['item']:
                lines.append(
                    f"  [{sid}] {slot['item'].name:20} qty={slot['quantity']:2}  "
                    f"price=${slot['item'].price:.2f}  ({slot['size_type']})"
                )
            else:
                lines.append(f"  [{sid}] {'EMPTY':20} ({slot['size_type']})")
        lines.append(
            f"\nTotal slots: 12  |  Stocked: {sum(1 for s in self.slots.values() if s['item'])}  |  "
            f"Items: {self.total_items()}"
        )
        return "\n".join(lines)

    def print_machine(self):
        """Print ASCII diagram of the vending machine."""
        print("┌─────────── VENDING MACHINE ───────────┐")
        for row in range(4):
            if row == 0:
                print("│         SMALL ITEMS (rows 0-1)        │")
                print("│  ┌─────────┬─────────┬─────────┐      │")
            elif row == 2:
                print("│  └─────────┴─────────┴─────────┘      │")
                print("│         LARGE ITEMS (rows 2-3)        │")
                print("│  ┌─────────┬─────────┬─────────┐      │")
            row_str = "│  │"
            for col in range(3):
                sid = f"{row}-{col}"
                s = self.slots[sid]
                if s['item']:
                    cell = f"{s['item'].name[:5]}({s['quantity']})"
                else:
                    cell = "EMPTY"
                row_str += f"{cell:^9}│"
            print(row_str + "  │")
        print("│  └─────────┴─────────┴─────────┘      │")
        print("└───────────────────────────────────────┘")
