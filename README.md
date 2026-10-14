# Insurance Pricing Algorithm

![CI](https://github.com/RTorres1980/insurance-pricing-algorithm/actions/workflows/ci.yml/badge.svg)

A transparent rating engine for level term life insurance. It prices each applicant from expected claims, applies risk-class, tobacco and size adjustments, enforces basic underwriting limits, and quotes annual and modal premiums.

## How a premium is built

1. **Mortality**: the chance of death at each age follows a Gompertz curve, `q(x) = 0.00002 × e^(0.09x)`, a standard simple model for adult mortality.
2. **Net premium per $1,000**: the present value of expected death benefits over the term, divided by the present value of a level premium paid each year the insured is alive. Both are discounted at 4%.
3. **Adjustments**
   - Risk class: Preferred Plus 0.70× up to Table 4 2.20×
   - Tobacco: 2.30×
   - Size discount: 5% at $500k and above, 10% at $1M and above
4. **Gross premium**: net rate ÷ (1 − 25% expense load) × face / 1,000, plus a $60 annual policy fee.
5. **Modal premium**: annual × 0.52 semi-annual, 0.265 quarterly, or 0.0875 monthly. Paying more often costs a little more over a year.

**Underwriting limits:** issue ages 18–75, issue age plus term no more than 85, and face amounts from $50,000 to $5,000,000. Applications outside these limits are declined with a reason rather than priced.

Net annual rates per $1,000 for a 20-year term:

| Issue age | Mortality q(x) per 1,000 | Net rate per 1,000 |
|---|---|---|
| 30 | 0.30 | 0.68 |
| 45 | 1.15 | 2.62 |
| 60 | 4.43 | 9.87 |

All parameters are illustrative. They show how the calculation works and are not filed or market rates.

## Run it

```bash
pip install -r requirements.txt
python run_pricing.py                 # monthly premiums; or --mode Annual / Quarterly / Semi-Annual
pytest -q
```

Quotes every client in `data/clients.csv` (24 sample applicants) for 10-, 20- and 30-year terms (`data/products.csv`). All results are written to `output_premiums.csv`:

```
product    Term 10  Term 20  Term 30
client_id
C001        861.09  1341.45  2026.64
C003         79.82   123.59   194.11
C010          7.74     9.20    11.55
...
60 quotes approved, 12 declined
C004 Term 10   Face amount outside $50,000-$5,000,000
C008 Term 10   Issue age 78 outside 18-75
C009 Term 20   Age 70 + 20-year term exceeds maximum expiry age 85
```

## Tests

The tests check that a 1-year term equals discounted mortality exactly; that rates rise with age and term; that premiums rank in risk-class order and are higher for tobacco users; the gross premium build-up; the size discount; each underwriting decline; and that monthly payments cost more than annual.

## Files

| Path | Purpose |
|---|---|
| `src/pricing_model.py` | Mortality, net premium, adjustments, underwriting and quoting |
| `run_pricing.py` | Prices the sample book and writes `output_premiums.csv` |
| `data/clients.csv`, `data/products.csv` | Sample applicants and term products |

## Author

Robert Torres · [LinkedIn](https://www.linkedin.com/in/robert-torres-394535381) · [GitHub](https://github.com/RTorres1980) · MIT License
