# Keerthi — AI Expense Tracker

> **Understand Your Money. Improve Your Future.**

A premium, modern personal expense tracker with AI-powered insights built with Streamlit, SQLite, and NVIDIA Nemotron.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

---

## Overview

**Keerthi** is a complete personal finance dashboard that helps you:
- 📝 **Record expenses** with categories, payment methods, merchants, and notes
- 📊 **Visualize spending** with interactive charts (daily, weekly, monthly, by category, by payment method)
- 🎯 **Set budgets** for overall spending and individual categories with visual warnings
- 🤖 **Get AI insights** powered by NVIDIA Nemotron for spending summaries, pattern detection, and savings suggestions
- 📥 **Export data** to CSV for external analysis
- 🔒 **Keep data private** with local SQLite storage

---

## Features

### Core Expense Tracking
- ✅ Full CRUD operations (Create, Read, Update, Delete)
- ✅ Validation for amounts, dates, categories, and payment methods
- ✅ Duplicate submission prevention
- ✅ Confirmation before deletion
- ✅ Searchable, filterable transaction tables
- ✅ Filters: date range, category, payment method, description, amount range
- ✅ CSV export of filtered data

### Analytics & Visualizations
- 📈 Daily spending trend with previous period comparison
- 📅 Weekly spending aggregation
- 📊 Monthly spending comparison
- 🏷️ Category-wise spending breakdown (pie chart + trends)
- 💳 Payment method analysis
- 💰 Top expenses ranking
- 📋 Summary cards: total, daily average, top category, transaction count

### Budget Management
- 🎯 Monthly overall budget
- 🏷️ Per-category budgets
- 📊 Visual budget vs actual charts
- ⚠️ Color-coded warnings: OK (green), Warning at 80% (orange), Over budget (red)
- 📈 Budget usage gauge charts

### AI-Powered Insights (Optional)
- 📋 **Spending Summary** - Overview with key observations
- 🔍 **Unusual Patterns** - Detect anomalies in spending
- 💡 **Savings Suggestions** - Practical, data-backed recommendations
- 🎯 **Budget Analysis** - Explain overruns with specific expenses
- 💬 **Natural Language Q&A** - Ask questions like "How much did I spend on food this month?"

### Design & UX
- 🌙 Dark navy theme with emerald green accents
- 📱 Responsive layout (desktop, tablet, mobile)
- 🎨 Professional cards, gradients, and typography
- ♿ Accessible color contrasts
- 🏷️ Clear empty states and loading indicators

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Web Framework | Streamlit 1.32+ |
| Language | Python 3.11+ |
| Database | SQLite (local file) |
| Data Analysis | Pandas 2.1+ |
| Visualizations | Plotly 5.18+ |
| AI Integration | NVIDIA Nemotron API |
| HTTP Client | Requests 2.31+ |
| Testing | Pytest 7.4+ |

---

## Project Structure

```
AI-Expense-Tracker/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .gitignore            # Git ignore rules
├── .env.example          # Environment variable template
├── config.py             # Configuration management
├── database.py           # SQLite database layer
├── expense_service.py    # Expense business logic
├── analytics.py          # Analytics & chart generation
├── ai_service.py         # NVIDIA Nemotron integration
├── assets/
│   ├── README.md         # Asset documentation
│   ├── keerthi.jpg       # Creator photo (optional)
│   └── gowtham.jpg       # Developer photo (optional)
├── .streamlit/
│   └── config.toml       # Streamlit configuration
└── tests/
    ├── test_database.py  # Database tests
    ├── test_analytics.py # Analytics tests
    └── test_expenses.py  # Expense service tests
```

---

## Prerequisites

- **Python 3.11 or 3.12** (tested on 3.11, 3.12)
- **Windows 10/11**, macOS, or Linux
- **Git** for version control
- **NVIDIA API Key** (optional, for AI insights) — get one at [build.nvidia.com](https://build.nvidia.com/)

---

## Installation (Windows)

### 1. Clone the Repository

```powershell
git clone https://github.com/Gowtham1745/AI-Expense-Tracker.git
cd AI-Expense-Tracker
```

### 2. Create Virtual Environment

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

> **Note:** If you get a script execution error, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3. Install Dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

```powershell
copy .env.example .env
```

Edit `.env` with your settings:
```env
# Required for AI insights (optional)
NVIDIA_API_KEY=your_api_key_here

# Optional overrides
NVIDIA_MODEL=nvidia/nemotron-3-ultra
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_TIMEOUT=30
NVIDIA_MAX_TOKENS=1024
```

### 5. Run the Application

```powershell
python -m streamlit run app.py
```

The app will open at **http://localhost:8501**

---

## NVIDIA API Key Setup

AI insights are **optional** — all core features work without an API key.

### Getting an API Key

1. Visit [build.nvidia.com](https://build.nvidia.com/)
2. Sign in or create an account
3. Navigate to **Nemotron 3 Ultra** (or your preferred model)
4. Generate an API key
5. Add it to your `.env` file or Streamlit secrets

### Streamlit Secrets (for Cloud Deployment)

In Streamlit Community Cloud, add secrets in the dashboard:

```toml
# .streamlit/secrets.toml
NVIDIA_API_KEY = "your_api_key_here"
NVIDIA_MODEL = "nvidia/nemotron-3-ultra"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_TIMEOUT = 30
NVIDIA_MAX_TOKENS = 1024
```

---

## GitHub Upload

```powershell
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Keerthi AI Expense Tracker"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/Gowtham1745/AI-Expense-Tracker.git

# Push
git push -u origin main
```

### Files That Should NOT Be Committed

The `.gitignore` excludes:
- `.env` (contains API keys)
- `*.db` (personal financial data)
- `venv/` (virtual environment)
- `__pycache__/` (compiled Python)
- `.streamlit/secrets.toml` (cloud secrets)

---

## Streamlit Community Cloud Deployment

### 1. Push to GitHub
Ensure your code is on GitHub (see above).

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/)
3. Click **New app**
4. Select your repository: `Gowtham1745/AI-Expense-Tracker`
5. Branch: `main`
6. Main file path: `app.py`
7. Click **Deploy!**

### 3. Configure Secrets

In the Streamlit Cloud dashboard:
1. Go to your app settings
2. Click **Secrets**
3. Add your NVIDIA API key:
   ```toml
   NVIDIA_API_KEY = "your_api_key_here"
   NVIDIA_MODEL = "nvidia/nemotron-3-ultra"
   ```
4. Save and the app will redeploy

### ⚠️ Important: Data Persistence on Cloud

**Streamlit Community Cloud uses ephemeral storage.** The SQLite database will be **reset on every redeploy**.

For production use with persistent data:
- Use a managed database (PostgreSQL, MySQL, etc.)
- Or use a persistent volume service
- This version is designed for **personal/local use**

---

## Usage Guide

### First Run
1. The app starts with an empty database
2. You'll see a welcome screen on the Dashboard
3. Click **"Load Sample Data to Explore"** to populate demo data
4. Or go to **Expenses** → **Add Expense** to start tracking

### Adding Expenses
1. Navigate to **Expenses** page
2. Click **➕ Add Expense**
3. Fill in: Date, Amount, Category, Description, Payment Method
4. Optional: Merchant, Notes
5. Click **Save**

### Setting Budgets
1. Go to **Budgets** page
2. Select a month
3. Set **Overall Budget** (total for the month)
4. Set **Category Budgets** for specific categories
5. Visual gauges show usage with warnings at 80% and 100%

### Viewing Analytics
1. **Dashboard** — Quick overview with key metrics and charts
2. **Analytics** — Detailed charts (Daily, Weekly, Monthly, Categories, Payments)
3. Use the **Period Selector** to change the date range

### AI Insights
1. Configure your NVIDIA API key (see above)
2. Go to **AI Insights** page
3. Click buttons to generate:
   - **Summary** — Spending overview
   - **Patterns** — Unusual spending detection
   - **Savings** — Money-saving suggestions
   - **Budgets** — Budget overrun analysis
4. **Ask AI** — Type natural language questions

---

## Known Limitations

| Limitation | Details |
|------------|---------|
| **Single User** | No authentication; designed for personal use |
| **No Encryption** | SQLite file is not encrypted |
| **Cloud Data Loss** | Ephemeral storage on Streamlit Cloud |
| **No FX Conversion** | Currency display only, no exchange rates |
| **AI Rate Limits** | NVIDIA API has rate limits |
| **Model Availability** | Depends on NVIDIA's hosted models |

---

## Privacy & Security

- 🔐 **No data leaves your machine** (except optional AI API calls)
- 🔑 **API keys stored in environment/secrets** — never in code
- 💾 **Local SQLite database** — you own your data
- ⚠️ **Public deployments without auth are not secure** — don't store sensitive data on public URLs
- 📝 **No telemetry or tracking** — completely offline-capable

---

## Troubleshooting

### App Won't Start
```powershell
# Check Python version
python --version

# Reinstall dependencies
python -m pip install -r requirements.txt --force-reinstall
```

### Database Errors
```powershell
# Delete database to reset (WARNING: loses all data)
del %USERPROFILE%\.keerthi_expense_tracker\expenses.db
```

### AI Not Working
- Check `NVIDIA_API_KEY` is set in `.env` or Streamlit secrets
- Verify the model name is correct (check NVIDIA Build)
- Check internet connection
- Look at terminal for error messages

### Port Already in Use
```powershell
# Run on different port
streamlit run app.py --server.port 8502
```

---

## Credits

**Created by Keerthi**  
📧 keerthanaskeerthi97@gmail.com

**Developed by Gowtham A**  
📧 gowthamgo1745@gmail.com

**Repository:** https://github.com/Gowtham1745/AI-Expense-Tracker

---

## License

MIT License — feel free to use, modify, and distribute.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python -m pytest tests/ -v`
5. Submit a pull request

---

## Support

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/Gowtham1745/AI-Expense-Tracker/issues)
- 💡 **Feature Requests:** [GitHub Discussions](https://github.com/Gowtham1745/AI-Expense-Tracker/discussions)
- 📧 **Email:** gowthamgo1745@gmail.com