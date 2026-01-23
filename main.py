# main.py
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # allows saving figures without a display

from src.Final_Data_Loading import load_and_prepare_processed
from src.analysis import run_analysis_bundle


# ---- Paths ----
PROCESSED_CSV = Path("data/processed/comtrade_natural_gas_clean.csv")

OUT_DIR = Path("data/processed")
FIG_DIR = OUT_DIR / "figures"
TAB_DIR = OUT_DIR / "tables"


def ensure_dirs() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TAB_DIR.mkdir(parents=True, exist_ok=True)


def save_figure(fig, filename: str) -> Path:
    path = FIG_DIR / filename
    fig.savefig(path, dpi=200, bbox_inches="tight")
    return path


def save_table(df, filename: str) -> Path:
    path = TAB_DIR / filename
    df.to_csv(path, index=False)
    return path


def main() -> int:
    ensure_dirs()

    # 1) Check processed CSV exists
    if not PROCESSED_CSV.exists():
        print(f"[ERROR] Missing processed dataset: {PROCESSED_CSV}")
        print("Run: python scripts/get_data.py")
        return 1

    # 2) Load once (shared dataframe for all analysis)
    df = load_and_prepare_processed(
        processed_csv_path=str(PROCESSED_CSV),
        year_min=2010,
        year_max=2024,
    )
    print(f"[OK] Loaded data: {len(df):,} rows | years 2010–2024")

    # 3) Your analysis bundle
    out = run_analysis_bundle(df)

    # 4) Save figures
    for fname, fig in out.get("figures", {}).items():
        p = save_figure(fig, fname)
        print(f"[FIG] {p}")
        try:
            import matplotlib.pyplot as plt
            plt.close(fig)
        except Exception:
            pass

    # 5) Save tables
    for fname, tdf in out.get("tables", {}).items():
        p = save_table(tdf, fname)
        print(f"[TAB] {p}")

    print("\n✅ Done. Outputs saved to:")
    print(f"   - {FIG_DIR}")
    print(f"   - {TAB_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
