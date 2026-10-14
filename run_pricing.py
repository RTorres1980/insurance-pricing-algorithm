"""Quote every client in data/clients.csv for every product in data/products.csv.

Usage: python run_pricing.py [--mode Monthly|Quarterly|Semi-Annual|Annual]
"""
import argparse

import pandas as pd

from src.pricing_model import MODAL_FACTOR, run_pricing


def main(mode):
    clients = pd.read_csv("data/clients.csv")
    products = pd.read_csv("data/products.csv")
    quotes = run_pricing(clients, products, mode)
    quotes.to_csv("output_premiums.csv", index=False)

    approved = quotes[quotes["status"] == "Approved"]
    pd.set_option("display.width", 160)
    print(approved.pivot_table(index="client_id", columns="product", values=f"{mode.lower()}_premium").round(2)
          .head(10).to_string())
    print(f"\n{len(approved)} quotes approved, {len(quotes) - len(approved)} declined")
    print(quotes.loc[quotes["status"] == "Declined", ["client_id", "product", "reason"]].to_string(index=False))
    print("\nAll quotes saved to output_premiums.csv")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mode", default="Monthly", choices=list(MODAL_FACTOR))
    main(p.parse_args().mode)
