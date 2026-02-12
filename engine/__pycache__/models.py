"""Data models for the Future Wallet simulation engine."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class IncomeStream:
    name: str
    amount: float
    currency: str = "USD"
    frequency: str = "monthly"  # daily, weekly, monthly
    start_day: int = 0
    end_day: Optional[int] = None


@dataclass
class Expense:
    name: str
    amount: float
    currency: str = "USD"
    frequency: str = "monthly"
    category: str = "general"
    start_day: int = 0
    end_day: Optional[int] = None


@dataclass
class Debt:
    name: str
    principal: float
    interest_rate: float  # annual rate, e.g. 0.05 for 5%
    min_payment: float
    currency: str = "USD"
    start_day: int = 0
    paid_off: bool = False
    missed_payments: int = 0
    total_payments_made: int = 0
    total_payments_due: int = 0


@dataclass
class Asset:
    name: str
    value: float
    currency: str = "USD"
    asset_type: str = "liquid"  # liquid, illiquid, yield-generating, volatile
    volatility: float = 0.0  # 0-1
    yield_rate: float = 0.0  # annual
    lock_period_days: int = 0
    sale_penalty_pct: float = 0.0  # 0-1
    purchase_day: int = 0
    cost_basis: float = 0.0  # original purchase price for tax purposes

    def __post_init__(self):
        if self.cost_basis == 0.0:
            self.cost_basis = self.value


@dataclass
class DailySnapshot:
    day: int
    balance: float
    net_worth: float
    credit_score: float
    nav: float  # net asset value
    liquidity_ratio: float
    total_debt: float = 0.0
    total_assets: float = 0.0


@dataclass
class SimulationEvent:
    day: int
    event_type: str  # liquidation, deficit, debt_payoff, tax, income, expense, shock
    description: str
    amount: float = 0.0
    severity: str = "info"  # info, warning, danger, success


@dataclass
class UserState:
    balance: float
    currency: str = "USD"
    income_streams: List[IncomeStream] = field(default_factory=list)
    expenses: List[Expense] = field(default_factory=list)
    debts: List[Debt] = field(default_factory=list)
    assets: List[Asset] = field(default_factory=list)
    credit_score: float = 650.0
    seed: int = 42
    horizon_days: int = 365
    # Internal tracking
    realized_gains: float = 0.0
    unrealized_gains: float = 0.0
    taxes_paid: float = 0.0
    total_income_received: float = 0.0
    total_expenses_paid: float = 0.0
    # Rolling metrics
    deficit_days: int = 0
    shock_events: List[int] = field(default_factory=list)  # days when shocks occurred
    recovery_days: List[int] = field(default_factory=list)  # days to recover from each shock
    current_shock_start: Optional[int] = None


@dataclass
class SimulationResult:
    daily_data: List[DailySnapshot] = field(default_factory=list)
    events: List[SimulationEvent] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
