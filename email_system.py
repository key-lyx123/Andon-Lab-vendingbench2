"""
VendingBench2 - Email System
Manages email communication between the operator agent and suppliers.
Suppliers are themselves driven by an LLM that can call schedule_delivery.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


# ── known suppliers ────────────────────────────────────────────────────────────

SUPPLIERS: Dict[str, Dict[str, Any]] = {
    "snacks@quickbite.com": {
        "name": "QuickBite Wholesale",
        "description": "Wholesale snack distributor. Carries chips, cookies, candy bars.",
        "min_order": 20,
        "lead_time_days": 2,
        "catalog": [
            {"name": "Chips", "size": "small", "unit_cost": 0.75},
            {"name": "Cookies", "size": "small", "unit_cost": 0.60},
            {"name": "Candy Bar", "size": "small", "unit_cost": 0.50},
            {"name": "Granola Bar", "size": "small", "unit_cost": 0.65},
            {"name": "Pretzels", "size": "small", "unit_cost": 0.55},
        ],
    },
    "drinks@refreshco.com": {
        "name": "RefreshCo Beverages",
        "description": "Beverage supplier. Carries sodas, water, energy drinks, juice.",
        "min_order": 12,
        "lead_time_days": 2,
        "catalog": [
            {"name": "Soda Can", "size": "large", "unit_cost": 0.80},
            {"name": "Water Bottle", "size": "large", "unit_cost": 0.40},
            {"name": "Energy Drink", "size": "large", "unit_cost": 1.20},
            {"name": "Orange Juice", "size": "large", "unit_cost": 1.10},
            {"name": "Sports Drink", "size": "large", "unit_cost": 0.90},
        ],
    },
    "orders@freshfood.com": {
        "name": "FreshFood Distributors",
        "description": "Fresh and healthy food options. Carries sandwiches, salads, fruit cups.",
        "min_order": 10,
        "lead_time_days": 1,
        "catalog": [
            {"name": "Sandwich", "size": "large", "unit_cost": 2.50},
            {"name": "Salad Cup", "size": "large", "unit_cost": 2.00},
            {"name": "Fruit Cup", "size": "small", "unit_cost": 1.50},
            {"name": "Yogurt", "size": "small", "unit_cost": 1.00},
            {"name": "Protein Bar", "size": "small", "unit_cost": 1.25},
        ],
    },
}

SUPPLIER_SYSTEM_PROMPT = """You are a wholesale supplier sales representative responding to customer orders via email.

Your company: {company_name}
Your catalog: {catalog}
Standard lead time: {lead_time_days} days
Minimum order: {min_order} units per product

When an operator emails you to order products:
1. Confirm which items you carry (check your catalog)
2. Confirm quantities and pricing
3. Call the schedule_delivery tool to arrange shipment
4. Reply with a professional confirmation email

If asked about items not in your catalog, politely decline and suggest alternatives.
Be helpful and professional. Keep responses concise.
"""


class Email:
    def __init__(self, sender: str, recipient: str, subject: str, body: str,
                 email_type: str = "general", email_id: Optional[str] = None,
                 timestamp: Optional[datetime] = None):
        self.email_id = email_id or str(uuid.uuid4())[:8]
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.body = body
        self.email_type = email_type
        self.timestamp = timestamp or datetime.utcnow()
        self.read = False
        self.replied = False  # tracks whether a supplier response was generated

    def __repr__(self):
        return f"Email(id={self.email_id}, from={self.sender}, subj={self.subject!r})"

    def format_for_agent(self) -> str:
        return (
            f"--- Email ID: {self.email_id} ---\n"
            f"From:    {self.sender}\n"
            f"Subject: {self.subject}\n"
            f"Date:    {self.timestamp.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"\n{self.body}\n"
        )


class EmailSystem:
    """
    Manages an inbox/outbox for the operator and simulates supplier responses.
    """

    def __init__(self):
        self.inbox: List[Email] = []
        self.outbox: List[Email] = []
        self.operator_email = "operator@vendingbench.local"

        # Seed with a welcome email
        welcome = Email(
            sender="support@vendingbench.local",
            recipient=self.operator_email,
            subject="Welcome to VendingBench2!",
            body=(
                "Welcome, vending machine operator!\n\n"
                "Your machine is set up at 1247 Business Park Drive, Chicago IL 60601.\n"
                "Starting balance: $500.00\n\n"
                "Available suppliers:\n"
                "  • QuickBite Wholesale (snacks): snacks@quickbite.com\n"
                "  • RefreshCo Beverages (drinks): drinks@refreshco.com\n"
                "  • FreshFood Distributors (fresh food): orders@freshfood.com\n\n"
                "Get started by emailing a supplier to place your first order!\n"
                "Include: item names, quantities, delivery address, and your account number (1234567890).\n"
            ),
            email_type="system",
        )
        self.inbox.append(welcome)

    # ── operator-facing ────────────────────────────────────────────────────────

    def send_email(self, recipient: str, subject: str, body: str,
                   email_type: str = "general") -> str:
        """Agent sends an email. Returns the email ID."""
        email = Email(
            sender=self.operator_email,
            recipient=recipient,
            subject=subject,
            body=body,
            email_type=email_type,
        )
        self.outbox.append(email)
        return email.email_id

    def receive_email(self, sender: str, subject: str, body: str,
                      email_type: str = "general") -> Email:
        """Deliver an inbound email to the operator's inbox."""
        email = Email(
            sender=sender,
            recipient=self.operator_email,
            subject=subject,
            body=body,
            email_type=email_type,
        )
        self.inbox.append(email)
        return email

    def get_unread_emails(self) -> List[Email]:
        return [e for e in self.inbox if not e.read]

    def get_unread_emails_for_agent(self) -> str:
        unread = self.get_unread_emails()
        if not unread:
            return "No new emails."
        parts = [f"You have {len(unread)} unread email(s):\n"]
        for email in unread:
            parts.append(email.format_for_agent())
            email.read = True
        return "\n".join(parts)

    # ── supplier simulation ────────────────────────────────────────────────────

    def generate_supplier_responses(self, simulation_ref) -> None:
        """
        For each unresponded outbound email to a known supplier address,
        generate a supplier reply using an LLM that can call schedule_delivery.
        """
        from tools import SUPPLIER_TOOLS, execute_supplier_tool  # avoid circular import at module level

        # Find outbound emails that haven't been replied to yet
        pending = [
            e for e in self.outbox
            if e.recipient in SUPPLIERS and not e.replied
        ]

        for out_email in pending:
            supplier_info = SUPPLIERS[out_email.recipient]
            self._handle_supplier_email(out_email, supplier_info, simulation_ref)
            out_email.replied = True

    def _handle_supplier_email(self, email: Email, supplier_info: Dict,
                                simulation_ref) -> None:
        """Generate a supplier LLM response and deliver it to the inbox."""
        from model_client import call_model
        from tools import SUPPLIER_TOOLS, execute_supplier_tool

        catalog_str = "\n".join(
            f"  - {p['name']} ({p['size']}) @ ${p['unit_cost']:.2f}/unit"
            for p in supplier_info["catalog"]
        )
        system = SUPPLIER_SYSTEM_PROMPT.format(
            company_name=supplier_info["name"],
            catalog=catalog_str,
            lead_time_days=supplier_info["lead_time_days"],
            min_order=supplier_info["min_order"],
        )
        prompt = (
            f"{system}\n\n"
            f"INCOMING EMAIL FROM CUSTOMER:\n"
            f"Subject: {email.subject}\n\n"
            f"{email.body}\n\n"
            f"Please process this order and reply professionally."
        )

        result = call_model(prompt, tools=SUPPLIER_TOOLS)
        reply_text = result.get("content", "") or ""
        tool_calls = result.get("tool_calls")

        # Execute any tool calls (schedule_delivery)
        delivery_info = ""
        if tool_calls:
            for tc in tool_calls:
                tr = execute_supplier_tool(tc, simulation_ref)
                delivery_info += tr.get("message", "")

        if not reply_text.strip():
            reply_text = (
                f"Thank you for your order. We have processed your request.\n"
                f"{delivery_info}"
            )
        elif delivery_info:
            reply_text += f"\n\n{delivery_info}"

        self.receive_email(
            sender=email.recipient,
            subject=f"Re: {email.subject}",
            body=reply_text,
            email_type="supplier_response",
        )

    # ── utilities ──────────────────────────────────────────────────────────────

    def get_inbox_summary(self) -> str:
        total = len(self.inbox)
        unread = len(self.get_unread_emails())
        return f"Inbox: {total} total, {unread} unread"

    def __repr__(self):
        return f"EmailSystem({self.get_inbox_summary()})"
