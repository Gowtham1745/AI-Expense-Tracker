"""
Analytics and visualization module for Keerthi AI Expense Tracker.
Provides data processing and Plotly chart generation.
"""

from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import calendar

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from database import db
from config import Config


class Analytics:
    """Analytics and chart generation service."""

    # Color scheme
    COLORS = {
        "primary": "#10B981",      # Emerald
        "primary_light": "#34D399",
        "primary_dark": "#059669",
        "background": "#0F172A",   # Dark navy
        "surface": "#1E293B",
        "surface_light": "#334155",
        "text": "#F1F5F9",
        "text_muted": "#94A3B8",
        "border": "#334155",
        "red": "#EF4444",
        "orange": "#F97316",
        "yellow": "#EAB308",
        "blue": "#3B82F6",
        "purple": "#A855F7",
        "pink": "#EC4899",
    }

    CATEGORY_COLORS = {
        "Food & Dining": "#EF4444",
        "Transportation": "#F97316",
        "Shopping": "#EAB308",
        "Bills & Utilities": "#3B82F6",
        "Rent": "#8B5CF6",
        "Education": "#EC4899",
        "Healthcare": "#14B8A6",
        "Entertainment": "#F43F5E",
        "Travel": "#06B6D4",
        "Personal Care": "#A855F7",
        "Investments": "#10B981",
        "Other": "#64748B",
    }

    PAYMENT_COLORS = {
        "Cash": "#EF4444",
        "UPI": "#10B981",
        "Debit Card": "#3B82F6",
        "Credit Card": "#8B5CF6",
        "Bank Transfer": "#F97316",
        "Other": "#64748B",
    }

    @staticmethod
    def get_layout_base(title: str = "", height: int = 400) -> Dict[str, Any]:
        """Get base Plotly layout with dark theme."""
        return {
            "title": {
                "text": title,
                "font": {"color": Analytics.COLORS["text"], "size": 16, "family": "Inter, sans-serif"},
                "x": 0.02,
                "xanchor": "left"
            },
            "paper_bgcolor": Analytics.COLORS["surface"],
            "plot_bgcolor": Analytics.COLORS["surface"],
            "font": {"color": Analytics.COLORS["text"], "family": "Inter, sans-serif", "size": 12},
            "height": height,
            "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
            "xaxis": {
                "gridcolor": Analytics.COLORS["border"],
                "zerolinecolor": Analytics.COLORS["border"],
                "tickfont": {"color": Analytics.COLORS["text_muted"]},
                "titlefont": {"color": Analytics.COLORS["text_muted"]}
            },
            "yaxis": {
                "gridcolor": Analytics.COLORS["border"],
                "zerolinecolor": Analytics.COLORS["border"],
                "tickfont": {"color": Analytics.COLORS["text_muted"]},
                "titlefont": {"color": Analytics.COLORS["text_muted"]}
            },
            "legend": {
                "bgcolor": "rgba(30, 41, 59, 0.8)",
                "bordercolor": Analytics.COLORS["border"],
                "borderwidth": 1,
                "font": {"color": Analytics.COLORS["text"], "size": 11},
                "orientation": "h",
                "yanchor": "bottom",
                "y": -0.25,
                "xanchor": "center",
                "x": 0.5
            },
            "hoverlabel": {
                "bgcolor": Analytics.COLORS["surface_light"],
                "font": {"color": Analytics.COLORS["text"], "size": 12},
                "bordercolor": Analytics.COLORS["border"]
            }
        }

    @staticmethod
    def format_currency(amount: float, symbol: str = Config.CURRENCY_SYMBOL) -> str:
        """Format amount as Indian currency."""
        if amount >= 10000000:  # 1 crore
            return f"{symbol}{amount/10000000:.2f} Cr"
        elif amount >= 100000:  # 1 lakh
            return f"{symbol}{amount/100000:.2f} L"
        elif amount >= 1000:
            return f"{symbol}{amount:,.2f}"
        else:
            return f"{symbol}{amount:.2f}"

    @staticmethod
    def get_date_range_options() -> Dict[str, Tuple[str, str]]:
        """Get predefined date range options."""
        today = date.today()
        ranges = {}

        # Today
        ranges["Today"] = (today.isoformat(), today.isoformat())

        # This week (Monday to Sunday)
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        ranges["This Week"] = (start_week.isoformat(), end_week.isoformat())

        # This month
        start_month = today.replace(day=1)
        if today.month == 12:
            end_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        ranges["This Month"] = (start_month.isoformat(), end_month.isoformat())

        # Last month
        if today.month == 1:
            last_month_start = today.replace(year=today.year - 1, month=12, day=1)
        else:
            last_month_start = today.replace(month=today.month - 1, day=1)
        last_month_end = start_month - timedelta(days=1)
        ranges["Last Month"] = (last_month_start.isoformat(), last_month_end.isoformat())

        # Last 3 months
        three_months_ago = today.replace(day=1) - timedelta(days=1)
        three_months_ago = three_months_ago.replace(day=1)
        for _ in range(2):
            three_months_ago = (three_months_ago - timedelta(days=1)).replace(day=1)
        ranges["Last 3 Months"] = (three_months_ago.isoformat(), end_month.isoformat())

        # Last 6 months
        six_months_ago = today.replace(day=1)
        for _ in range(5):
            six_months_ago = (six_months_ago - timedelta(days=1)).replace(day=1)
        ranges["Last 6 Months"] = (six_months_ago.isoformat(), end_month.isoformat())

        # This year
        start_year = today.replace(month=1, day=1)
        ranges["This Year"] = (start_year.isoformat(), today.isoformat())

        # All time
        ranges["All Time"] = (None, None)

        return ranges

    @staticmethod
    def get_period_dates(period_key: str) -> Tuple[Optional[str], Optional[str]]:
        """Get start and end dates for a period key."""
        ranges = Analytics.get_date_range_options()
        return ranges.get(period_key, (None, None))

    @staticmethod
    def get_previous_period(start_date: str, end_date: str) -> Tuple[str, str]:
        """Get the previous equivalent period for comparison."""
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        days_diff = (end - start).days + 1

        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days_diff - 1)

        return (prev_start.isoformat(), prev_end.isoformat())

    @staticmethod
    def calculate_period_stats(start_date: str, end_date: str) -> Dict[str, Any]:
        """Calculate comprehensive statistics for a period."""
        expenses = db.get_expenses(start_date=start_date, end_date=end_date)

        if not expenses:
            return {
                "total": 0.0,
                "count": 0,
                "average": 0.0,
                "daily_average": 0.0,
                "top_category": None,
                "top_category_amount": 0.0,
                "by_category": {},
                "by_payment": {},
                "daily_totals": [],
                "largest_expense": None
            }

        df = pd.DataFrame([dict(row) for row in expenses])
        df["date"] = pd.to_datetime(df["date"])
        df["amount"] = pd.to_numeric(df["amount"])

        total = df["amount"].sum()
        count = len(df)
        average = total / count if count > 0 else 0

        # Daily average
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        days_in_period = (end_dt - start_dt).days + 1
        daily_average = total / days_in_period if days_in_period > 0 else 0

        # By category
        by_category = df.groupby("category")["amount"].sum().sort_values(ascending=False)
        top_category = by_category.index[0] if len(by_category) > 0 else None
        top_category_amount = float(by_category.iloc[0]) if len(by_category) > 0 else 0

        # By payment method
        by_payment = df.groupby("payment_method")["amount"].sum().sort_values(ascending=False)

        # Daily totals
        daily_totals = df.groupby("date")["amount"].sum().reset_index()
        daily_totals = daily_totals.rename(columns={"date": "date", "amount": "total"})
        daily_totals["date"] = daily_totals["date"].dt.strftime("%Y-%m-%d")

        # Largest expense
        largest = df.loc[df["amount"].idxmax()] if len(df) > 0 else None
        largest_expense = {
            "id": int(largest["id"]),
            "date": largest["date"].strftime("%Y-%m-%d"),
            "amount": float(largest["amount"]),
            "category": largest["category"],
            "description": largest["description"]
        } if largest is not None else None

        return {
            "total": float(total),
            "count": int(count),
            "average": float(average),
            "daily_average": float(daily_average),
            "top_category": top_category,
            "top_category_amount": float(top_category_amount),
            "by_category": {k: float(v) for k, v in by_category.items()},
            "by_payment": {k: float(v) for k, v in by_payment.items()},
            "daily_totals": daily_totals.to_dict("records"),
            "largest_expense": largest_expense
        }

    @staticmethod
    def create_spending_trend_chart(
        start_date: str,
        end_date: str,
        compare_previous: bool = False
    ) -> go.Figure:
        """Create daily spending trend chart."""
        daily_data = db.get_daily_spending(start_date, end_date)

        fig = go.Figure()

        if daily_data:
            dates = [row["date"] for row in daily_data]
            totals = [float(row["total"]) for row in daily_data]

            fig.add_trace(go.Scatter(
                x=dates,
                y=totals,
                mode="lines+markers",
                name="Daily Spending",
                line={"color": Analytics.COLORS["primary"], "width": 2.5, "shape": "spline"},
                marker={"size": 6, "color": Analytics.COLORS["primary"]},
                fill="tozeroy",
                fillcolor="rgba(16, 185, 129, 0.1)",
                hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>"
            ))

        # Previous period comparison
        if compare_previous:
            prev_start, prev_end = Analytics.get_previous_period(start_date, end_date)
            prev_data = db.get_daily_spending(prev_start, prev_end)
            if prev_data:
                prev_dates = [row["date"] for row in prev_data]
                prev_totals = [float(row["total"]) for row in prev_data]
                fig.add_trace(go.Scatter(
                    x=prev_dates,
                    y=prev_totals,
                    mode="lines",
                    name="Previous Period",
                    line={"color": Analytics.COLORS["text_muted"], "width": 2, "dash": "dash"},
                    hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>"
                ))

        layout = Analytics.get_layout_base("Daily Spending Trend", 350)
        layout["xaxis"]["title"] = "Date"
        layout["yaxis"]["title"] = f"Amount ({Config.CURRENCY_SYMBOL})"
        fig.update_layout(layout)

        return fig

    @staticmethod
    def create_category_pie_chart(start_date: str, end_date: str) -> go.Figure:
        """Create category-wise spending pie chart."""
        cat_data = db.get_spending_by_category(start_date, end_date)

        fig = go.Figure()

        if cat_data:
            labels = [row["category"] for row in cat_data]
            values = [float(row["total"]) for row in cat_data]
            colors = [Analytics.CATEGORY_COLORS.get(cat, Analytics.COLORS["primary"]) for cat in labels]

            fig.add_trace(go.Pie(
                labels=labels,
                values=values,
                hole=0.5,
                marker={"colors": colors, "line": {"color": Analytics.COLORS["surface"], "width": 2}},
                textinfo="label+percent",
                textfont={"color": Analytics.COLORS["text"], "size": 11},
                hovertemplate="%{label}<br>%{value:,.2f} (%{percent})<extra></extra>",
                pull=[0.02 if i == 0 else 0 for i in range(len(labels))]
            ))

        layout = Analytics.get_layout_base("Spending by Category", 350)
        layout["showlegend"] = True
        layout["legend"]["orientation"] = "v"
        layout["legend"]["x"] = 1.02
        layout["legend"]["y"] = 0.5
        layout["margin"]["r"] = 180
        fig.update_layout(layout)

        return fig

    @staticmethod
    def create_payment_method_chart(start_date: str, end_date: str) -> go.Figure:
        """Create payment method breakdown chart."""
        pay_data = db.get_spending_by_payment_method(start_date, end_date)

        fig = go.Figure()

        if pay_data:
            labels = [row["payment_method"] for row in pay_data]
            values = [float(row["total"]) for row in pay_data]
            colors = [Analytics.PAYMENT_COLORS.get(pay, Analytics.COLORS["primary"]) for pay in labels]

            fig.add_trace(go.Bar(
                x=labels,
                y=values,
                marker={"color": colors},
                text=[Analytics.format_currency(v) for v in values],
                textposition="outside",
                textfont={"color": Analytics.COLORS["text"], "size": 11},
                hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>"
            ))

        layout = Analytics.get_layout_base("Spending by Payment Method", 300)
        layout["xaxis"]["title"] = "Payment Method"
        layout["yaxis"]["title"] = f"Amount ({Config.CURRENCY_SYMBOL})"
        layout["showlegend"] = False
        fig.update_layout(layout)

        return fig

    @staticmethod
    def create_monthly_comparison_chart() -> go.Figure:
        """Create monthly spending comparison chart."""
        monthly_data = db.get_monthly_spending()

        fig = go.Figure()

        if monthly_data:
            months = [row["month"] for row in monthly_data]
            totals = [float(row["total"]) for row in monthly_data]

            fig.add_trace(go.Bar(
                x=months,
                y=totals,
                marker={"color": Analytics.COLORS["primary"]},
                text=[Analytics.format_currency(v) for v in totals],
                textposition="outside",
                textfont={"color": Analytics.COLORS["text"], "size": 11},
                hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
                name="Monthly Spending"
            ))

        layout = Analytics.get_layout_base("Monthly Spending Comparison", 350)
        layout["xaxis"]["title"] = "Month"
        layout["yaxis"]["title"] = f"Amount ({Config.CURRENCY_SYMBOL})"
        layout["showlegend"] = False
        fig.update_layout(layout)

        return fig

    @staticmethod
    def create_category_monthly_trend(category: str, months: int = 6, reference_date: Optional[str] = None) -> go.Figure:
        """Create monthly trend for a specific category."""
        trend_data = db.get_category_monthly_trend(category, months, reference_date)

        fig = go.Figure()

        if trend_data:
            months_labels = [row["month"] for row in trend_data]
            totals = [float(row["total"]) for row in trend_data]
            color = Analytics.CATEGORY_COLORS.get(category, Analytics.COLORS["primary"])
            # Plotly expects rgba() or 6-digit hex; an 8-digit hex suffix is not
            # accepted by every supported Plotly version.
            hex_color = color.lstrip("#")
            if len(hex_color) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in hex_color):
                red, green, blue = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
                fill_color = f"rgba({red}, {green}, {blue}, 0.12)"
            else:
                fill_color = color

            fig.add_trace(go.Scatter(
                x=months_labels,
                y=totals,
                mode="lines+markers",
                name=category,
                line={"color": color, "width": 3, "shape": "spline"},
                marker={"size": 8, "color": color},
                fill="tozeroy",
                fillcolor=fill_color,
                hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>"
            ))

        layout = Analytics.get_layout_base(f"{category} Monthly Trend", 300)
        layout["xaxis"]["title"] = "Month"
        layout["yaxis"]["title"] = f"Amount ({Config.CURRENCY_SYMBOL})"
        layout["showlegend"] = False
        fig.update_layout(layout)

        return fig

    @staticmethod
    def create_budget_gauge(
        spent: float,
        budget: float,
        title: str = "Budget Usage"
    ) -> go.Figure:
        """Create a gauge chart for budget usage."""
        if budget <= 0:
            # No budget set
            fig = go.Figure(go.Indicator(
                mode="number",
                value=spent,
                number={"prefix": Config.CURRENCY_SYMBOL, "font": {"size": 32, "color": Analytics.COLORS["text"]}},
                title={"text": "No Budget Set", "font": {"color": Analytics.COLORS["text_muted"], "size": 14}},
            ))
            fig.update_layout(
                paper_bgcolor=Analytics.COLORS["surface"],
                height=200,
                margin={"l": 20, "r": 20, "t": 40, "b": 20}
            )
            return fig

        percentage = (spent / budget) * 100

        # Determine color based on usage
        if percentage >= 100:
            gauge_color = Analytics.COLORS["red"]
        elif percentage >= 80:
            gauge_color = Analytics.COLORS["orange"]
        else:
            gauge_color = Analytics.COLORS["primary"]

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=spent,
            delta={"reference": budget, "relative": True, "valueformat": ".1%", "font": {"size": 14}},
            number={"prefix": Config.CURRENCY_SYMBOL, "font": {"size": 28, "color": Analytics.COLORS["text"]}},
            title={"text": title, "font": {"color": Analytics.COLORS["text"], "size": 14}},
            gauge={
                "axis": {"range": [0, budget * 1.2], "tickcolor": Analytics.COLORS["text_muted"]},
                "bar": {"color": gauge_color, "thickness": 0.3},
                "bgcolor": Analytics.COLORS["surface_light"],
                "borderwidth": 1,
                "bordercolor": Analytics.COLORS["border"],
                "steps": [
                    {"range": [0, budget * 0.5], "color": "rgba(16, 185, 129, 0.2)"},
                    {"range": [budget * 0.5, budget * 0.8], "color": "rgba(234, 179, 8, 0.2)"},
                    {"range": [budget * 0.8, budget], "color": "rgba(249, 115, 22, 0.2)"},
                    {"range": [budget, budget * 1.2], "color": "rgba(239, 68, 68, 0.2)"}
                ],
                "threshold": {
                    "line": {"color": Analytics.COLORS["red"], "width": 3},
                    "thickness": 0.8,
                    "value": budget
                }
            }
        ))

        fig.update_layout(
            paper_bgcolor=Analytics.COLORS["surface"],
            height=220,
            margin={"l": 20, "r": 20, "t": 40, "b": 20},
            font={"color": Analytics.COLORS["text"], "family": "Inter, sans-serif"}
        )

        return fig

    @staticmethod
    def create_budget_bar_chart(budget_status: Dict[str, Any]) -> go.Figure:
        """Create horizontal bar chart for category budgets."""
        categories = budget_status.get("categories", {})

        fig = go.Figure()

        if categories:
            cats = list(categories.keys())
            budgets = [categories[c]["budget"] for c in cats]
            spent = [categories[c]["spent"] for c in cats]

            fig.add_trace(go.Bar(
                y=cats,
                x=budgets,
                orientation="h",
                name="Budget",
                marker={"color": Analytics.COLORS["surface_light"]},
                hovertemplate="Budget: %{x:,.2f}<extra></extra>"
            ))

            fig.add_trace(go.Bar(
                y=cats,
                x=spent,
                orientation="h",
                name="Spent",
                marker={"color": Analytics.COLORS["primary"]},
                hovertemplate="Spent: %{x:,.2f}<extra></extra>"
            ))

            # Add over-budget markers
            for i, cat in enumerate(cats):
                if categories[cat]["warning"] == "over":
                    fig.add_annotation(
                        x=spent[i],
                        y=cat,
                        text="⚠ Over budget",
                        showarrow=False,
                        font={"color": Analytics.COLORS["red"], "size": 10},
                        xanchor="left",
                        xshift=5
                    )

        layout = Analytics.get_layout_base("Category Budgets vs Actual", 400)
        layout["barmode"] = "overlay"
        layout["xaxis"]["title"] = f"Amount ({Config.CURRENCY_SYMBOL})"
        layout["yaxis"]["title"] = ""
        layout["legend"]["orientation"] = "h"
        layout["legend"]["y"] = -0.15
        fig.update_layout(layout)

        return fig

    @staticmethod
    def create_top_expenses_chart(start_date: str, end_date: str, limit: int = 10) -> go.Figure:
        """Create chart of top expenses."""
        top_expenses = db.get_top_expenses(start_date, end_date, limit)

        fig = go.Figure()

        if top_expenses:
            labels = [f"{row['description'][:30]}..." if len(row['description']) > 30 else row['description'] for row in top_expenses]
            values = [float(row["amount"]) for row in top_expenses]
            cats = [row["category"] for row in top_expenses]
            colors = [Analytics.CATEGORY_COLORS.get(cat, Analytics.COLORS["primary"]) for cat in cats]

            fig.add_trace(go.Bar(
                y=labels[::-1],  # Reverse for top-to-bottom
                x=values[::-1],
                orientation="h",
                marker={"color": colors[::-1]},
                text=[Analytics.format_currency(v) for v in values[::-1]],
                textposition="outside",
                textfont={"color": Analytics.COLORS["text"], "size": 11},
                hovertemplate="%{y}<br>%{x:,.2f}<extra></extra>"
            ))

        layout = Analytics.get_layout_base(f"Top {limit} Expenses", 400)
        layout["xaxis"]["title"] = f"Amount ({Config.CURRENCY_SYMBOL})"
        layout["yaxis"]["title"] = ""
        layout["showlegend"] = False
        layout["margin"]["l"] = 200
        fig.update_layout(layout)

        return fig

    @staticmethod
    def create_weekly_spending_chart(start_date: str, end_date: str) -> go.Figure:
        """Create weekly spending aggregation chart."""
        expenses = db.get_expenses(start_date=start_date, end_date=end_date)

        fig = go.Figure()

        if expenses:
            df = pd.DataFrame([dict(row) for row in expenses])
            df["date"] = pd.to_datetime(df["date"])
            df["amount"] = pd.to_numeric(df["amount"])
            df["week"] = df["date"].dt.strftime("%Y-W%U")

            weekly = df.groupby("week")["amount"].sum().reset_index()
            weekly = weekly.sort_values("week")

            fig.add_trace(go.Bar(
                x=weekly["week"],
                y=weekly["amount"],
                marker={"color": Analytics.COLORS["primary"]},
                text=[Analytics.format_currency(v) for v in weekly["amount"]],
                textposition="outside",
                textfont={"color": Analytics.COLORS["text"], "size": 10},
                hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>"
            ))

        layout = Analytics.get_layout_base("Weekly Spending", 300)
        layout["xaxis"]["title"] = "Week"
        layout["yaxis"]["title"] = f"Amount ({Config.CURRENCY_SYMBOL})"
        layout["showlegend"] = False
        fig.update_layout(layout)

        return fig

    @staticmethod
    def get_summary_cards(start_date: str, end_date: str) -> Dict[str, Any]:
        """Get summary statistics for dashboard cards."""
        stats = Analytics.calculate_period_stats(start_date, end_date)

        # Previous period comparison
        prev_start, prev_end = Analytics.get_previous_period(start_date, end_date)
        prev_stats = Analytics.calculate_period_stats(prev_start, prev_end)

        total = stats["total"]
        prev_total = prev_stats["total"]
        change_pct = ((total - prev_total) / prev_total * 100) if prev_total > 0 else 0

        return {
            "total_spending": {
                "value": total,
                "formatted": Analytics.format_currency(total),
                "change": change_pct,
                "change_formatted": f"{change_pct:+.1f}%",
                "period": f"{start_date} to {end_date}"
            },
            "current_month": {
                "value": stats["total"],
                "formatted": Analytics.format_currency(stats["total"]),
            },
            "today": {
                "value": 0,  # Would need today's date filter
                "formatted": Analytics.format_currency(0),
            },
            "daily_average": {
                "value": stats["daily_average"],
                "formatted": Analytics.format_currency(stats["daily_average"]),
            },
            "top_category": {
                "name": stats["top_category"],
                "amount": stats["top_category_amount"],
                "formatted": Analytics.format_currency(stats["top_category_amount"]),
            },
            "transaction_count": stats["count"],
            "average_transaction": Analytics.format_currency(stats["average"])
        }


# Global analytics instance
analytics = Analytics()