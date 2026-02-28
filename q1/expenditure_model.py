"""
expenditure_model.py — M3 Challenge 2026 Q1

Estimates essential (non-discretionary) annual expenses for an individual
given their salary, age, and state.

Mathematical Model
------------------
We use BLS Consumer Expenditure Survey 2024 data as baseline expenditures for
each age group and geographic region. These are then scaled to the individual's
specific income using an Engel curve power-law (constant elasticity) model,
which is a tractable approximation of the QUAIDS (Quadratic Almost Ideal Demand
System) framework of Banks, Blundell & Lewbel (1997).

Scaling formula (per category i):
    E_scaled_i = E_BLS_i(age_group, region) × (Salary / AvgIncome_AgeGroup)^beta_i

where:
    E_BLS_i    = BLS mean annual expenditure for category i (age × region)
    beta_i     = income elasticity (Banks et al. 1997; see constants.py)
    AvgIncome  = BLS CPS 2024 median annual earnings for the age group

Essential expenditure for category i:
    E_essential_i = E_scaled_i × alpha_i

where alpha_i = essential fraction (fraction of spending that is non-discretionary).

Total essential expenses = Σ E_essential_i

OECD Equivalence Scale Note
----------------------------
BLS CES data is household-level. For individuals aged < 30 (typically single-
person households), this is an appropriate approximation. For ages 30-55,
a multi-person household would overstate individual expenses. The model
treats salary as the individual's contribution and household expenses as
shared; a first-order correction would divide by household size.
In this implementation, we assume single-person household or sole earner
as documented in the assumption list. Sensitivity is noted in the notebook.

References
----------
Banks, J., Blundell, R., & Lewbel, A. (1997). Quadratic Engel Curves and
    Consumer Demand. Review of Economics and Statistics, 79(4), 527-539.
BLS Consumer Expenditure Survey (2024). bls.gov/cex
BLS CPS Earnings Tables (2024). bls.gov/cps/earnings.htm
OECD (2024). Household Disposable Income. oecd.org
"""

import math
from constants import (
    ESSENTIAL_FRACTIONS,
    INCOME_ELASTICITY,
    AVG_INCOME_BY_AGE,   # kept for documentation; computation uses BLS CES income
    STATE_TO_REGION,
)


# ---------------------------------------------------------------------------
# Age group mapping
# ---------------------------------------------------------------------------

_AGE_BREAKS = [
    (0,  24,  'Under 25'),
    (25, 34,  '25-34'),
    (35, 44,  '35-44'),
    (45, 54,  '45-54'),
    (55, 64,  '55-64'),
    (65, 74,  '65-74'),
    (75, 999, '75 and older'),
]


def get_age_group(age: int) -> str:
    """
    Map a numeric age to the BLS CES age-group label.

    Parameters
    ----------
    age : int
        Age in years.

    Returns
    -------
    str
        Age group label matching BLS CES data (e.g., '25-34').
    """
    for lo, hi, label in _AGE_BREAKS:
        if lo <= age <= hi:
            return label
    raise ValueError(f"Age {age} is out of expected range (0–999)")


def get_region_for_state(state: str) -> str:
    """
    Return the BLS geographic region for a given state.

    Parameters
    ----------
    state : str
        Full state name (e.g., 'California').

    Returns
    -------
    str
        BLS region label: 'Northeast', 'Midwest', 'South', or 'West'.
    """
    if state not in STATE_TO_REGION:
        raise ValueError(
            f"State '{state}' not found in STATE_TO_REGION. "
            f"Check constants.py for supported states."
        )
    return STATE_TO_REGION[state]


# ---------------------------------------------------------------------------
# Engel curve scaling
# ---------------------------------------------------------------------------

def _scale_expenditure(
    bls_amount: float,
    salary: float,
    avg_income: float,
    beta: float,
) -> float:
    """
    Scale a BLS expenditure amount to an individual's salary using power law.

    E_scaled = E_BLS × (salary / avg_income)^beta

    This is a constant-elasticity (log-linear) approximation of the QUAIDS
    model. It is exact at salary = avg_income and valid within ±50% of mean.
    For large deviations, the quadratic QUAIDS term becomes significant
    (documented as a model limitation).

    Parameters
    ----------
    bls_amount : float
        BLS mean annual expenditure for this category (USD).
    salary : float
        Individual's gross annual income (USD).
    avg_income : float
        Average income for the individual's age group (USD).
    beta : float
        Income elasticity for this category.

    Returns
    -------
    float
        Income-scaled expenditure estimate (USD).
    """
    if avg_income <= 0 or salary <= 0:
        return bls_amount
    ratio = salary / avg_income
    return bls_amount * (ratio ** beta)


# ---------------------------------------------------------------------------
# Main expenditure computation
# ---------------------------------------------------------------------------

def compute_essential_expenses(
    salary: float,
    age: int,
    state: str,
    exp_data: dict,
    use_region_blend: bool = True,
) -> dict:
    """
    Estimate annual essential (non-discretionary) expenses.

    The function uses a blend of age-group and regional data to capture both
    demographic and geographic variation in spending patterns:
        E_base = 0.6 × E_BLS(age_group) + 0.4 × E_BLS(region)

    This blend weights age group more heavily since age captures lifecycle
    expenditure patterns most directly (Engel's Law), while region captures
    local cost-of-living differences (e.g., housing markets).

    Parameters
    ----------
    salary : float
        Annual gross income in USD.
    age : int
        Age in years.
    state : str
        Full state name (e.g., 'California').
    exp_data : dict
        Parsed from data_loader.load_expenditure_data().
    use_region_blend : bool
        If True, blend age-group + regional data (recommended).
        If False, use age-group data only.

    Returns
    -------
    dict with keys:
        'total_essential'         : float — total essential expenses (USD)
        'total_all'               : float — total expenses (essential + discret.)
        'by_category'             : dict  — per-category breakdown
        'age_group'               : str
        'region'                  : str
        'avg_income_for_age_group': float
        'income_ratio'            : float  (salary / avg_income)
    """
    age_group = get_age_group(age)
    region = get_region_for_state(state)

    # Use BLS CES mean household income for this age group as the Engel
    # scaling reference point. This is internally consistent: the BLS CES
    # expenditure data is calibrated to this same survey's income measure.
    # BLS CPS individual earnings (AVG_INCOME_BY_AGE) are preserved in
    # constants.py for documentation; the CES household income is used here
    # because it represents the actual income at which BLS CES expenditures
    # were observed.
    avg_income = exp_data['mean_income_by_age'].get(age_group, AVG_INCOME_BY_AGE[age_group])

    age_data = exp_data['by_age'][age_group]
    region_data = exp_data['by_region'][region]

    # Blend weights
    w_age = 0.6 if use_region_blend else 1.0
    w_reg = 0.4 if use_region_blend else 0.0

    categories = exp_data['categories']
    by_category = {}
    total_essential = 0.0
    total_all = 0.0

    for cat in categories:
        age_bls = age_data.get(cat, 0.0)
        reg_bls = region_data.get(cat, 0.0)

        # Blended BLS baseline
        bls_base = w_age * age_bls + w_reg * reg_bls

        # Engel curve scaling
        beta = INCOME_ELASTICITY.get(cat, 1.0)
        scaled = _scale_expenditure(bls_base, salary, avg_income, beta)

        # Essential fraction
        alpha = ESSENTIAL_FRACTIONS.get(cat, 0.0)
        essential = scaled * alpha

        by_category[cat] = {
            'bls_age':   age_bls,
            'bls_region': reg_bls,
            'bls_blended': bls_base,
            'scaled':    scaled,
            'alpha':     alpha,
            'beta':      beta,
            'essential': essential,
        }

        total_essential += essential
        total_all += scaled

    return {
        'total_essential': round(total_essential, 2),
        'total_all': round(total_all, 2),
        'by_category': by_category,
        'age_group': age_group,
        'region': region,
        'avg_income_for_age_group': avg_income,
        'income_ratio': salary / avg_income if avg_income > 0 else 1.0,
    }


def get_essential_breakdown(exp_result: dict) -> dict:
    """
    Return just the essential amounts by category (convenience function).

    Parameters
    ----------
    exp_result : dict
        Output of compute_essential_expenses().

    Returns
    -------
    dict mapping category name → essential USD amount.
    """
    return {
        cat: info['essential']
        for cat, info in exp_result['by_category'].items()
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_expenditure_module(exp_data: dict) -> None:
    """Quick sanity checks on the expenditure model."""
    print("=" * 60)
    print("Expenditure Module Validation")
    print("=" * 60)

    # Age group mapping
    assert get_age_group(23) == 'Under 25'
    assert get_age_group(25) == '25-34'
    assert get_age_group(35) == '35-44'
    assert get_age_group(75) == '75 and older'
    print("Age group mapping: OK ✓")

    # Region mapping
    assert get_region_for_state('California') == 'West'
    assert get_region_for_state('Texas') == 'South'
    assert get_region_for_state('New York') == 'Northeast'
    assert get_region_for_state('Illinois') == 'Midwest'
    print("Region mapping: OK ✓")

    # Engel scaling: at avg income, scaled = bls_amount
    bls_amt = 9_630.0  # Food, 25-34
    avg_inc = AVG_INCOME_BY_AGE['25-34']
    scaled = _scale_expenditure(bls_amt, avg_inc, avg_inc, 0.55)
    assert abs(scaled - bls_amt) < 0.01, f"Scaling at mean income != BLS: {scaled}"
    print("Engel scaling at mean income: OK ✓")

    # Higher income → higher expenses (elastic categories)
    scaled_hi = _scale_expenditure(bls_amt, avg_inc * 2, avg_inc, 0.55)
    assert scaled_hi > bls_amt
    print(f"  Food at 2× income (beta=0.55): ${scaled_hi:,.0f} vs BLS ${bls_amt:,.0f} ✓")

    # Compute for a profile at avg income → essential ≈ reasonable fraction
    result = compute_essential_expenses(avg_inc, 30, 'California', exp_data)
    ess_frac = result['total_essential'] / avg_inc
    print(f"\nProfile: age=30, salary=$62k, CA")
    print(f"  Total essential: ${result['total_essential']:,.0f}")
    print(f"  Total all:       ${result['total_all']:,.0f}")
    print(f"  Essential / salary: {ess_frac:.1%}  [expected: 40-70%]")
    assert 0.30 < ess_frac < 0.90, f"Essential fraction {ess_frac:.2%} outside 30-90%"

    print("\nExpenditure module validation PASSED ✓")
