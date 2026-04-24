"""
VendingBench2 - Database Layer
Enhanced SQLite logging for simulation state, daily financials, and agent actions.
Used by the analysis toolkit to reproduce paper figures.
"""
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class SimulationDatabase:
    def __init__(self, db_path: str = "vending_simulation.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS simulation_state (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id      TEXT    NOT NULL,
                model_name  TEXT    NOT NULL DEFAULT 'unknown',
                timestamp   TEXT    NOT NULL,
                day         INTEGER NOT NULL DEFAULT 0,
                balance     REAL    NOT NULL,
                net_worth   REAL    NOT NULL DEFAULT 0,
                revenue     REAL    NOT NULL DEFAULT 0,
                cogs        REAL    NOT NULL DEFAULT 0,
                inventory_value REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS agent_actions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id      TEXT    NOT NULL,
                model_name  TEXT    NOT NULL DEFAULT 'unknown',
                timestamp   TEXT    NOT NULL,
                day         INTEGER NOT NULL DEFAULT 0,
                action_type TEXT    NOT NULL,
                details     TEXT
            );

            CREATE TABLE IF NOT EXISTS daily_summary (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id      TEXT    NOT NULL,
                model_name  TEXT    NOT NULL DEFAULT 'unknown',
                day         INTEGER NOT NULL,
                balance     REAL    NOT NULL,
                net_worth   REAL    NOT NULL DEFAULT 0,
                revenue     REAL    NOT NULL DEFAULT 0,
                cogs        REAL    NOT NULL DEFAULT 0,
                weather     TEXT,
                items_sold  INTEGER NOT NULL DEFAULT 0
            );
        """)
        self.conn.commit()

    # ── write helpers ──────────────────────────────────────────────────────────

    def log_state(self, run_id: str, timestamp: datetime, day: int,
                  balance: float, net_worth: float = 0.0, revenue: float = 0.0,
                  cogs: float = 0.0, inventory_value: float = 0.0,
                  model_name: str = "unknown"):
        self.conn.execute(
            "INSERT INTO simulation_state "
            "(run_id, model_name, timestamp, day, balance, net_worth, revenue, cogs, inventory_value) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, model_name, timestamp.isoformat(), day,
             balance, net_worth, revenue, cogs, inventory_value)
        )
        self.conn.commit()

    def log_action(self, run_id: str, timestamp: datetime, day: int,
                   action_type: str, details: str = "", model_name: str = "unknown"):
        self.conn.execute(
            "INSERT INTO agent_actions (run_id, model_name, timestamp, day, action_type, details) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, model_name, timestamp.isoformat(), day, action_type, details)
        )
        self.conn.commit()

    def log_daily_summary(self, run_id: str, day: int, balance: float,
                          net_worth: float = 0.0, revenue: float = 0.0,
                          cogs: float = 0.0, weather: str = "", items_sold: int = 0,
                          model_name: str = "unknown"):
        self.conn.execute(
            "INSERT INTO daily_summary "
            "(run_id, model_name, day, balance, net_worth, revenue, cogs, weather, items_sold) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, model_name, day, balance, net_worth, revenue, cogs, weather, items_sold)
        )
        self.conn.commit()

    # ── read helpers ───────────────────────────────────────────────────────────

    def get_balance_history(self, run_id: str) -> List[Tuple]:
        return self.conn.execute(
            "SELECT day, balance, net_worth FROM simulation_state WHERE run_id=? ORDER BY day",
            (run_id,)
        ).fetchall()

    def get_daily_summaries(self, run_id: str) -> List[Tuple]:
        return self.conn.execute(
            "SELECT * FROM daily_summary WHERE run_id=? ORDER BY day",
            (run_id,)
        ).fetchall()

    def get_action_counts(self, run_id: str) -> Dict:
        rows = self.conn.execute(
            "SELECT action_type, COUNT(*) as cnt FROM agent_actions "
            "WHERE run_id=? GROUP BY action_type",
            (run_id,)
        ).fetchall()
        return {r["action_type"]: r["cnt"] for r in rows}

    def get_all_run_ids(self) -> List[str]:
        rows = self.conn.execute(
            "SELECT DISTINCT run_id FROM simulation_state"
        ).fetchall()
        return [r[0] for r in rows]

    def get_simulation_history(self, run_id: str) -> List[Tuple]:
        """Backwards-compatible helper."""
        return self.conn.execute(
            "SELECT timestamp, balance FROM simulation_state WHERE run_id=? ORDER BY day",
            (run_id,)
        ).fetchall()

    def close(self):
        self.conn.close()


def clear_database(db_path: str = "vending_simulation.db"):
    db = SimulationDatabase(db_path)
    for table in ("simulation_state", "agent_actions", "daily_summary"):
        db.conn.execute(f"DELETE FROM {table}")
    db.conn.commit()
    db.close()
    print(f"Database '{db_path}' cleared.")
