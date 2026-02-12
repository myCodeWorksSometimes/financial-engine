"""State snapshotting, what-if branching, and scenario comparison."""

from __future__ import annotations
import copy
from typing import Any, Dict, Optional

from .models import UserState, SimulationResult, DailySnapshot


def snapshot(state: UserState) -> UserState:
    """Create a deep copy of the entire simulation state."""
    return copy.deepcopy(state)


def branch(base_snapshot: UserState, modifications: Dict[str, Any]) -> UserState:
    """Create a modified copy of a snapshot for what-if analysis.

    Supported modifications:
        - balance: new starting balance
        - credit_score: new credit score
        - add_income: dict with IncomeStream fields
        - remove_income: name of income to remove
        - add_expense: dict with Expense fields
        - remove_expense: name of expense to remove
        - add_debt: dict with Debt fields
        - remove_debt: name of debt to remove
        - add_asset: dict with Asset fields
        - remove_asset: name of asset to remove
        - seed: new seed for the branched simulation
    """
    from .models import IncomeStream, Expense, Debt, Asset

    branched = copy.deepcopy(base_snapshot)

    if "balance" in modifications:
        branched.balance = modifications["balance"]

    if "credit_score" in modifications:
        branched.credit_score = modifications["credit_score"]

    if "seed" in modifications:
        branched.seed = modifications["seed"]

    if "horizon_days" in modifications:
        branched.horizon_days = modifications["horizon_days"]

    # Income modifications
    if "add_income" in modifications:
        inc = modifications["add_income"]
        branched.income_streams.append(IncomeStream(**inc))

    if "remove_income" in modifications:
        name = modifications["remove_income"]
        branched.income_streams = [i for i in branched.income_streams if i.name != name]

    # Expense modifications
    if "add_expense" in modifications:
        exp = modifications["add_expense"]
        branched.expenses.append(Expense(**exp))

    if "remove_expense" in modifications:
        name = modifications["remove_expense"]
        branched.expenses = [e for e in branched.expenses if e.name != name]

    # Debt modifications
    if "add_debt" in modifications:
        d = modifications["add_debt"]
        branched.debts.append(Debt(**d))

    if "remove_debt" in modifications:
        name = modifications["remove_debt"]
        branched.debts = [d for d in branched.debts if d.name != name]

    # Asset modifications
    if "add_asset" in modifications:
        a = modifications["add_asset"]
        branched.assets.append(Asset(**a))

    if "remove_asset" in modifications:
        name = modifications["remove_asset"]
        branched.assets = [a for a in branched.assets if a.name != name]

    return branched


def compare(result_a: SimulationResult, result_b: SimulationResult) -> Dict[str, Any]:
    """Compare two simulation results and return comparison metrics."""
    summary_a = result_a.summary
    summary_b = result_b.summary

    def _safe_diff(key):
        va = summary_a.get(key, 0)
        vb = summary_b.get(key, 0)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            return round(vb - va, 2)
        return None

    comparison = {
        "original": summary_a,
        "branched": summary_b,
        "deltas": {
            "final_balance": _safe_diff("final_balance"),
            "final_net_worth": _safe_diff("final_net_worth"),
            "final_credit_score": _safe_diff("final_credit_score"),
            "collapse_probability": _safe_diff("collapse_probability"),
            "shock_resilience_index": _safe_diff("shock_resilience_index"),
        },
        "original_daily": [_snap_to_dict(s) for s in result_a.daily_data],
        "branched_daily": [_snap_to_dict(s) for s in result_b.daily_data],
    }
    return comparison


def _snap_to_dict(snap: DailySnapshot) -> dict:
    return {
        "day": snap.day,
        "balance": snap.balance,
        "net_worth": snap.net_worth,
        "credit_score": snap.credit_score,
        "nav": snap.nav,
        "liquidity_ratio": snap.liquidity_ratio,
    }
