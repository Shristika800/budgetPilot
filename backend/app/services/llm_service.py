import logging
import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in environment.")
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-1.5-flash")
    return _model


SYSTEM_PROMPT = """You are BudgetPilot, a friendly and concise personal finance assistant.
You help users understand their spending, track expenses, and make better financial decisions.

Rules:
- Keep responses short and conversational (2-4 sentences max unless a list is needed)
- Always use ₹ for currency amounts
- Be encouraging, not preachy
- If you don't have enough data to answer, say so honestly
- Never make up transaction data — only use what's provided in the context
"""


def ask_gemini(user_message: str, financial_context: str) -> str:
    try:
        model = _get_model()

        prompt = f"""{SYSTEM_PROMPT}

--- USER'S FINANCIAL CONTEXT ---
{financial_context}
--- END CONTEXT ---

User: {user_message}
Assistant:"""

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as exc:
        logger.error("Gemini API error: %s", exc)
        return "I'm having trouble connecting right now. Please try again in a moment."
