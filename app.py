"""Flask server for Future Wallet financial simulation engine."""

from flask import Flask, render_template, request, jsonify

from engine.models import (
    UserState, IncomeStream, Expense, Debt, Asset,
    SimulationResult, DailySnapshot, SimulationEvent,
)
from engine.simulator import run_simulation
from engine.branching import snapshot, branch, compare

app = Flask(__name__)


def _parse_user_state(data: dict) -> UserState:
    """Parse JSON input into a UserState object."""
    income_streams = [
        IncomeStream(
            name=i.get("name", "Income"),
            amount=float(i.get("amount", 0)),
            currency=i.get("currency", "USD"),
            frequency=i.get("frequency", "monthly"),
            start_day=int(i.get("start_day", 0)),
            end_day=int(i["end_day"]) if i.get("end_day") else None,
        )
        for i in data.get("income_streams", [])
    ]

    expenses = [
        Expense(
            name=e.get("name", "Expense"),
            amount=float(e.get("amount", 0)),
            currency=e.get("currency", "USD"),
            frequency=e.get("frequency", "monthly"),
            category=e.get("category", "general"),
            start_day=int(e.get("start_day", 0)),
            end_day=int(e["end_day"]) if e.get("end_day") else None,
        )
        for e in data.get("expenses", [])
    ]

    debts = [
        Debt(
            name=d.get("name", "Debt"),
            principal=float(d.get("principal", 0)),
            interest_rate=float(d.get("interest_rate", 0)),
            min_payment=float(d.get("min_payment", 0)),
            currency=d.get("currency", "USD"),
            start_day=int(d.get("start_day", 0)),
        )
        for d in data.get("debts", [])
    ]

    assets = [
        Asset(
            name=a.get("name", "Asset"),
            value=float(a.get("value", 0)),
            currency=a.get("currency", "USD"),
            asset_type=a.get("asset_type", "liquid"),
            volatility=float(a.get("volatility", 0)),
            yield_rate=float(a.get("yield_rate", 0)),
            lock_period_days=int(a.get("lock_period_days", 0)),
            sale_penalty_pct=float(a.get("sale_penalty_pct", 0)),
        )
        for a in data.get("assets", [])
    ]

    return UserState(
        balance=float(data.get("balance", 5000)),
        currency=data.get("currency", "USD"),
        income_streams=income_streams,
        expenses=expenses,
        debts=debts,
        assets=assets,
        credit_score=float(data.get("credit_score", 650)),
        seed=int(data.get("seed", 42)),
        horizon_days=int(data.get("horizon_days", 365)),
    )


def _result_to_json(result: SimulationResult) -> dict:
    """Convert simulation result to JSON-serializable dict."""
    return {
        "daily_data": [
            {
                "day": s.day,
                "balance": s.balance,
                "net_worth": s.net_worth,
                "credit_score": s.credit_score,
                "nav": s.nav,
                "liquidity_ratio": s.liquidity_ratio,
                "total_debt": s.total_debt,
                "total_assets": s.total_assets,
            }
            for s in result.daily_data
        ],
        "events": [
            {
                "day": e.day,
                "event_type": e.event_type,
                "description": e.description,
                "amount": e.amount,
                "severity": e.severity,
            }
            for e in result.events
        ],
        "summary": result.summary,
    }


# Store last simulation state for branching
_last_state = None
_last_result = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/simulate", methods=["POST"])
def simulate():
    global _last_state, _last_result
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    state = _parse_user_state(data)
    _last_state = snapshot(state)  # save for branching
    result = run_simulation(state)
    _last_result = result

    return jsonify(_result_to_json(result))


@app.route("/api/branch", methods=["POST"])
def branch_simulation():
    global _last_state, _last_result
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    if _last_state is None:
        return jsonify({"error": "No simulation has been run yet. Run a simulation first."}), 400

    branch_day = int(data.get("branch_day", 0))
    modifications = data.get("modifications", {})

    # Re-run original simulation up to branch_day to get exact state
    original_state = snapshot(_last_state)
    original_state.horizon_days = branch_day
    original_partial = run_simulation(original_state)

    # Now original_state has been mutated to the state at branch_day
    # Create the branched state
    remaining_days = _last_state.horizon_days - branch_day
    original_state.horizon_days = remaining_days

    branched_state = branch(original_state, modifications)
    branched_state.horizon_days = remaining_days

    # Run both from branch point
    original_continuation_state = snapshot(original_state)
    # Use different seed section for continuation to avoid correlation
    original_result = run_simulation(original_continuation_state, start_day=branch_day)

    branched_result = run_simulation(branched_state, start_day=branch_day)

    comparison = compare(original_result, branched_result)
    comparison["branch_day"] = branch_day

    return jsonify(comparison)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
