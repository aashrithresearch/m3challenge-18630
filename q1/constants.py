"""
constants.py — M3 Challenge 2026 Q1: Disposable Income Model

All tax parameters, expenditure elasticities, and demographic calibration
constants used across the model.

Sources:
  - IRS Rev. Proc. 2024-61 (2025 tax brackets, standard deduction)
  - SSA 2025 (Social Security wage base)
  - Tax Foundation 2025 State Tax Data (state effective rates)
  - BLS CPS Table A-9, 2024 (median weekly earnings by age group)
  - Banks, Blundell & Lewbel (1997) [QJE] — income elasticities
  - BLS Consumer Expenditure Survey 2024 — essential fraction (alpha) values
"""

# ---------------------------------------------------------------------------
# 1. FEDERAL INCOME TAX — 2025 (IRS Rev. Proc. 2024-61)
# ---------------------------------------------------------------------------

# Standard deduction for a single filer, 2025
STANDARD_DEDUCTION_SINGLE = 15_000  # USD

# Progressive tax brackets: (upper_bound, rate)
# Upper bound = None means top bracket (no ceiling)
FEDERAL_BRACKETS_SINGLE_2025 = [
    (11_925,    0.10),
    (48_475,    0.12),
    (103_350,   0.22),
    (197_300,   0.24),
    (250_525,   0.32),
    (626_350,   0.35),
    (None,      0.37),
]

# ---------------------------------------------------------------------------
# 2. FICA — 2025
# ---------------------------------------------------------------------------

# Social Security: 6.2% on wages up to $176,100 (SSA 2025 announcement)
SS_RATE = 0.062
SS_WAGE_BASE = 176_100

# Medicare: 1.45% on all wages; +0.9% surcharge above $200,000 (single filer)
MEDICARE_RATE = 0.0145
MEDICARE_SURCHARGE_RATE = 0.009
MEDICARE_SURCHARGE_THRESHOLD = 200_000

# ---------------------------------------------------------------------------
# 3. STATE INCOME TAX — 2025 effective rates (Tax Foundation 2025)
#
# Stored as a list of (income_threshold, effective_rate) breakpoints per state.
# Linear interpolation is used between breakpoints.
# Source: Tax Foundation 2025 State Income Tax Rates and Brackets.
# ---------------------------------------------------------------------------

# Breakpoints: [(income, effective_rate), ...] in ascending income order
# Effective rate = total state tax / gross income (approximate, single filer)
STATE_TAX_SCHEDULE = {
    'Texas': [(0, 0.0)],        # No state income tax
    'Florida': [(0, 0.0)],      # No state income tax
    'Nevada': [(0, 0.0)],       # No state income tax
    'Washington': [(0, 0.0)],   # No state income tax (income tax)
    'Wyoming': [(0, 0.0)],      # No state income tax

    # Illinois — flat 4.95% (excluding 2% credit phase-outs)
    'Illinois': [
        (0,       0.020),   # Low income after personal exemption credit
        (30_000,  0.040),
        (50_000,  0.046),
        (75_000,  0.048),
        (100_000, 0.049),
        (200_000, 0.049),
    ],

    # Georgia — progressive, top rate 5.49% (2025 after reform)
    'Georgia': [
        (0,       0.00),
        (20_000,  0.025),
        (40_000,  0.038),
        (60_000,  0.042),
        (85_000,  0.044),
        (150_000, 0.047),
        (300_000, 0.049),
    ],

    # New York — progressive, top 10.9% on $25M+; city tax adds ~3.9%
    # State only (excluding NYC city tax) — state effective rates:
    'New York': [
        (0,       0.00),
        (20_000,  0.030),
        (40_000,  0.045),
        (65_000,  0.055),
        (100_000, 0.060),
        (150_000, 0.065),
        (300_000, 0.070),
        (500_000, 0.080),
        (1_000_000, 0.090),
    ],

    # California — progressive, top 13.3% on $1M+ (SDI adds 0.9%)
    'California': [
        (0,       0.00),
        (20_000,  0.030),
        (40_000,  0.052),
        (65_000,  0.068),
        (100_000, 0.078),
        (150_000, 0.085),
        (300_000, 0.095),
        (500_000, 0.105),
        (1_000_000, 0.120),
    ],

    # Pennsylvania — flat 3.07%
    'Pennsylvania': [(0, 0.0307)],

    # Ohio — progressive, low rates
    'Ohio': [
        (0,       0.00),
        (26_050,  0.025),
        (100_000, 0.033),
        (115_300, 0.040),
    ],

    # Michigan — flat 4.25%
    'Michigan': [(0, 0.0425)],

    # North Carolina — flat 4.5% (2025)
    'North Carolina': [(0, 0.045)],

    # Virginia — progressive to 5.75%
    'Virginia': [
        (0,       0.00),
        (17_000,  0.020),
        (17_001,  0.030),
        (17_001,  0.050),
        (50_000,  0.055),
        (100_000, 0.057),
        (200_000, 0.058),
    ],

    # Colorado — flat 4.4% (2025, reduced from 4.55%)
    'Colorado': [(0, 0.044)],

    # Arizona — flat 2.5% (2025)
    'Arizona': [(0, 0.025)],

    # Massachusetts — 5% flat (9% on long-term capital gains; income: 5%)
    'Massachusetts': [(0, 0.050)],

    # Tennessee — 0% (Hall tax repealed 2021; no wage income tax)
    'Tennessee': [(0, 0.0)],
}

# Map state → BLS region for expenditure lookup
STATE_TO_REGION = {
    # Northeast
    'Connecticut': 'Northeast', 'Maine': 'Northeast', 'Massachusetts': 'Northeast',
    'New Hampshire': 'Northeast', 'Rhode Island': 'Northeast', 'Vermont': 'Northeast',
    'New Jersey': 'Northeast', 'New York': 'Northeast', 'Pennsylvania': 'Northeast',

    # Midwest
    'Illinois': 'Midwest', 'Indiana': 'Midwest', 'Michigan': 'Midwest',
    'Ohio': 'Midwest', 'Wisconsin': 'Midwest', 'Iowa': 'Midwest',
    'Kansas': 'Midwest', 'Minnesota': 'Midwest', 'Missouri': 'Midwest',
    'Nebraska': 'Midwest', 'North Dakota': 'Midwest', 'South Dakota': 'Midwest',

    # South
    'Delaware': 'South', 'Florida': 'South', 'Georgia': 'South',
    'Maryland': 'South', 'North Carolina': 'South', 'South Carolina': 'South',
    'Virginia': 'South', 'West Virginia': 'South', 'District of Columbia': 'South',
    'Alabama': 'South', 'Kentucky': 'South', 'Mississippi': 'South',
    'Tennessee': 'South', 'Arkansas': 'South', 'Louisiana': 'South',
    'Oklahoma': 'South', 'Texas': 'South',

    # West
    'Arizona': 'West', 'Colorado': 'West', 'Idaho': 'West', 'Montana': 'West',
    'Nevada': 'West', 'New Mexico': 'West', 'Utah': 'West', 'Wyoming': 'West',
    'Alaska': 'West', 'California': 'West', 'Hawaii': 'West',
    'Oregon': 'West', 'Washington': 'West',
}

# ---------------------------------------------------------------------------
# 4. EXPENDITURE ESSENTIAL FRACTIONS (alpha)
#    Source: BLS CES 2024; food-at-home vs away-from-home split from USDA ERS
# ---------------------------------------------------------------------------

# alpha_i = fraction of total category spending that is essential/non-discretionary
ESSENTIAL_FRACTIONS = {
    'Food': 0.70,             # ~70% food-at-home (essential); 30% dining out (discretionary)
    'Housing': 1.00,          # Fully essential
    'Utilities, fuel, public services': 1.00,  # Fully essential
    'Household operations': 0.50,   # Half essential (childcare yes, housekeeping optional)
    'Housekeeping supplies': 0.70,   # Basic cleaning supplies essential
    'Household furnishings and equipement': 0.20,  # Mostly discretionary
    'Apparel and services': 0.60,    # Basic clothing essential
    'Transportation': 0.75,          # Commuting essential; recreational travel not
    'Healthcare': 1.00,              # Fully essential
    'Entertainment': 0.00,           # Fully discretionary
    'Personal care': 0.80,           # Basic hygiene essential
    'Education': 0.50,               # Mixed (required tuition vs elective)
    'Miscellaneous': 0.00,           # Discretionary
    'Personal insurance': 0.10,
    # NOTE: BLS CES "Personal insurance and pensions" includes Social Security
    # contributions and pension contributions, both of which are excluded from
    # this model (SS counted in FICA above; retirement savings treated as
    # disposable per Assumption 6). Only life/health insurance premiums (~10%
    # of this category) are treated as essential here.
}

# ---------------------------------------------------------------------------
# 5. INCOME ELASTICITIES (beta) — Engel Curve Power-Law Approximation
#    Source: Banks, Blundell & Lewbel (1997), Rev. Econ. Stat.
#    Full QUAIDS model: w_i = alpha_i + beta_i*log(m) + gamma_i*[log(m)]^2
#    Constant elasticity is tractable approximation valid near mean income.
# ---------------------------------------------------------------------------

INCOME_ELASTICITY = {
    'Food': 0.55,                          # Most inelastic — Engel's Law
    'Housing': 0.70,                        # Inelastic
    'Utilities, fuel, public services': 0.60,
    'Household operations': 0.90,
    'Housekeeping supplies': 0.75,
    'Household furnishings and equipement': 1.10,  # Elastic
    'Apparel and services': 0.85,
    'Transportation': 0.80,
    'Healthcare': 0.65,                     # Inelastic
    'Entertainment': 1.20,                  # Elastic
    'Personal care': 0.75,
    'Education': 0.90,
    'Miscellaneous': 1.00,
    'Personal insurance': 0.95,
}

# ---------------------------------------------------------------------------
# 6. AVERAGE INCOME BY AGE GROUP (AVG_INCOME_BY_AGE)
#    Source: BLS CPS Table A-9, 2024 median usual weekly earnings, full-time
#    workers, annualized (× 52). Cross-validated with Census P60-286 (2025).
# ---------------------------------------------------------------------------

# Keys match the age groups in the BLS CES Excel file
AVG_INCOME_BY_AGE = {
    'Under 25': 42_000,    # BLS CPS: ~$808/week × 52
    '25-34':    62_000,    # BLS CPS: ~$1,192/week × 52
    '35-44':    83_000,    # BLS CPS: ~$1,596/week × 52
    '45-54':    88_000,    # BLS CPS: ~$1,692/week × 52
    '55-64':    80_000,    # BLS CPS: ~$1,538/week × 52
    '65-74':    58_000,    # BLS CPS: ~$1,115/week (part-time prevalence)
    '75 and older': 44_000,  # BLS CPS + Census P60 estimate
}

# ---------------------------------------------------------------------------
# 7. DEMOGRAPHIC PROFILES for demonstration (Section 5 of notebook)
# ---------------------------------------------------------------------------

DEMO_PROFILES = [
    {'label': 'P1', 'age': 23, 'salary': 42_000,  'state': 'Texas',      'archetype': 'Entry-level, no state tax'},
    {'label': 'P2', 'age': 28, 'salary': 65_000,  'state': 'Illinois',   'archetype': 'Young professional, flat tax'},
    {'label': 'P3', 'age': 40, 'salary': 85_000,  'state': 'Georgia',    'archetype': 'Mid-career, South'},
    {'label': 'P4', 'age': 32, 'salary': 145_000, 'state': 'California', 'archetype': 'Tech worker, high tax'},
    {'label': 'P5', 'age': 50, 'salary': 210_000, 'state': 'New York',   'archetype': 'Senior professional, high tax'},
    {'label': 'P6', 'age': 60, 'salary': 75_000,  'state': 'Florida',    'archetype': 'Pre-retirement, no state tax'},
    {'label': 'P7', 'age': 67, 'salary': 48_000,  'state': 'Georgia',    'archetype': 'Early retiree'},
    {'label': 'P8', 'age': 22, 'salary': 28_000,  'state': 'Texas',      'archetype': 'Low-income'},
]
