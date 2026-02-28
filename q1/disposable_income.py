"""
disposable_income.py — M3 Challenge 2026 Q1

Master function: compute_disposable_income()

Mathematical Model
------------------
Official definition (Bureau of Economic Analysis, bea.gov):
    Disposable Income = Personal Income − Personal Current Taxes

Extended definition (this model — accounts for non-discretionary expenses):
    DI = Salary − T_federal − T_fica − T_state − E_essential

where:
    T_federal  = federal income tax (IRS 2025 brackets, single filer)
    T_fica     = FICA payroll taxes (SS + Medicare, 2025 rates)
    T_state    = state income tax (Tax Foundation 2025)
    E_essential = Σ [ E_BLS_i × (Salary/AvgIncome)^beta_i × alpha_i ]

Normalized metric:
    DI_fraction = DI / Salary   (dimensionless; typical range 0.15-0.40)

Key Assumptions (documented for judges)
----------------------------------------
1. Single filer — standard deduction only (~90% of filers; IRS 2023 SOI)
2. Salary is sole income source; no investment income, capital gains, etc.
3. Standard deduction taken (not itemized); more conservative than itemizing
4. State rates are 2025 effective rates at median income; actual rates vary
5. BLS household expenditure used for individual — valid for single-person
   households (most common for age < 30); may overstate expenses for ages 30-55
6. No 401(k)/IRA deductions — voluntary retirement savings treated as disposable
7. Static model — no career progression, inflation, or life events
8. Engel curve: constant elasticity is tractable approximation of QUAIDS
   (valid near mean income; quadratic term important far from mean)

References
----------
BEA (2024). Disposable Personal Income. bea.gov/data/income-saving
IRS Rev. Proc. 2024-61. 2025 tax brackets and standard deduction.
SSA (2025). Social Security wage base $176,100.
Tax Foundation (2025). State income tax rates. taxfoundation.org
BLS CES (2024). Consumer Expenditure Survey. bls.gov/cex
Banks, Blundell & Lewbel (1997). Quadratic Engel Curves. Rev. Econ. Stat.
Federal Reserve SHED (2025). Report on Economic Well-Being. federalreserve.gov
MIT Living Wage Calculator (Feb 2026). livingwage.mit.edu
"""

from tax_calculator import compute_all_taxes
from expenditure_model import compute_essential_expenses


def compute_disposable_income(
    gross_income: float,
    age: int,
    state: str,
    exp_data: dict,
    use_region_blend: bool = True,
) -> dict:
    """
    Compute annual disposable income for an individual.

    Parameters
    ----------
    gross_income : float
        Annual gross salary in USD.
    age : int
        Age in years.
    state : str
        Full U.S. state name (e.g., 'Texas', 'California', 'New York').
    exp_data : dict
        Parsed expenditure data from data_loader.load_expenditure_data().
    use_region_blend : bool
        Blend age-group + regional BLS data (recommended, default True).

    Returns
    -------
    dict with full breakdown:
        'gross_income'       : float  — input salary
        'taxes'              : dict   — breakdown by type
        'total_tax'          : float  — sum of all taxes
        'expenses'           : dict   — expenditure model output
        'total_essential'    : float  — total essential expenses
        'disposable_income'  : float  — net amount after taxes + essentials
        'di_fraction'        : float  — DI / gross_income
        'age_group'          : str
        'region'             : str
        'assumptions'        : list[str]

    Notes
    -----
    If disposable_income < 0, the individual's salary is below the living cost
    threshold for their demographic and location. This is not mathematically
    invalid — it indicates financial stress (negative savings capacity).
    """
    if gross_income < 0:
        raise ValueError(f"gross_income must be non-negative; got {gross_income}")
    if not (0 <= age <= 120):
        raise ValueError(f"age must be in [0, 120]; got {age}")

    # --- 1. Taxes ---
    taxes = compute_all_taxes(gross_income, state)

    # --- 2. Essential Expenses ---
    exp_result = compute_essential_expenses(
        salary=gross_income,
        age=age,
        state=state,
        exp_data=exp_data,
        use_region_blend=use_region_blend,
    )

    # --- 3. Disposable Income ---
    total_tax = taxes['total']
    total_essential = exp_result['total_essential']
    disposable = gross_income - total_tax - total_essential
    di_fraction = disposable / gross_income if gross_income > 0 else 0.0

    # --- 4. Assemble Output ---
    return {
        # Inputs
        'gross_income': gross_income,
        'age': age,
        'state': state,

        # Taxes
        'taxes': {
            'federal': taxes['federal'],
            'social_security': taxes['fica']['social_security'],
            'medicare': taxes['fica']['medicare'],
            'fica_total': taxes['fica']['total'],
            'state': taxes['state'],
            'total': total_tax,
        },
        'total_tax': total_tax,
        'effective_tax_rate': taxes['effective_total_rate'],

        # Expenses
        'expenses': exp_result,
        'total_essential': total_essential,
        'total_all_expenses': exp_result['total_all'],

        # Disposable Income
        'disposable_income': round(disposable, 2),
        'di_fraction': round(di_fraction, 4),

        # Demographics
        'age_group': exp_result['age_group'],
        'region': exp_result['region'],
        'income_ratio': exp_result['income_ratio'],

        # Model metadata
        'assumptions': [
            'Single filer, standard deduction ($15,000, IRS 2025)',
            'Salary is sole income source',
            'State rates: 2025 effective rates at income level (Tax Foundation)',
            'BLS CES 2024 household expenditure, treated as individual',
            'Engel curve: constant elasticity (power law) approximation of QUAIDS',
            'No 401(k)/IRA deductions; voluntary savings treated as disposable',
            'Static model: no career progression or inflation',
        ],
    }


def format_result(result: dict, title: str = None) -> str:
    """
    Return a human-readable string summary of a disposable income result.

    Parameters
    ----------
    result : dict
        Output of compute_disposable_income().
    title : str, optional
        Optional title line (e.g., profile label).

    Returns
    -------
    str
    """
    lines = []
    if title:
        lines.append(f"\n{'=' * 55}")
        lines.append(f"  {title}")
        lines.append(f"{'=' * 55}")

    g = result['gross_income']
    lines.append(f"  Gross Income:          ${g:>12,.0f}")
    lines.append(f"  Age: {result['age']}   State: {result['state']}")
    lines.append(f"  Age Group: {result['age_group']:<15}  Region: {result['region']}")
    lines.append(f"  Income vs. age avg:    {result['income_ratio']:>8.2f}×")
    lines.append("")
    lines.append("  ── TAXES ──────────────────────────────")
    taxes = result['taxes']
    lines.append(f"    Federal income tax:  ${taxes['federal']:>10,.0f}  ({taxes['federal']/g:.1%})")
    lines.append(f"    Social Security:     ${taxes['social_security']:>10,.0f}  ({taxes['social_security']/g:.1%})")
    lines.append(f"    Medicare:            ${taxes['medicare']:>10,.0f}  ({taxes['medicare']/g:.1%})")
    lines.append(f"    State ({result['state']:<12}):${taxes['state']:>10,.0f}  ({taxes['state']/g:.1%})")
    lines.append(f"    ─────────────────────────────────────")
    lines.append(f"    TOTAL TAXES:         ${taxes['total']:>10,.0f}  ({result['effective_tax_rate']:.1%})")
    lines.append("")
    lines.append("  ── ESSENTIAL EXPENSES ──────────────────")

    by_cat = result['expenses']['by_category']
    for cat, info in by_cat.items():
        if info['essential'] > 10:
            lines.append(f"    {cat:<35} ${info['essential']:>8,.0f}  (α={info['alpha']:.0%})")
    lines.append(f"    ─────────────────────────────────────")
    lines.append(f"    TOTAL ESSENTIAL:     ${result['total_essential']:>10,.0f}  ({result['total_essential']/g:.1%})")
    lines.append("")
    lines.append("  ── DISPOSABLE INCOME ───────────────────")
    di = result['disposable_income']
    lines.append(f"    DISPOSABLE INCOME:   ${di:>10,.0f}  ({result['di_fraction']:.1%} of gross)")
    if di < 0:
        lines.append("    ⚠ Negative DI: income below living cost threshold")
    elif result['di_fraction'] < 0.10:
        lines.append("    ⚠ Very low DI fraction (<10% of income)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Run all 8 demographic profiles
# ---------------------------------------------------------------------------

def run_all_profiles(exp_data: dict) -> list:
    """
    Compute disposable income for all 8 demographic demonstration profiles.

    Returns
    -------
    list of dicts (one per profile, with 'label' and 'archetype' added)
    """
    from constants import DEMO_PROFILES

    results = []
    for p in DEMO_PROFILES:
        result = compute_disposable_income(
            gross_income=p['salary'],
            age=p['age'],
            state=p['state'],
            exp_data=exp_data,
        )
        result['label'] = p['label']
        result['archetype'] = p['archetype']
        results.append(result)

    return results


if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import load_expenditure_data, get_default_excel_path, validate_data

    print("Loading expenditure data...")
    exp_data = load_expenditure_data(get_default_excel_path())
    validate_data(exp_data)

    print("\nRunning 8 demographic profiles...\n")
    results = run_all_profiles(exp_data)
    for r in results:
        label = f"{r['label']}: Age {r['age']}, ${r['gross_income']:,.0f}, {r['state']} — {r['archetype']}"
        print(format_result(r, title=label))

    # Summary table
    print("\n" + "=" * 75)
    print("SUMMARY TABLE")
    print("=" * 75)
    print(f"{'Profile':<5} {'Age':>4} {'Salary':>10} {'State':<12} "
          f"{'Tax%':>6} {'Ess%':>6} {'DI':>10} {'DI%':>6}")
    print("-" * 75)
    for r in results:
        g = r['gross_income']
        print(f"{r['label']:<5} {r['age']:>4} ${g:>9,.0f} {r['state']:<12} "
              f"{r['effective_tax_rate']:>5.1%} "
              f"{r['total_essential']/g:>5.1%} "
              f"${r['disposable_income']:>9,.0f} "
              f"{r['di_fraction']:>5.1%}")
