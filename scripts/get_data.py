# scripts/get_data.py
import os
from pathlib import Path
from datetime import datetime
from io import BytesIO

import pandas as pd
import requests
from dotenv import load_dotenv

import comtradeapicall as cd  # keep your existing dependency

RAW_DIR = Path("data/raw/nat_gas_2000-2025_Trade_data")
PROCESSED_DIR = Path("data/processed")
PROCESSED_CSV = PROCESSED_DIR / "comtrade_natural_gas_clean.csv"

NAT_GAS_CODES = ["271111", "271121"]
NG_CODES_STR = ",".join(NAT_GAS_CODES)

def month_adder(year: int) -> str:
    months = [f"{year}{m:02d}" for m in range(1, 13)]
    return ",".join(months)

def download_year(year: int, api_key: str) -> pd.DataFrame:
    """Download monthly data for a year via UN Comtrade API."""
    data = cd.getFinalData(
        subscription_key=api_key,
        typeCode="C",
        freqCode="M",
        clCode="HS",
        period=month_adder(year),
        reporterCode=None,
        cmdCode=NG_CODES_STR,
        flowCode=None,
        partnerCode=None,
        partner2Code=None,
        customsCode=None,
        motCode=None,
        format_output="JSON",
    )
    return data

def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def download_all_years(api_key: str, start_year: int = 2000, end_year: int | None = None):
    """Download and store raw yearly files."""
    if end_year is None:
        end_year = datetime.now().year - 1  # last complete year

    for year in range(start_year, end_year + 1):
        out_path = RAW_DIR / f"{year}.csv"
        if out_path.exists():
            print(f"[SKIP] Raw file exists: {out_path}")
            continue

        print(f"[DL] Downloading year {year} ...")
        df_year = download_year(year, api_key)
        df_year.to_csv(out_path, index=False)
        print(f"[OK] Saved {out_path}")

def concat_raw_years(start_year: int = 2000, end_year: int | None = None) -> pd.DataFrame:
    """Concatenate all yearly raw CSV files."""
    if end_year is None:
        end_year = datetime.now().year - 1

    frames = []
    for year in range(start_year, end_year + 1):
        p = RAW_DIR / f"{year}.csv"
        if p.exists():
            frames.append(pd.read_csv(p))
        else:
            print(f"[WARN] Missing {p}")

    if not frames:
        raise FileNotFoundError("No raw yearly files found. Run download first.")

    return pd.concat(frames, ignore_index=True)

def load_codebooks() -> dict:
    """
    Load Comtrade codebooks (flows, transport, qty, customs, countries).
    Mirrors your existing approach (Excel from comtrade wiki endpoint).
    """
    url = "https://comtradeapi.un.org/files/v1/app/wiki/ComtradePlus_DataItems.xlsx"
    r = requests.get(url)
    r.raise_for_status()
    excel = pd.ExcelFile(BytesIO(r.content))

    codebooks = {
        "flow_codes": pd.read_excel(excel, sheet_name="REF FLOWS").set_index("flwCode"),
        "mot_codes": pd.read_excel(excel, sheet_name="REF MOT").set_index("motCode"),
        "qty_codes": pd.read_excel(excel, sheet_name="REF QTY").set_index("qtyCode"),
        "customs_codes": pd.read_excel(excel, sheet_name="REF CUSTOMS").set_index("cstCode"),
        "country_codes": pd.read_excel(excel, sheet_name="REF COUNTRIES").set_index("geoAreaCode"),
    }
    return codebooks

def build_clean_dataset(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    This is where you paste/adapt your cleaning logic:
    - select cols_to_keep
    - map codes to names (reporter/partner/flow/transport/etc.)
    - remove aggregates
    - remove flow subcategories that double-count
    - parse period
    - numeric conversions
    """
    cols_to_keep = [
        "period","refYear","refMonth","reporterCode","flowCode","partnerCode",
        "classificationCode","cmdCode","customsCode","motCode",
        "qtyUnitCode","qty","isQtyEstimated","altQtyUnitCode","altQty","isAltQtyEstimated",
        "netWgt","isNetWgtEstimated","primaryValue","isAggregate"
    ]
    df = df_raw[cols_to_keep].copy()

    # load codebooks
    cb = load_codebooks()
    country_codes = cb["country_codes"]
    flow_codes = cb["flow_codes"]
    mot_codes = cb["mot_codes"]
    qty_codes = cb["qty_codes"]
    customs_codes = cb["customs_codes"]

    # map codes 
    df["reporter"] = df["reporterCode"].apply(lambda x: country_codes.loc[x].values[0] if x in country_codes.index else None)
    df["partner"]  = df["partnerCode"].apply(lambda x: country_codes.loc[x].values[0] if x in country_codes.index else None)

    # flow + flow_detail
    df["flow"] = df["flowCode"].apply(lambda x: "Import" if "M" in str(x) else "Export" if "X" in str(x) else None)
    df["flow_detail"] = df["flowCode"].apply(lambda x: flow_codes.loc[x, "flwDescription"] if x in flow_codes.index else None)

    df["transport"] = df["motCode"].apply(lambda x: mot_codes.loc[x].values[0] if x in mot_codes.index else None)
    df["qty_type"] = df["qtyUnitCode"].apply(lambda x: qty_codes.loc[x, "qtyAbbr"] if x in qty_codes.index else None)
    df["alt_qty_type"] = df["altQtyUnitCode"].apply(lambda x: qty_codes.loc[x, "qtyDescription"] if x in qty_codes.index else None)
    df["customs_type"] = df["customsCode"].apply(lambda x: customs_codes.loc[x].values[0] if x in customs_codes.index else None)

    # types
    df["period"] = pd.to_datetime(df["period"].astype(str), format="%Y%m", errors="coerce")
    df["primaryValue"] = pd.to_numeric(df["primaryValue"], errors="coerce")
    df["netWgt"] = pd.to_numeric(df["netWgt"], errors="coerce")
    df["cmdCode"] = df["cmdCode"].astype(str)

    # remove aggregates + flow subcategories 
    dfr = df[df["isAggregate"] == False].copy()
    dfr = dfr[(dfr["flow_detail"] == "Export") | (dfr["flow_detail"] == "Import")].copy()
    dfr = dfr.drop(columns=["flow_detail"])

    return dfr

def main():
    load_dotenv()
    api_key = os.getenv("COMTRADE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing COMTRADE_API_KEY. Put it in a .env file.")

    ensure_dirs()

    #  Download raw yearly files (may take a long time)
    download_all_years(api_key, start_year=2000, end_year=2024)

    # Conatenate raw files
    df_raw = concat_raw_years(start_year=2000, end_year=2024)
    print(f"[INFO] Raw concatenated rows: {len(df_raw):,}")

    # Clean 
    df_clean = build_clean_dataset(df_raw)
    print(f"[INFO] Clean rows: {len(df_clean):,}")

    # Save processed dataset
    df_clean.to_csv(PROCESSED_CSV, index=False)
    print(f"[OK] Saved processed dataset: {PROCESSED_CSV}")

if __name__ == "__main__":
    main()
