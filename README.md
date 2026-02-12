# Future Wallet

High-Fidelity Financial Projection & Simulation Engine — DATAFEST'26

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000 in your browser. Sample data is pre-filled.

## Features

- **Deterministic Simulation**: Seeded RNG produces bit-exact reproducible results
- **Day-by-Day Engine**: DAG-resolved daily processing of income, expenses, debts, assets
- **Multi-Currency**: USD, EUR, GBP, PKR, JPY with daily exchange rate fluctuations
- **Asset Portfolio**: Liquid, illiquid, yield-generating, and volatile assets with auto-liquidation
- **Credit Scoring**: 300-850 range model based on debt ratio, punctuality, restructuring
- **Progressive Taxation**: US-style brackets on realized capital gains
- **What-If Branching**: Snapshot any day, modify parameters, compare scenarios
- **Interactive Dashboard**: Dark-themed Bootstrap 5 UI with Chart.js visualizations

## Architecture

```
engine/
  models.py      - Data classes (IncomeStream, Expense, Debt, Asset, UserState)
  simulator.py   - Core day-by-day simulation loop with DAG ordering
  currency.py    - Multi-currency exchange rate engine
  credit.py      - Credit score model
  tax.py         - Progressive tax brackets
  assets.py      - Asset valuation and liquidation logic
  branching.py   - State snapshot and what-if branching
```

## API

- `POST /api/simulate` — Run simulation with JSON input
- `POST /api/branch` — Branch from a day with modified parameters
