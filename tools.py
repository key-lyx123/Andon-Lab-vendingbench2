"""
VendingBench2 - Agent Tools
All tools the primary (operator) agent can call.
"""
from datetime import timedelta
import json
from typing import Any


# ── tool implementations ───────────────────────────────────────────────────────

def wait_for_next_day(simulation_ref) -> str:
    current = simulation_ref.get_current_time()
    next_6am = (current.replace(hour=6, minute=0, second=0, microsecond=0)
                + timedelta(days=1))
    simulation_ref.current_time = next_6am
    return f"Advanced to {next_6am.strftime('%Y-%m-%d %H:%M UTC')}"


def send_email(simulation_ref, recipient: str, subject: str, body: str) -> str:
    eid = simulation_ref.email_system.send_email(
        recipient=recipient, subject=subject, body=body, email_type="order"
    )
    simulation_ref.db.log_action(
        simulation_ref.run_id, simulation_ref.current_time,
        simulation_ref.days_passed, "send_email",
        f"to={recipient} subject={subject}", simulation_ref.model_name
    )
    return f"Email sent to {recipient} (ID: {eid})"


def read_email(simulation_ref) -> str:
    result = simulation_ref.email_system.get_unread_emails_for_agent()
    simulation_ref.db.log_action(
        simulation_ref.run_id, simulation_ref.current_time,
        simulation_ref.days_passed, "read_email", "", simulation_ref.model_name
    )
    return result


def check_storage_quantities(simulation_ref) -> str:
    return simulation_ref.storage.get_storage_report()


def check_vending_machine(simulation_ref) -> str:
    return simulation_ref.vending_machine.get_inventory_report()


def stock_vending_machine(simulation_ref, item_name: str, quantity: int,
                           slot_id: str = "") -> str:
    """
    Move *quantity* units of *item_name* from back-room storage into the
    vending machine. If *slot_id* is given, stock that specific slot;
    otherwise find the first compatible slot automatically.
    """
    storage = simulation_ref.storage
    machine = simulation_ref.vending_machine

    item = storage.get_item(item_name)
    if item is None:
        return f"Error: '{item_name}' not found in storage."

    available = storage.get_quantity(item_name)
    qty = min(quantity, available)
    if qty <= 0:
        return f"Error: no '{item_name}' in storage."

    # Determine target slot
    if slot_id:
        target_slots = [slot_id] if machine.can_stock_item(slot_id, item) else []
    else:
        target_slots = machine.get_available_slots(item.size)

    if not target_slots:
        return f"Error: no available slot for '{item_name}' (size={item.size})."

    # Try to stock into the first valid slot
    for sid in target_slots:
        if machine.stock_item(sid, item, qty):
            storage.remove_items(item_name, qty)
            simulation_ref.db.log_action(
                simulation_ref.run_id, simulation_ref.current_time,
                simulation_ref.days_passed, "stock_machine",
                f"item={item_name} qty={qty} slot={sid}", simulation_ref.model_name
            )
            return f"Stocked {qty} x '{item_name}' into slot {sid}."

    return f"Error: could not stock '{item_name}' (capacity full?)."


def set_price(simulation_ref, item_name: str, new_price: float) -> str:
    """Update the selling price for *item_name* across the vending machine."""
    machine = simulation_ref.vending_machine
    storage = simulation_ref.storage
    updated = machine.update_price(item_name, new_price)
    storage.update_price(item_name, new_price)
    simulation_ref.db.log_action(
        simulation_ref.run_id, simulation_ref.current_time,
        simulation_ref.days_passed, "set_price",
        f"item={item_name} price={new_price}", simulation_ref.model_name
    )
    if updated:
        return f"Price for '{item_name}' set to ${new_price:.2f}."
    return f"Warning: '{item_name}' not found in machine."


# ── tools schema (OpenAI function-calling format) ──────────────────────────────

TOOLS_LIST = [
    {
        "type": "function",
        "function": {
            "name": "wait_for_next_day",
            "description": (
                "Advance simulation time to 6:00 AM of the next day. "
                "Daily fees are applied and weather updates."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": (
                "Send an email to a supplier or business contact "
                "to place orders or ask questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body text"},
                },
                "required": ["recipient", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_email",
            "description": (
                "Read all unread emails in your inbox "
                "(supplier responses, delivery notices, etc.)."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_storage_quantities",
            "description": "Check the current inventory in your back-room storage.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_vending_machine",
            "description": (
                "Check what items are currently stocked in the vending machine "
                "and their quantities."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stock_vending_machine",
            "description": "Move items from back-room storage into the vending machine for sale.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string", "description": "Name of the item to stock"},
                    "quantity": {"type": "integer", "description": "Number of units to stock"},
                    "slot_id": {
                        "type": "string",
                        "description": "Specific slot ID (e.g. '0-1'). Leave empty for auto-assignment.",
                    },
                },
                "required": ["item_name", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_price",
            "description": "Update the selling price for an item in the vending machine.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string", "description": "Name of the item"},
                    "new_price": {"type": "number", "description": "New selling price in USD"},
                },
                "required": ["item_name", "new_price"],
            },
        },
    },
]

TOOLS_FUNCTIONS = {
    "wait_for_next_day": wait_for_next_day,
    "send_email": send_email,
    "read_email": read_email,
    "check_storage_quantities": check_storage_quantities,
    "check_vending_machine": check_vending_machine,
    "stock_vending_machine": stock_vending_machine,
    "set_price": set_price,
}


def execute_tool(tool_call: Any, simulation_ref) -> dict:
    """Execute a single agent tool call."""
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
    print(f"  [tool] {name}({args})")
    if name in TOOLS_FUNCTIONS:
        try:
            result = TOOLS_FUNCTIONS[name](simulation_ref, **args)
            print(f"  [tool result] {result}")
            return {"success": True, "message": f"\n\n[Tool: {name} → {result}]"}
        except Exception as e:
            msg = f"Tool execution error: {e}"
            print(f"  [tool error] {msg}")
            return {"success": False, "message": f"\n\n[Tool error: {name} – {msg}]"}
    return {"success": False, "message": f"\n\n[Tool error: unknown tool '{name}']"}


# ── supplier-side tools ────────────────────────────────────────────────────────

def supplier_schedule_delivery(simulation_ref, days_until_delivery: int,
                                supplier: str = "Supplier",
                                reference: str | None = None,
                                items: list | None = None) -> str:
    if items is None:
        items = []
    arrival = simulation_ref.storage.schedule_delivery(
        current_time=simulation_ref.current_time,
        items=items,
        days_until_delivery=int(days_until_delivery),
        supplier=supplier,
        reference=reference,
    )
    return f"Delivery scheduled for {arrival.strftime('%Y-%m-%d 06:00 UTC')}"


SUPPLIER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "schedule_delivery",
            "description": "Schedule a shipment to the operator. Call only when confirming an order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_until_delivery": {"type": "integer", "minimum": 1},
                    "supplier": {"type": "string"},
                    "reference": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "size": {"type": "string", "enum": ["small", "large"]},
                                "quantity": {"type": "integer", "minimum": 1},
                                "unit_cost": {"type": "number", "minimum": 0},
                            },
                            "required": ["name", "size", "quantity", "unit_cost"],
                        },
                        "minItems": 1,
                    },
                },
                "required": ["days_until_delivery", "items"],
            },
        },
    }
]

SUPPLIER_TOOLS_FUNCTIONS = {"schedule_delivery": supplier_schedule_delivery}


def execute_supplier_tool(tool_call: Any, simulation_ref) -> dict:
    """Execute a supplier-side tool call."""
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
    print(f"  [supplier tool] {name}({args})")
    if name in SUPPLIER_TOOLS_FUNCTIONS:
        try:
            result = SUPPLIER_TOOLS_FUNCTIONS[name](simulation_ref, **args)
            return {"success": True, "message": f"\n\n[Supplier tool: {name} → {result}]"}
        except Exception as e:
            return {"success": False, "message": f"\n\n[Supplier tool error: {name} – {e}]"}
    return {"success": False, "message": f"\n\n[Supplier tool error: unknown '{name}']"}
