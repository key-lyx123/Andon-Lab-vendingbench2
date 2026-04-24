"""
VendingBench2 - Benchmark Runner
Main entry point for running VendingBench2 simulations.

Examples:
    # Run with Claude Sonnet for 100 steps
    python run_benchmark.py --model claude-4-sonnet --steps 100

    # Compare multiple models
    python run_benchmark.py --model gpt-4o --steps 50
    python run_benchmark.py --model claude-4-sonnet --steps 50

    # Analyze results
    python analysis/analyze_results.py
"""
from __future__ import annotations
import argparse
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional; env vars may be set externally

from main_simulation import run_simulation


def check_env():
    """Warn if no LLM API key is configured."""
    providers = {
        "Anthropic (Claude)": "ANTHROPIC_API_KEY",
        "OpenAI (GPT)": "OPENAI_API_KEY",
        "xAI (Grok)": "XAI_API_KEY",
    }
    found = [(name, key) for name, key in providers.items() if os.getenv(key)]
    if not found:
        print("⚠  WARNING: No LLM API key found in environment.")
        print("   Copy .env.example to .env and add at least one API key.")
        print("   Supported providers:")
        for name, key in providers.items():
            print(f"     {name}: {key}")
        sys.exit(1)
    print("✅ API keys detected:", ", ".join(n for n, _ in found))


def main():
    parser = argparse.ArgumentParser(
        description="VendingBench2 – AI Agent Vending Machine Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--model",
        default="claude-4-sonnet",
        help=(
            "LiteLLM model name. Examples:\n"
            "  claude-4-sonnet  (default)\n"
            "  claude-4-opus\n"
            "  gpt-4o\n"
            "  grok-3-beta\n"
            "  gemini-2.5-pro"
        ),
    )
    parser.add_argument("--steps", type=int, default=100,
                        help="Maximum number of agent actions (default: 100)")
    parser.add_argument("--db", default="vending_simulation.db",
                        help="SQLite database path (default: vending_simulation.db)")
    parser.add_argument("--no-store", action="store_true",
                        help="Disable state logging to database")
    parser.add_argument("--skip-check", action="store_true",
                        help="Skip API key check")
    args = parser.parse_args()

    if not args.skip_check:
        check_env()

    print(f"\n🎰 VendingBench2")
    print(f"   Model: {args.model}")
    print(f"   Steps: {args.steps}")
    print(f"   DB:    {args.db}\n")

    run_id = run_simulation(
        model_name=args.model,
        max_steps=args.steps,
        store_state=not args.no_store,
        db_path=args.db,
    )

    print(f"\nRun ID: {run_id}")
    print("To analyze results: python analysis/analyze_results.py")


if __name__ == "__main__":
    main()
