"""Multi-currency exchange rate engine with seeded daily fluctuations."""

from __future__ import annotations
import random as _random_module
from typing import Dict

# Base rates relative to USD (approximate real-world values)
BASE_RATES: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "PKR": 278.50,
    "JPY": 149.80,
}

# Daily volatility per currency pair (standard deviation as fraction of rate)
VOLATILITY: Dict[str, float] = {
    "USD": 0.0,
    "EUR": 0.002,
    "GBP": 0.0025,
    "PKR": 0.004,
    "JPY": 0.003,
}

SUPPORTED_CURRENCIES = list(BASE_RATES.keys())


class CurrencyEngine:
    """Generates deterministic daily exchange rate tables from a seeded RNG."""

    def __init__(self, rng: _random_module.Random):
        self.rng = rng
        # Current rates (USD-relative): how many units of X per 1 USD
        self.rates: Dict[str, float] = dict(BASE_RATES)
        self._rate_history: Dict[int, Dict[str, float]] = {}

    def advance_day(self, day: int) -> Dict[str, float]:
        """Generate exchange rates for a new day. Returns rates dict."""
        for currency in SUPPORTED_CURRENCIES:
            if currency == "USD":
                continue
            vol = VOLATILITY[currency]
            # Seeded Gaussian fluctuation
            change = self.rng.gauss(0, vol)
            self.rates[currency] = round(self.rates[currency] * (1 + change), 6)
            # Clamp to positive
            if self.rates[currency] < 0.0001:
                self.rates[currency] = 0.0001
        self._rate_history[day] = dict(self.rates)
        return dict(self.rates)

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount from one currency to another at current day's rate."""
        if from_currency == to_currency:
            return round(amount, 6)
        # Convert from_currency -> USD -> to_currency
        # rates[X] = how many X per 1 USD
        usd_amount = amount / self.rates[from_currency]
        result = usd_amount * self.rates[to_currency]
        return round(result, 6)

    def get_rate(self, from_currency: str, to_currency: str) -> float:
        """Get current exchange rate from one currency to another."""
        if from_currency == to_currency:
            return 1.0
        usd_from = 1.0 / self.rates[from_currency]
        return round(usd_from * self.rates[to_currency], 6)

    def get_rates_snapshot(self) -> Dict[str, float]:
        return dict(self.rates)
