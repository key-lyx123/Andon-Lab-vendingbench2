"""
VendingBench2 - Results Analysis Script
Run this after completing one or more simulations to generate paper figures and tables.

Usage:
    python analysis/analyze_results.py --db vending_simulation.db --output analysis/output
"""
from __future__ import annotations
import argparse
import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.metrics import load_runs, compute_summary_table, compute_survival_rate
from analysis.visualize import generate_all_figures


def print_summary_table(rows):
    keys = ["run_id", "model", "days", "final_balance", "final_net_worth",
            "total_revenue", "gross_profit", "emails_sent", "emails_read", "stock_actions"]
    headers = ["Run ID", "Model", "Days", "Balance", "Net Worth", "Revenue",
               "Gross Profit", "Emails Sent", "Emails Read", "Stock Actions"]
    col_widths = [
        max(len(h), max((len(str(r.get(k, ""))) for r in rows), default=0))
        for h, k in zip(headers, keys)
    ]
    sep_width = sum(col_widths) + 2 * (len(col_widths) - 1)
    fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
    print("\n" + "=" * sep_width)
    print("SIMULATION RESULTS SUMMARY")
    print("=" * sep_width)
    print(fmt.format(*headers))
    print("-" * sep_width)
    for r in rows:
        print(fmt.format(
            r["run_id"], r["model"], r["days"],
            f"${r['final_balance']:.2f}", f"${r['final_net_worth']:.2f}",
            f"${r['total_revenue']:.2f}", f"${r['gross_profit']:.2f}",
            r["emails_sent"], r["emails_read"], r["stock_actions"],
        ))
    print()


def main():
    parser = argparse.ArgumentParser(description="VendingBench2 Results Analyser")
    parser.add_argument("--db", default="vending_simulation.db",
                        help="Path to SQLite database")
    parser.add_argument("--output", default="analysis/output",
                        help="Output directory for figures")
    parser.add_argument("--no-figures", action="store_true",
                        help="Skip figure generation")
    args = parser.parse_args()

    print(f"Loading results from: {args.db}")
    runs = load_runs(args.db)

    if not runs:
        print("No simulation data found. Run a simulation first with run_benchmark.py")
        return

    print(f"Found {len(runs)} simulation run(s).")

    summary = compute_summary_table(runs)
    print_summary_table(summary)

    survival = compute_survival_rate(runs, target_days=30)
    print("Survival Rate (≥30 days, balance > $0):")
    for model, rate in survival.items():
        print(f"  {model}: {rate:.1%}")

    if not args.no_figures:
        print(f"\nGenerating figures → {args.output}/")
        generate_all_figures(runs, summary, args.output)


if __name__ == "__main__":
    main()
