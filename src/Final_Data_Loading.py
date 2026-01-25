# src/Final_Data_Loading.py
import pandas as pd

PRODUCT_MAP = {
    "271111": "LNG (271111)",
    "271121": "Gaseous NG (271121)",
}

def load_processed(path: str) -> pd.DataFrame:
    """Load the processed (cleaned+consolidated) Comtrade dataset."""
    return pd.read_csv(path)

def standardize_types(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure consistent dtypes used throughout analysis/network modules."""
    out = df.copy()
    
    # Converting to proper datetime
    out["period"] = pd.to_datetime(out["period"], errors="coerce")
    out["primaryValue"] = pd.to_numeric(out["primaryValue"], errors="coerce")
    out["netWgt"] = pd.to_numeric(out["netWgt"], errors="coerce")

    out["cmdCode"] = out["cmdCode"].astype(str)

    # If product not present
    if "product" not in out.columns:
        out["product"] = out["cmdCode"].map(PRODUCT_MAP).fillna("Other/Unknown")

    return out

def filter_valid_trade(df: pd.DataFrame) -> pd.DataFrame:
    """Drop invalid rows (missing/negative trade values)."""
    out = df.copy()
    out = out[out["primaryValue"].notna() & (out["primaryValue"] >= 0)].copy()
    return out

def filter_years(df: pd.DataFrame, year_min: int = 2010, year_max: int = 2024) -> pd.DataFrame:
    """Filter by refYear inclusive."""
    out = df.copy()
    return out[(out["refYear"] >= year_min) & (out["refYear"] <= year_max)].copy()

def load_and_prepare_processed(
    processed_csv_path: str,
    year_min: int = 2010,
    year_max: int = 2024
) -> pd.DataFrame:
    """
    Main entry used by main.py:
    load processed -> standardize -> filter -> year filter
    """
    df = load_processed(processed_csv_path)
    df = standardize_types(df)
    df = filter_valid_trade(df)
    df = filter_years(df, year_min=year_min, year_max=year_max)
    return df

