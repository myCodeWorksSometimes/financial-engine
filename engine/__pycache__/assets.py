"""Asset valuation, liquidation logic, and liquidity management."""

from __future__ import annotations
import random as _random_module
from typing import List, Tuple

from .models import Asset, SimulationEvent

# Liquidation priority order (most liquid first)
LIQUIDATION_ORDER = ["liquid", "yield-generating", "volatile", "illiquid"]


def update_asset_values(assets: List[Asset], rng: _random_module.Random, day: int) -> None:
    """Update asset values based on volatility and yield parameters.

    Modifies assets in place.
    """
    for asset in assets:
        if asset.value <= 0:
            continue

        # Apply daily yield (annual yield / 365)
        if asset.yield_rate > 0:
            daily_yield = asset.yield_rate / 365.0
            asset.value = round(asset.value * (1 + daily_yield), 6)

        # Apply volatility-driven price movement
        if asset.volatility > 0:
            # Daily volatility is annual vol / sqrt(365) approximated
            daily_vol = asset.volatility / 19.1  # ~sqrt(365)
            change = rng.gauss(0, daily_vol)
            asset.value = round(asset.value * (1 + change), 6)
            if asset.value < 0:
                asset.value = 0.0


def get_total_asset_value(assets: List[Asset]) -> float:
    """Return total value of all assets."""
    return round(sum(a.value for a in assets), 6)


def get_liquid_asset_value(assets: List[Asset], current_day: int) -> float:
    """Return total value of assets that can be immediately sold."""
    total = 0.0
    for a in assets:
        if a.value <= 0:
            continue
        if a.lock_period_days > 0 and (current_day - a.purchase_day) < a.lock_period_days:
            continue
        if a.asset_type in ("liquid", "yield-generating", "volatile"):
            total += a.value
    return round(total, 6)


def get_liquidity_ratio(assets: List[Asset], current_day: int) -> float:
    """Return ratio of liquid assets to total assets."""
    total = get_total_asset_value(assets)
    if total <= 0:
        return 1.0
    liquid = get_liquid_asset_value(assets, current_day)
    return round(liquid / total, 6)


def liquidate_to_cover(
    assets: List[Asset],
    deficit: float,
    current_day: int,
) -> Tuple[float, List[SimulationEvent]]:
    """Sell assets to cover a deficit. Returns (amount_recovered, events).

    Sells in priority order: liquid -> yield-generating -> volatile -> illiquid.
    Respects lock periods and applies sale penalties.
    """
    events: List[SimulationEvent] = []
    recovered = 0.0
    remaining = deficit

    for asset_type in LIQUIDATION_ORDER:
        if remaining <= 0:
            break
        for asset in assets:
            if remaining <= 0:
                break
            if asset.asset_type != asset_type or asset.value <= 0:
                continue
            # Check lock period
            if asset.lock_period_days > 0:
                if (current_day - asset.purchase_day) < asset.lock_period_days:
                    continue

            # Calculate how much we can get from this asset
            sellable_value = asset.value * (1 - asset.sale_penalty_pct)

            if sellable_value <= remaining:
                # Sell entire asset
                actual_sale = sellable_value
                realized_gain = asset.value - asset.cost_basis
                events.append(SimulationEvent(
                    day=current_day,
                    event_type="liquidation",
                    description=f"Sold entire {asset.name} ({asset.asset_type}) for {actual_sale:.2f} (penalty: {asset.sale_penalty_pct*100:.0f}%)",
                    amount=actual_sale,
                    severity="warning",
                ))
                asset.value = 0.0
            else:
                # Partial sale
                fraction_needed = remaining / sellable_value
                actual_sale = remaining
                partial_value = asset.value * fraction_needed
                realized_gain = partial_value - (asset.cost_basis * fraction_needed)
                asset.value = round(asset.value - partial_value, 6)
                asset.cost_basis = round(asset.cost_basis * (1 - fraction_needed), 6)
                events.append(SimulationEvent(
                    day=current_day,
                    event_type="liquidation",
                    description=f"Partially sold {asset.name} ({asset.asset_type}) for {actual_sale:.2f}",
                    amount=actual_sale,
                    severity="warning",
                ))

            recovered += actual_sale
            remaining -= actual_sale

    return round(recovered, 6), events
