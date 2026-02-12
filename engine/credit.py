"""Credit score model: debt ratio + payment punctuality + restructuring events."""

from __future__ import annotations

SCORE_MIN = 300
SCORE_MAX = 850
MAX_DAILY_CHANGE = 2.0

# Factor weights
WEIGHT_DEBT_RATIO = 0.40
WEIGHT_PUNCTUALITY = 0.35
WEIGHT_RESTRUCTURING = 0.25


def compute_credit_delta(
    credit_score: float,
    total_debt: float,
    total_income: float,
    missed_payments: int,
    total_payments_due: int,
    liquidation_events_today: int,
) -> float:
    """Compute the daily credit score change.

    Returns a delta clamped to [-MAX_DAILY_CHANGE, +MAX_DAILY_CHANGE].
    """
    # --- Debt-to-income ratio factor ---
    if total_income > 0:
        dti = total_debt / total_income
    else:
        dti = 1.0 if total_debt > 0 else 0.0
    # Lower DTI is better; target ideal DTI < 0.3
    if dti <= 0.3:
        dti_score = 1.0
    elif dti <= 0.5:
        dti_score = 0.5
    elif dti <= 0.8:
        dti_score = 0.0
    else:
        dti_score = -1.0

    # --- Payment punctuality factor ---
    if total_payments_due > 0:
        punctuality = 1.0 - (missed_payments / total_payments_due)
    else:
        punctuality = 1.0  # no debts = perfect
    punct_score = (punctuality - 0.5) * 2  # map [0,1] -> [-1,1]

    # --- Restructuring / liquidation factor ---
    if liquidation_events_today > 0:
        restruct_score = -1.0
    else:
        restruct_score = 0.2  # slight positive for stability

    # Weighted sum
    raw_delta = (
        WEIGHT_DEBT_RATIO * dti_score
        + WEIGHT_PUNCTUALITY * punct_score
        + WEIGHT_RESTRUCTURING * restruct_score
    )

    # Scale: raw_delta is in [-1, 1], map to [-MAX_DAILY_CHANGE, MAX_DAILY_CHANGE]
    delta = raw_delta * MAX_DAILY_CHANGE
    delta = max(-MAX_DAILY_CHANGE, min(MAX_DAILY_CHANGE, delta))
    return delta


def update_credit_score(
    credit_score: float,
    total_debt: float,
    total_income: float,
    missed_payments: int,
    total_payments_due: int,
    liquidation_events_today: int,
) -> float:
    """Return the new credit score after daily update."""
    delta = compute_credit_delta(
        credit_score, total_debt, total_income,
        missed_payments, total_payments_due, liquidation_events_today
    )
    new_score = credit_score + delta
    return max(SCORE_MIN, min(SCORE_MAX, round(new_score, 2)))
