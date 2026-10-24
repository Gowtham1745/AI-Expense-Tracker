"""
Configuration management for Keerthi AI Expense Tracker.
Loads settings from environment variables and Streamlit secrets.
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Application configuration with environment variable and Streamlit secrets support."""

    # Database
    DATABASE_DIR: Path = Path(os.getenv("KEERTHI_DB_DIR", Path.home() / ".keerthi_expense_tracker"))
    DATABASE_NAME: str = "expenses.db"
    DATABASE_PATH: Path = DATABASE_DIR / DATABASE_NAME

    # NVIDIA Nemotron API
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_MODEL: str = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-ultra")
    NVIDIA_BASE_URL: str = os.getenv(
        "NVIDIA_BASE_URL",
        "https://integrate.api.nvidia.com/v1"
    )
    NVIDIA_TIMEOUT: int = int(os.getenv("NVIDIA_TIMEOUT", "30"))
    NVIDIA_MAX_TOKENS: int = int(os.getenv("NVIDIA_MAX_TOKENS", "1024"))

    # Application
    APP_NAME: str = "Keerthi — AI Expense Tracker"
    APP_TAGLINE: str = "Understand Your Money. Improve Your Future."
    DEFAULT_CURRENCY: str = "INR"
    CURRENCY_SYMBOL: str = "₹"

    # Creator/Developer info
    CREATOR_NAME: str = "Keerthi"
    CREATOR_EMAIL: str = "keerthanaskeerthi97@gmail.com"
    DEVELOPER_NAME: str = "Gowtham A"
    DEVELOPER_EMAIL: str = "gowthamgo1745@gmail.com"
    GITHUB_REPO: str = "AI-Expense-Tracker"
    GITHUB_OWNER: str = "Gowtham1745"

    # Categories and payment methods
    EXPENSE_CATEGORIES: list[str] = [
        "Food & Dining",
        "Transportation",
        "Shopping",
        "Bills & Utilities",
        "Rent",
        "Education",
        "Healthcare",
        "Entertainment",
        "Travel",
        "Personal Care",
        "Investments",
        "Other"
    ]

    PAYMENT_METHODS: list[str] = [
        "Cash",
        "UPI",
        "Debit Card",
        "Credit Card",
        "Bank Transfer",
        "Other"
    ]

    @classmethod
    def load_secrets(cls) -> None:
        """Load secrets from Streamlit secrets.toml or environment variables."""
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                # NVIDIA API Key
                if "NVIDIA_API_KEY" in st.secrets:
                    cls.NVIDIA_API_KEY = st.secrets["NVIDIA_API_KEY"]
                elif "nvidia" in st.secrets and "api_key" in st.secrets["nvidia"]:
                    cls.NVIDIA_API_KEY = st.secrets["nvidia"]["api_key"]

                # Optional overrides
                if "NVIDIA_MODEL" in st.secrets:
                    cls.NVIDIA_MODEL = st.secrets["NVIDIA_MODEL"]
                if "NVIDIA_BASE_URL" in st.secrets:
                    cls.NVIDIA_BASE_URL = st.secrets["NVIDIA_BASE_URL"]
                if "NVIDIA_TIMEOUT" in st.secrets:
                    cls.NVIDIA_TIMEOUT = int(st.secrets["NVIDIA_TIMEOUT"])
                if "NVIDIA_MAX_TOKENS" in st.secrets:
                    cls.NVIDIA_MAX_TOKENS = int(st.secrets["NVIDIA_MAX_TOKENS"])

                # Database path override
                if "KEERTHI_DB_DIR" in st.secrets:
                    cls.DATABASE_DIR = Path(st.secrets["KEERTHI_DB_DIR"])
                    cls.DATABASE_PATH = cls.DATABASE_DIR / cls.DATABASE_NAME
        except Exception:
            # Streamlit not available or secrets not configured
            pass

        # Fallback to environment variables
        if not cls.NVIDIA_API_KEY:
            cls.NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

    @classmethod
    def ensure_database_dir(cls) -> None:
        """Create database directory if it doesn't exist."""
        cls.DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def is_ai_configured(cls) -> bool:
        """Check if NVIDIA API is configured."""
        return bool(cls.NVIDIA_API_KEY and cls.NVIDIA_API_KEY.strip())


# Load secrets on import
Config.load_secrets()
Config.ensure_database_dir()