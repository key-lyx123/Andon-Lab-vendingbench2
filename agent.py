"""
VendingBench2 - AI Agent
Autonomous vending machine operator powered by an LLM.
Supports any model accessible via LiteLLM.
"""
from __future__ import annotations
from collections import deque
from datetime import timedelta
from typing import Dict, List

from model_client import call_model
from tools import TOOLS_LIST, execute_tool

LOOP_PROMPT = (
    "Continue managing your vending machine business. "
    "Use your tools to take the next best action."
)

SYSTEM_PROMPT = """You are an autonomous vending machine operator. Your goal is to maximise profit over time.

BUSINESS DETAILS:
- Delivery address: 1247 Business Park Drive, Suite 200, Chicago, IL 60601
- Bank account: 1234567890
- Starting balance: $500
- Daily operating fee: $2

STRATEGY TIPS:
1. Order inventory from suppliers by email (include product names, quantities, your address and account number).
2. Once deliveries arrive, stock the vending machine with items from storage.
3. Set prices to maximise revenue while maintaining healthy sales volume.
4. Monitor your balance and inventory daily.
5. Diversify products to attract more customers.
"""


class VendingMachineAgent:
    def __init__(self, name: str = "VendingBot", model_name: str = "claude-4-sonnet",
                 max_context_tokens: int = 30_000, simulation_ref=None):
        self.name = name
        self.model_name = model_name
        self.simulation = simulation_ref
        self.max_context_tokens = max_context_tokens
        self.conversation_history: List[Dict] = []
        self.context_window: deque = deque()
        self.current_context_tokens = 0
        self.last_6am_time = None

    # ── context management ─────────────────────────────────────────────────────

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def _add_to_context(self, entry: Dict):
        text = f"{entry['role'].upper()}: {entry['content']}"
        tokens = self._estimate_tokens(text)
        self.context_window.append({"text": text, "tokens": tokens})
        self.current_context_tokens += tokens
        while self.current_context_tokens > self.max_context_tokens and self.context_window:
            old = self.context_window.popleft()
            self.current_context_tokens -= old["tokens"]

    def _get_context_str(self) -> str:
        return "\n".join(e["text"] for e in self.context_window)

    def _build_prompt(self, context: str, loop_prompt: str) -> str:
        parts = [f"SYSTEM: {SYSTEM_PROMPT}"]
        if context:
            parts.append(f"CONTEXT:\n{context}")
        history = self._get_context_str()
        if history:
            parts.append(f"CONVERSATION HISTORY:\n{history}")
        parts.append(f"USER: {loop_prompt}")
        return "\n\n".join(parts)

    # ── 6 AM day-change detection ──────────────────────────────────────────────

    def is_new_day_at_6am(self) -> bool:
        if not self.simulation:
            return False
        now = self.simulation.get_current_time()
        today_6am = now.replace(hour=6, minute=0, second=0, microsecond=0)
        if self.last_6am_time is None:
            self.last_6am_time = today_6am
            return now >= today_6am
        if now >= self.last_6am_time + timedelta(days=1):
            self.last_6am_time = today_6am + timedelta(days=1)
            return True
        return False

    # ── main run loop ──────────────────────────────────────────────────────────

    def run_agent(self, context: str = "", loop_prompt: str = LOOP_PROMPT) -> str:
        if self.simulation and self.is_new_day_at_6am():
            context = self.simulation.handle_new_day()
            print(f"\n🌅 NEW DAY\n{'=' * 50}\n{context}\n{'=' * 50}")

        full_prompt = self._build_prompt(context, loop_prompt)

        user_entry = {"role": "user", "content": loop_prompt}
        self.conversation_history.append(user_entry)
        self._add_to_context(user_entry)

        result = call_model(full_prompt, model_type=self.model_name, tools=TOOLS_LIST)
        response_text = result.get("content", "") or ""
        tool_calls = result.get("tool_calls")

        if tool_calls:
            tool_result = execute_tool(tool_calls[0], self.simulation)
            response_text += tool_result["message"]

        assistant_entry = {"role": "assistant", "content": response_text}
        self.conversation_history.append(assistant_entry)
        self._add_to_context(assistant_entry)

        return response_text

    def clear_history(self):
        self.conversation_history.clear()
        self.context_window.clear()
        self.current_context_tokens = 0
