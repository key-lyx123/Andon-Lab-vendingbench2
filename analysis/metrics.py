"""
VendingBench2 Analysis – Metrics
Compute paper-relevant performance metrics from simulation database.
"""
from __future__ import annotations
from typing import Dict, List
import sqlite3


def load_runs(db_path: str = "vending_simulation.db") -> Dict[str, Dict]:
    """
    Load all simulation runs from the database.
    Returns {run_id: {model_name, days, final_balance, final_net_worth,
                       total_revenue, action_counts, daily_series}}
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    runs: Dict[str, Dict] = {}
    for row in conn.execute(
        "SELECT DISTINCT run_id, model_name FROM simulation_state"
    ):
        run_id = row["run_id"]
        model = row["model_name"]

        states = conn.execute(
            "SELECT day, balance, net_worth, revenue, cogs "
            "FROM simulation_state WHERE run_id=? ORDER BY day",
            (run_id,)
        ).fetchall()

        if not states:
            continue

        last = states[-1]
        total_rev = sum(r["revenue"] for r in states)
        total_cogs = sum(r["cogs"] for r in states)

        actions = {
            r["action_type"]: r["cnt"]
            for r in conn.execute(
                "SELECT action_type, COUNT(*) as cnt FROM agent_actions "
                "WHERE run_id=? GROUP BY action_type",
                (run_id,)
            )
        }

        runs[run_id] = {
            "model_name": model,
            "days": last["day"],
            "final_balance": last["balance"],
            "final_net_worth": last["net_worth"],
            "total_revenue": total_rev,
            "total_cogs": total_cogs,
            "gross_profit": total_rev - total_cogs,
            "action_counts": actions,
            "daily_series": [dict(r) for r in states],
        }

    conn.close()
    return runs


def compute_summary_table(runs: Dict[str, Dict]) -> List[Dict]:
    """Return a list of dicts suitable for a DataFrame / LaTeX table."""
    rows = []
    for run_id, data in runs.items():
        rows.append({
            "run_id": run_id[:8],
            "model": data["model_name"],
            "days": data["days"],
            "final_balance": round(data["final_balance"], 2),
            "final_net_worth": round(data["final_net_worth"], 2),
            "total_revenue": round(data["total_revenue"], 2),
            "gross_profit": round(data["gross_profit"], 2),
            "emails_sent": data["action_counts"].get("send_email", 0),
            "emails_read": data["action_counts"].get("read_email", 0),
            "stock_actions": data["action_counts"].get("stock_machine", 0),
        })
    rows.sort(key=lambda r: r["final_net_worth"], reverse=True)
    return rows


def compute_survival_rate(runs: Dict[str, Dict], target_days: int = 30) -> Dict[str, float]:
    """
    Fraction of runs per model that survived ≥ target_days with balance > 0.
    """
    model_total: Dict[str, int] = {}
    model_survived: Dict[str, int] = {}
    for data in runs.values():
        m = data["model_name"]
        model_total[m] = model_total.get(m, 0) + 1
        survived = data["days"] >= target_days and data["final_balance"] > 0
        model_survived[m] = model_survived.get(m, 0) + int(survived)
    return {
        m: model_survived.get(m, 0) / model_total[m]
        for m in model_total
    }
