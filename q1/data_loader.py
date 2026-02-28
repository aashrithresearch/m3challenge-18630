"""
data_loader.py — M3 Challenge 2026 Q1

Parses the 'Expenditures (U.S.)' sheet from the M3 Excel data file into a
structured nested dictionary.

Output schema:
  exp_data = {
      'by_age': {
          'Under 25':      {'Food': 7215.0, 'Housing': 16853.0, ...},
          '25-34':         {...},
          ...
          '75 and older':  {...},
      },
      'by_region': {
          'Northeast': {'Food': 11372.0, 'Housing': 29469.0, ...},
          'Midwest':   {...},
          'South':     {...},
          'West':      {...},
      },
      'mean_income_by_age': {
          'Under 25': 48514.0,
          ...
      },
      'mean_income_by_region': {
          'Northeast': 115770.0,
          ...
      },
  }

Source: M3-Challenge-Problem-Data-2026.xlsx, sheet 'Expenditures (U.S.)'
BLS Consumer Expenditure Survey 2024.
"""

import os
import re
import openpyxl


# ---------------------------------------------------------------------------
# Layout constants (row/column indices, 0-based)
# ---------------------------------------------------------------------------

_HEADER_ROW = 2       # Row with column labels: 'Age Group', 'Under 25', ...
_DATA_START_ROW = 10  # First data row: 'All expenditures'
_DATA_END_ROW = 24    # Last data row: 'Personal insurance'

_AGE_COLS = {
    'Under 25':      1,
    '25-34':         2,
    '35-44':         3,
    '45-54':         4,
    '55-64':         5,
    '65-74':         6,
    '75 and older':  7,
}

_REGION_COLS = {
    'Northeast': 8,
    'Midwest':   9,
    'South':     10,
    'West':      11,
}

_MEAN_INCOME_ROW = 3  # 'Mean income before taxes'

# Expenditure categories to extract (row labels, stripped)
_EXPENDITURE_CATEGORIES = [
    'Food',
    'Housing',
    'Utilities, fuel, public services',
    'Household operations',
    'Housekeeping supplies',
    'Household furnishings and equipement',
    'Apparel and services',
    'Transportation',
    'Healthcare',
    'Entertainment',
    'Personal care',
    'Education',
    'Miscellaneous',
    'Personal insurance',
    'All expenditures',
]


def _parse_number(val):
    """Convert cell value to float, handling comma-formatted strings."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = val.replace(',', '').replace('$', '').strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def load_expenditure_data(excel_path: str) -> dict:
    """
    Parse 'Expenditures (U.S.)' sheet from the M3 Excel file.

    Parameters
    ----------
    excel_path : str
        Absolute path to M3-Challenge-Problem-Data-2026.xlsx

    Returns
    -------
    dict with keys: 'by_age', 'by_region', 'mean_income_by_age',
                    'mean_income_by_region', 'categories'
    """
    wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
    ws = wb['Expenditures (U.S.)']

    # Read all rows into a list for random access
    rows = list(ws.iter_rows(values_only=True))

    # ---- Mean income by age group ----------------------------------------
    income_row = rows[_MEAN_INCOME_ROW]
    mean_income_by_age = {
        age: _parse_number(income_row[col])
        for age, col in _AGE_COLS.items()
    }
    mean_income_by_region = {
        region: _parse_number(income_row[col])
        for region, col in _REGION_COLS.items()
    }

    # ---- Expenditure data -------------------------------------------------
    by_age = {age: {} for age in _AGE_COLS}
    by_region = {region: {} for region in _REGION_COLS}

    for row_idx in range(_DATA_START_ROW, _DATA_END_ROW + 1):
        if row_idx >= len(rows):
            break
        row = rows[row_idx]
        label = str(row[0]).strip() if row[0] is not None else ''

        # Match against known categories (case-insensitive, strip trailing spaces)
        matched_cat = None
        for cat in _EXPENDITURE_CATEGORIES:
            if label.lower() == cat.lower():
                matched_cat = cat
                break

        if matched_cat is None:
            continue  # skip rows we don't need

        for age, col in _AGE_COLS.items():
            val = _parse_number(row[col])
            if val is not None:
                by_age[age][matched_cat] = val

        for region, col in _REGION_COLS.items():
            val = _parse_number(row[col])
            if val is not None:
                by_region[region][matched_cat] = val

    wb.close()

    return {
        'by_age': by_age,
        'by_region': by_region,
        'mean_income_by_age': mean_income_by_age,
        'mean_income_by_region': mean_income_by_region,
        'categories': [c for c in _EXPENDITURE_CATEGORIES if c != 'All expenditures'],
        'all_expenditures_by_age': {
            age: by_age[age].get('All expenditures') for age in _AGE_COLS
        },
        'all_expenditures_by_region': {
            region: by_region[region].get('All expenditures') for region in _REGION_COLS
        },
    }


def get_default_excel_path() -> str:
    """Return the expected path to the M3 Excel data file."""
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(this_dir, '..', 'M3-Challenge-Problem-Data-2026.xlsx')


def validate_data(exp_data: dict) -> None:
    """
    Quick sanity checks on the parsed data.
    Raises AssertionError if something looks wrong.
    """
    # Check all age groups present
    expected_ages = list(_AGE_COLS.keys())
    assert set(exp_data['by_age'].keys()) == set(expected_ages), \
        f"Missing age groups: {set(expected_ages) - set(exp_data['by_age'].keys())}"

    # Check all regions present
    assert set(exp_data['by_region'].keys()) == {'Northeast', 'Midwest', 'South', 'West'}

    # Check key categories present for each age group
    for age in expected_ages:
        for cat in ['Food', 'Housing', 'Transportation', 'Healthcare']:
            assert cat in exp_data['by_age'][age], \
                f"Missing '{cat}' for age group '{age}'"
            assert exp_data['by_age'][age][cat] > 0, \
                f"Zero/negative value for '{cat}' in age group '{age}'"

    # Cross-check: Food for 25-34 should be ~$9,630 (known from BLS 2024)
    food_25_34 = exp_data['by_age']['25-34']['Food']
    assert abs(food_25_34 - 9630) < 100, \
        f"Food for 25-34 = {food_25_34}, expected ~9630 (BLS CES 2024)"

    print("Data validation passed.")
    print(f"  Age groups: {list(exp_data['by_age'].keys())}")
    print(f"  Regions: {list(exp_data['by_region'].keys())}")
    print(f"  Categories: {exp_data['categories']}")
    print(f"  Mean income 25-34: ${exp_data['mean_income_by_age']['25-34']:,.0f}")
    print(f"  Food (25-34): ${food_25_34:,.0f}  [BLS 2024: $9,630 ✓]")
