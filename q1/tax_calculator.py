"""
tax_calculator.py — M3 Challenge 2026 Q1

Computes federal income tax, FICA payroll taxes, and state income tax for a
single filer with wages (salary) as sole income source.

References
----------
IRS Rev. Proc. 2024-61          : 2025 federal brackets, standard deduction $15,000
SSA 2025 Announcement            : Social Security wage base $176,100
Tax Foundation 2025 State Data   : State effective rate schedules
"""

import math
from constants import (
    STANDARD_DEDUCTION_SINGLE,
    FEDERAL_BRACKETS_SINGLE_2025,
    SS_RATE, SS_WAGE_BASE,
    MEDICARE_RATE, MEDICARE_SURCHARGE_RATE, MEDICARE_SURCHARGE_THRESHOLD,
    STATE_TAX_SCHEDULE,
)


# ---------------------------------------------------------------------------
# Federal Income Tax
# ---------------------------------------------------------------------------

def compute_federal_tax(gross_income: float) -> float:
    """
    Compute 2025 federal income tax for a single filer using standard deduction.

    Taxable income = max(0, gross_income - standard_deduction)
    Progressive brackets applied incrementally.

    Parameters
    ----------
    gross_income : float
        Annual gross salary in USD.

    Returns
    -------
    float
        Federal income tax owed in USD.

    Validation
    ----------
    $60,000 gross → taxable = $45,000
      10% on $11,925 = $1,192.50
      12% on $33,075 = $3,969.00
      Total = $5,161.50
    (IRS example: ~$5,162)
    """
    taxable = max(0.0, gross_income - STANDARD_DEDUCTION_SINGLE)

    tax = 0.0
    prev_limit = 0.0
    for upper, rate in FEDERAL_BRACKETS_SINGLE_2025:
        if upper is None:
            # Top bracket — no ceiling
            bracket_income = max(0.0, taxable - prev_limit)
        else:
            bracket_income = max(0.0, min(taxable, upper) - prev_limit)

        tax += bracket_income * rate

        if upper is not None and taxable <= upper:
            break
        if upper is not None:
            prev_limit = upper

    return round(tax, 2)


def compute_effective_federal_rate(gross_income: float) -> float:
    """Return federal income tax as a fraction of gross income."""
    if gross_income <= 0:
        return 0.0
    return compute_federal_tax(gross_income) / gross_income


# ---------------------------------------------------------------------------
# FICA Payroll Taxes
# ---------------------------------------------------------------------------

def compute_fica(gross_income: float) -> dict:
    """
    Compute Social Security and Medicare payroll taxes (employee share).

    Parameters
    ----------
    gross_income : float
        Annual gross salary in USD.

    Returns
    -------
    dict with keys:
        'social_security'  : float — SS tax owed
        'medicare'         : float — Medicare tax owed (base + surcharge)
        'total'            : float — sum of both
    """
    # Social Security: 6.2% on first $176,100
    ss_taxable = min(gross_income, SS_WAGE_BASE)
    social_security = round(ss_taxable * SS_RATE, 2)

    # Medicare: 1.45% on all wages
    medicare_base = round(gross_income * MEDICARE_RATE, 2)
    # Additional 0.9% surcharge on wages above $200,000 (single filer)
    medicare_surcharge = 0.0
    if gross_income > MEDICARE_SURCHARGE_THRESHOLD:
        medicare_surcharge = round(
            (gross_income - MEDICARE_SURCHARGE_THRESHOLD) * MEDICARE_SURCHARGE_RATE, 2
        )

    medicare_total = round(medicare_base + medicare_surcharge, 2)

    return {
        'social_security': social_security,
        'medicare': medicare_total,
        'medicare_base': medicare_base,
        'medicare_surcharge': medicare_surcharge,
        'total': round(social_security + medicare_total, 2),
    }


# ---------------------------------------------------------------------------
# State Income Tax
# ---------------------------------------------------------------------------

def _interpolate_rate(schedule: list, income: float) -> float:
    """
    Look up effective state tax rate for given income using linear interpolation
    between breakpoints in the schedule.

    schedule: [(income_threshold, effective_rate), ...] sorted ascending
    """
    if len(schedule) == 1:
        return schedule[0][1]

    # Find surrounding breakpoints
    for i in range(len(schedule) - 1):
        lo_inc, lo_rate = schedule[i]
        hi_inc, hi_rate = schedule[i + 1]
        if lo_inc <= income <= hi_inc:
            if hi_inc == lo_inc:
                return lo_rate
            frac = (income - lo_inc) / (hi_inc - lo_inc)
            return lo_rate + frac * (hi_rate - lo_rate)

    # Beyond last breakpoint: use last rate
    return schedule[-1][1]


def compute_state_tax(gross_income: float, state: str) -> float:
    """
    Compute 2025 state income tax for a single filer.

    Uses effective rate schedules from Tax Foundation 2025. Rates are
    approximations valid for the salary range $20,000–$500,000. For states
    with no income tax (TX, FL, NV, WA, WY, TN), returns 0.

    Parameters
    ----------
    gross_income : float
        Annual gross salary in USD.
    state : str
        Full state name (e.g., 'California', 'Texas').

    Returns
    -------
    float
        State income tax owed in USD.

    Raises
    ------
    ValueError
        If state is not found in the schedule table.
    """
    if state not in STATE_TAX_SCHEDULE:
        raise ValueError(
            f"State '{state}' not in STATE_TAX_SCHEDULE. "
            f"Available states: {sorted(STATE_TAX_SCHEDULE.keys())}"
        )

    schedule = STATE_TAX_SCHEDULE[state]
    effective_rate = _interpolate_rate(schedule, gross_income)
    return round(gross_income * effective_rate, 2)


def compute_all_taxes(gross_income: float, state: str) -> dict:
    """
    Compute all taxes for a given gross income and state.

    Returns
    -------
    dict with keys:
        'federal'          : float
        'fica'             : dict  (from compute_fica)
        'state'            : float
        'total'            : float
        'effective_total_rate': float  (total tax / gross)
    """
    federal = compute_federal_tax(gross_income)
    fica = compute_fica(gross_income)
    state_tax = compute_state_tax(gross_income, state)
    total = round(federal + fica['total'] + state_tax, 2)

    return {
        'federal': federal,
        'fica': fica,
        'state': state_tax,
        'total': total,
        'effective_total_rate': total / gross_income if gross_income > 0 else 0.0,
        'effective_federal_rate': federal / gross_income if gross_income > 0 else 0.0,
        'effective_state_rate': state_tax / gross_income if gross_income > 0 else 0.0,
    }


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_tax_module() -> None:
    """
    Run known-answer tests to validate the tax module.

    Test cases from IRS 2025 estimator and Tax Foundation state data.
    """
    print("=" * 60)
    print("Tax Module Validation")
    print("=" * 60)

    # --- Federal: $60,000 salary ---
    # Taxable = 60,000 - 15,000 = 45,000
    # 10% on 11,925 = 1,192.50
    # 12% on (45,000 - 11,925) = 12% on 33,075 = 3,969.00
    # Total = 5,161.50
    federal_60k = compute_federal_tax(60_000)
    print(f"\nFederal tax on $60,000:")
    print(f"  Computed: ${federal_60k:,.2f}")
    print(f"  Expected: ~$5,161.50  [IRS 2025 brackets]")
    assert abs(federal_60k - 5161.50) < 5, f"Federal tax mismatch: {federal_60k}"

    # --- Federal: $100,000 salary ---
    # Taxable = 85,000
    # 10%: 1,192.50; 12%: (48,475-11,925)*0.12=4,386; 22%: (85,000-48,475)*0.22=8,035.50
    # Total = 1,192.50 + 4,386 + 8,035.50 = 13,614
    federal_100k = compute_federal_tax(100_000)
    print(f"\nFederal tax on $100,000:")
    print(f"  Computed: ${federal_100k:,.2f}")
    print(f"  Expected: ~$13,614  [IRS 2025 brackets]")
    assert abs(federal_100k - 13_614) < 50, f"Federal tax mismatch: {federal_100k}"

    # --- FICA: $60,000 ---
    fica_60k = compute_fica(60_000)
    expected_ss = 60_000 * 0.062       # 3,720
    expected_med = 60_000 * 0.0145    # 870
    print(f"\nFICA on $60,000:")
    print(f"  SS computed:  ${fica_60k['social_security']:,.2f}  expected: ${expected_ss:,.2f}")
    print(f"  Medicare:     ${fica_60k['medicare']:,.2f}  expected: ${expected_med:,.2f}")
    assert abs(fica_60k['social_security'] - expected_ss) < 1
    assert abs(fica_60k['medicare'] - expected_med) < 1

    # --- FICA surcharge: $250,000 ---
    fica_250k = compute_fica(250_000)
    expected_ss_250k = SS_WAGE_BASE * SS_RATE   # 10,918.20
    expected_med_250k = 250_000 * 0.0145 + (250_000 - 200_000) * 0.009
    print(f"\nFICA on $250,000:")
    print(f"  SS: ${fica_250k['social_security']:,.2f}  expected: ${expected_ss_250k:,.2f}")
    print(f"  Medicare+surcharge: ${fica_250k['medicare']:,.2f}  expected: ${expected_med_250k:,.2f}")
    assert abs(fica_250k['social_security'] - expected_ss_250k) < 1
    assert abs(fica_250k['medicare'] - expected_med_250k) < 1

    # --- State tax: Texas = 0 ---
    tx_tax = compute_state_tax(100_000, 'Texas')
    print(f"\nState tax (Texas, $100k): ${tx_tax:,.2f}  expected: $0.00")
    assert tx_tax == 0.0

    # --- State tax: California ~$65k ---
    ca_tax = compute_state_tax(65_000, 'California')
    ca_rate = ca_tax / 65_000
    print(f"State tax (California, $65k): ${ca_tax:,.2f}  effective rate: {ca_rate:.1%}")
    print(f"  Expected effective rate: ~6.8%-7.5% (Tax Foundation 2025)")
    assert 0.06 < ca_rate < 0.08, f"CA rate {ca_rate:.3f} outside 6-8% range"

    print("\nAll tax module validations PASSED ✓")


if __name__ == '__main__':
    validate_tax_module()

    # Print effective rate table for all states at $65k
    print("\n\nEffective total tax rates at $65,000 by state:")
    print(f"{'State':<20} {'Federal':>10} {'FICA':>8} {'State':>8} {'Total':>8}")
    print("-" * 58)
    for state in sorted(STATE_TAX_SCHEDULE.keys()):
        result = compute_all_taxes(65_000, state)
        print(f"{state:<20} "
              f"{result['effective_federal_rate']:>9.1%} "
              f"{result['fica']['total']/65000:>7.1%} "
              f"{result['effective_state_rate']:>7.1%} "
              f"{result['effective_total_rate']:>7.1%}")
