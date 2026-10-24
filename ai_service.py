"""
NVIDIA Nemotron AI integration for Keerthi AI Expense Tracker.
Provides AI-powered financial insights and natural language query support.
"""

import os
import json
import time
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from datetime import date, datetime, timedelta
from functools import lru_cache

import requests
from config import Config
from database import db
from expense_service import expense_service


class AIService:
    """NVIDIA Nemotron AI service for financial insights."""

    def __init__(self):
        self.api_key = Config.NVIDIA_API_KEY
        self.model = Config.NVIDIA_MODEL
        self.base_url = Config.NVIDIA_BASE_URL.rstrip("/")
        self.timeout = Config.NVIDIA_TIMEOUT
        self.max_tokens = Config.NVIDIA_MAX_TOKENS
        self._cache: Dict[str, Tuple[float, str]] = {}  # Simple in-memory cache: key -> (timestamp, response)
        self.cache_ttl = 300  # 5 minutes

    def is_configured(self) -> bool:
        """Check if AI service is properly configured."""
        return Config.is_ai_configured()

    def _make_cache_key(self, prompt: str) -> str:
        """Generate a cache key from prompt."""
        return hashlib.md5(prompt.encode()).hexdigest()

    def _get_cached(self, key: str) -> Optional[str]:
        """Get cached response if not expired."""
        if key in self._cache:
            timestamp, response = self._cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return response
            else:
                del self._cache[key]
        return None

    def _set_cache(self, key: str, response: str) -> None:
        """Cache a response."""
        self._cache[key] = (time.time(), response)

    def _call_api(self, messages: List[Dict[str, str]], temperature: float = 0.3) -> Tuple[bool, str]:
        """Call NVIDIA Nemotron API."""
        if not self.is_configured():
            return False, "NVIDIA API key not configured. Please set NVIDIA_API_KEY in .env or Streamlit secrets."

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
            "stream": False
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                return True, content.strip()
            else:
                return False, "Unexpected API response format"

        except requests.exceptions.Timeout:
            return False, "AI request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            return False, "Could not connect to NVIDIA API. Check your internet connection."
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return False, "Invalid NVIDIA API key. Please check your configuration."
            elif e.response.status_code == 404:
                return False, f"Model '{self.model}' not found. Check NVIDIA_MODEL setting."
            elif e.response.status_code == 429:
                return False, "Rate limit exceeded. Please wait before trying again."
            else:
                return False, f"API error ({e.response.status_code}): {e.response.text}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def _build_context(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_expenses: bool = True,
        max_expenses: int = 50
    ) -> Dict[str, Any]:
        """Build context data for AI prompts."""
        if not start_date:
            start_date = date.today().replace(day=1).isoformat()
        if not end_date:
            end_date = date.today().isoformat()

        # Get summary statistics
        total_spent = db.get_total_spending(start_date, end_date)
        by_category = db.get_spending_by_category(start_date, end_date)
        by_payment = db.get_spending_by_payment_method(start_date, end_date)
        top_expenses = db.get_top_expenses(start_date, end_date, 10)
        monthly_trend = db.get_monthly_spending()

        # Budget status for current month
        current_month = date.today().strftime("%Y-%m")
        budget_status = expense_service.get_budget_status(current_month)

        context = {
            "period": {"start": start_date, "end": end_date},
            "total_spent": total_spent,
            "by_category": [
                {"category": row["category"], "amount": float(row["total"]), "count": row["count"]}
                for row in by_category
            ],
            "by_payment_method": [
                {"method": row["payment_method"], "amount": float(row["total"]), "count": row["count"]}
                for row in by_payment
            ],
            "top_expenses": [
                {
                    "date": row["date"],
                    "amount": float(row["amount"]),
                    "category": row["category"],
                    "description": row["description"],
                    "payment_method": row["payment_method"],
                    "merchant": row["merchant"]
                }
                for row in top_expenses
            ],
            "monthly_trend": [
                {"month": row["month"], "total": float(row["total"])}
                for row in monthly_trend[-6:]  # Last 6 months
            ],
            "budget_status": budget_status,
            "currency_symbol": Config.CURRENCY_SYMBOL
        }

        if include_expenses:
            expenses = db.get_expenses(start_date=start_date, end_date=end_date, limit=max_expenses)
            context["recent_expenses"] = [
                {
                    "date": row["date"],
                    "amount": float(row["amount"]),
                    "category": row["category"],
                    "description": row["description"],
                    "payment_method": row["payment_method"]
                }
                for row in expenses
            ]

        return context

    def _format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """Format context data as a readable string for the prompt."""
        lines = [
            f"PERIOD: {context['period']['start']} to {context['period']['end']}",
            f"TOTAL SPENT: {context['currency_symbol']}{context['total_spent']:,.2f}",
            "",
            "SPENDING BY CATEGORY:"
        ]
        for cat in context["by_category"]:
            pct = (cat["amount"] / context["total_spent"] * 100) if context["total_spent"] > 0 else 0
            lines.append(f"  - {cat['category']}: {context['currency_symbol']}{cat['amount']:,.2f} ({pct:.1f}%)")

        lines.append("\nSPENDING BY PAYMENT METHOD:")
        for pay in context["by_payment_method"]:
            pct = (pay["amount"] / context["total_spent"] * 100) if context["total_spent"] > 0 else 0
            lines.append(f"  - {pay['method']}: {context['currency_symbol']}{pay['amount']:,.2f} ({pct:.1f}%)")

        lines.append("\nTOP 10 EXPENSES:")
        for exp in context["top_expenses"]:
            lines.append(f"  - {exp['date']}: {context['currency_symbol']}{exp['amount']:,.2f} | {exp['category']} | {exp['description']}")

        lines.append("\nMONTHLY TREND (Last 6 months):")
        for month in context["monthly_trend"]:
            lines.append(f"  - {month['month']}: {context['currency_symbol']}{month['total']:,.2f}")

        budget = context["budget_status"]
        if budget["overall_budget"] > 0:
            lines.append(f"\nOVERALL BUDGET ({budget['month']}): {context['currency_symbol']}{budget['overall_budget']:,.2f}")
            lines.append(f"  SPENT: {context['currency_symbol']}{budget['total_spent']:,.2f} ({budget['overall_percentage']:.1f}%)")
            lines.append(f"  REMAINING: {context['currency_symbol']}{budget['overall_remaining']:,.2f}")
            if budget["overall_warning"] != "ok":
                lines.append(f"  STATUS: {budget['overall_warning'].upper()}")

        if budget["categories"]:
            lines.append("\nCATEGORY BUDGETS:")
            for cat, data in budget["categories"].items():
                if data["budget"] > 0:
                    lines.append(f"  - {cat}: Budget {context['currency_symbol']}{data['budget']:,.2f}, Spent {context['currency_symbol']}{data['spent']:,.2f} ({data['percentage']:.1f}%) [{data['warning']}]")

        return "\n".join(lines)

    def get_spending_summary(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Get AI-generated spending summary for the period."""
        context = self._build_context(start_date, end_date)
        context_str = self._format_context_for_prompt(context)

        prompt = f"""You are a helpful financial analyst. Analyze the following expense data and provide a concise, actionable summary.

{context_str}

Please provide:
1. A 2-3 sentence overview of spending patterns
2. Top 3 observations about where money is going
3. 2-3 practical suggestions for saving money
4. Any unusual patterns you notice

Keep it concise, friendly, and actionable. Use the currency symbol {Config.CURRENCY_SYMBOL}. Do not invent data not in the context."""

        cache_key = self._make_cache_key(f"summary_{context_str}")
        cached = self._get_cached(cache_key)
        if cached:
            return True, cached

        messages = [
            {"role": "system", "content": "You are a personal finance assistant. Provide clear, actionable insights based only on the data provided. Never make up numbers."},
            {"role": "user", "content": prompt}
        ]

        success, response = self._call_api(messages, temperature=0.4)
        if success:
            self._set_cache(cache_key, response)
        return success, response

    def identify_unusual_patterns(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Identify unusual spending patterns."""
        context = self._build_context(start_date, end_date)
        context_str = self._format_context_for_prompt(context)

        prompt = f"""Analyze the following expense data for unusual or noteworthy spending patterns.

{context_str}

Look for:
- Categories with unusually high spending compared to typical patterns
- Large individual expenses that stand out
- Payment method anomalies
- Day-of-week or temporal patterns
- Budget overruns

Respond with:
1. Specific patterns you observe (with numbers from the data)
2. Whether each pattern is concerning or normal
3. One actionable recommendation per pattern

If there's insufficient data for comparison, say so. Be specific with numbers from the data provided."""

        cache_key = self._make_cache_key(f"patterns_{context_str}")
        cached = self._get_cached(cache_key)
        if cached:
            return True, cached

        messages = [
            {"role": "system", "content": "You are a financial analyst. Identify patterns only from the provided data. Be specific with numbers. Admit when data is insufficient."},
            {"role": "user", "content": prompt}
        ]

        success, response = self._call_api(messages, temperature=0.3)
        if success:
            self._set_cache(cache_key, response)
        return success, response

    def suggest_savings_opportunities(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Suggest practical savings opportunities."""
        context = self._build_context(start_date, end_date)
        context_str = self._format_context_for_prompt(context)

        prompt = f"""Based on the following expense data, suggest practical, specific savings opportunities.

{context_str}

Provide 3-5 specific, actionable suggestions. Each should:
- Reference actual spending categories/amounts from the data
- Be realistic and practical for daily life
- Include estimated potential savings
- Be prioritized by impact

Format as a numbered list. Be encouraging but realistic."""

        cache_key = self._make_cache_key(f"savings_{context_str}")
        cached = self._get_cached(cache_key)
        if cached:
            return True, cached

        messages = [
            {"role": "system", "content": "You are a practical financial coach. Suggest realistic savings based only on the provided data. Reference specific numbers."},
            {"role": "user", "content": prompt}
        ]

        success, response = self._call_api(messages, temperature=0.4)
        if success:
            self._set_cache(cache_key, response)
        return success, response

    def compare_periods(
        self,
        current_start: str,
        current_end: str,
        previous_start: str,
        previous_end: str
    ) -> Tuple[bool, str]:
        """Compare spending between two periods."""
        current_context = self._build_context(current_start, current_end)
        prev_context = self._build_context(previous_start, previous_end)

        current_str = self._format_context_for_prompt(current_context)
        prev_str = self._format_context_for_prompt(prev_context)

        prompt = f"""Compare spending between two periods.

CURRENT PERIOD ({current_start} to {current_end}):
{current_str}

PREVIOUS PERIOD ({previous_start} to {previous_end}):
{prev_str}

Provide:
1. Total spending change (amount and percentage)
2. Top category changes
3. New expenses in current period
4. Expenses that decreased
5. Overall assessment: better or worse financial behavior

Be specific with numbers. Calculate percentages from the data provided."""

        cache_key = self._make_cache_key(f"compare_{current_str}_{prev_str}")
        cached = self._get_cached(cache_key)
        if cached:
            return True, cached

        messages = [
            {"role": "system", "content": "You are a financial analyst. Compare periods using only the provided data. Calculate changes accurately."},
            {"role": "user", "content": prompt}
        ]

        success, response = self._call_api(messages, temperature=0.3)
        if success:
            self._set_cache(cache_key, response)
        return success, response

    def explain_budget_overruns(
        self,
        month: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Explain budget overruns for a month."""
        if not month:
            month = date.today().strftime("%Y-%m")

        budget_status = expense_service.get_budget_status(month)
        context = self._build_context(f"{month}-01", f"{month}-31")
        context_str = self._format_context_for_prompt(context)

        overruns = []
        for cat, data in budget_status.get("categories", {}).items():
            if data["warning"] in ("warning", "over"):
                overruns.append(f"  - {cat}: Budget {Config.CURRENCY_SYMBOL}{data['budget']:,.2f}, Spent {Config.CURRENCY_SYMBOL}{data['spent']:,.2f} ({data['percentage']:.1f}%)")

        overrun_str = "\n".join(overruns) if overruns else "No category budgets exceeded."

        prompt = f"""Explain the budget situation for {month}.

{context_str}

BUDGET OVERRUNS:
{overrun_str}

Provide:
1. Which categories are over budget and by how much
2. Specific expenses that contributed to overruns (from the top expenses list)
3. Whether overruns are one-time or recurring
4. 2-3 suggestions to get back on track

Be specific with numbers from the data. Distinguish between essential and discretionary overspending."""

        cache_key = self._make_cache_key(f"budget_{month}_{context_str}")
        cached = self._get_cached(cache_key)
        if cached:
            return True, cached

        messages = [
            {"role": "system", "content": "You are a budget coach. Explain overruns using only provided data. Be specific and constructive."},
            {"role": "user", "content": prompt}
        ]

        success, response = self._call_api(messages, temperature=0.3)
        if success:
            self._set_cache(cache_key, response)
        return success, response

    def answer_question(
        self,
        question: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Answer a natural language question about expenses."""
        context = self._build_context(start_date, end_date, include_expenses=True, max_expenses=100)
        context_str = self._format_context_for_prompt(context)

        prompt = f"""Answer the user's question about their expenses using ONLY the data provided below.

EXPENSE DATA:
{context_str}

USER QUESTION: {question}

Rules:
- Calculate answers from the data provided, don't ask the model to do math
- If the question asks for a specific calculation (e.g., "How much did I spend on food?"), the data above contains the answer
- If data is insufficient, say so clearly
- Distinguish facts (from data) from suggestions/opinions
- Never invent expenses or statistics
- Use {Config.CURRENCY_SYMBOL} for currency
- Be concise and helpful"""

        # Don't cache Q&A as questions vary
        messages = [
            {"role": "system", "content": "You are a personal expense tracker assistant. Answer questions using ONLY the provided expense data. Calculate values from the data. Admit when data is missing."},
            {"role": "user", "content": prompt}
        ]

        return self._call_api(messages, temperature=0.2)

    def get_comprehensive_insights(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all AI insights at once (for dashboard)."""
        if not self.is_configured():
            return {
                "configured": False,
                "message": "NVIDIA API key not configured. Add NVIDIA_API_KEY to .env or Streamlit secrets to enable AI insights."
            }

        results = {"configured": True}

        # Run all insights
        success, summary = self.get_spending_summary(start_date, end_date)
        results["summary"] = summary if success else f"Error: {summary}"

        success, patterns = self.identify_unusual_patterns(start_date, end_date)
        results["patterns"] = patterns if success else f"Error: {patterns}"

        success, savings = self.suggest_savings_opportunities(start_date, end_date)
        results["savings"] = savings if success else f"Error: {savings}"

        success, budget = self.explain_budget_overruns()
        results["budget"] = budget if success else f"Error: {budget}"

        return results


# Global AI service instance
ai_service = AIService()