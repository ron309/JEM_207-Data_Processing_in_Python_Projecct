# scripts/get_data.py
import os
from pathlib import Path
from datetime import datetime
from io import BytesIO

import pandas as pd
import requests
from dotenv import load_dotenv

import comtradeapicall as cd
import time

RAW_DIR = Path("data/raw/nat_gas_2000-2025_Trade_data")
PROCESSED_DIR = Path("data/processed")
PROCESSED_CSV = PROCESSED_DIR / "comtrade_natural_gas_clean.csv"

nat_gas_codes = ["271111", "271121"]
ng_codes_str = ",".join(nat_gas_codes)


def month_adder(year: int) -> str:
    """
    This function creates a string of YYYYMM values to call api on every month in this year.
    Input: one year you need to create year+month from.
    Output: string of 12 months of this year.
    """
    months = [f"{year}{m:02d}" for m in range(1, 13)]
    return ",".join(months)


def download_year(year: int, api_key: str) -> pd.DataFrame | None:
    """This function downloads monthly data for a year via UN Comtrade API with 3 retries."""
    max_retries = 3

    for attempt in range(max_retries):
        print(f"Attempt number {attempt+1} out of {max_retries}. ")
        try:
            data = cd.getFinalData(
                subscription_key=api_key,
                typeCode="C",
                freqCode="M",
                clCode="HS",
                period=month_adder(year),
                reporterCode=None,
                cmdCode=ng_codes_str,
                flowCode=None,
                partnerCode=None,
                partner2Code=None,
                customsCode=None,
                motCode=None,
                format_output="JSON",
            )

            if data is not None:
                return data

            print(f"[WARN] Call for year {year} returned None. Retrying in 7 seconds...")
            time.sleep(7)

        except Exception as e:
            print(f"[ERROR] Error of type: {e} for the year {year} for the attempt {attempt}. Retrying in 7 seconds... ")
            time.sleep(7)

    print(f"[FAIL] Could not download the data with {max_retries} attempts.")
    return None


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
        if df_year is None:
            print(f"[SKIP] No data for year {year}. Moving to the next year.")
            continue
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


def load_codebooks(cache_path: Path | None = None) -> dict:
    """
    Load Comtrade codebooks (flows, transport, qty, customs, and countries).
    These dfs are needed to map codes in in some columns of the main df to human-readable words.
    """
    if cache_path is None:
        cache_path = PROCESSED_DIR / "ComtradePlus_DataItems.xlsx"

    # if cache exists, use it; otherwise download once and save it
    if cache_path.exists():
        excel_codes = pd.ExcelFile(cache_path)
    else:
        response = requests.get("https://comtradeapi.un.org/files/v1/app/wiki/ComtradePlus_DataItems.xlsx")
        response.raise_for_status()
        if response.status_code == 200:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(response.content)
            excel_codes = pd.ExcelFile(BytesIO(response.content))
        else:
            raise RuntimeError(f"Failed to download codebooks. HTTP {response.status_code}")

    print(excel_codes.sheet_names)

    iso_codes = {
        "REF FLOWS": "flwCode",
        "REF MOT": "motCode",
        "REF QTY": "qtyCode",
        "REF CUSTOMS": "cstCode",
        "REF COUNTRIES": "geoAreaCode",
    }

    dfs_codes = {}

    for sheet_name, col_name in iso_codes.items():
        codes = pd.read_excel(excel_codes, sheet_name=sheet_name)
        codes.set_index(col_name, inplace=True)

        dfs_codes[col_name] = codes

    return dfs_codes


def map_codes(series_codes: pd.Series, df: pd.DataFrame, column=None) -> pd.Series:
    """
    Function that maps given codes to needed descriptions. Returns series.
    Inputs: series_codes: series (column of df that needed to be decoded);
    df: dataframe used to locate codes by index to get the needed description;
    column: if needed, the column name can be specified to return values from this column. By default, the function returns everything.
    """
    if column:
        return series_codes.apply(lambda x: df.loc[x, column] if x in df.index else pd.NA)
    else:
        return series_codes.apply(lambda x: df.loc[x] if x in df.index else pd.NA)


def build_clean_dataset(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    This function cleans and filters dataset to prepare for comfortable analysis, it:
    - selects cols_to_keep
    - maps codes to names (reporter/partner/flow/transport/etc.)
    - removes aggregates
    - removes flow subcategories that double-count
    - parses period
    - provides numeric conversions
    """
    cols_to_keep = [
        "period", "refYear", "refMonth", "reporterCode", "flowCode", "partnerCode",
        "classificationCode", "cmdCode", "customsCode", "motCode",
        "qtyUnitCode", "qty", "isQtyEstimated", "altQtyUnitCode", "altQty", "isAltQtyEstimated",
        "netWgt", "isNetWgtEstimated", "primaryValue", "isAggregate",
    ]
    df = df_raw[cols_to_keep].copy()

    # load codebooks
    dfs_codes = load_codebooks()

    to_map = {
        ("reporter", "reporterCode"): {"geoAreaDescription": dfs_codes["geoAreaCode"]},
        ("partner", "partnerCode"): {"geoAreaDescription": dfs_codes["geoAreaCode"]},
        ("customs_type", "customsCode"): {"cstDescription": dfs_codes["cstCode"]},
        ("transport", "motCode"): {"motName": dfs_codes["motCode"]},
        ("flow_detail", "flowCode"): {"flwDescription": dfs_codes["flwCode"]},
        ("qty_type", "qtyUnitCode"): {"qtyAbbr": dfs_codes["qtyCode"]},
        ("alt_qty_type", "altQtyUnitCode"): {"qtyDescription": dfs_codes["qtyCode"]},
    }

    for (col_name, codes_col), col_and_df in to_map.items():
        for source_col, source_df in col_and_df.items():
            df[col_name] = map_codes(series_codes=df[codes_col], df=source_df, column=source_col)

    df["cmdCode"] = df["cmdCode"].astype(str)
    df["type"] = df["cmdCode"].map({"271111": "liquefied", "271121": "gaseous"})  #adding types of gas from codes
    df["flow"] = df["flowCode"].astype(str).map({"M": "Import", "X": "Export"})  # adding category of flow: Import/Export

    df["period"] = pd.to_datetime(df["period"].astype(str), format="%Y%m")  # now we have it in date format to easily work with time series
    for column in ["primaryValue", "netWgt"]:  #everything to numeric
        df[column] = pd.to_numeric(df[column], errors="coerce")

    dfr = df[df["isAggregate"] == False].copy()  #Now we have dataframe that contains only reports without any type of aggregation
    dfr = dfr[(dfr["flow_detail"] == "Export") | (dfr["flow_detail"] == "Import")].copy()  # It appeared that sub-categories double actual values artificially, as for this df we want no aggregated data we filter this
    dfr = dfr.drop(columns=["flow_detail"])

    dfr = dfr[dfr["flow"].notna()].copy()
    dfr = dfr[dfr["type"].notna()].copy()

    return dfr


def main():
    load_dotenv()
    api_key = os.getenv("COMTRADE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing COMTRADE_API_KEY. Put it in a .env file.")

    ensure_dirs()

    #  Download raw yearly files (may take 90-150 minutes)
    download_all_years(api_key, start_year=2010, end_year=2025)

    # Conatenate raw files
    df_raw = concat_raw_years(start_year=2010, end_year=2025)
    print(f"[INFO] Raw concatenated rows: {len(df_raw):,}")

    # Clean
    df_clean = build_clean_dataset(df_raw)
    print(f"[INFO] Clean rows: {len(df_clean):,}")

    # Save processed dataset
    df_clean.to_csv(PROCESSED_CSV, index=False)
    print(f"[OK] Saved processed dataset: {PROCESSED_CSV}")


if __name__ == "__main__":
    main()
