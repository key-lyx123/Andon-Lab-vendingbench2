"""
VendingBench2 Analysis – Visualization
Generate publication-quality figures for paper writing.
"""
from __future__ import annotations
import os
from typing import Dict, List, Optional

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Paper-quality defaults
FIGSIZE = (8, 5)
DPI = 150
COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]


def _require_matplotlib():
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib is required. Run: pip install matplotlib")


def save_or_show(fig, path: Optional[str] = None):
    if path:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        fig.savefig(path, dpi=DPI, bbox_inches="tight")
        print(f"Saved figure: {path}")
    else:
        plt.show()
    plt.close(fig)


# ── individual plot functions ──────────────────────────────────────────────────

def plot_balance_over_time(runs: Dict, output_path: Optional[str] = None):
    """Line chart: cash balance per day, one line per run/model."""
    _require_matplotlib()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for i, (run_id, data) in enumerate(runs.items()):
        series = data["daily_series"]
        days = [r["day"] for r in series]
        balances = [r["balance"] for r in series]
        label = f"{data['model_name']} ({run_id[:6]})"
        ax.plot(days, balances, label=label,
                color=COLORS[i % len(COLORS)], linewidth=1.8)
    ax.axhline(0, color="red", linestyle="--", linewidth=1, alpha=0.6, label="Bankruptcy")
    ax.set_xlabel("Simulation Day")
    ax.set_ylabel("Cash Balance ($)")
    ax.set_title("Agent Cash Balance Over Time")
    ax.legend(fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
    ax.grid(True, alpha=0.3)
    save_or_show(fig, output_path)


def plot_net_worth_over_time(runs: Dict, output_path: Optional[str] = None):
    """Line chart: net worth (cash + inventory) per day."""
    _require_matplotlib()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for i, (run_id, data) in enumerate(runs.items()):
        series = data["daily_series"]
        days = [r["day"] for r in series]
        nw = [r["net_worth"] for r in series]
        label = f"{data['model_name']} ({run_id[:6]})"
        ax.plot(days, nw, label=label,
                color=COLORS[i % len(COLORS)], linewidth=1.8)
    ax.axhline(500, color="grey", linestyle=":", linewidth=1,
               alpha=0.6, label="Starting $500")
    ax.set_xlabel("Simulation Day")
    ax.set_ylabel("Net Worth ($)")
    ax.set_title("Agent Net Worth Over Time")
    ax.legend(fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
    ax.grid(True, alpha=0.3)
    save_or_show(fig, output_path)


def plot_model_comparison_bar(summary_rows: List[Dict], metric: str = "final_net_worth",
                               output_path: Optional[str] = None):
    """Bar chart comparing models on a single metric."""
    _require_matplotlib()
    if not HAS_NUMPY:
        raise ImportError("numpy is required. Run: pip install numpy")
    models = [r["model"] for r in summary_rows]
    values = [r[metric] for r in summary_rows]
    fig, ax = plt.subplots(figsize=FIGSIZE)
    bars = ax.bar(models, values, color=COLORS[:len(models)])
    money_metrics = {"final_net_worth", "final_balance", "total_revenue", "gross_profit"}
    fmt = "$%.1f" if metric in money_metrics else "%.1f"
    ax.bar_label(bars, fmt=fmt, padding=3, fontsize=9)
    ax.set_xlabel("Model")
    ax.set_ylabel(metric.replace("_", " ").title())
    ax.set_title(f"Model Comparison: {metric.replace('_', ' ').title()}")
    ax.grid(True, axis="y", alpha=0.3)
    plt.xticks(rotation=15, ha="right")
    save_or_show(fig, output_path)


def plot_action_distribution(runs: Dict, output_path: Optional[str] = None):
    """Stacked bar chart of action types per model."""
    _require_matplotlib()
    action_types = [
        "send_email", "read_email", "stock_machine", "set_price", "wait_for_next_day"
    ]
    model_data: Dict[str, Dict[str, int]] = {}
    for data in runs.values():
        m = data["model_name"]
        if m not in model_data:
            model_data[m] = {a: 0 for a in action_types}
        for a, cnt in data["action_counts"].items():
            model_data[m][a] = model_data[m].get(a, 0) + cnt

    models = list(model_data.keys())
    fig, ax = plt.subplots(figsize=FIGSIZE)
    bottoms = [0] * len(models)
    for j, action in enumerate(action_types):
        vals = [model_data[m].get(action, 0) for m in models]
        ax.bar(models, vals, bottom=bottoms,
               label=action.replace("_", " "), color=COLORS[j % len(COLORS)])
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax.set_xlabel("Model")
    ax.set_ylabel("Action Count")
    ax.set_title("Agent Action Distribution by Model")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, axis="y", alpha=0.3)
    plt.xticks(rotation=15, ha="right")
    save_or_show(fig, output_path)


def generate_all_figures(runs: Dict, summary_rows: List[Dict],
                          output_dir: str = "analysis/output"):
    """Generate all figures used in the paper."""
    os.makedirs(output_dir, exist_ok=True)
    plot_balance_over_time(runs, f"{output_dir}/balance_over_time.png")
    plot_net_worth_over_time(runs, f"{output_dir}/net_worth_over_time.png")
    plot_model_comparison_bar(
        summary_rows, "final_net_worth",
        f"{output_dir}/model_comparison_net_worth.png"
    )
    plot_model_comparison_bar(
        summary_rows, "total_revenue",
        f"{output_dir}/model_comparison_revenue.png"
    )
    plot_action_distribution(runs, f"{output_dir}/action_distribution.png")
    print(f"\n✅ All figures saved to {output_dir}/")
