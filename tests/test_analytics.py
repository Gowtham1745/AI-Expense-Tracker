"""
Tests for the analytics module.
"""

import os
import sys
import tempfile
from datetime import date, timedelta

import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from database import Database
from analytics import Analytics


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_db_dir = Config.DATABASE_DIR
        original_db_path = Config.DATABASE_PATH
        Config.DATABASE_DIR = Path(tmpdir)
        Config.DATABASE_PATH = Path(tmpdir) / "test_expenses.db"

        db = Database()

        # Add test data
        test_expenses = [
            ("2025-01-01", 1000.00, "Food & Dining", "Breakfast", "Cash", None, None),
            ("2025-01-01", 2000.00, "Transportation", "Taxi", "UPI", None, None),
            ("2025-01-02", 1500.00, "Food & Dining", "Lunch", "Card", None, None),
            ("2025-01-03", 5000.00, "Shopping", "Clothes", "Credit Card", None, None),
            ("2025-01-05", 15000.00, "Rent", "January rent", "Bank Transfer", None, None),
            ("2025-02-01", 1000.00, "Food & Dining", "Breakfast", "Cash", None, None),
            ("2025-02-10", 15000.00, "Rent", "February rent", "Bank Transfer", None, None),
            ("2025-02-15", 3000.00, "Entertainment", "Movie", "UPI", None, None),
        ]
        for exp in test_expenses:
            db.add_expense(*exp)

        # Add budgets
        db.set_budget("2025-01", 25000.00)
        db.set_budget("2025-01", 5000.00, "Food & Dining")
        db.set_budget("2025-02", 25000.00)

        yield db
        db.close()

        Config.DATABASE_DIR = original_db_dir
        Config.DATABASE_PATH = original_db_path


from pathlib import Path


class TestAnalyticsCalculations:
    """Test analytics calculation functions."""

    def test_calculate_period_stats(self, temp_db):
        """Test period statistics calculation."""
        stats = Analytics.calculate_period_stats("2025-01-01", "2025-01-31")

        assert stats["total"] == 24500.00  # 1000+2000+1500+5000+15000
        assert stats["count"] == 5
        assert stats["average"] == 4900.00
        assert stats["daily_average"] == 24500.00 / 31  # 31 days in Jan

        # Top category should be Rent
        assert stats["top_category"] == "Rent"
        assert stats["top_category_amount"] == 15000.00

        # Category breakdown
        assert stats["by_category"]["Rent"] == 15000.00
        assert stats["by_category"]["Food & Dining"] == 2500.00
        assert stats["by_category"]["Shopping"] == 5000.00
        assert stats["by_category"]["Transportation"] == 2000.00

        # Payment breakdown
        assert stats["by_payment"]["Bank Transfer"] == 15000.00
        assert stats["by_payment"]["Cash"] == 1000.00
        assert stats["by_payment"]["UPI"] == 2000.00
        assert stats["by_payment"]["Credit Card"] == 5000.00

        # Largest expense
        assert stats["largest_expense"]["amount"] == 15000.00
        assert stats["largest_expense"]["category"] == "Rent"

    def test_calculate_period_stats_empty(self, temp_db):
        """Test stats for period with no data."""
        stats = Analytics.calculate_period_stats("2025-03-01", "2025-03-31")

        assert stats["total"] == 0.0
        assert stats["count"] == 0
        assert stats["average"] == 0.0
        assert stats["daily_average"] == 0.0
        assert stats["top_category"] is None
        assert stats["largest_expense"] is None

    def test_format_currency(self):
        """Test currency formatting."""
        assert Analytics.format_currency(0) == "₹0.00"
        assert Analytics.format_currency(500) == "₹500.00"
        assert Analytics.format_currency(1250.50) == "₹1,250.50"
        assert Analytics.format_currency(100000) == "₹1.00 L"
        assert Analytics.format_currency(15000000) == "₹1.50 Cr"

    def test_get_date_range_options(self):
        """Test date range options."""
        ranges = Analytics.get_date_range_options()

        assert "Today" in ranges
        assert "This Week" in ranges
        assert "This Month" in ranges
        assert "Last Month" in ranges
        assert "Last 3 Months" in ranges
        assert "Last 6 Months" in ranges
        assert "This Year" in ranges
        assert "All Time" in ranges

        # All Time should return (None, None)
        assert ranges["All Time"] == (None, None)

    def test_get_previous_period(self):
        """Test previous period calculation."""
        # 30-day period
        prev_start, prev_end = Analytics.get_previous_period("2025-01-01", "2025-01-30")
        assert prev_start == "2024-12-02"
        assert prev_end == "2024-12-31"

        # 7-day period
        prev_start, prev_end = Analytics.get_previous_period("2025-01-01", "2025-01-07")
        assert prev_start == "2024-12-25"
        assert prev_end == "2024-12-31"


class TestChartCreation:
    """Test chart creation functions."""

    def test_create_spending_trend_chart(self, temp_db):
        """Test daily trend chart creation."""
        fig = Analytics.create_spending_trend_chart("2025-01-01", "2025-01-31")
        assert fig is not None
        assert len(fig.data) >= 1

    def test_create_spending_trend_chart_with_comparison(self, temp_db):
        """Test trend chart with previous period."""
        fig = Analytics.create_spending_trend_chart(
            "2025-01-01", "2025-01-31", compare_previous=True
        )
        assert fig is not None
        assert len(fig.data) >= 1

    def test_create_category_pie_chart(self, temp_db):
        """Test category pie chart."""
        fig = Analytics.create_category_pie_chart("2025-01-01", "2025-01-31")
        assert fig is not None
        assert len(fig.data) == 1
        assert fig.data[0].type == "pie"

    def test_create_payment_method_chart(self, temp_db):
        """Test payment method chart."""
        fig = Analytics.create_payment_method_chart("2025-01-01", "2025-01-31")
        assert fig is not None
        assert len(fig.data) == 1
        assert fig.data[0].type == "bar"

    def test_create_monthly_comparison_chart(self, temp_db):
        """Test monthly comparison chart."""
        fig = Analytics.create_monthly_comparison_chart()
        assert fig is not None
        assert len(fig.data) == 1
        assert fig.data[0].type == "bar"

    def test_create_category_monthly_trend(self, temp_db):
        """Test category trend chart."""
        fig = Analytics.create_category_monthly_trend("Rent", months=6)
        assert fig is not None
        assert len(fig.data) == 1
        assert fig.data[0].type == "scatter"

    def test_create_budget_gauge_no_budget(self, temp_db):
        """Test gauge with no budget."""
        fig = Analytics.create_budget_gauge(1000, 0)
        assert fig is not None
        assert len(fig.data) == 1
        assert fig.data[0].type == "indicator"

    def test_create_budget_gauge_with_budget(self, temp_db):
        """Test gauge with budget."""
        fig = Analytics.create_budget_gauge(20000, 25000)
        assert fig is not None
        assert len(fig.data) == 1
        assert fig.data[0].type == "indicator"

    def test_create_budget_gauge_over_budget(self, temp_db):
        """Test gauge when over budget."""
        fig = Analytics.create_budget_gauge(30000, 25000)
        assert fig is not None

    def test_create_budget_bar_chart(self, temp_db):
        """Test budget bar chart."""
        budget_status = {
            "categories": {
                "Food & Dining": {"budget": 5000, "spent": 2500, "warning": "ok"},
                "Shopping": {"budget": 3000, "spent": 3500, "warning": "over"},
            }
        }
        fig = Analytics.create_budget_bar_chart(budget_status)
        assert fig is not None
        assert len(fig.data) == 2

    def test_create_top_expenses_chart(self, temp_db):
        """Test top expenses chart."""
        fig = Analytics.create_top_expenses_chart("2025-01-01", "2025-01-31", limit=5)
        assert fig is not None
        assert len(fig.data) == 1

    def test_create_weekly_spending_chart(self, temp_db):
        """Test weekly spending chart."""
        fig = Analytics.create_weekly_spending_chart("2025-01-01", "2025-01-31")
        assert fig is not None


class TestSummaryCards:
    """Test summary card generation."""

    def test_get_summary_cards(self, temp_db):
        """Test summary cards data."""
        summary = Analytics.get_summary_cards("2025-01-01", "2025-01-31")

        assert "total_spending" in summary
        assert "daily_average" in summary
        assert "top_category" in summary
        assert "transaction_count" in summary
        assert "average_transaction" in summary

        assert summary["total_spending"]["value"] == 24500.00
        assert summary["transaction_count"] == 5
        assert summary["top_category"]["name"] == "Rent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])