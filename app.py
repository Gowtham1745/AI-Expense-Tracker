#!/usr/bin/env python3
"""
Keerthi — AI Expense Tracker
Main Streamlit application entry point.
"""

import streamlit as st
import os
import sys
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database import db
from expense_service import expense_service, Expense
from analytics import analytics
from ai_service import ai_service


# Page configuration
st.set_page_config(
    page_title=Config.APP_NAME,
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": f"https://github.com/{Config.GITHUB_OWNER}/{Config.GITHUB_REPO}",
        "Report a bug": f"https://github.com/{Config.GITHUB_OWNER}/{Config.GITHUB_REPO}/issues",
        "About": f"""
        **{Config.APP_NAME}**
        
        {Config.APP_TAGLINE}
        
        Created by {Config.CREATOR_NAME} ({Config.CREATOR_EMAIL})
        Developed by {Config.DEVELOPER_NAME} ({Config.DEVELOPER_EMAIL})
        
        Version 1.0.0
        """
    }
)


# Custom CSS for premium dark theme
CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {{
        --primary: {analytics.COLORS["primary"]};
        --primary-light: {analytics.COLORS["primary_light"]};
        --primary-dark: {analytics.COLORS["primary_dark"]};
        --background: {analytics.COLORS["background"]};
        --surface: {analytics.COLORS["surface"]};
        --surface-light: {analytics.COLORS["surface_light"]};
        --text: {analytics.COLORS["text"]};
        --text-muted: {analytics.COLORS["text_muted"]};
        --border: {analytics.COLORS["border"]};
        --red: {analytics.COLORS["red"]};
        --orange: {analytics.COLORS["orange"]};
        --yellow: {analytics.COLORS["yellow"]};
    }}

    /* Global styles */
    .stApp {{
        background-color: var(--background);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }}

    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    /* Main container */
    .main .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, var(--surface) 0%, var(--background) 100%);
        border-right: 1px solid var(--border);
    }}

    section[data-testid="stSidebar"] .stMarkdown {{
        color: var(--text);
    }}

    /* Cards */
    .metric-card {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.25rem;
        transition: all 0.2s ease;
    }}

    .metric-card:hover {{
        border-color: var(--primary);
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.1);
    }}

    .metric-label {{
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }}

    .metric-value {{
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text);
        line-height: 1.2;
    }}

    .metric-change {{
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 0.25rem;
    }}

    .metric-change.positive {{ color: var(--red); }}
    .metric-change.negative {{ color: var(--primary); }}

    /* Section headers */
    .section-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
    }}

    .section-title {{
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text);
    }}

    .section-subtitle {{
        font-size: 0.875rem;
        color: var(--text-muted);
    }}

    /* Buttons */
    .stButton > button {{
        background: var(--primary);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.875rem;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
    }}

    .stButton > button:hover {{
        background: var(--primary-dark);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }}

    .stButton > button[kind="secondary"] {{
        background: var(--surface-light);
        color: var(--text);
        border: 1px solid var(--border);
    }}

    .stButton > button[kind="secondary"]:hover {{
        background: var(--border);
    }}

    /* Form inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div,
    .stDateInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background: var(--surface);
        border: 1px solid var(--border);
        color: var(--text);
        border-radius: 8px;
    }}

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus,
    .stDateInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
    }}

    /* Dataframe */
    .stDataFrame {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
    }}

    .stDataFrame [data-testid="stTable"] {{
        color: var(--text);
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        background: var(--surface);
        border-radius: 8px;
        padding: 4px;
        border: 1px solid var(--border);
    }}

    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        color: var(--text-muted);
        border-radius: 6px;
        font-weight: 500;
    }}

    .stTabs [aria-selected="true"] {{
        background: var(--primary) !important;
        color: white !important;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        color: var(--text);
        font-weight: 500;
    }}

    .streamlit-expanderContent {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-top: none;
        border-radius: 0 0 8px 8px;
    }}

    /* Alert boxes */
    .alert {{
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid;
    }}

    .alert-info {{
        background: rgba(59, 130, 246, 0.1);
        border-color: var(--blue);
        color: var(--text);
    }}

    .alert-success {{
        background: rgba(16, 185, 129, 0.1);
        border-color: var(--primary);
        color: var(--text);
    }}

    .alert-warning {{
        background: rgba(249, 115, 22, 0.1);
        border-color: var(--orange);
        color: var(--text);
    }}

    .alert-error {{
        background: rgba(239, 68, 68, 0.1);
        border-color: var(--red);
        color: var(--text);
    }}

    /* Avatar */
    .avatar {{
        width: 36px;
        height: 36px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid var(--border);
    }}

    .avatar-placeholder {{
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--primary), var(--primary-dark));
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 0.875rem;
    }}

    /* Logo */
    .app-logo {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.5rem 0;
        margin-bottom: 1rem;
    }}

    .app-logo-icon {{
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, var(--primary), var(--primary-dark));
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
    }}

    .app-logo-text {{
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text);
        letter-spacing: -0.02em;
    }}

    .app-tagline {{
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-top: -0.25rem;
    }}

    /* Attribution */
    .attribution {{
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border);
    }}

    .attribution-item {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0;
        font-size: 0.75rem;
        color: var(--text-muted);
    }}

    .attribution-name {{
        font-weight: 600;
        color: var(--text);
    }}

    /* Empty state */
    .empty-state {{
        text-align: center;
        padding: 3rem 2rem;
        color: var(--text-muted);
    }}

    .empty-state-icon {{
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }}

    .empty-state-title {{
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 0.5rem;
    }}

    .empty-state-text {{
        font-size: 0.875rem;
        line-height: 1.5;
    }}

    /* Budget warning badges */
    .budget-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.2rem 0.5rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
    }}

    .budget-badge.ok {{ background: rgba(16, 185, 129, 0.2); color: var(--primary); }}
    .budget-badge.warning {{ background: rgba(249, 115, 22, 0.2); color: var(--orange); }}
    .budget-badge.over {{ background: rgba(239, 68, 68, 0.2); color: var(--red); }}

    /* Chat message */
    .chat-message {{
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        animation: fadeIn 0.3s ease;
    }}

    .chat-message.user {{
        background: var(--primary);
        color: white;
        margin-left: 2rem;
    }}

    .chat-message.assistant {{
        background: var(--surface);
        border: 1px solid var(--border);
        margin-right: 2rem;
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Plotly chart container */
    .js-plotly-plot {{
        background: var(--surface) !important;
        border-radius: 12px;
        border: 1px solid var(--border);
    }}

    /* Scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}

    ::-webkit-scrollbar-track {{
        background: var(--background);
    }}

    ::-webkit-scrollbar-thumb {{
        background: var(--border);
        border-radius: 4px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: var(--text-muted);
    }}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"
    if "selected_period" not in st.session_state:
        st.session_state.selected_period = "This Month"
    if "custom_start_date" not in st.session_state:
        st.session_state.custom_start_date = date.today().replace(day=1)
    if "custom_end_date" not in st.session_state:
        st.session_state.custom_end_date = date.today()
    if "show_add_expense" not in st.session_state:
        st.session_state.show_add_expense = False
    if "editing_expense_id" not in st.session_state:
        st.session_state.editing_expense_id = None
    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []
    if "confirm_delete_id" not in st.session_state:
        st.session_state.confirm_delete_id = None
    if "show_sample_data_confirm" not in st.session_state:
        st.session_state.show_sample_data_confirm = False


def render_sidebar():
    """Render the sidebar with navigation and attribution."""
    with st.sidebar:
        # App Logo
        st.markdown(f"""
        <div class="app-logo">
            <div class="app-logo-icon">💰</div>
            <div>
                <div class="app-logo-text">Keerthi</div>
                <div class="app-tagline">{Config.APP_TAGLINE}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        st.markdown("### Navigation")
        pages = {
            "dashboard": "📊 Dashboard",
            "expenses": "💸 Expenses",
            "analytics": "📈 Analytics",
            "budgets": "🎯 Budgets",
            "ai_insights": "🤖 AI Insights",
            "settings": "⚙️ Settings"
        }

        for key, label in pages.items():
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if st.session_state.current_page == key else "secondary"
            ):
                st.session_state.current_page = key
                st.rerun()

        # Attribution
        st.markdown("""
        <div class="attribution">
            <div class="attribution-item">
                <span class="avatar-placeholder">K</span>
                <div>
                    <div class="attribution-name">Created by Keerthi</div>
                    <div>keerthanaskeerthi97@gmail.com</div>
                </div>
            </div>
            <div class="attribution-item">
                <span class="avatar-placeholder">G</span>
                <div>
                    <div class="attribution-name">Developed by Gowtham A</div>
                    <div>gowthamgo1745@gmail.com</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def get_date_range() -> tuple:
    """Get the current date range based on selected period."""
    period = st.session_state.selected_period

    if period == "Custom":
        return (
            st.session_state.custom_start_date.isoformat(),
            st.session_state.custom_end_date.isoformat()
        )

    ranges = analytics.get_date_range_options()
    return ranges.get(period, (None, None))


def render_period_selector():
    """Render the period selector in the main area."""
    ranges = analytics.get_date_range_options()
    period_options = list(ranges.keys()) + ["Custom"]

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        selected = st.selectbox(
            "Time Period",
            period_options,
            index=period_options.index(st.session_state.selected_period) if st.session_state.selected_period in period_options else 0,
            key="period_selector"
        )
        st.session_state.selected_period = selected

    if selected == "Custom":
        with col2:
            start_date = st.date_input(
                "Start Date",
                value=st.session_state.custom_start_date,
                max_value=date.today(),
                key="custom_start"
            )
            st.session_state.custom_start_date = start_date
        with col3:
            end_date = st.date_input(
                "End Date",
                value=st.session_state.custom_end_date,
                max_value=date.today(),
                key="custom_end"
            )
            st.session_state.custom_end_date = end_date

    start_date, end_date = get_date_range()
    return start_date, end_date


def render_metric_card(label: str, value: str, change: str = None, change_positive: bool = True):
    """Render a metric card."""
    change_class = "negative" if change_positive else "positive"
    change_html = f'<div class="metric-change {change_class}">{change}</div>' if change else ""

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {change_html}
    </div>
    """, unsafe_allow_html=True)


def render_dashboard():
    """Render the main dashboard."""
    st.markdown("""
    <div class="section-header">
        <h1 class="section-title">Dashboard</h1>
    </div>
    """, unsafe_allow_html=True)

    start_date, end_date = render_period_selector()

    # Get summary stats
    summary = analytics.get_summary_cards(start_date, end_date)

    # Summary cards row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card(
            "Total Spending",
            summary["total_spending"]["formatted"],
            summary["total_spending"]["change_formatted"],
            change_positive=(summary["total_spending"]["change"] <= 0)
        )

    with col2:
        render_metric_card(
            "Daily Average",
            summary["daily_average"]["formatted"]
        )

    with col3:
        render_metric_card(
            "Top Category",
            summary["top_category"]["formatted"],
            summary["top_category"]["name"]
        )

    with col4:
        render_metric_card(
            "Transactions",
            str(summary["transaction_count"]),
            f"Avg: {summary['average_transaction']}"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts row 1
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="section-header"><h2 class="section-title">Spending Trend</h2></div>', unsafe_allow_html=True)
        fig = analytics.create_spending_trend_chart(start_date, end_date, compare_previous=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        st.markdown('<div class="section-header"><h2 class="section-title">By Category</h2></div>', unsafe_allow_html=True)
        fig = analytics.create_category_pie_chart(start_date, end_date)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Charts row 2
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header"><h2 class="section-title">By Payment Method</h2></div>', unsafe_allow_html=True)
        fig = analytics.create_payment_method_chart(start_date, end_date)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        st.markdown('<div class="section-header"><h2 class="section-title">Monthly Comparison</h2></div>', unsafe_allow_html=True)
        fig = analytics.create_monthly_comparison_chart()
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Recent transactions
    st.markdown('<div class="section-header"><h2 class="section-title">Recent Transactions</h2></div>', unsafe_allow_html=True)

    recent_expenses = expense_service.get_expenses(
        start_date=start_date,
        end_date=end_date,
        limit=10
    )

    if recent_expenses:
        df_data = []
        for exp in recent_expenses:
            df_data.append({
                "Date": exp.date,
                "Amount": f"{Config.CURRENCY_SYMBOL}{exp.amount:,.2f}",
                "Category": exp.category,
                "Description": exp.description,
                "Payment": exp.payment_method,
                "Merchant": exp.merchant or "—"
            })
        st.dataframe(
            df_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Amount": st.column_config.TextColumn("Amount", width="medium"),
                "Category": st.column_config.TextColumn("Category", width="medium"),
                "Description": st.column_config.TextColumn("Description", width="large"),
            }
        )
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📭</div>
            <div class="empty-state-title">No transactions yet</div>
            <div class="empty-state-text">Add your first expense to see it here</div>
        </div>
        """, unsafe_allow_html=True)


def render_expenses_page():
    """Render the expenses management page."""
    st.markdown("""
    <div class="section-header">
        <h1 class="section-title">Expenses</h1>
    </div>
    """, unsafe_allow_html=True)

    # Add expense button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add Expense", use_container_width=True):
            st.session_state.show_add_expense = True
            st.session_state.editing_expense_id = None
            st.rerun()

    # Filters
    with st.expander("🔍 Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_start = st.date_input("From", value=date.today().replace(day=1), key="filter_start")
            filter_category = st.selectbox("Category", ["All"] + Config.EXPENSE_CATEGORIES, key="filter_category")
        with col2:
            filter_end = st.date_input("To", value=date.today(), key="filter_end")
            filter_payment = st.selectbox("Payment Method", ["All"] + Config.PAYMENT_METHODS, key="filter_payment")
        with col3:
            filter_search = st.text_input("Search", placeholder="Description, merchant, notes...", key="filter_search")
            col_min, col_max = st.columns(2)
            with col_min:
                filter_min = st.number_input("Min Amount", min_value=0.0, value=0.0, step=100.0, key="filter_min")
            with col_max:
                filter_max = st.number_input("Max Amount", min_value=0.0, value=0.0, step=100.0, key="filter_max")

    # Get filtered expenses
    expenses = expense_service.get_expenses(
        start_date=filter_start.isoformat() if filter_start else None,
        end_date=filter_end.isoformat() if filter_end else None,
        category=filter_category if filter_category != "All" else None,
        payment_method=filter_payment if filter_payment != "All" else None,
        search_text=filter_search if filter_search else None,
        min_amount=filter_min if filter_min > 0 else None,
        max_amount=filter_max if filter_max > 0 else None
    )

    # Add/Edit expense form
    if st.session_state.show_add_expense or st.session_state.editing_expense_id:
        editing_expense = None
        if st.session_state.editing_expense_id:
            editing_expense = expense_service.get_expense(st.session_state.editing_expense_id)

        with st.form("expense_form", clear_on_submit=False):
            st.markdown("### " + ("Edit Expense" if editing_expense else "Add New Expense"))

            col1, col2 = st.columns(2)
            with col1:
                exp_date = st.date_input(
                    "Date *",
                    value=datetime.strptime(editing_expense.date, "%Y-%m-%d").date() if editing_expense else date.today(),
                    max_value=date.today()
                )
                amount = st.number_input(
                    "Amount *",
                    min_value=0.01,
                    value=float(editing_expense.amount) if editing_expense else 0.0,
                    step=1.0,
                    format="%.2f"
                )
                category = st.selectbox(
                    "Category *",
                    Config.EXPENSE_CATEGORIES,
                    index=Config.EXPENSE_CATEGORIES.index(editing_expense.category) if editing_expense else 0
                )
            with col2:
                description = st.text_input(
                    "Description *",
                    value=editing_expense.description if editing_expense else "",
                    placeholder="e.g., Lunch at restaurant"
                )
                payment_method = st.selectbox(
                    "Payment Method *",
                    Config.PAYMENT_METHODS,
                    index=Config.PAYMENT_METHODS.index(editing_expense.payment_method) if editing_expense else 0
                )
                merchant = st.text_input(
                    "Merchant/Payee",
                    value=editing_expense.merchant if editing_expense and editing_expense.merchant else "",
                    placeholder="e.g., Saravana Bhavan"
                )
            notes = st.text_area(
                "Notes",
                value=editing_expense.notes if editing_expense and editing_expense.notes else "",
                placeholder="Optional notes..."
            )

            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                submitted = st.form_submit_button("Save", type="primary", use_container_width=True)
            with col2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

            if submitted:
                is_valid, error = expense_service.validate_expense(
                    amount, exp_date.isoformat(), category, description, payment_method
                )
                if not is_valid:
                    st.error(error)
                else:
                    if editing_expense:
                        success, error, updated = expense_service.update_expense(
                            editing_expense.id,
                            exp_date.isoformat(), amount, category, description,
                            payment_method, merchant, notes
                        )
                        if success:
                            st.success("Expense updated!")
                            st.session_state.show_add_expense = False
                            st.session_state.editing_expense_id = None
                            st.rerun()
                        else:
                            st.error(error)
                    else:
                        success, error, new_expense = expense_service.add_expense(
                            exp_date.isoformat(), amount, category, description,
                            payment_method, merchant, notes
                        )
                        if success:
                            st.success("Expense added!")
                            st.session_state.show_add_expense = False
                            st.rerun()
                        else:
                            st.error(error)

            if cancelled:
                st.session_state.show_add_expense = False
                st.session_state.editing_expense_id = None
                st.rerun()

    # Expense list
    if expenses:
        # Export button
        col1, col2 = st.columns([3, 1])
        with col2:
            export_expenses = expense_service.get_expenses_for_export(
                start_date=filter_start.isoformat() if filter_start else None,
                end_date=filter_end.isoformat() if filter_end else None,
                category=filter_category if filter_category != "All" else None,
                payment_method=filter_payment if filter_payment != "All" else None
            )
            if export_expenses:
                csv_data = expense_service.export_to_csv(export_expenses)
                st.download_button(
                    "📥 Export CSV",
                    csv_data,
                    file_name=f"expenses_{filter_start.isoformat()}_to_{filter_end.isoformat()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        st.markdown(f"**{len(expenses)} transaction(s) found**")

        for exp in expenses:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 3, 1])

                with col1:
                    st.caption(exp.date)
                with col2:
                    st.markdown(f"**{Config.CURRENCY_SYMBOL}{exp.amount:,.2f}**")
                with col3:
                    st.caption(exp.category)
                with col4:
                    desc = exp.description
                    if exp.merchant:
                        desc += f" — {exp.merchant}"
                    st.caption(desc)
                with col5:
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("✏️", key=f"edit_{exp.id}", help="Edit"):
                            st.session_state.editing_expense_id = exp.id
                            st.session_state.show_add_expense = True
                            st.rerun()
                    with btn_col2:
                        if st.session_state.confirm_delete_id == exp.id:
                            if st.button("✅", key=f"confirm_del_{exp.id}", help="Confirm delete"):
                                success, error = expense_service.delete_expense(exp.id)
                                if success:
                                    st.success("Deleted!")
                                    st.session_state.confirm_delete_id = None
                                    st.rerun()
                                else:
                                    st.error(error)
                        else:
                            if st.button("🗑️", key=f"del_{exp.id}", help="Delete"):
                                st.session_state.confirm_delete_id = exp.id
                                st.rerun()
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📭</div>
            <div class="empty-state-title">No expenses found</div>
            <div class="empty-state-text">Adjust your filters or add a new expense</div>
        </div>
        """, unsafe_allow_html=True)


def render_analytics_page():
    """Render the analytics page."""
    st.markdown("""
    <div class="section-header">
        <h1 class="section-title">Analytics</h1>
    </div>
    """, unsafe_allow_html=True)

    start_date, end_date = render_period_selector()

    # Tabs for different analytics views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📅 Daily", "📆 Weekly", "📊 Monthly", "🏷️ Categories", "💳 Payments"
    ])

    with tab1:
        st.markdown('<div class="section-header"><h2 class="section-title">Daily Spending</h2></div>', unsafe_allow_html=True)
        fig = analytics.create_spending_trend_chart(start_date, end_date, compare_previous=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Daily stats
        daily_data = db.get_daily_spending(start_date, end_date)
        if daily_data:
            df = pd.DataFrame([dict(row) for row in daily_data])
            df["total"] = pd.to_numeric(df["total"])
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Highest Day", f"{Config.CURRENCY_SYMBOL}{df['total'].max():,.2f}")
            with col2:
                st.metric("Lowest Day", f"{Config.CURRENCY_SYMBOL}{df['total'].min():,.2f}")
            with col3:
                st.metric("Average", f"{Config.CURRENCY_SYMBOL}{df['total'].mean():,.2f}")

    with tab2:
        st.markdown('<div class="section-header"><h2 class="section-title">Weekly Spending</h2></div>', unsafe_allow_html=True)
        fig = analytics.create_weekly_spending_chart(start_date, end_date)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with tab3:
        st.markdown('<div class="section-header"><h2 class="section-title">Monthly Spending</h2></div>', unsafe_allow_html=True)
        fig = analytics.create_monthly_comparison_chart()
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Monthly stats
        monthly_data = db.get_monthly_spending()
        if monthly_data:
            df = pd.DataFrame([dict(row) for row in monthly_data])
            df["total"] = pd.to_numeric(df["total"])
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Highest Month", f"{Config.CURRENCY_SYMBOL}{df['total'].max():,.2f}")
            with col2:
                st.metric("Lowest Month", f"{Config.CURRENCY_SYMBOL}{df['total'].min():,.2f}")
            with col3:
                st.metric("Average", f"{Config.CURRENCY_SYMBOL}{df['total'].mean():,.2f}")

    with tab4:
        st.markdown('<div class="section-header"><h2 class="section-title">Category Analysis</h2></div>', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 2])
        with col1:
            cat_data = db.get_spending_by_category(start_date, end_date)
            if cat_data:
                selected_cat = st.selectbox(
                    "Select category for trend",
                    [row["category"] for row in cat_data],
                    key="cat_trend_select"
                )
            else:
                selected_cat = None

        with col2:
            if selected_cat:
                fig = analytics.create_category_monthly_trend(selected_cat, 12)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Category breakdown table
        if cat_data:
            df_data = []
            total = sum(float(row["total"]) for row in cat_data)
            for row in cat_data:
                pct = (float(row["total"]) / total * 100) if total > 0 else 0
                df_data.append({
                    "Category": row["category"],
                    "Amount": f"{Config.CURRENCY_SYMBOL}{float(row['total']):,.2f}",
                    "Transactions": row["count"],
                    "Percentage": f"{pct:.1f}%"
                })
            st.dataframe(df_data, use_container_width=True, hide_index=True)

    with tab5:
        st.markdown('<div class="section-header"><h2 class="section-title">Payment Method Analysis</h2></div>', unsafe_allow_html=True)
        fig = analytics.create_payment_method_chart(start_date, end_date)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        pay_data = db.get_spending_by_payment_method(start_date, end_date)
        if pay_data:
            df_data = []
            total = sum(float(row["total"]) for row in pay_data)
            for row in pay_data:
                pct = (float(row["total"]) / total * 100) if total > 0 else 0
                df_data.append({
                    "Payment Method": row["payment_method"],
                    "Amount": f"{Config.CURRENCY_SYMBOL}{float(row['total']):,.2f}",
                    "Transactions": row["count"],
                    "Percentage": f"{pct:.1f}%"
                })
            st.dataframe(df_data, use_container_width=True, hide_index=True)

    # Top expenses
    st.markdown('<div class="section-header"><h2 class="section-title">Largest Expenses</h2></div>', unsafe_allow_html=True)
    fig = analytics.create_top_expenses_chart(start_date, end_date, 10)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_budgets_page():
    """Render the budgets management page."""
    st.markdown("""
    <div class="section-header">
        <h1 class="section-title">Budgets</h1>
    </div>
    """, unsafe_allow_html=True)

    # Month selector
    col1, col2 = st.columns([2, 1])
    with col1:
        months = []
        for i in range(12):
            d = date.today().replace(day=1) - timedelta(days=1)
            d = d.replace(day=1)
            for _ in range(i):
                d = (d - timedelta(days=1)).replace(day=1)
            months.append(d.strftime("%Y-%m"))
        months.reverse()

        selected_month = st.selectbox(
            "Select Month",
            months,
            index=months.index(date.today().strftime("%Y-%m")) if date.today().strftime("%Y-%m") in months else 0
        )

    # Budget status
    budget_status = expense_service.get_budget_status(selected_month)

    # Overall budget gauge
    st.markdown('<div class="section-header"><h2 class="section-title">Overall Budget</h2></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        fig = analytics.create_budget_gauge(
            budget_status["total_spent"],
            budget_status["overall_budget"],
            f"Budget: {selected_month}"
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        if budget_status["overall_budget"] > 0:
            status = budget_status["overall_warning"]
            badge_class = "ok" if status == "ok" else ("warning" if status == "warning" else "over")
            st.markdown(f"""
            <div style="padding: 1rem;">
                <div class="budget-badge {badge_class}">{status.upper()}</div>
                <div style="margin-top: 1rem; font-size: 1.125rem;">
                    <strong>Budget:</strong> {Config.CURRENCY_SYMBOL}{budget_status['overall_budget']:,.2f}<br>
                    <strong>Spent:</strong> {Config.CURRENCY_SYMBOL}{budget_status['total_spent']:,.2f}<br>
                    <strong>Remaining:</strong> {Config.CURRENCY_SYMBOL}{budget_status['overall_remaining']:,.2f}<br>
                    <strong>Used:</strong> {budget_status['overall_percentage']:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No overall budget set for this month. Set one below.")

    # Set overall budget
    with st.form("overall_budget_form"):
        st.markdown("### Set Overall Budget")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            overall_budget = st.number_input(
                "Monthly Budget",
                min_value=0.0,
                value=float(budget_status["overall_budget"]),
                step=1000.0,
                format="%.2f"
            )
        with col2:
            if st.form_submit_button("Save", type="primary"):
                success, error, budget = expense_service.set_budget(selected_month, overall_budget)
                if success:
                    st.success("Overall budget updated!")
                    st.rerun()
                else:
                    st.error(error)
        with col3:
            if budget_status["overall_budget"] > 0:
                if st.form_submit_button("Remove", type="secondary"):
                    success, error = expense_service.delete_budget(selected_month)
                    if success:
                        st.success("Budget removed!")
                        st.rerun()
                    else:
                        st.error(error)

    st.markdown("<br>", unsafe_allow_html=True)

    # Category budgets
    st.markdown('<div class="section-header"><h2 class="section-title">Category Budgets</h2></div>', unsafe_allow_html=True)

    # Chart
    fig = analytics.create_budget_bar_chart(budget_status)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Category budget forms
    st.markdown("### Set Category Budgets")

    # Show existing category budgets
    cat_budgets = budget_status.get("categories", {})

    for category in Config.EXPENSE_CATEGORIES:
        existing = cat_budgets.get(category, {})
        budget_amt = existing.get("budget", 0)

        with st.expander(f"{category}" + (f" — Budget: {Config.CURRENCY_SYMBOL}{budget_amt:,.2f}" if budget_amt > 0 else ""), expanded=False):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                cat_budget = st.number_input(
                    f"Budget for {category}",
                    min_value=0.0,
                    value=float(budget_amt),
                    step=500.0,
                    format="%.2f",
                    key=f"budget_{category}"
                )
            with col2:
                if st.button("Save", key=f"save_budget_{category}", use_container_width=True):
                    success, error, budget = expense_service.set_budget(selected_month, cat_budget, category)
                    if success:
                        st.success(f"Budget for {category} updated!")
                        st.rerun()
                    else:
                        st.error(error)
            with col3:
                if budget_amt > 0:
                    if st.button("Remove", key=f"remove_budget_{category}", use_container_width=True):
                        success, error = expense_service.delete_budget(selected_month, category)
                        if success:
                            st.success(f"Budget for {category} removed!")
                            st.rerun()
                        else:
                            st.error(error)


def render_ai_insights_page():
    """Render the AI insights page."""
    st.markdown("""
    <div class="section-header">
        <h1 class="section-title">AI Insights</h1>
    </div>
    """, unsafe_allow_html=True)

    if not ai_service.is_configured():
        st.markdown("""
        <div class="alert alert-info">
            <h3>🤖 AI Insights Not Configured</h3>
            <p>To enable AI-powered insights, you need to configure your NVIDIA Nemotron API key.</p>
            <p><strong>Steps to configure:</strong></p>
            <ol>
                <li>Get an API key from <a href="https://build.nvidia.com/" target="_blank">NVIDIA Build</a></li>
                <li>Add it to your <code>.env</code> file: <code>NVIDIA_API_KEY=your_key_here</code></li>
                <li>Or configure in Streamlit secrets: <code>NVIDIA_API_KEY = "your_key_here"</code></li>
                <li>Restart the application</li>
            </ol>
            <p><em>All expense tracking features work without an API key. AI insights are optional.</em></p>
        </div>
        """, unsafe_allow_html=True)

        # Show configuration info
        with st.expander("ℹ️ Configuration Details"):
            st.code(f"""
# .env file
NVIDIA_API_KEY=your_api_key_here
NVIDIA_MODEL={Config.NVIDIA_MODEL}
NVIDIA_BASE_URL={Config.NVIDIA_BASE_URL}
NVIDIA_TIMEOUT={Config.NVIDIA_TIMEOUT}
NVIDIA_MAX_TOKENS={Config.NVIDIA_MAX_TOKENS}
            """)

        # Still allow period selection for when AI is configured
        start_date, end_date = render_period_selector()
        return

    # Period selector
    start_date, end_date = render_period_selector()

    # Tabs for different insights
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Summary", "🔍 Patterns", "💡 Savings", "🎯 Budgets", "💬 Ask AI"
    ])

    with tab1:
        if st.button("Generate Summary", key="gen_summary", type="primary"):
            with st.spinner("Analyzing your spending..."):
                success, result = ai_service.get_spending_summary(start_date, end_date)
                if success:
                    st.markdown(result)
                else:
                    st.error(result)

    with tab2:
        if st.button("Identify Patterns", key="gen_patterns", type="primary"):
            with st.spinner("Looking for unusual patterns..."):
                success, result = ai_service.identify_unusual_patterns(start_date, end_date)
                if success:
                    st.markdown(result)
                else:
                    st.error(result)

    with tab3:
        if st.button("Suggest Savings", key="gen_savings", type="primary"):
            with st.spinner("Finding savings opportunities..."):
                success, result = ai_service.suggest_savings_opportunities(start_date, end_date)
                if success:
                    st.markdown(result)
                else:
                    st.error(result)

    with tab4:
        if st.button("Analyze Budgets", key="gen_budget", type="primary"):
            with st.spinner("Analyzing budget performance..."):
                success, result = ai_service.explain_budget_overruns()
                if success:
                    st.markdown(result)
                else:
                    st.error(result)

    with tab5:
        st.markdown("### Ask a Question")
        st.caption("Examples: 'How much did I spend on food this month?', 'What was my largest expense?', 'Compare this month to last month'")

        # Chat history
        for msg in st.session_state.ai_chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-message user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message assistant">{msg["content"]}</div>', unsafe_allow_html=True)

        # Question input
        with st.form("ai_question_form", clear_on_submit=True):
            question = st.text_input("Your question", placeholder="Ask about your expenses...", key="ai_question")
            submitted = st.form_submit_button("Ask", type="primary")

            if submitted and question:
                st.session_state.ai_chat_history.append({"role": "user", "content": question})

                with st.spinner("Thinking..."):
                    success, answer = ai_service.answer_question(question, start_date, end_date)
                    if success:
                        st.session_state.ai_chat_history.append({"role": "assistant", "content": answer})
                    else:
                        st.session_state.ai_chat_history.append({"role": "assistant", "content": f"Error: {answer}"})
                st.rerun()


def render_settings_page():
    """Render the settings page."""
    st.markdown("""
    <div class="section-header">
        <h1 class="section-title">Settings</h1>
    </div>
    """, unsafe_allow_html=True)

    # Currency settings
    st.markdown('<div class="section-header"><h2 class="section-title">Display Settings</h2></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        currency = st.selectbox(
            "Display Currency",
            ["INR (₹)", "USD ($)", "EUR (€)", "GBP (£)"],
            index=0,
            help="Changes display only. No currency conversion is performed."
        )
    with col2:
        st.info("💡 Changing the display currency only affects how amounts are shown. No foreign exchange conversion is performed.")

    # AI Configuration
    st.markdown('<div class="section-header"><h2 class="section-title">AI Configuration</h2></div>', unsafe_allow_html=True)

    ai_configured = ai_service.is_configured()
    if ai_configured:
        st.success("✅ NVIDIA API key is configured")
        st.caption(f"Model: {Config.NVIDIA_MODEL}")
        st.caption(f"Endpoint: {Config.NVIDIA_BASE_URL}")
    else:
        st.warning("⚠️ NVIDIA API key not configured")
        st.caption("Add NVIDIA_API_KEY to .env or Streamlit secrets to enable AI insights")

    with st.expander("AI Settings"):
        st.code(f"""
# Environment variables or Streamlit secrets
NVIDIA_API_KEY=your_key_here
NVIDIA_MODEL={Config.NVIDIA_MODEL}
NVIDIA_BASE_URL={Config.NVIDIA_BASE_URL}
NVIDIA_TIMEOUT={Config.NVIDIA_TIMEOUT}
NVIDIA_MAX_TOKENS={Config.NVIDIA_MAX_TOKENS}
        """)

    # Data management
    st.markdown('<div class="section-header"><h2 class="section-title">Data Management</h2></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Sample Data")
        sample_loaded = db.get_setting("sample_data_loaded") == "1"
        if sample_loaded:
            st.info("Sample data is already loaded")
        else:
            if st.button("Load Sample Data", type="secondary", use_container_width=True):
                st.session_state.show_sample_data_confirm = True

        if st.session_state.show_sample_data_confirm:
            st.warning("This will add ~20 sample expenses and budgets. Continue?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Yes, Load Sample Data", type="primary", use_container_width=True):
                    with st.spinner("Loading sample data..."):
                        success, error, count = expense_service.load_sample_data()
                        if success:
                            st.success(f"Loaded {count} sample expenses!")
                            st.session_state.show_sample_data_confirm = False
                            st.rerun()
                        else:
                            st.error(error)
            with col_no:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.show_sample_data_confirm = False
                    st.rerun()

    with col2:
        st.markdown("#### Database")
        st.caption(f"Location: `{Config.DATABASE_PATH}`")
        st.caption("⚠️ On Streamlit Community Cloud, the database is ephemeral and will reset on redeploy. Use a persistent database service for production.")

        # Database stats
        total_expenses = db.count_expenses()
        st.caption(f"Total expenses in database: {total_expenses}")

    # About
    st.markdown('<div class="section-header"><h2 class="section-title">About</h2></div>', unsafe_allow_html=True)

    st.markdown(f"""
    **{Config.APP_NAME}** v1.0.0

    {Config.APP_TAGLINE}

    **Creator:** {Config.CREATOR_NAME}  
    **Email:** {Config.CREATOR_EMAIL}

    **Developer:** {Config.DEVELOPER_NAME}  
    **Email:** {Config.DEVELOPER_EMAIL}

    **GitHub:** https://github.com/{Config.GITHUB_OWNER}/{Config.GITHUB_REPO}

    **Technology Stack:**
    - Python 3.11+
    - Streamlit
    - SQLite
    - Pandas
    - Plotly
    - NVIDIA Nemotron API

    **Privacy Notice:** This is a single-user personal expense tracker. 
    Data is stored locally in SQLite. On cloud deployments without persistent storage, 
    data may be lost on redeploy. Do not use a public deployment without authentication 
    for sensitive financial data.
    """)


def render_welcome_screen():
    """Render welcome screen for first-time users."""
    st.markdown(f"""
    <div style="text-align: center; padding: 3rem 2rem;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">💰</div>
        <h1 style="font-size: 2.5rem; font-weight: 700; color: var(--text); margin-bottom: 0.5rem;">Welcome to Keerthi</h1>
        <p style="font-size: 1.25rem; color: var(--text-muted); margin-bottom: 2rem;">{Config.APP_TAGLINE}</p>
        <div style="max-width: 500px; margin: 0 auto; text-align: left;">
            <p style="color: var(--text); line-height: 1.7;">
                Keerthi helps you track expenses, understand spending patterns, 
                set budgets, and get AI-powered financial insights.
            </p>
            <h3 style="margin-top: 1.5rem; margin-bottom: 1rem;">Get Started:</h3>
            <ol style="color: var(--text); line-height: 2;">
                <li>Click <strong>Expenses</strong> in the sidebar to add your first expense</li>
                <li>Set <strong>Budgets</strong> to track your spending limits</li>
                <li>View <strong>Analytics</strong> for visual insights</li>
                <li>Configure <strong>AI Insights</strong> with your NVIDIA API key for smart recommendations</li>
            </ol>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Load Sample Data to Explore", type="primary", use_container_width=True):
            with st.spinner("Loading sample data..."):
                success, error, count = expense_service.load_sample_data()
                if success:
                    st.success(f"Loaded {count} sample expenses! Navigate to Dashboard to explore.")
                    st.rerun()
                else:
                    st.error(error)


def render_project_credit_header():
    """Keep college-project credits visible at the top of every page."""
    creator_photo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "KEERTHI PROFILE PIC.jpeg")
    developer_photo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Gowtham Profile Professional.jpg")

    st.markdown(
        """
        <div style="padding: 0.45rem 0 0.2rem 0;">
            <div style="font-size:0.72rem; letter-spacing:0.12em; text-transform:uppercase;
                        color:#34D399; font-weight:700;">College Project · Project Credits</div>
            <h1 style="margin:0.2rem 0 0.6rem 0; font-size:1.65rem;">
                Keerthi — AI Personal Expense Tracker
            </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    creator_col, developer_col = st.columns(2, gap="medium")
    with creator_col:
        with st.container(border=True):
            photo_col, details_col = st.columns([1, 3], vertical_alignment="center")
            with photo_col:
                if os.path.isfile(creator_photo):
                    st.image(creator_photo, width=84)
                else:
                    st.markdown("## 👩🏻")
            with details_col:
                st.markdown("**CREATOR**")
                st.markdown("### Keerthi")
                st.markdown("📧 keerthanaskeerthi97@gmail.com")
    with developer_col:
        with st.container(border=True):
            photo_col, details_col = st.columns([1, 3], vertical_alignment="center")
            with photo_col:
                if os.path.isfile(developer_photo):
                    st.image(developer_photo, width=84)
                else:
                    st.markdown("## 👨🏻‍💻")
            with details_col:
                st.markdown("**DEVELOPER**")
                st.markdown("### Gowtham A")
                st.markdown("📧 gowthamgo1745@gmail.com")

    st.divider()


def main():
    """Main application entry point."""
    init_session_state()

    # Show creator and developer credits above the application content.
    render_project_credit_header()

    # Render sidebar
    render_sidebar()

    # Check if database has any expenses
    total_expenses = db.count_expenses()

    # Render current page
    if total_expenses == 0 and st.session_state.current_page != "settings":
        # Show welcome screen for empty database
        if st.session_state.current_page == "dashboard":
            render_welcome_screen()
        else:
            # Redirect to dashboard for empty state
            st.session_state.current_page = "dashboard"
            st.rerun()
    else:
        # Render selected page
        if st.session_state.current_page == "dashboard":
            render_dashboard()
        elif st.session_state.current_page == "expenses":
            render_expenses_page()
        elif st.session_state.current_page == "analytics":
            render_analytics_page()
        elif st.session_state.current_page == "budgets":
            render_budgets_page()
        elif st.session_state.current_page == "ai_insights":
            render_ai_insights_page()
        elif st.session_state.current_page == "settings":
            render_settings_page()


if __name__ == "__main__":
    main()