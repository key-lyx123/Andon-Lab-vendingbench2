"""
VendingBench2 - Main Simulation Orchestrator
Ties together the vending machine, storage, weather, economic environment,
email system, database logger, and AI agent.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone

from database import SimulationDatabase
from weather import generate_next_weather
from agent import VendingMachineAgent
from email_system import EmailSystem
from storage import StorageSystem
from vending_machine import VendingMachine
from economic_environment import calculate_total_sales

STARTING_BALANCE = 500.0
DAILY_FEE = 2.0


class VendingMachineSimulation:
    def __init__(self, model_name: str = "claude-4-sonnet",
                 store_state: bool = True,
                 db_path: str = "vending_simulation.db"):
        self.run_id = str(uuid.uuid4())
        self.model_name = model_name
        self.balance = STARTING_BALANCE
        self.days_passed = 0
        self.message_count = 0

        # Components
        self.storage = StorageSystem()
        self.vending_machine = VendingMachine()
        self.email_system = EmailSystem()
        self.db = SimulationDatabase(db_path)

        # Time – start at today's 06:00 UTC
        now = datetime.now(timezone.utc)
        self.current_time = now.replace(hour=6, minute=0, second=0, microsecond=0)

        # Weather
        self.current_weather = "sunny"

        # Daily financials
        self._day_revenue = 0.0
        self._day_cogs = 0.0
        self._day_items_sold = 0

        self.store_state = store_state
        self.agent = VendingMachineAgent(
            name="VendingBot",
            model_name=model_name,
            simulation_ref=self,
        )

        # Log initial state
        if self.store_state:
            self._log_state()

    # ── time helpers ───────────────────────────────────────────────────────────

    def get_current_time(self) -> datetime:
        return self.current_time

    def _get_season(self) -> str:
        m = self.current_time.month
        if m in (12, 1, 2):
            return "Winter"
        if m in (3, 4, 5):
            return "Spring"
        if m in (6, 7, 8):
            return "Summer"
        return "Fall"

    # ── logging ────────────────────────────────────────────────────────────────

    def _log_state(self):
        inv_value = self.storage.get_total_value()
        net_worth = self.balance + inv_value
        self.db.log_state(
            run_id=self.run_id,
            timestamp=self.current_time,
            day=self.days_passed,
            balance=self.balance,
            net_worth=net_worth,
            revenue=self._day_revenue,
            cogs=self._day_cogs,
            inventory_value=inv_value,
            model_name=self.model_name,
        )

    # ── daily cycle ────────────────────────────────────────────────────────────

    def handle_new_day(self) -> str:
        """Called at each 06:00 threshold. Returns the daily report string."""
        if self.message_count > 0:
            self.days_passed += 1
            self.balance -= DAILY_FEE

        # Weather
        self.current_weather = generate_next_weather(
            self.current_time.month, self.current_weather
        )

        # Simulate sales for the previous day
        if self.vending_machine.total_items() > 0:
            revenue, cogs, sales_report = calculate_total_sales(
                self.vending_machine,
                weather=self.current_weather,
                month=self.current_time.month,
                day_of_week=self.current_time.weekday(),
            )
            self.balance += revenue - cogs
            self._day_revenue = revenue
            self._day_cogs = cogs
        else:
            sales_report = "No items in vending machine – no sales today."
            self._day_revenue = 0.0
            self._day_cogs = 0.0

        # Process deliveries
        def _on_delivery(supplier, ref, body):
            self.email_system.receive_email(
                sender=supplier, subject="Delivery Notice", body=body,
                email_type="delivery_notice"
            )

        delivery_cost = self.storage.process_arrivals(self.current_time, on_arrival=_on_delivery)
        self.balance -= delivery_cost

        # Supplier email responses
        self.email_system.generate_supplier_responses(self)

        # Log daily summary
        if self.store_state:
            self.db.log_daily_summary(
                run_id=self.run_id,
                day=self.days_passed,
                balance=self.balance,
                net_worth=self.balance + self.storage.get_total_value(),
                revenue=self._day_revenue,
                cogs=self._day_cogs,
                weather=self.current_weather,
                model_name=self.model_name,
            )

        return self._build_daily_report(sales_report)

    def _build_daily_report(self, sales_report: str) -> str:
        t = self.current_time
        unread = len(self.email_system.get_unread_emails())
        inv_value = self.storage.get_total_value()
        net_worth = self.balance + inv_value
        return (
            f"DAILY REPORT – {t.strftime('%A, %B %d %Y')} at {t.strftime('%H:%M UTC')}\n"
            f"{'=' * 60}\n"
            f"FINANCIALS:\n"
            f"  Cash Balance:    ${self.balance:.2f}\n"
            f"  Inventory Value: ${inv_value:.2f}\n"
            f"  Net Worth:       ${net_worth:.2f}\n"
            f"  Days Operating:  {self.days_passed}\n"
            f"\nENVIRONMENT:\n"
            f"  Weather: {self.current_weather}  |  Season: {self._get_season()}\n"
            f"\nEMAILS: {unread} unread\n"
            f"\n{sales_report}\n"
            f"\nACTION REQUIRED: Use your tools to manage the business."
        )

    # ── agent step ─────────────────────────────────────────────────────────────

    def run_agent_step(self) -> str:
        self.message_count += 1
        response = self.agent.run_agent()
        print(f"\n[Step {self.message_count}] {self.current_time.strftime('%H:%M')}: {response[:200]}…")
        if self.store_state:
            self._log_state()
        return response

    # ── main loop ──────────────────────────────────────────────────────────────

    def start_simulation(self, max_steps: int = 100):
        print(f"🚀 VendingBench2 Simulation")
        print(f"   Run ID:  {self.run_id}")
        print(f"   Model:   {self.model_name}")
        print(f"   Steps:   {max_steps}")
        print("=" * 60)

        while self.message_count < max_steps:
            try:
                self.run_agent_step()
            except KeyboardInterrupt:
                print("\n⏹  Interrupted.")
                break
            except Exception as e:
                print(f"\n⚠  Error at step {self.message_count}: {e}")
                break

        inv_value = self.storage.get_total_value()
        print(f"\n✅ Simulation complete")
        print(f"   Steps: {self.message_count}  Days: {self.days_passed}")
        print(f"   Cash: ${self.balance:.2f}  Net Worth: ${self.balance + inv_value:.2f}")


def run_simulation(model_name: str = "claude-4-sonnet", max_steps: int = 100,
                   store_state: bool = True, db_path: str = "vending_simulation.db"):
    sim = VendingMachineSimulation(model_name=model_name,
                                   store_state=store_state, db_path=db_path)
    try:
        sim.start_simulation(max_steps)
    finally:
        sim.db.close()
    return sim.run_id


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="VendingBench2 Simulation")
    parser.add_argument("--model", default="claude-4-sonnet", help="LiteLLM model name")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--db", default="vending_simulation.db")
    parser.add_argument("--no-store", action="store_true")
    args = parser.parse_args()
    run_simulation(model_name=args.model, max_steps=args.steps,
                   store_state=not args.no_store, db_path=args.db)
