"""
Tests for the expense service module.
"""

import os
import sys
import tempfile
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as database_module
import expense_service as expense_service_module
from config import Config
from database import Database
from expense_service import expense_service, ExpenseService, Expense, Budget


@pytest.fixture
def temp_db(monkeypatch):
    """Create an isolated temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_db_dir = Config.DATABASE_DIR
        original_db_path = Config.DATABASE_PATH
        Config.DATABASE_DIR = Path(tmpdir)
        Config.DATABASE_PATH = Path(tmpdir) / "test_expenses.db"

        db = Database()
        monkeypatch.setattr(database_module, "db", db)
        monkeypatch.setattr(expense_service_module, "db", db)
        yield db
        db.close()

        Config.DATABASE_DIR = original_db_dir
        Config.DATABASE_PATH = original_db_path


from pathlib import Path


class TestExpenseValidation:
    """Test expense validation."""

    def test_valid_expense(self, temp_db):
        """Test validation passes for valid expense."""
        is_valid, error = ExpenseService.validate_expense(
            amount=1000.00,
            expense_date="2025-01-15",
            category="Food & Dining",
            description="Lunch",
            payment_method="Cash"
        )
        assert is_valid
        assert error is None

    def test_invalid_amount_zero(self, temp_db):
        """Test validation fails for zero amount."""
        is_valid, error = ExpenseService.validate_expense(
            amount=0,
            expense_date="2025-01-15",
            category="Food & Dining",
            description="Lunch",
            payment_method="Cash"
        )
        assert not is_valid
        assert "positive" in error.lower()

    def test_invalid_amount_negative(self, temp_db):
        """Test validation fails for negative amount."""
        is_valid, error = ExpenseService.validate_expense(
            amount=-100,
            expense_date="2025-01-15",
            category="Food & Dining",
            description="Lunch",
            payment_method="Cash"
        )
        assert not is_valid
        assert "positive" in error.lower()

    def test_invalid_amount_nan(self, temp_db):
        """Test validation fails for NaN."""
        is_valid, error = ExpenseService.validate_expense(
            amount=float('nan'),
            expense_date="2025-01-15",
            category="Food & Dining",
            description="Lunch",
            payment_method="Cash"
        )
        assert not is_valid
        assert "finite" in error.lower() or "nan" in error.lower()

    def test_invalid_amount_infinity(self, temp_db):
        """Test validation fails for infinity."""
        is_valid, error = ExpenseService.validate_expense(
            amount=float('inf'),
            expense_date="2025-01-15",
            category="Food & Dining",
            description="Lunch",
            payment_method="Cash"
        )
        assert not is_valid
        assert "finite" in error.lower()

    def test_invalid_date_format(self, temp_db):
        """Test validation fails for invalid date format."""
        is_valid, error = ExpenseService.validate_expense(
            amount=1000,
            expense_date="15-01-2025",
            category="Food & Dining",
            description="Lunch",
            payment_method="Cash"
        )
        assert not is_valid
        assert "format" in error.lower()

    def test_invalid_future_date(self, temp_db):
        """Test validation fails for future date."""
        future = (date.today() + timedelta(days=1)).isoformat()
        is_valid, error = ExpenseService.validate_expense(
            amount=1000,
            expense_date=future,
            category="Food & Dining",
            description="Lunch",
            payment_method="Cash"
        )
        assert not is_valid
        assert "future" in error.lower()

    def test_invalid_category(self, temp_db):
        """Test validation fails for invalid category."""
        is_valid, error = ExpenseService.validate_expense(
            amount=1000,
            expense_date="2025-01-15",
            category="Invalid Category",
            description="Lunch",
            payment_method="Cash"
        )
        assert not is_valid
        assert "category" in error.lower()

    def test_empty_description(self, temp_db):
        """Test validation fails for empty description."""
        is_valid, error = ExpenseService.validate_expense(
            amount=1000,
            expense_date="2025-01-15",
            category="Food & Dining",
            description="",
            payment_method="Cash"
        )
        assert not is_valid
        assert "description" in error.lower()

    def test_invalid_payment_method(self, temp_db):
        """Test validation fails for invalid payment method."""
        is_valid, error = ExpenseService.validate_expense(
            amount=1000,
            expense_date="2025-01-15",
            category="Food & Dining",
            description="Lunch",
            payment_method="Invalid Method"
        )
        assert not is_valid
        assert "payment" in error.lower()


class TestExpenseCRUD:
    """Test expense CRUD operations through service layer."""

    def test_add_expense(self, temp_db):
        """Test adding expense via service."""
        success, error, expense = expense_service.add_expense(
            expense_date="2025-01-15",
            amount=1250.50,
            category="Food & Dining",
            description="Lunch at restaurant",
            payment_method="UPI",
            merchant="Saravana Bhavan",
            notes="Team lunch"
        )
        assert success
        assert error is None
        assert expense is not None
        assert isinstance(expense, Expense)
        assert expense.amount == 1250.50
        assert expense.category == "Food & Dining"
        assert expense.merchant == "Saravana Bhavan"
        assert expense.notes == "Team lunch"

    def test_add_expense_minimal(self, temp_db):
        """Test adding expense with only required fields."""
        success, error, expense = expense_service.add_expense(
            expense_date="2025-01-15",
            amount=1000,
            category="Food & Dining",
            description="Lunch",
            payment_method="Cash"
        )
        assert success
        assert expense.merchant is None
        assert expense.notes is None

    def test_add_expense_invalid_data(self, temp_db):
        """Test adding expense with invalid data fails."""
        success, error, expense = expense_service.add_expense(
            expense_date="2025-01-15",
            amount=-100,
            category="Food & Dining",
            description="Lunch",
            payment_method="Cash"
        )
        assert not success
        assert error is not None
        assert expense is None

    def test_get_expense(self, temp_db):
        """Test getting expense by ID."""
        success, _, expense = expense_service.add_expense(
            expense_date="2025-01-15",
            amount=1000,
            category="Food & Dining",
            description="Lunch",
            payment_method="Cash"
        )
        assert success

        retrieved = expense_service.get_expense(expense.id)
        assert retrieved is not None
        assert retrieved.id == expense.id
        assert retrieved.amount == expense.amount

    def test_get_nonexistent_expense(self, temp_db):
        """Test getting non-existent expense returns None."""
        expense = expense_service.get_expense(99999)
        assert expense is None

    def test_update_expense(self, temp_db):
        """Test updating expense."""
        success, _, expense = expense_service.add_expense(
            expense_date="2025-01-15",
            amount=1000,
            category="Food & Dining",
            description="Original",
            payment_method="Cash"
        )
        assert success

        success, error, updated = expense_service.update_expense(
            expense_id=expense.id,
            expense_date="2025-01-16",
            amount=1500,
            category="Shopping",
            description="Updated",
            payment_method="UPI",
            merchant="Store",
            notes="New note"
        )
        assert success
        assert error is None
        assert updated.amount == 1500
        assert updated.category == "Shopping"
        assert updated.description == "Updated"
        assert updated.payment_method == "UPI"
        assert updated.merchant == "Store"
        assert updated.notes == "New note"

    def test_update_nonexistent_expense(self, temp_db):
        """Test updating non-existent expense fails."""
        success, error, updated = expense_service.update_expense(
            expense_id=99999,
            expense_date="2025-01-15",
            amount=1000,
            category="Food & Dining",
            description="Test",
            payment_method="Cash"
        )
        assert not success
        assert "not found" in error.lower()
        assert updated is None

    def test_delete_expense(self, temp_db):
        """Test deleting expense."""
        success, _, expense = expense_service.add_expense(
            expense_date="2025-01-15",
            amount=1000,
            category="Food & Dining",
            description="To delete",
            payment_method="Cash"
        )
        assert success

        success, error = expense_service.delete_expense(expense.id)
        assert success
        assert error is None

        # Verify deleted
        retrieved = expense_service.get_expense(expense.id)
        assert retrieved is None

    def test_delete_nonexistent_expense(self, temp_db):
        """Test deleting non-existent expense fails."""
        success, error = expense_service.delete_expense(99999)
        assert not success
        assert "not found" in error.lower()


class TestExpenseFiltering:
    """Test expense filtering and listing."""

    def test_get_expenses_with_filters(self, temp_db):
        """Test getting filtered expenses."""
        # Add test data
        expense_service.add_expense("2025-01-15", 1000, "Food & Dining", "Lunch", "Cash")
        expense_service.add_expense("2025-01-20", 2000, "Shopping", "Clothes", "Debit Card")
        expense_service.add_expense("2025-02-01", 1500, "Food & Dining", "Dinner", "UPI")

        # Filter by date
        expenses = expense_service.get_expenses(start_date="2025-01-01", end_date="2025-01-31")
        assert len(expenses) == 2

        # Filter by category
        expenses = expense_service.get_expenses(category="Food & Dining")
        assert len(expenses) == 2
        assert all(e.category == "Food & Dining" for e in expenses)

        # Filter by payment method
        expenses = expense_service.get_expenses(payment_method="Cash")
        assert len(expenses) == 1
        assert expenses[0].payment_method == "Cash"

        # Filter by search text
        expenses = expense_service.get_expenses(search_text="lunch")
        assert len(expenses) == 1
        assert "lunch" in expenses[0].description.lower()

        # Filter by amount
        expenses = expense_service.get_expenses(min_amount=1500)
        assert len(expenses) == 2
        assert all(e.amount >= 1500 for e in expenses)

    def test_count_expenses(self, temp_db):
        """Test counting expenses."""
        expense_service.add_expense("2025-01-15", 1000, "Food & Dining", "Lunch", "Cash")
        expense_service.add_expense("2025-01-20", 2000, "Shopping", "Clothes", "Debit Card")

        count = expense_service.count_expenses()
        assert count == 2

        count = expense_service.count_expenses(category="Food & Dining")
        assert count == 1


class TestCSVExport:
    """Test CSV export functionality."""

    def test_export_to_csv(self, temp_db):
        """Test CSV export."""
        expense_service.add_expense("2025-01-15", 1250.50, "Food & Dining", "Lunch", "UPI", "Restaurant", "Team")
        expense_service.add_expense("2025-01-20", 2000, "Shopping", "Clothes", "Debit Card")

        expenses = expense_service.get_expenses()
        csv_data = expense_service.export_to_csv(expenses)

        lines = csv_data.strip().split('\n')
        assert len(lines) == 3  # Header + 2 data rows

        # Check header
        assert "ID" in lines[0]
        assert "Amount" in lines[0]
        assert "Category" in lines[0]

        # Check data without assuming a specific transaction sort order.
        assert "1250.50" in csv_data
        assert "Food & Dining" in csv_data
        assert "2000.00" in csv_data

    def test_export_empty_list(self, temp_db):
        """Test CSV export with empty list."""
        csv_data = expense_service.export_to_csv([])
        lines = csv_data.strip().split('\n')
        assert len(lines) == 1  # Only header


class TestBudgetManagement:
    """Test budget operations."""

    def test_set_overall_budget(self, temp_db):
        """Test setting overall budget."""
        success, error, budget = expense_service.set_budget("2025-01", 25000.00)
        assert success
        assert error is None
        assert budget is not None
        assert budget.month == "2025-01"
        assert budget.category is None
        assert budget.amount == 25000.00

    def test_set_category_budget(self, temp_db):
        """Test setting category budget."""
        success, error, budget = expense_service.set_budget("2025-01", 5000.00, "Food & Dining")
        assert success
        assert budget.category == "Food & Dining"
        assert budget.amount == 5000.00

    def test_set_budget_invalid_month(self, temp_db):
        """Test setting budget with invalid month format."""
        success, error, budget = expense_service.set_budget("01-2025", 25000.00)
        assert not success
        assert "format" in error.lower()

    def test_set_budget_negative_amount(self, temp_db):
        """Test setting budget with negative amount fails."""
        success, error, budget = expense_service.set_budget("2025-01", -1000)
        assert not success
        assert "negative" in error.lower()

    def test_set_budget_invalid_category(self, temp_db):
        """Test setting budget with invalid category fails."""
        success, error, budget = expense_service.set_budget("2025-01", 5000, "Invalid Category")
        assert not success
        assert "invalid category" in error.lower()

    def test_get_budget_status(self, temp_db):
        """Test budget status calculation."""
        # Add expenses
        expense_service.add_expense("2025-01-15", 3000, "Food & Dining", "Groceries", "Cash")
        expense_service.add_expense("2025-01-20", 15000, "Rent", "Jan rent", "Bank Transfer")

        # Set budgets
        expense_service.set_budget("2025-01", 25000)
        expense_service.set_budget("2025-01", 5000, "Food & Dining")

        status = expense_service.get_budget_status("2025-01")

        assert status["month"] == "2025-01"
        assert status["overall_budget"] == 25000.00
        assert status["total_spent"] == 18000.00
        assert status["overall_remaining"] == 7000.00
        assert status["overall_percentage"] == 72.0
        assert status["overall_warning"] == "ok"

        # Check category status
        assert "Food & Dining" in status["categories"]
        cat_status = status["categories"]["Food & Dining"]
        assert cat_status["budget"] == 5000.00
        assert cat_status["spent"] == 3000.00
        assert cat_status["percentage"] == 60.0
        assert cat_status["warning"] == "ok"

    def test_budget_warning_at_80_percent(self, temp_db):
        """Test warning at 80% budget usage."""
        expense_service.add_expense("2025-01-15", 4000, "Food & Dining", "Food", "Cash")
        expense_service.set_budget("2025-01", 5000, "Food & Dining")

        status = expense_service.get_budget_status("2025-01")
        cat_status = status["categories"]["Food & Dining"]
        assert cat_status["percentage"] == 80.0
        assert cat_status["warning"] == "warning"

    def test_budget_over_at_100_percent(self, temp_db):
        """Test over budget at 100%+."""
        expense_service.add_expense("2025-01-15", 6000, "Food & Dining", "Food", "Cash")
        expense_service.set_budget("2025-01", 5000, "Food & Dining")

        status = expense_service.get_budget_status("2025-01")
        cat_status = status["categories"]["Food & Dining"]
        assert cat_status["percentage"] == 120.0
        assert cat_status["warning"] == "over"

    def test_delete_budget(self, temp_db):
        """Test deleting budget."""
        expense_service.set_budget("2025-01", 25000)
        success, error = expense_service.delete_budget("2025-01")
        assert success

        budget = expense_service.get_budget("2025-01")
        assert budget is None


class TestSampleData:
    """Test sample data loading."""

    def test_load_sample_data(self, temp_db):
        """Test loading sample data."""
        success, error, count = expense_service.load_sample_data()
        assert success
        assert error is None
        assert count > 0

        # Verify data was added
        expenses = expense_service.get_expenses()
        assert len(expenses) == count

        # Verify budgets were set
        jan_budgets = expense_service.get_budgets_for_month("2025-01")
        assert len(jan_budgets) >= 2  # Overall + category

        # Verify setting was updated
        from database import db
        sample_loaded = db.get_setting("sample_data_loaded")
        assert sample_loaded == "1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])