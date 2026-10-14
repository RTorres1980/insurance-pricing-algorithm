"""Level term life rating engine.

Net premium = present value of expected death benefits over the term
              / present value of a level annual premium paid while alive (annuity-due)
Gross premium = net premium x risk-class factor x tobacco factor / (1 - expense load) + policy fee

Mortality follows a Gompertz curve, q(x) = A * exp(B * x), a standard simple model for adult
mortality. All parameters are illustrative, not filed rates.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

GOMPERTZ_A = 0.00002
GOMPERTZ_B = 0.09
INTEREST = 0.04
EXPENSE_LOAD = 0.25            # share of gross premium for commissions, admin and profit
POLICY_FEE = 60.0              # flat annual fee
MAX_ISSUE_AGE = 75
MAX_EXPIRY_AGE = 85            # issue age + term must not exceed this
MIN_FACE, MAX_FACE = 50_000, 5_000_000

RISK_CLASS_FACTOR = {"Preferred Plus": 0.70, "Preferred": 0.85, "Standard Plus": 1.00, "Standard": 1.20,
                     "Table 2": 1.70, "Table 4": 2.20}
TOBACCO_FACTOR = {False: 1.00, True: 2.30}
# Per-$1,000 rate discounts for larger policies.
BAND_DISCOUNT = [(1_000_000, 0.10), (500_000, 0.05), (0, 0.0)]
MODAL_FACTOR = {"Annual": (1.0, 1), "Semi-Annual": (0.52, 2), "Quarterly": (0.265, 4), "Monthly": (0.0875, 12)}


@dataclass
class Quote:
    client_id: str
    product: str
    face_amount: float
    status: str
    reason: str = ""
    rate_per_1000: float = float("nan")
    annual_premium: float = float("nan")
    modal_premium: float = float("nan")


def mortality(age):
    """Annual probability of death at a given age (capped at 1)."""
    return np.minimum(GOMPERTZ_A * np.exp(GOMPERTZ_B * np.asarray(age, dtype=float)), 1.0)


def net_rate_per_1000(issue_age, term, interest=INTEREST):
    """Level annual net premium per $1,000 of coverage for a term policy."""
    ages = issue_age + np.arange(term)
    q = mortality(ages)
    survival = np.concatenate([[1.0], np.cumprod(1 - q)[:-1]])   # alive at start of each year
    v = 1 / (1 + interest)
    pv_benefits = np.sum(survival * q * v ** np.arange(1, term + 1)) * 1000
    pv_annuity = np.sum(survival * v ** np.arange(term))
    return pv_benefits / pv_annuity


def band_discount(face):
    return next(d for floor, d in BAND_DISCOUNT if face >= floor)


def underwrite(client, product):
    """Return a decline reason, or '' if the application can be rated."""
    age, term, face = client["age"], product["term_years"], client["face_amount"]
    if client["risk_class"] not in RISK_CLASS_FACTOR:
        return f"Risk class '{client['risk_class']}' not offered"
    if age < 18 or age > MAX_ISSUE_AGE:
        return f"Issue age {age} outside 18-{MAX_ISSUE_AGE}"
    if age + term > MAX_EXPIRY_AGE:
        return f"Age {age} + {term}-year term exceeds maximum expiry age {MAX_EXPIRY_AGE}"
    if not MIN_FACE <= face <= MAX_FACE:
        return f"Face amount outside ${MIN_FACE:,}-${MAX_FACE:,}"
    return ""


def price(client, product, mode="Annual"):
    reason = underwrite(client, product)
    q = Quote(client["client_id"], product["product"], client["face_amount"], "Declined" if reason else "Approved",
              reason)
    if reason:
        return q
    rate = (net_rate_per_1000(client["age"], product["term_years"])
            * RISK_CLASS_FACTOR[client["risk_class"]]
            * TOBACCO_FACTOR[bool(client["tobacco"])]
            * (1 - band_discount(client["face_amount"]))
            / (1 - EXPENSE_LOAD))
    annual = rate * client["face_amount"] / 1000 + POLICY_FEE
    factor, _ = MODAL_FACTOR[mode]
    q.rate_per_1000 = round(rate, 4)
    q.annual_premium = round(annual, 2)
    q.modal_premium = round(annual * factor, 2)
    return q


def run_pricing(clients, products, mode="Monthly"):
    """Quote every client for every product."""
    quotes = [price(c, p, mode) for _, c in clients.iterrows() for _, p in products.iterrows()]
    out = pd.DataFrame([q.__dict__ for q in quotes])
    return out.rename(columns={"modal_premium": f"{mode.lower()}_premium"})
