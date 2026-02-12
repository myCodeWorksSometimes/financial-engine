"""Core day-by-day deterministic simulation loop."""

from __future__ import annotations
import random as _random_module
from typing import List, Optional

from .models import (
    UserState, DailySnapshot, SimulationEvent, SimulationResult,
    IncomeStream, Expense, Debt, Asset,
)
from .currency import CurrencyEngine
from .credit import update_credit_score
from .tax import calculate_tax
from .assets import (
    update_asset_values, get_total_asset_value,
    get_liquid_asset_value, get_liquidity_ratio,
    liquidate_to_cover,
)


def _is_payment_day(day: int, frequency: str) -> bool:
    """Check if a payment/income is due on this day based on frequency."""
    if frequency == "daily":
        return True
    if frequency == "weekly":
        return day % 7 == 0
    if frequency == "monthly":
        return day % 30 == 0
    return False


def _in_active_range(day: int, start_day: int, end_day: Optional[int]) -> bool:
    if day < start_day:
        return False
    if end_day is not None and day > end_day:
        return False
    return True


def run_simulation(state: UserState, start_day: int = 0) -> SimulationResult:
    """Run the full deterministic day-by-day simulation.

    DAG order per day:
        1. Apply exchange rate fluctuations
        2. Credit income streams
        3. Deduct expenses
        4. Process debt payments (interest + principal)
        5. Update asset valuations
        6. Check deficit -> auto liquidate
        7. Calculate taxes on realized gains
        8. Update credit score
        9. Record daily snapshot

    Args:
        state: The UserState with all inputs and parameters.
        start_day: The day number to start from (for branching support).

    Returns:
        SimulationResult with daily data, events, and summary.
    """
    rng = _random_module.Random(state.seed)
    currency_engine = CurrencyEngine(rng)

    daily_data: List[DailySnapshot] = []
    events: List[SimulationEvent] = []

    balance = state.balance
    credit_score = state.credit_score
    realized_gains = state.realized_gains
    unrealized_gains = 0.0
    taxes_paid = state.taxes_paid
    total_income_received = state.total_income_received
    total_expenses_paid = state.total_expenses_paid
    deficit_days = state.deficit_days
    shock_events = list(state.shock_events)
    recovery_days = list(state.recovery_days)
    current_shock_start = state.current_shock_start

    # Track total missed / due for credit calculation
    total_missed = sum(d.missed_payments for d in state.debts)
    total_due = sum(d.total_payments_due for d in state.debts)

    end_day = start_day + state.horizon_days

    for day in range(start_day, end_day):
        day_events: List[SimulationEvent] = []
        liquidation_count = 0

        # ---- Step 1: Exchange rate fluctuations ----
        currency_engine.advance_day(day)

        # ---- Step 2: Credit income streams ----
        for inc in state.income_streams:
            if not _in_active_range(day, inc.start_day, inc.end_day):
                continue
            if _is_payment_day(day, inc.frequency):
                amount_in_base = currency_engine.convert(
                    inc.amount, inc.currency, state.currency
                )
                balance += amount_in_base
                total_income_received += amount_in_base

        # ---- Step 3: Deduct expenses ----
        for exp in state.expenses:
            if not _in_active_range(day, exp.start_day, exp.end_day):
                continue
            if _is_payment_day(day, exp.frequency):
                amount_in_base = currency_engine.convert(
                    exp.amount, exp.currency, state.currency
                )
                balance -= amount_in_base
                total_expenses_paid += amount_in_base

        # ---- Step 4: Process debt payments ----
        for debt in state.debts:
            if debt.paid_off:
                continue
            if not _in_active_range(day, debt.start_day, None):
                continue

            # Accrue daily interest
            daily_rate = debt.interest_rate / 365.0
            interest = debt.principal * daily_rate
            debt.principal = round(debt.principal + interest, 6)

            # Monthly payments
            if _is_payment_day(day, "monthly"):
                debt.total_payments_due += 1
                total_due += 1
                payment = min(debt.min_payment, debt.principal)

                if balance >= payment:
                    balance -= payment
                    debt.principal = round(debt.principal - payment, 6)
                    debt.total_payments_made += 1
                else:
                    # Missed payment
                    debt.missed_payments += 1
                    total_missed += 1
                    day_events.append(SimulationEvent(
                        day=day,
                        event_type="deficit",
                        description=f"Missed payment on {debt.name} (owed {payment:.2f})",
                        amount=payment,
                        severity="danger",
                    ))

                # Check if debt is paid off
                if debt.principal <= 0.01:
                    debt.principal = 0.0
                    debt.paid_off = True
                    day_events.append(SimulationEvent(
                        day=day,
                        event_type="debt_payoff",
                        description=f"Paid off {debt.name}!",
                        amount=0,
                        severity="success",
                    ))

        # ---- Step 5: Update asset valuations ----
        old_asset_total = get_total_asset_value(state.assets)
        update_asset_values(state.assets, rng, day)
        new_asset_total = get_total_asset_value(state.assets)
        unrealized_gains = sum(
            max(0, a.value - a.cost_basis) for a in state.assets
        )

        # ---- Step 6: Check deficit -> auto liquidation ----
        if balance < 0:
            deficit_amount = abs(balance)
            recovered, liq_events = liquidate_to_cover(
                state.assets, deficit_amount, day
            )
            balance += recovered
            # Liquidation generates realized gains
            for ev in liq_events:
                realized_gains += max(0, ev.amount)  # simplified
            liquidation_count += len(liq_events)
            day_events.extend(liq_events)

            if balance < 0:
                day_events.append(SimulationEvent(
                    day=day,
                    event_type="deficit",
                    description=f"Balance negative: {balance:.2f} (insufficient assets to cover)",
                    amount=abs(balance),
                    severity="danger",
                ))

        # Track shocks (balance going negative)
        if balance < 0:
            deficit_days += 1
            if current_shock_start is None:
                current_shock_start = day
                shock_events.append(day)
        else:
            if current_shock_start is not None:
                recovery_days.append(day - current_shock_start)
                current_shock_start = None

        # ---- Step 7: Taxes on realized gains (annual settlement, simplified daily accrual) ----
        # We track realized gains; taxes are computed at the end for summary
        # but we can also do periodic tax deductions (e.g., quarterly)
        if day > 0 and day % 90 == 0 and realized_gains > 0:
            tax_due = calculate_tax(realized_gains)
            tax_increment = tax_due - taxes_paid
            if tax_increment > 0:
                balance -= tax_increment
                taxes_paid = tax_due
                day_events.append(SimulationEvent(
                    day=day,
                    event_type="tax",
                    description=f"Quarterly tax payment: {tax_increment:.2f}",
                    amount=tax_increment,
                    severity="info",
                ))

        # ---- Step 8: Update credit score ----
        total_debt_value = sum(d.principal for d in state.debts if not d.paid_off)
        credit_score = update_credit_score(
            credit_score,
            total_debt_value,
            total_income_received / max(1, day + 1) * 365,  # annualized income
            total_missed,
            max(1, total_due),
            liquidation_count,
        )

        # ---- Step 9: Record daily snapshot ----
        total_assets = get_total_asset_value(state.assets)
        total_debts = sum(d.principal for d in state.debts if not d.paid_off)
        net_worth = balance + total_assets - total_debts
        nav = total_assets
        liq_ratio = get_liquidity_ratio(state.assets, day)

        snapshot = DailySnapshot(
            day=day,
            balance=round(balance, 2),
            net_worth=round(net_worth, 2),
            credit_score=round(credit_score, 2),
            nav=round(nav, 2),
            liquidity_ratio=round(liq_ratio, 4),
            total_debt=round(total_debts, 2),
            total_assets=round(total_assets, 2),
        )
        daily_data.append(snapshot)
        events.extend(day_events)

    # ---- Build summary ----
    horizon = state.horizon_days
    final = daily_data[-1] if daily_data else None
    total_days = len(daily_data)
    collapse_prob = round(deficit_days / max(1, total_days) * 100, 2)

    # First deficit day
    first_deficit = None
    for snap in daily_data:
        if snap.balance < 0:
            first_deficit = snap.day
            break

    # Financial vibe
    balance_volatility = _compute_volatility(daily_data)
    if final and final.balance > 0 and collapse_prob == 0:
        if balance_volatility < 0.05:
            vibe = "Thriving"
            vibe_emoji = "\U0001f680"
        else:
            vibe = "Stable"
            vibe_emoji = "\U0001f60a"
    elif collapse_prob < 20:
        vibe = "Stressed"
        vibe_emoji = "\U0001f630"
    elif collapse_prob < 50:
        vibe = "Critical"
        vibe_emoji = "\U0001f525"
    else:
        vibe = "Collapsed"
        vibe_emoji = "\U0001f480"

    # Pet state
    if vibe == "Thriving":
        pet = "Happy Cat \U0001f431"
    elif vibe == "Stable":
        pet = "Nervous Dog \U0001f436"
    elif vibe == "Stressed":
        pet = "Hibernating Bear \U0001f43b"
    elif vibe == "Critical":
        pet = "Phoenix Rising \U0001f525"
    else:
        pet = "Ghost \U0001f47b"

    # Shock resilience index (0-100)
    if len(recovery_days) > 0:
        avg_recovery = sum(recovery_days) / len(recovery_days)
        sri = max(0, min(100, round(100 - avg_recovery * 2, 2)))
    elif deficit_days == 0:
        sri = 100.0
    else:
        sri = 0.0

    summary = {
        "final_balance": final.balance if final else 0,
        "final_net_worth": final.net_worth if final else 0,
        "final_credit_score": final.credit_score if final else state.credit_score,
        "collapse_probability": collapse_prob,
        "collapse_timing": first_deficit,
        "financial_vibe": f"{vibe_emoji} {vibe}",
        "pet_state": pet,
        "shock_resilience_index": sri,
        "total_income": round(total_income_received, 2),
        "total_expenses": round(total_expenses_paid, 2),
        "total_taxes_paid": round(taxes_paid, 2),
        "realized_gains": round(realized_gains, 2),
        "unrealized_gains": round(unrealized_gains, 2),
        "total_liquidation_events": sum(1 for e in events if e.event_type == "liquidation"),
        "deficit_days": deficit_days,
    }

    # Update state for potential branching
    state.balance = balance
    state.credit_score = credit_score
    state.realized_gains = realized_gains
    state.taxes_paid = taxes_paid
    state.total_income_received = total_income_received
    state.total_expenses_paid = total_expenses_paid
    state.deficit_days = deficit_days
    state.shock_events = shock_events
    state.recovery_days = recovery_days
    state.current_shock_start = current_shock_start

    return SimulationResult(
        daily_data=daily_data,
        events=events,
        summary=summary,
    )


def _compute_volatility(daily_data: List[DailySnapshot]) -> float:
    """Compute coefficient of variation of daily balances."""
    if len(daily_data) < 2:
        return 0.0
    balances = [s.balance for s in daily_data]
    mean = sum(balances) / len(balances)
    if mean == 0:
        return 1.0
    variance = sum((b - mean) ** 2 for b in balances) / len(balances)
    std = variance ** 0.5
    return abs(std / mean)
