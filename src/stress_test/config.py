"""
Defining all assumptions as constants/dictionaries.
Importable with no side effects beyond basic validation.
Easy to audit.
"""

# Frequency constant
FREQUENCY = "Q"

# Bank list
BANK_NAMES = [
    "HSBC",
    "Lloyds Banking Group",
    "Standard Chartered"
]

# Base portfolio constants
MORTGAGES_OO = "mortgages_oo"
CONSUMER_UNSECURED = "consumer_unsecured"
SME_LOANS = "sme_loans"
LARGE_CORP_LOANS = "large_corp_loans"

# Base portfolio list
BASE_PORTFOLIOS = [
    MORTGAGES_OO,
    CONSUMER_UNSECURED,
    SME_LOANS,
    LARGE_CORP_LOANS
]

# Risk weights dictionary
RISK_WEIGHT = {
    MORTGAGES_OO: 0.25,
    CONSUMER_UNSECURED: 0.5,
    SME_LOANS: 0.75,
    LARGE_CORP_LOANS: 1.0
}

# Loss Given Default (LGD) dictionary
BASELINE_LGD = {
    MORTGAGES_OO: 0.2,
    CONSUMER_UNSECURED: 0.8,
    SME_LOANS: 0.6,
    LARGE_CORP_LOANS: 0.4
}

# Portfolio shares per bank
BANK_BASE_PORTFOLIO_SHARES = {
    "HSBC": {
        MORTGAGES_OO: 0.20,
        CONSUMER_UNSECURED: 0.15,
        SME_LOANS: 0.25,
        LARGE_CORP_LOANS: 0.40
    },
    "Lloyds Banking Group": {
        MORTGAGES_OO: 0.55,
        CONSUMER_UNSECURED: 0.25,
        SME_LOANS: 0.15,
        LARGE_CORP_LOANS: 0.05
    },
    "Standard Chartered": {
        MORTGAGES_OO: 0.05,
        CONSUMER_UNSECURED: 0.05,
        SME_LOANS: 0.30,
        LARGE_CORP_LOANS: 0.60
    }
}

# Overlay shares (subsets)
HIGH_LTV_SHARE_OF_MORTGAGES = {
    "HSBC": 0.18,
    "Lloyds Banking Group": 0.25,
    "Standard Chartered": 0.10
}

EXPORT_SHARE_OF_LARGE_CORP = {
    "HSBC": 0.40,
    "Lloyds Banking Group": 0.15,
    "Standard Chartered": 0.55 
}

ENERGY_INTENSIVE_SHARE_OF_CORP = {
    "HSBC": 0.12,
    "Lloyds Banking Group": 0.10,
    "Standard Chartered": 0.18 
}

# Scale choices
TOTAL_EAD_BN = {
    "HSBC": 800,
    "Lloyds Banking Group": 600,
    "Standard Chartered": 400
}

TARGET_CET1_RATIO = {
    "HSBC": 0.14,
    "Lloyds Banking Group": 0.15,
    "Standard Chartered": 0.13
}


# Lightweight validation
for bank in BANK_NAMES:
    # Bank coverage checks
    if bank not in BANK_BASE_PORTFOLIO_SHARES:
        raise KeyError(f"Missing {bank} in BANK_BASE_PORTFOLIO_SHARES")
    if bank not in TOTAL_EAD_BN:
        raise KeyError(f"Missing {bank} in TOTAL_EAD_BN")
    if bank not in TARGET_CET1_RATIO:
        raise KeyError(f"Missing {bank} in TARGET_CET1_RATIO")
    if bank not in HIGH_LTV_SHARE_OF_MORTGAGES:
        raise KeyError(f"Missing {bank} in HIGH_LTV_SHARE_OF_MORTGAGES")
    if bank not in EXPORT_SHARE_OF_LARGE_CORP:
        raise KeyError(f"Missing {bank} in EXPORT_SHARE_OF_LARGE_CORP")
    if bank not in ENERGY_INTENSIVE_SHARE_OF_CORP:
        raise KeyError(f"Missing {bank} in ENERGY_INTENSIVE_SHARE_OF_CORP")

    # Base-portfolio key coverage + bounds
    shares = BANK_BASE_PORTFOLIO_SHARES[bank]
    for portfolio in BASE_PORTFOLIOS:
        if portfolio not in shares:
            raise KeyError(f"Missing portfolio {portfolio} for bank {bank} in BANK_BASE_PORTFOLIO_SHARES")
        val = shares[portfolio]
        if not (0.0 <= val <= 1.0):
            raise ValueError(f"Share for bank {bank}, portfolio {portfolio} must be in [0,1], got {val}")

    # Shares must sum to 1 (tolerance for floating point)
    total = sum(shares[p] for p in BASE_PORTFOLIOS)
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"Portfolio shares for {bank} do not sum to 1.0 (got {total})")

# Sanity checks for parameter bounds
for p in BASE_PORTFOLIOS:
    lgd = BASELINE_LGD[p]
    rw = RISK_WEIGHT[p]
    if not (0.0 <= lgd <= 1.0):
        raise ValueError(f"BASELINE_LGD for portfolio {p} must be in [0,1], got {lgd}")
    if rw < 0.0:
        raise ValueError(f"RISK_WEIGHT for portfolio {p} must be non-negative, got {rw}")

for bank in BANK_NAMES:
    cet1 = TARGET_CET1_RATIO[bank]
    ead = TOTAL_EAD_BN[bank]
    if not (0.0 < cet1 < 1.0):
        raise ValueError(f"TARGET_CET1_RATIO for {bank} must be in (0,1), got {cet1}")
    if ead <= 0.0:
        raise ValueError(f"TOTAL_EAD_BN for {bank} must be > 0, got {ead}")

    hl = HIGH_LTV_SHARE_OF_MORTGAGES[bank]
    ex = EXPORT_SHARE_OF_LARGE_CORP[bank]
    en = ENERGY_INTENSIVE_SHARE_OF_CORP[bank]
    for name, v in (
        ("HIGH_LTV_SHARE_OF_MORTGAGES", hl),
        ("EXPORT_SHARE_OF_LARGE_CORP", ex),
        ("ENERGY_INTENSIVE_SHARE_OF_CORP", en),
    ):
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"{name} for {bank} must be in [0,1], got {v}")


# Scenario variables
GDP_GROWTH = "gdp_growth"
UNEMPLOYMENT_RATE = "unemployment_rate"
HOUSE_PRICE_GROWTH = "house_price_growth"
POLICY_RATE = "policy_rate"
GILT_10Y = "gilt_10y"

REQUIRED_SCENARIO_COLUMNS = {
    GDP_GROWTH,
    UNEMPLOYMENT_RATE,
    HOUSE_PRICE_GROWTH,
    POLICY_RATE,
    GILT_10Y,
}