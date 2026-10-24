"""
Expense service layer for Keerthi AI Expense Tracker.
Provides high-level business logic for expense management.
"""

from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import csv
import io

from database import db
from config import Config


@dataclass
class Expense:
    """Expense data class."""
    id: int
    date: str
    amount: float
    category: str
    description: str
    payment_method: str
    merchant: Optional[str]
    notes: Optional[str]
    created_at: str

    @classmethod
    def from_row(cls, row) -> "Expense":
        """Create Expense from database row."""
        return cls(
            id=row["id"],
            date=row["date"],
            amount=row["amount"],
            category=row["category"],
            description=row["description"],
            payment_method=row["payment_method"],
            merchant=row["merchant"],
            notes=row["notes"],
            created_at=row["created_at"]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "date": self.date,
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "payment_method": self.payment_method,
            "merchant": self.merchant,
            "notes": self.notes,
            "created_at": self.created_at
        }


@dataclass
class Budget:
    """Budget data class."""
    id: int
    month: str
    category: Optional[str]
    amount: float
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row) -> "Budget":
        """Create Budget from database row."""
        return cls(
            id=row["id"],
            month=row["month"],
            category=row["category"],
            amount=row["amount"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )


class ExpenseService:
    """High-level expense management service."""

    @staticmethod
    def validate_expense(
        amount: float,
        expense_date: str,
        category: str,
        description: str,
        payment_method: str
    ) -> Tuple[bool, Optional[str]]:
        """Validate expense data. Returns (is_valid, error_message)."""
        # Validate amount
        if not isinstance(amount, (int, float)):
            return False, "Amount must be a number"
        if amount <= 0:
            return False, "Amount must be positive"
        if amount != amount:  # NaN check
            return False, "Amount cannot be NaN"
        if amount == float('inf') or amount == float('-inf'):
            return False, "Amount must be finite"

        # Validate date
        try:
            parsed_date = datetime.strptime(expense_date, "%Y-%m-%d").date()
            if parsed_date > date.today():
                return False, "Date cannot be in the future"
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD"

        # Validate category
        if not category or category not in Config.EXPENSE_CATEGORIES:
            return False, f"Invalid category. Must be one of: {', '.join(Config.EXPENSE_CATEGORIES)}"

        # Validate description
        if not description or not description.strip():
            return False, "Description is required"

        # Validate payment method
        if not payment_method or payment_method not in Config.PAYMENT_METHODS:
            return False, f"Invalid payment method. Must be one of: {', '.join(Config.PAYMENT_METHODS)}"

        return True, None

    @staticmethod
    def add_expense(
        expense_date: str,
        amount: float,
        category: str,
        description: str,
        payment_method: str,
        merchant: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[Expense]]:
        """Add a new expense. Returns (success, error_message, expense)."""
        is_valid, error = ExpenseService.validate_expense(
            amount, expense_date, category, description, payment_method
        )
        if not is_valid:
            return False, error, None

        try:
            expense_id = db.add_expense(
                date=expense_date,
                amount=round(amount, 2),
                category=category,
                description=description.strip(),
                payment_method=payment_method,
                merchant=merchant.strip() if merchant else None,
                notes=notes.strip() if notes else None
            )
            expense_row = db.get_expense(expense_id)
            if expense_row:
                return True, None, Expense.from_row(expense_row)
            return False, "Failed to retrieve created expense", None
        except Exception as e:
            return False, f"Database error: {str(e)}", None

    @staticmethod
    def update_expense(
        expense_id: int,
        expense_date: str,
        amount: float,
        category: str,
        description: str,
        payment_method: str,
        merchant: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[Expense]]:
        """Update an existing expense."""
        # Check if expense exists
        existing = db.get_expense(expense_id)
        if not existing:
            return False, "Expense not found", None

        is_valid, error = ExpenseService.validate_expense(
            amount, expense_date, category, description, payment_method
        )
        if not is_valid:
            return False, error, None

        try:
            success = db.update_expense(
                expense_id=expense_id,
                date=expense_date,
                amount=round(amount, 2),
                category=category,
                description=description.strip(),
                payment_method=payment_method,
                merchant=merchant.strip() if merchant else None,
                notes=notes.strip() if notes else None
            )
            if success:
                updated_row = db.get_expense(expense_id)
                if updated_row:
                    return True, None, Expense.from_row(updated_row)
            return False, "Failed to update expense", None
        except Exception as e:
            return False, f"Database error: {str(e)}", None

    @staticmethod
    def delete_expense(expense_id: int) -> Tuple[bool, Optional[str]]:
        """Delete an expense."""
        existing = db.get_expense(expense_id)
        if not existing:
            return False, "Expense not found"

        try:
            success = db.delete_expense(expense_id)
            return success, None if success else "Failed to delete expense"
        except Exception as e:
            return False, f"Database error: {str(e)}"

    @staticmethod
    def get_expense(expense_id: int) -> Optional[Expense]:
        """Get a single expense by ID."""
        row = db.get_expense(expense_id)
        return Expense.from_row(row) if row else None

    @staticmethod
    def get_expenses(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        payment_method: Optional[str] = None,
        search_text: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Expense]:
        """Get filtered expenses."""
        rows = db.get_expenses(
            start_date=start_date,
            end_date=end_date,
            category=category,
            payment_method=payment_method,
            search_text=search_text,
            min_amount=min_amount,
            max_amount=max_amount,
            limit=limit,
            offset=offset
        )
        return [Expense.from_row(row) for row in rows]

    @staticmethod
    def count_expenses(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        payment_method: Optional[str] = None,
        search_text: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None
    ) -> int:
        """Count filtered expenses."""
        return db.count_expenses(
            start_date=start_date,
            end_date=end_date,
            category=category,
            payment_method=payment_method,
            search_text=search_text,
            min_amount=min_amount,
            max_amount=max_amount
        )

    @staticmethod
    def get_expenses_for_export(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        payment_method: Optional[str] = None
    ) -> List[Expense]:
        """Get expenses for CSV export."""
        rows = db.export_expenses_csv(
            start_date=start_date,
            end_date=end_date,
            category=category,
            payment_method=payment_method
        )
        return [Expense.from_row(row) for row in rows]

    @staticmethod
    def export_to_csv(
        expenses: List[Expense],
        currency_symbol: str = Config.CURRENCY_SYMBOL
    ) -> str:
        """Export expenses to CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "ID", "Date", f"Amount ({currency_symbol})", "Category",
            "Description", "Payment Method", "Merchant", "Notes", "Created At"
        ])

        # Data rows
        for exp in expenses:
            writer.writerow([
                exp.id,
                exp.date,
                f"{exp.amount:.2f}",
                exp.category,
                exp.description,
                exp.payment_method,
                exp.merchant or "",
                exp.notes or "",
                exp.created_at
            ])

        return output.getvalue()

    # Budget methods
    @staticmethod
    def set_budget(month: str, amount: float, category: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[Budget]]:
        """Set a budget for a month (overall or category-specific)."""
        # Validate month format (YYYY-MM)
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            return False, "Invalid month format. Use YYYY-MM", None

        if amount < 0:
            return False, "Budget amount cannot be negative", None

        if category and category not in Config.EXPENSE_CATEGORIES:
            return False, f"Invalid category", None

        try:
            budget_id = db.set_budget(month, amount, category)
            budget_row = db.get_budget(month, category)
            if budget_row:
                return True, None, Budget.from_row(budget_row)
            return False, "Failed to retrieve created budget", None
        except Exception as e:
            return False, f"Database error: {str(e)}", None

    @staticmethod
    def get_budget(month: str, category: Optional[str] = None) -> Optional[Budget]:
        """Get a budget."""
        row = db.get_budget(month, category)
        return Budget.from_row(row) if row else None

    @staticmethod
    def get_budgets_for_month(month: str) -> List[Budget]:
        """Get all budgets for a month."""
        rows = db.get_budgets_for_month(month)
        return [Budget.from_row(row) for row in rows]

    @staticmethod
    def delete_budget(month: str, category: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Delete a budget."""
        try:
            success = db.delete_budget(month, category)
            return success, None if success else "Budget not found"
        except Exception as e:
            return False, f"Database error: {str(e)}"

    @staticmethod
    def get_budget_status(month: str) -> Dict[str, Any]:
        """Get budget vs actual spending for a month."""
        overall_budget = ExpenseService.get_budget(month)
        category_budgets = ExpenseService.get_budgets_for_month(month)

        # Get actual spending for the month
        start_date = f"{month}-01"
        # Calculate end of month
        if month.endswith("-12"):
            end_date = f"{int(month[:4]) + 1}-01-01"
        else:
            next_month = int(month[5:7]) + 1
            end_date = f"{month[:4]}-{next_month:02d}-01"

        spending_by_category = db.get_spending_by_category(start_date, end_date)
        total_spent = db.get_total_spending(start_date, end_date)

        category_status = {}
        for cat_row in spending_by_category:
            cat = cat_row["category"]
            spent = float(cat_row["total"])
            budget_row = next((b for b in category_budgets if b.category == cat), None)
            budget_amt = float(budget_row.amount) if budget_row else 0

            category_status[cat] = {
                "budget": budget_amt,
                "spent": spent,
                "remaining": budget_amt - spent if budget_amt > 0 else None,
                "percentage": (spent / budget_amt * 100) if budget_amt > 0 else None,
                "warning": "over" if budget_amt > 0 and spent > budget_amt else ("warning" if budget_amt > 0 and spent >= budget_amt * 0.8 else "ok")
            }

        overall_budget_amt = float(overall_budget.amount) if overall_budget else 0
        return {
            "month": month,
            "overall_budget": overall_budget_amt,
            "total_spent": total_spent,
            "overall_remaining": overall_budget_amt - total_spent if overall_budget_amt > 0 else None,
            "overall_percentage": (total_spent / overall_budget_amt * 100) if overall_budget_amt > 0 else None,
            "overall_warning": "over" if overall_budget_amt > 0 and total_spent > overall_budget_amt else ("warning" if overall_budget_amt > 0 and total_spent >= overall_budget_amt * 0.8 else "ok"),
            "categories": category_status
        }

    @staticmethod
    def load_sample_data() -> Tuple[bool, Optional[str], int]:
        """Load sample expense data for demonstration."""
        sample_expenses = [
            ("2025-01-15", 1250.00, "Food & Dining", "Lunch at restaurant", "UPI", "Saravana Bhavan", "Team lunch"),
            ("2025-01-16", 3200.00, "Shopping", "New shoes", "Credit Card", "Bata", "Running shoes"),
            ("2025-01-18", 450.00, "Transportation", "Auto fare", "Cash", None, "Office commute"),
            ("2025-01-20", 15000.00, "Rent", "January rent", "Bank Transfer", "Landlord", "Monthly rent"),
            ("2025-01-22", 890.00, "Food & Dining", "Groceries", "Debit Card", "Big Bazaar", "Weekly groceries"),
            ("2025-01-25", 2100.00, "Healthcare", "Doctor consultation", "UPI", "Apollo Clinic", "General checkup"),
            ("2025-01-28", 550.00, "Entertainment", "Movie tickets", "Credit Card", "PVR Cinemas", "Weekend movie"),
            ("2025-02-02", 1800.00, "Food & Dining", "Dinner with friends", "UPI", "Barbeque Nation", "Birthday celebration"),
            ("2025-02-05", 4200.00, "Shopping", "Electronics", "Credit Card", "Croma", "Headphones"),
            ("2025-02-08", 650.00, "Transportation", "Fuel", "Cash", "Petrol Pump", "Bike fuel"),
            ("2025-02-10", 15000.00, "Rent", "February rent", "Bank Transfer", "Landlord", "Monthly rent"),
            ("2025-02-14", 3200.00, "Personal Care", "Salon & spa", "UPI", "Lakme Salon", "Haircut and facial"),
            ("2025-02-18", 980.00, "Food & Dining", "Valentine's dinner", "Credit Card", "Theobroma", "Special occasion"),
            ("2025-02-22", 1200.00, "Education", "Online course", "Debit Card", "Udemy", "Python course"),
            ("2025-02-25", 750.00, "Entertainment", "Streaming subscription", "UPI", "Netflix", "Monthly subscription"),
            ("2025-03-01", 15000.00, "Rent", "March rent", "Bank Transfer", "Landlord", "Monthly rent"),
            ("2025-03-05", 2100.00, "Food & Dining", "Groceries", "UPI", "DMart", "Monthly groceries"),
            ("2025-03-10", 450.00, "Transportation", "Metro pass", "Cash", "Metro Station", "Monthly pass"),
            ("2025-03-12", 3500.00, "Bills & Utilities", "Electricity bill", "UPI", "TNEB", "February bill"),
            ("2025-03-15", 1800.00, "Shopping", "Clothes", "Credit Card", "H&M", "Spring collection"),
        ]

        count = 0
        for exp in sample_expenses:
            try:
                db.add_expense(*exp)
                count += 1
            except Exception:
                pass

        # Set sample budgets
        db.set_budget("2025-01", 25000.00)
        db.set_budget("2025-01", 5000.00, "Food & Dining")
        db.set_budget("2025-01", 3000.00, "Shopping")
        db.set_budget("2025-02", 25000.00)
        db.set_budget("2025-02", 5000.00, "Food & Dining")
        db.set_budget("2025-03", 25000.00)

        db.set_setting("sample_data_loaded", "1")

        return True, None, count


# Global service instance
expense_service = ExpenseService()