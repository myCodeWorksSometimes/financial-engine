"""Progressive tax bracket system for realized gains."""

from __future__ import annotations
from typing import List, Tuple

# US-style progressive brackets (annual income thresholds, rate)
DEFAULT_BRACKETS: List[Tuple[float, float]] = [
    (10_000, 0.10),
    (40_000, 0.12),
    (85_000, 0.22),
    (165_000, 0.24),
    (float("inf"), 0.32),
]


def calculate_tax(realized_gains: float, brackets: List[Tuple[float, float]] = None) -> float:
    """Calculate progressive tax on realized gains.

    Args:
        realized_gains: Total realized gains to be taxed.
        brackets: List of (upper_bound, rate) tuples. Defaults to US-style.

    Returns:
        Total tax amount owed.
    """
    if brackets is None:
        brackets = DEFAULT_BRACKETS

    if realized_gains <= 0:
        return 0.0

    tax = 0.0
    prev_bound = 0.0

    for upper_bound, rate in brackets:
        if realized_gains <= prev_bound:
            break
        taxable_in_bracket = min(realized_gains, upper_bound) - prev_bound
        if taxable_in_bracket > 0:
            tax += taxable_in_bracket * rate
        prev_bound = upper_bound

    return round(tax, 6)


def calculate_marginal_tax(amount: float, existing_gains: float,
                           brackets: List[Tuple[float, float]] = None) -> float:
    """Calculate tax on an additional amount given existing realized gains."""
    if brackets is None:
        brackets = DEFAULT_BRACKETS
    total_tax = calculate_tax(existing_gains + amount, brackets)
    existing_tax = calculate_tax(existing_gains, brackets)
    return round(total_tax - existing_tax, 6)
