"""
Tests for the database module.
Uses temporary databases to avoid affecting user data.
"""

import os
import tempfile
import pytest
from datetime import date, timedelta
from pathlib import Path

# Import after setting up test environment
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from database import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override config for testing
        original_db_dir = Config.DATABASE_DIR
        original_db_path = Config.DATABASE_PATH
        Config.DATABASE_DIR = Path(tmpdir)
        Config.DATABASE_PATH = Path(tmpdir) / "test_expenses.db"

        # Create fresh database instance
        db = Database()
        yield db
        db.close()

        # Restore config
        Config.DATABASE_DIR = original_db_dir
        Config.DATABASE_PATH = original_db_path


@pytest.fixture
def sample_expenses(temp_db):
    """Add sample expenses to test database."""
    expenses = [
        ("2025-01-15", 1250.00, "Food & Dining", "Lunch", "UPI", "Restaurant", "Team lunch"),
        ("2025-01-16", 3200.00, "Shopping", "Shoes", "Credit Card", "Store", None),
        ("2025-01-20", 15000.00, "Rent", "January rent", "Bank Transfer", "Landlord", None),
        ("2025-02-05", 890.00, "Food & Dining", "Groceries", "Debit Card", "Market", None),
        ("2025-02-10", 15000.00, "Rent", "February rent", "Bank Transfer", "Landlord", None),
    ]
    ids = []
    for exp in expenses:
        eid = temp_db.add_expense(*exp)
        ids.append(eid)
    return ids


class TestDatabaseBasics:
    """Test basic database operations."""

    def test_database_creation(self, temp_db):
        """Test database file is created."""
        # The database connection creates the file; verify via table existence
        tables = temp_db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [t["name"] for t in tables]
        assert "expenses" in table_names
        assert "budgets" in table_names
        assert "settings" in table_names

    def test_tables_exist(self, temp_db):
        """Test all required tables exist."""
        tables = temp_db.fetchall("""
            SELECT name FROM sqlite_master WHERE type='table'
        """)
        table_names = [t["name"] for t in tables]
        assert "expenses" in table_names
        assert "budgets" in table_names
        assert "settings" in table_names

    def test_indexes_exist(self, temp_db):
        """Test indexes are created."""
        indexes = temp_db.fetchall("""
            SELECT name FROM sqlite_master WHERE type='index'
        """)
        index_names = [i["name"] for i in indexes]
        assert "idx_expenses_date" in index_names
        assert "idx_expenses_category" in index_names


class TestExpenseOperations:
    """Test expense CRUD operations."""

    def test_add_expense(self, temp_db):
        """Test adding an expense."""
        eid = temp_db.add_expense(
            date="2025-01-15",
            amount=1000.00,
            category="Food & Dining",
            description="Test expense",
            payment_method="Cash"
        )
        assert eid > 0

        # Verify it was added
        expense = temp_db.get_expense(eid)
        assert expense is not None
        assert expense["amount"] == 1000.00
        assert expense["category"] == "Food & Dining"
        assert expense["description"] == "Test expense"
        assert expense["payment_method"] == "Cash"
        assert expense["merchant"] is None
        assert expense["notes"] is None

    def test_add_expense_with_optional_fields(self, temp_db):
        """Test adding expense with merchant and notes."""
        eid = temp_db.add_expense(
            date="2025-01-15",
            amount=500.00,
            category="Transportation",
            description="Auto fare",
            payment_method="Cash",
            merchant="Auto driver",
            notes="Rainy day"
        )
        expense = temp_db.get_expense(eid)
        assert expense["merchant"] == "Auto driver"
        assert expense["notes"] == "Rainy day"

    def test_get_expense_not_found(self, temp_db):
        """Test getting non-existent expense returns None."""
        expense = temp_db.get_expense(99999)
        assert expense is None

    def test_update_expense(self, temp_db):
        """Test updating an expense."""
        eid = temp_db.add_expense(
            date="2025-01-15",
            amount=1000.00,
            category="Food & Dining",
            description="Original",
            payment_method="Cash"
        )

        success = temp_db.update_expense(
            expense_id=eid,
            date="2025-01-16",
            amount=1500.00,
            category="Shopping",
            description="Updated",
            payment_method="UPI",
            merchant="Shop",
            notes="Updated note"
        )
        assert success

        expense = temp_db.get_expense(eid)
        # Handle date being returned as date object or string
        exp_date = expense["date"]
        if hasattr(exp_date, 'isoformat'):
            exp_date = exp_date.isoformat()
        assert exp_date == "2025-01-16"
        assert expense["amount"] == 1500.00
        assert expense["category"] == "Shopping"
        assert expense["description"] == "Updated"
        assert expense["payment_method"] == "UPI"
        assert expense["merchant"] == "Shop"
        assert expense["notes"] == "Updated note"

    def test_update_nonexistent_expense(self, temp_db):
        """Test updating non-existent expense returns False."""
        success = temp_db.update_expense(
            expense_id=99999,
            date="2025-01-15",
            amount=1000.00,
            category="Food & Dining",
            description="Test",
            payment_method="Cash"
        )
        assert not success

    def test_delete_expense(self, temp_db):
        """Test deleting an expense."""
        eid = temp_db.add_expense(
            date="2025-01-15",
            amount=1000.00,
            category="Food & Dining",
            description="To delete",
            payment_method="Cash"
        )

        success = temp_db.delete_expense(eid)
        assert success

        expense = temp_db.get_expense(eid)
        assert expense is None

    def test_delete_nonexistent_expense(self, temp_db):
        """Test deleting non-existent expense returns False."""
        success = temp_db.delete_expense(99999)
        assert not success


class TestExpenseQueries:
    """Test expense query and filtering operations."""

    def test_get_expenses_no_filters(self, temp_db, sample_expenses):
        """Test getting all expenses."""
        expenses = temp_db.get_expenses()
        assert len(expenses) == 5

    def test_get_expenses_date_filter(self, temp_db, sample_expenses):
        """Test filtering by date range."""
        # January only
        expenses = temp_db.get_expenses(start_date="2025-01-01", end_date="2025-01-31")
        assert len(expenses) == 3

        # February only
        expenses = temp_db.get_expenses(start_date="2025-02-01", end_date="2025-02-28")
        assert len(expenses) == 2

    def test_get_expenses_category_filter(self, temp_db, sample_expenses):
        """Test filtering by category."""
        expenses = temp_db.get_expenses(category="Food & Dining")
        assert len(expenses) == 2
        assert all(e["category"] == "Food & Dining" for e in expenses)

    def test_get_expenses_payment_filter(self, temp_db, sample_expenses):
        """Test filtering by payment method."""
        expenses = temp_db.get_expenses(payment_method="Bank Transfer")
        assert len(expenses) == 2
        assert all(e["payment_method"] == "Bank Transfer" for e in expenses)

    def test_get_expenses_search_filter(self, temp_db, sample_expenses):
        """Test text search filter."""
        expenses = temp_db.get_expenses(search_text="rent")
        assert len(expenses) == 2
        assert all("rent" in e["description"].lower() for e in expenses)

    def test_get_expenses_amount_filter(self, temp_db, sample_expenses):
        """Test filtering by amount range."""
        expenses = temp_db.get_expenses(min_amount=10000, max_amount=20000)
        assert len(expenses) == 2
        assert all(10000 <= e["amount"] <= 20000 for e in expenses)

    def test_get_expenses_pagination(self, temp_db, sample_expenses):
        """Test limit and offset."""
        expenses = temp_db.get_expenses(limit=2, offset=0)
        assert len(expenses) == 2

        expenses = temp_db.get_expenses(limit=2, offset=2)
        assert len(expenses) == 2

        expenses = temp_db.get_expenses(limit=2, offset=4)
        assert len(expenses) == 1

    def test_count_expenses(self, temp_db, sample_expenses):
        """Test counting expenses with filters."""
        count = temp_db.count_expenses()
        assert count == 5

        count = temp_db.count_expenses(category="Food & Dining")
        assert count == 2

        count = temp_db.count_expenses(start_date="2025-02-01", end_date="2025-02-28")
        assert count == 2


class TestBudgetOperations:
    """Test budget operations."""

    def test_set_overall_budget(self, temp_db):
        """Test setting overall budget."""
        bid = temp_db.set_budget("2025-01", 25000.00)
        assert bid > 0

        budget = temp_db.get_budget("2025-01")
        assert budget is not None
        assert budget["month"] == "2025-01"
        assert budget["category"] is None
        assert budget["amount"] == 25000.00

    def test_set_category_budget(self, temp_db):
        """Test setting category-specific budget."""
        bid = temp_db.set_budget("2025-01", 5000.00, "Food & Dining")
        assert bid > 0

        budget = temp_db.get_budget("2025-01", "Food & Dining")
        assert budget is not None
        assert budget["category"] == "Food & Dining"
        assert budget["amount"] == 5000.00

    def test_update_budget(self, temp_db):
        """Test updating existing budget."""
        temp_db.set_budget("2025-01", 25000.00)
        bid = temp_db.set_budget("2025-01", 30000.00)  # Should update
        assert bid > 0

        budget = temp_db.get_budget("2025-01")
        assert budget["amount"] == 30000.00

    def test_get_budgets_for_month(self, temp_db):
        """Test getting all budgets for a month."""
        temp_db.set_budget("2025-01", 25000.00)
        temp_db.set_budget("2025-01", 5000.00, "Food & Dining")
        temp_db.set_budget("2025-01", 3000.00, "Shopping")

        budgets = temp_db.get_budgets_for_month("2025-01")
        assert len(budgets) == 3

        # Overall budget should be first (category IS NULL)
        assert budgets[0]["category"] is None
        assert budgets[0]["amount"] == 25000.00

    def test_delete_budget(self, temp_db):
        """Test deleting a budget."""
        temp_db.set_budget("2025-01", 25000.00)
        success = temp_db.delete_budget("2025-01")
        assert success

        budget = temp_db.get_budget("2025-01")
        assert budget is None

    def test_delete_category_budget(self, temp_db):
        """Test deleting a category budget."""
        temp_db.set_budget("2025-01", 5000.00, "Food & Dining")
        success = temp_db.delete_budget("2025-01", "Food & Dining")
        assert success

        budget = temp_db.get_budget("2025-01", "Food & Dining")
        assert budget is None


class TestAnalyticsQueries:
    """Test analytics queries."""

    def test_get_total_spending(self, temp_db, sample_expenses):
        """Test total spending calculation."""
        total = temp_db.get_total_spending("2025-01-01", "2025-01-31")
        # 1250 + 3200 + 15000 = 19450
        assert total == 19450.00

        total = temp_db.get_total_spending("2025-02-01", "2025-02-28")
        # 890 + 15000 = 15890
        assert total == 15890.00

    def test_get_spending_by_category(self, temp_db, sample_expenses):
        """Test category-wise spending."""
        cats = temp_db.get_spending_by_category("2025-01-01", "2025-01-31")
        assert len(cats) == 3

        # Should be ordered by total DESC
        amounts = [float(c["total"]) for c in cats]
        assert amounts == sorted(amounts, reverse=True)

        # Check specific values
        cat_dict = {c["category"]: float(c["total"]) for c in cats}
        assert cat_dict["Rent"] == 15000.00
        assert cat_dict["Shopping"] == 3200.00
        assert cat_dict["Food & Dining"] == 1250.00

    def test_get_spending_by_payment_method(self, temp_db, sample_expenses):
        """Test payment method spending."""
        pays = temp_db.get_spending_by_payment_method("2025-01-01", "2025-01-31")
        assert len(pays) == 3

        pay_dict = {p["payment_method"]: float(p["total"]) for p in pays}
        assert pay_dict["Bank Transfer"] == 15000.00
        assert pay_dict["Credit Card"] == 3200.00
        assert pay_dict["UPI"] == 1250.00

    def test_get_daily_spending(self, temp_db, sample_expenses):
        """Test daily spending aggregation."""
        daily = temp_db.get_daily_spending("2025-01-01", "2025-01-31")
        # 3 distinct days in Jan: 15th, 16th, 20th
        assert len(daily) == 3

        totals = {}
        for d in daily:
            date_val = d["date"]
            if hasattr(date_val, 'isoformat'):
                date_val = date_val.isoformat()
            totals[date_val] = float(d["total"])
        
        assert totals["2025-01-15"] == 1250.00
        assert totals["2025-01-16"] == 3200.00
        assert totals["2025-01-20"] == 15000.00

    def test_get_monthly_spending(self, temp_db, sample_expenses):
        """Test monthly spending aggregation."""
        monthly = temp_db.get_monthly_spending()
        assert len(monthly) == 2

        months = {m["month"]: float(m["total"]) for m in monthly}
        assert months["2025-01"] == 19450.00
        assert months["2025-02"] == 15890.00

    def test_get_top_expenses(self, temp_db, sample_expenses):
        """Test top expenses query."""
        top = temp_db.get_top_expenses("2025-01-01", "2025-01-31", limit=2)
        assert len(top) == 2
        assert float(top[0]["amount"]) == 15000.00  # Rent
        assert float(top[1]["amount"]) == 3200.00   # Shopping

    def test_get_category_monthly_trend(self, temp_db, sample_expenses):
        """Test category monthly trend."""
        # Add more rent data for testing trend
        temp_db.add_expense("2025-03-10", 15000.00, "Rent", "March rent", "Bank Transfer", "Landlord", None)
        
        # Use a reference date that includes our test data
        trend = temp_db.get_category_monthly_trend("Rent", months=6, reference_date="2025-03-15")
        # Should find data for Jan, Feb, Mar
        assert len(trend) >= 2
        months = {}
        for t in trend:
            month_val = t["month"]
            if hasattr(month_val, 'isoformat'):
                month_val = month_val.isoformat()[:7]  # Get YYYY-MM
            months[month_val] = float(t["total"])
        
        assert "2025-01" in months
        assert "2025-02" in months
        assert months["2025-01"] == 15000.00
        assert months["2025-02"] == 15000.00


class TestSettings:
    """Test settings operations."""

    def test_get_set_setting(self, temp_db):
        """Test getting and setting settings."""
        # Default value
        val = temp_db.get_setting("nonexistent", "default")
        assert val == "default"

        # Set and get
        temp_db.set_setting("test_key", "test_value")
        val = temp_db.get_setting("test_key")
        assert val == "test_value"

        # Update
        temp_db.set_setting("test_key", "updated_value")
        val = temp_db.get_setting("test_key")
        assert val == "updated_value"

    def test_default_settings(self, temp_db):
        """Test default settings are created."""
        currency = temp_db.get_setting("currency")
        assert currency == "INR"

        symbol = temp_db.get_setting("currency_symbol")
        assert symbol == "₹"

        sample = temp_db.get_setting("sample_data_loaded")
        assert sample == "0"


class TestExport:
    """Test CSV export."""

    def test_export_expenses_csv(self, temp_db, sample_expenses):
        """Test CSV export query."""
        rows = temp_db.export_expenses_csv()
        assert len(rows) == 5

        # Check columns
        row = rows[0]
        assert "id" in row.keys()
        assert "date" in row.keys()
        assert "amount" in row.keys()
        assert "category" in row.keys()
        assert "description" in row.keys()
        assert "payment_method" in row.keys()
        assert "merchant" in row.keys()
        assert "notes" in row.keys()
        assert "created_at" in row.keys()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])