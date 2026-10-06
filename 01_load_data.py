"""
Step 1: Load raw data from Excel into SQLite.

This script:
- Reads both sheets from online_retail_II.xlsx ('Year 2009-2010' and 'Year 2010-2011')
- Stacks them into a single dataframe, tagging which sheet each row came from
- Writes the result into a SQLite database as a table called `raw_transactions`
- Does NOT clean or filter anything — this is the raw source of truth

Run this once. If you re-run it, it will replace the raw_transactions table.
"""

import pandas as pd
from sqlalchemy import create_engine

# ---- Paths ----
EXCEL_PATH = "../data/online_retail_II.xlsx"
DB_PATH = "../data/online_retail.db"

SHEET_NAMES = ["Year 2009-2010", "Year 2010-2011"]


def load_excel_sheets(path: str, sheet_names: list[str]) -> pd.DataFrame:
    """Read each sheet and stack them into one dataframe, keeping track of source sheet."""
    frames = []
    for sheet in sheet_names:
        print(f"Reading sheet: {sheet} ...")
        df = pd.read_excel(path, sheet_name=sheet)
        df["SourceSheet"] = sheet  # keep provenance in case it's useful later
        frames.append(df)
        print(f"  -> {len(df):,} rows")

    combined = pd.concat(frames, ignore_index=True)
    print(f"\nCombined total: {len(combined):,} rows")
    return combined


def main():
    df = load_excel_sheets(EXCEL_PATH, SHEET_NAMES)

    # Basic column name cleanup: no spaces, consistent casing.
    # Original columns: Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country
    df = df.rename(columns={
        "Customer ID": "CustomerID",
    })

    engine = create_engine(f"sqlite:///{DB_PATH}")

    print(f"\nWriting to {DB_PATH} as table 'raw_transactions' ...")
    df.to_sql("raw_transactions", engine, if_exists="replace", index=False)

    print("Done. Row count in DB:")
    with engine.connect() as conn:
        result = conn.exec_driver_sql("SELECT COUNT(*) FROM raw_transactions")
        print(f"  raw_transactions: {result.scalar():,} rows")


if __name__ == "__main__":
    main()
