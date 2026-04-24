"""
VendingBench2 - Web Search
Optional search utility using the Perplexity API or a stub fallback.
Used by the agent to research suppliers, products, and market prices.
"""
from __future__ import annotations
import os
from typing import Dict, Any


def search_web(query: str, max_results: int = 5) -> str:
    """
    Perform a web search and return a formatted string of results.
    Uses Perplexity API if PERPLEXITY_API_KEY is set, otherwise returns a stub.
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if api_key:
        return _perplexity_search(query, api_key, max_results)
    return _stub_search(query)


def _perplexity_search(query: str, api_key: str, max_results: int) -> str:
    """Search using the Perplexity API."""
    try:
        import requests
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": "Be concise and factual. Provide short, relevant answers."},
                {"role": "user", "content": query},
            ],
            "max_tokens": 512,
        }
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
            timeout=15,
        )
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return f"Search results for '{query}':\n\n{content}"
        return f"Search failed (HTTP {response.status_code}): {response.text[:200]}"
    except Exception as e:
        return f"Search error: {e}"


def _stub_search(query: str) -> str:
    """Return a helpful stub when no API key is configured."""
    stubs: Dict[str, str] = {
        "vending machine": (
            "Vending machines typically carry snacks ($1–$3), beverages ($1.50–$3), "
            "and fresh food ($4–$8). High-traffic locations see 50–100+ sales/day."
        ),
        "snack": (
            "Popular vending snacks: chips ($0.75 cost, $1.50 retail), "
            "cookies ($0.60 cost, $1.25 retail), candy bars ($0.50 cost, $1.25 retail)."
        ),
        "drink": (
            "Vending beverages: sodas ($0.80 cost, $1.75 retail), "
            "water ($0.40 cost, $1.25 retail), energy drinks ($1.20 cost, $2.50 retail)."
        ),
        "supplier": (
            "Common vending suppliers: VISTAR, McLane, Core-Mark. "
            "Typical wholesale margin is 40–60% below retail price."
        ),
        "price": (
            "Vending machine pricing: small items $1.00–$2.00, large items $1.50–$3.50. "
            "Price elasticity is typically -0.8 to -1.5 for snacks."
        ),
    }
    query_lower = query.lower()
    for key, result in stubs.items():
        if key in query_lower:
            return f"Search results for '{query}':\n\n{result}"
    return (
        f"Search results for '{query}':\n\n"
        "No specific results found. Consider contacting suppliers directly via email "
        "to get current pricing and availability."
    )


def format_search_results(results: str, query: str) -> str:
    """Format search results for display in agent context."""
    return f"\n[Web Search: {query}]\n{results}\n"
