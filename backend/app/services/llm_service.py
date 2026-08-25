import logging
import os

import google.generativeai as genai
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.services.agent_tools import (
    add_transaction,
    compare_periods,
    get_anomalies,
    get_recent_transactions,
    get_spending_by_category,
    get_spending_summary,
)

load_dotenv()
logger = logging.getLogger(__name__)

MODEL_NAME = "models/gemini-flash-latest"

SYSTEM_PROMPT = """You are BudgetPilot, a smart and concise personal finance assistant.
You have access to the user's real transaction data through tools.

Rules:
- Always call a tool to get real data before answering financial questions
- Keep responses short and conversational
- Use ₹ for all currency amounts
- Be encouraging, not preachy
- If a tool returns no data, say so honestly
- For adding transactions, confirm what was added and mention the category
"""

_genai_configured = False


def _configure():
    global _genai_configured
    if not _genai_configured:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set.")
        genai.configure(api_key=api_key)
        _genai_configured = True


# ── Tool dispatcher ───────────────────────────────────────────────────────────
# Maps Gemini function call names to actual Python functions.
# Each handler receives (db, **args) and returns a string.

def _dispatch(name: str, args: dict, db: Session) -> str:
    try:
        if name == "get_spending_summary":
            return get_spending_summary(db, **args)
        if name == "get_spending_by_category":
            return get_spending_by_category(db, **args)
        if name == "get_recent_transactions":
            return get_recent_transactions(db, **args)
        if name == "get_anomalies":
            return get_anomalies(db)
        if name == "compare_periods":
            return compare_periods(db, **args)
        if name == "add_transaction":
            return add_transaction(db, **args)
        return f"Unknown tool: {name}"
    except Exception as exc:
        logger.error("Tool %s failed: %s", name, exc)
        return f"Tool error: {exc}"


# ── Agent entry point ─────────────────────────────────────────────────────────

def run_agent(user_message: str, db: Session) -> str:
    """
    Run the agentic loop:
    1. Send user message to Gemini with tools
    2. If Gemini calls a tool, execute it against the DB
    3. Send result back to Gemini
    4. Repeat until Gemini gives a final text response
    """
    _configure()

    # Define tools as plain Python functions — the SDK reads their
    # docstrings and type hints to build the function declaration automatically.
    def get_spending_summary_tool(period: str = "this_month") -> str:
        """
        Get total income, expenses, and balance for a time period.
        period options: today, this_week, this_month, last_month, this_year, all_time
        """
        return get_spending_summary(db, period=period)

    def get_spending_by_category_tool(period: str = "this_month", category: str = "") -> str:
        """
        Get expense totals grouped by category, or filtered to one category.
        Leave category empty to get all categories.
        period options: today, this_week, this_month, last_month, this_year, all_time
        """
        return get_spending_by_category(db, period=period, category=category)

    def get_recent_transactions_tool(limit: int = 10) -> str:
        """Get the most recent transactions. limit: number of transactions to return (max 50)."""
        return get_recent_transactions(db, limit=limit)

    def get_anomalies_tool() -> str:
        """Get all transactions that were flagged as unusually high for their category."""
        return get_anomalies(db)

    def compare_periods_tool(category: str, period1: str, period2: str) -> str:
        """
        Compare spending in a category across two time periods.
        Use this for questions like 'did I spend more on food this month vs last month?'
        category: spending category (food, transport, shopping, etc.) or empty for all
        period1, period2: today, this_week, this_month, last_month, this_year, all_time
        """
        return compare_periods(db, category=category, period1=period1, period2=period2)

    def add_transaction_tool(description: str, amount: float, transaction_type: str = "expense") -> str:
        """
        Add a new transaction. The ML model will auto-categorize it.
        description: what the transaction was for (e.g. 'Swiggy dinner')
        amount: transaction amount in rupees (must be > 0)
        transaction_type: 'expense' or 'income'
        """
        return add_transaction(db, description=description, amount=amount, transaction_type=transaction_type)

    tools = [
        get_spending_summary_tool,
        get_spending_by_category_tool,
        get_recent_transactions_tool,
        get_anomalies_tool,
        compare_periods_tool,
        add_transaction_tool,
    ]

    try:
        model = genai.GenerativeModel(MODEL_NAME, tools=tools, system_instruction=SYSTEM_PROMPT)
        messages = [{"role": "user", "parts": [user_message]}]

        # Agent loop — max 5 tool calls to prevent runaway loops
        for _ in range(5):
            response = model.generate_content(messages)
            candidate = response.candidates[0]
            parts = candidate.content.parts

            # Check if any part is a function call
            tool_calls = [p for p in parts if hasattr(p, "function_call") and p.function_call.name]

            if not tool_calls:
                # No tool calls — extract the final text response
                text_parts = [p.text for p in parts if hasattr(p, "text") and p.text]
                return " ".join(text_parts).strip() or "I couldn't generate a response."

            # Execute all tool calls and collect results
            function_responses = []
            for part in tool_calls:
                fc = part.function_call
                tool_result = _dispatch(fc.name, dict(fc.args), db)
                logger.info("Tool %s(%s) → %s", fc.name, dict(fc.args), tool_result[:100])

                function_responses.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fc.name,
                            response={"result": tool_result},
                        )
                    )
                )

            # Append model's tool-call turn and our results to the conversation
            messages.append({"role": "model", "parts": parts})
            messages.append({"role": "user", "parts": function_responses})

        return "I wasn't able to complete that request. Please try again."

    except Exception as exc:
        logger.error("Agent error: %s", exc)
        return "I'm having trouble right now. Please try again in a moment."
