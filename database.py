"""
Database layer for Keerthi AI Expense Tracker.
Handles SQLite connections, schema initialization, and low-level queries.
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from config import Config


class Database:
    """SQLite database manager with connection pooling and transaction support."""

    _instance: Optional["Database"] = None
    _connection: Optional[sqlite3.Connection] = None

    def __new__(cls) -> "Database":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._connection is None:
            self._initialize()

    def _initialize(self) -> None:
        """Initialize database connection and create tables."""
        Config.ensure_database_dir()
        self._connection = sqlite3.connect(
            str(Config.DATABASE_PATH),
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._create_tables()
        self._create_indexes()

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        with self._transaction() as conn:
            # Expenses table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    amount REAL NOT NULL CHECK(amount > 0),
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    payment_method TEXT NOT NULL,
                    merchant TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Budgets table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    month TEXT NOT NULL,  -- Format: YYYY-MM
                    category TEXT,        -- NULL means overall budget
                    amount REAL NOT NULL CHECK(amount >= 0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(month, category)
                )
            """)

            # Settings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert default settings if not present
            conn.execute("""
                INSERT OR IGNORE INTO settings (key, value) VALUES
                ('currency', 'INR'),
                ('currency_symbol', '₹'),
                ('sample_data_loaded', '0')
            """)

    def _create_indexes(self) -> None:
        """Create database indexes for query performance."""
        with self._transaction() as conn:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expenses_payment_method ON expenses(payment_method)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expenses_created_at ON expenses(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_budgets_month ON budgets(month)")

    @contextmanager
    def _transaction(self):
        """Context manager for database transactions."""
        conn = self._connection
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """Execute a query within a transaction."""
        with self._transaction() as conn:
            return conn.execute(query, params)

    def fetchone(self, query: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        """Fetch a single row."""
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Fetch all rows."""
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def insert(self, query: str, params: Tuple = ()) -> int:
        """Insert a row and return the last row ID."""
        with self._transaction() as conn:
            cursor = conn.execute(query, params)
            return cursor.lastrowid

    def update(self, query: str, params: Tuple = ()) -> int:
        """Update rows and return the number of affected rows."""
        with self._transaction() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount

    def delete(self, query: str, params: Tuple = ()) -> int:
        """Delete rows and return the number of affected rows."""
        with self._transaction() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount

    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            Database._instance = None

    # Expense operations
    def add_expense(
        self,
        date: str,
        amount: float,
        category: str,
        description: str,
        payment_method: str,
        merchant: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """Add a new expense and return its ID."""
        return self.insert("""
            INSERT INTO expenses (date, amount, category, description, payment_method, merchant, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date, amount, category, description, payment_method, merchant, notes))

    def get_expense(self, expense_id: int) -> Optional[sqlite3.Row]:
        """Get a single expense by ID."""
        return self.fetchone("SELECT * FROM expenses WHERE id = ?", (expense_id,))

    def update_expense(
        self,
        expense_id: int,
        date: str,
        amount: float,
        category: str,
        description: str,
        payment_method: str,
        merchant: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Update an existing expense."""
        rows = self.update("""
            UPDATE expenses
            SET date = ?, amount = ?, category = ?, description = ?,
                payment_method = ?, merchant = ?, notes = ?
            WHERE id = ?
        """, (date, amount, category, description, payment_method, merchant, notes, expense_id))
        return rows > 0

    def delete_expense(self, expense_id: int) -> bool:
        """Delete an expense by ID."""
        rows = self.delete("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return rows > 0

    def get_expenses(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        payment_method: Optional[str] = None,
        search_text: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: str = "date DESC, created_at DESC"
    ) -> List[sqlite3.Row]:
        """Get expenses with optional filters."""
        conditions = []
        params = []

        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        if category:
            conditions.append("category = ?")
            params.append(category)
        if payment_method:
            conditions.append("payment_method = ?")
            params.append(payment_method)
        if search_text:
            conditions.append("(description LIKE ? OR merchant LIKE ? OR notes LIKE ?)")
            search_param = f"%{search_text}%"
            params.extend([search_param, search_param, search_param])
        if min_amount is not None:
            conditions.append("amount >= ?")
            params.append(min_amount)
        if max_amount is not None:
            conditions.append("amount <= ?")
            params.append(max_amount)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        limit_clause = f"LIMIT {limit}" if limit else ""
        offset_clause = f"OFFSET {offset}" if offset else ""

        query = f"""
            SELECT * FROM expenses
            {where_clause}
            ORDER BY {order_by}
            {limit_clause} {offset_clause}
        """
        return self.fetchall(query, tuple(params))

    def count_expenses(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        payment_method: Optional[str] = None,
        search_text: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None
    ) -> int:
        """Count expenses with optional filters."""
        conditions = []
        params = []

        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        if category:
            conditions.append("category = ?")
            params.append(category)
        if payment_method:
            conditions.append("payment_method = ?")
            params.append(payment_method)
        if search_text:
            conditions.append("(description LIKE ? OR merchant LIKE ? OR notes LIKE ?)")
            search_param = f"%{search_text}%"
            params.extend([search_param, search_param, search_param])
        if min_amount is not None:
            conditions.append("amount >= ?")
            params.append(min_amount)
        if max_amount is not None:
            conditions.append("amount <= ?")
            params.append(max_amount)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"SELECT COUNT(*) as count FROM expenses {where_clause}"
        result = self.fetchone(query, tuple(params))
        return result["count"] if result else 0

    # Budget operations
    def set_budget(self, month: str, amount: float, category: Optional[str] = None) -> int:
        """Set or update a budget for a month (and optional category)."""
        existing = self.fetchone(
            "SELECT id FROM budgets WHERE month = ? AND category IS ?",
            (month, category)
        )
        if existing:
            self.update("""
                UPDATE budgets SET amount = ?, updated_at = CURRENT_TIMESTAMP
                WHERE month = ? AND category IS ?
            """, (amount, month, category))
            return existing["id"]
        else:
            return self.insert("""
                INSERT INTO budgets (month, category, amount)
                VALUES (?, ?, ?)
            """, (month, category, amount))

    def get_budget(self, month: str, category: Optional[str] = None) -> Optional[sqlite3.Row]:
        """Get a budget for a month and optional category."""
        return self.fetchone(
            "SELECT * FROM budgets WHERE month = ? AND category IS ?",
            (month, category)
        )

    def get_budgets_for_month(self, month: str) -> List[sqlite3.Row]:
        """Get all budgets for a specific month."""
        return self.fetchall(
            "SELECT * FROM budgets WHERE month = ? ORDER BY category NULLS FIRST",
            (month,)
        )

    def delete_budget(self, month: str, category: Optional[str] = None) -> bool:
        """Delete a budget."""
        rows = self.delete(
            "DELETE FROM budgets WHERE month = ? AND category IS ?",
            (month, category)
        )
        return rows > 0

    # Settings operations
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value."""
        result = self.fetchone("SELECT value FROM settings WHERE key = ?", (key,))
        return result["value"] if result else default

    def set_setting(self, key: str, value: str) -> None:
        """Set a setting value."""
        self.update("""
            INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP
        """, (key, value, value))

    # Analytics queries
    def get_total_spending(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> float:
        """Get total spending for a date range."""
        conditions = []
        params = []
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        result = self.fetchone(f"SELECT COALESCE(SUM(amount), 0) as total FROM expenses {where_clause}", tuple(params))
        return float(result["total"]) if result else 0.0

    def get_spending_by_category(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[sqlite3.Row]:
        """Get spending grouped by category."""
        conditions = []
        params = []
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        return self.fetchall(f"""
            SELECT category, COALESCE(SUM(amount), 0) as total, COUNT(*) as count
            FROM expenses
            {where_clause}
            GROUP BY category
            ORDER BY total DESC
        """, tuple(params))

    def get_spending_by_payment_method(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[sqlite3.Row]:
        """Get spending grouped by payment method."""
        conditions = []
        params = []
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        return self.fetchall(f"""
            SELECT payment_method, COALESCE(SUM(amount), 0) as total, COUNT(*) as count
            FROM expenses
            {where_clause}
            GROUP BY payment_method
            ORDER BY total DESC
        """, tuple(params))

    def get_daily_spending(
        self,
        start_date: str,
        end_date: str
    ) -> List[sqlite3.Row]:
        """Get daily spending totals for a date range."""
        return self.fetchall("""
            SELECT date, COALESCE(SUM(amount), 0) as total
            FROM expenses
            WHERE date >= ? AND date <= ?
            GROUP BY date
            ORDER BY date
        """, (start_date, end_date))

    def get_monthly_spending(self) -> List[sqlite3.Row]:
        """Get monthly spending totals."""
        return self.fetchall("""
            SELECT strftime('%Y-%m', date) as month, COALESCE(SUM(amount), 0) as total
            FROM expenses
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month
        """)

    def get_top_expenses(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10
    ) -> List[sqlite3.Row]:
        """Get largest individual expenses."""
        conditions = []
        params = []
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)
        return self.fetchall(f"""
            SELECT * FROM expenses
            {where_clause}
            ORDER BY amount DESC
            LIMIT ?
        """, tuple(params))

    def get_category_monthly_trend(
        self,
        category: str,
        months: int = 12,
        reference_date: Optional[str] = None
    ) -> List[sqlite3.Row]:
        """Get monthly spending trend for a specific category."""
        if reference_date:
            date_filter = f"date >= date(?, ? || ' months')"
            params = (category, reference_date, f"-{months}")
        else:
            date_filter = "date >= date('now', ? || ' months')"
            params = (category, f"-{months}")
        
        return self.fetchall(f"""
            SELECT strftime('%Y-%m', date) as month, COALESCE(SUM(amount), 0) as total
            FROM expenses
            WHERE category = ? AND {date_filter}
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month
        """, params)

    def export_expenses_csv(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        payment_method: Optional[str] = None
    ) -> List[sqlite3.Row]:
        """Export expenses for CSV download."""
        conditions = []
        params = []
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        if category:
            conditions.append("category = ?")
            params.append(category)
        if payment_method:
            conditions.append("payment_method = ?")
            params.append(payment_method)
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        return self.fetchall(f"""
            SELECT id, date, amount, category, description, payment_method,
                   merchant, notes, created_at
            FROM expenses
            {where_clause}
            ORDER BY date DESC, created_at DESC
        """, tuple(params))


# Global database instance
db = Database()