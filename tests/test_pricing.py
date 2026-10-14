import pandas as pd
import pytest

from src import pricing_model as pm


def client(**kw):
    c = {"client_id": "C1", "age": 40, "risk_class": "Standard Plus", "tobacco": False, "face_amount": 250_000}
    c.update(kw)
    return pd.Series(c)


TERM20 = pd.Series({"product": "Term 20", "term_years": 20})


def test_one_year_term_equals_discounted_mortality():
    # For a 1-year term the net premium is just q(x) discounted one year.
    q = float(pm.mortality(40))
    assert pm.net_rate_per_1000(40, 1) == pytest.approx(1000 * q / 1.04)


def test_rates_increase_with_age_and_term():
    assert pm.net_rate_per_1000(50, 20) > pm.net_rate_per_1000(40, 20)
    assert pm.net_rate_per_1000(40, 30) > pm.net_rate_per_1000(40, 10)


def test_risk_class_and_tobacco_order():
    prices = [pm.price(client(risk_class=rc), TERM20).annual_premium for rc in pm.RISK_CLASS_FACTOR]
    assert prices == sorted(prices)
    assert pm.price(client(tobacco=True), TERM20).annual_premium > pm.price(client(), TERM20).annual_premium


def test_gross_premium_build_up():
    q = pm.price(client(face_amount=100_000), TERM20)
    expected_rate = pm.net_rate_per_1000(40, 20) / (1 - pm.EXPENSE_LOAD)
    assert q.rate_per_1000 == pytest.approx(expected_rate, abs=1e-4)
    assert q.annual_premium == pytest.approx(expected_rate * 100 + pm.POLICY_FEE, abs=0.01)


def test_large_face_gets_band_discount():
    small = pm.price(client(face_amount=400_000), TERM20).rate_per_1000
    large = pm.price(client(face_amount=1_000_000), TERM20).rate_per_1000
    assert large == pytest.approx(small * 0.90, rel=1e-3)


@pytest.mark.parametrize("kw,fragment", [
    ({"age": 17}, "Issue age"),
    ({"age": 70}, "maximum expiry age"),
    ({"face_amount": 10_000}, "Face amount"),
    ({"risk_class": "Super Preferred"}, "not offered"),
])
def test_underwriting_declines(kw, fragment):
    q = pm.price(client(**kw), TERM20)
    assert q.status == "Declined" and fragment in q.reason
    assert pd.isna(q.annual_premium)


def test_monthly_mode_costs_more_over_a_year():
    q = pm.price(client(), TERM20, mode="Monthly")
    assert q.modal_premium * 12 > q.annual_premium
