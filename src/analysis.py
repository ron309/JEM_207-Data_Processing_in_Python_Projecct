# src/analysis.py
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from pathlib import Path


# Small helpers

def safe_filename_key(s: str) -> str:
    """
    Makes sure a string can be used as a safe file name or dictionary key.
    Converts to lowercase and replaces spaces, slashes, and dashes with underscores or hyphens.
    """
    return (
        s.lower()
        .replace(" ", "_")
        .replace("—", "-")
        .replace("–", "-")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
    )


def format_axis_billions(ax, axis="y", label=None, decimals=0):
    """
    Format an axis to display values in billions (USD / 1e9).
    """
    formatter = FuncFormatter(lambda v, pos: f"{v / 1e9:,.{decimals}f}")

    if axis == "y":
        ax.yaxis.set_major_formatter(formatter)
        ax.yaxis.get_offset_text().set_visible(False)
        if label is not None:
            ax.set_ylabel(label)

    elif axis == "x":
        ax.xaxis.set_major_formatter(formatter)
        ax.xaxis.get_offset_text().set_visible(False)
        if label is not None:
            ax.set_xlabel(label)


# To ensure unique storing of results
def add_table(tables: dict, filename: str, df: pd.DataFrame) -> None:
    """
    Adds a DataFrame to a dictionary while ensuring the filename key is unique.
    Raises a KeyError if the filename already exists in the dictionary.
    """
    if filename in tables:
        raise KeyError(f"Duplicate table key: {filename}")
    tables[filename] = df


def add_figure(figures: dict, filename: str, fig) -> None:
    """
    Essentially the sam, but for figures
    """
    if filename in figures:
        raise KeyError(f"Duplicate figure key: {filename}")
    figures[filename] = fig


# Annual trade (global)

def comp_annual_trade(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates trade data by year and product to calculate total imports and exports.
    Computes a net trade column (Export - Import) and returns a pivoted DataFrame.
    """
    annual_val = (
        df.groupby(["refYear", "flow", "product"], as_index=False)
          .agg(value_usd=("primaryValue", "sum"))
    )

    annual_val_piv = (
        annual_val.pivot_table(
            index=["refYear", "product"],
            columns="flow",
            values="value_usd",
            fill_value=0
        )
        .reset_index()
    )

    annual_val_piv["net_trade_usd"] = annual_val_piv.get("Export", 0) - annual_val_piv.get("Import", 0)
    return annual_val_piv


def plot_trade_by_product(annual_val_piv: pd.DataFrame, product: str, start_year: int = 2010, figsize=(10, 4)):
    """
    Generates a line plot showing Import and Export trends for a specific product.
    Filters data by the provided start year.
    """
    tmp = annual_val_piv[annual_val_piv["product"] == product].sort_values("refYear")
    tmp = tmp[tmp["refYear"] >= start_year]

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(tmp["refYear"], tmp.get("Import", 0), label="Import (USD)")
    ax.plot(tmp["refYear"], tmp.get("Export", 0), label="Export (USD)")
    ax.set_title(f"Global Trade Value — {product}")
    ax.set_xlabel("Year")
    format_axis_billions(ax, axis="y", label="USD (billions)")
    ax.legend()
    fig.tight_layout()
    return fig


# Continent mapping + continental analysis

def build_default_continent_map() -> dict[int, str]:
    """
    Creates a mapping of numeric country codes to their respective continents.
    Returns a dictionary where keys are integer codes and values are continent names.
    """
    Africa = [12, 24, 72, 108, 120, 132, 148, 178, 180, 204, 231, 262, 266, 270, 288,
              324, 384, 404, 454, 466, 504, 516, 562, 566, 646, 686, 710, 716, 729,
              768, 788, 800, 818]
    Americas = [32, 68, 76, 124, 152, 170, 188, 214, 218, 222, 320, 340, 484, 558, 591,
                600, 604, 740, 858, 862, 840]
    Asia = [31, 48, 50, 51, 96, 104, 116, 144, 156, 196, 275, 344, 360, 364, 376, 392,
            398, 400, 410, 414, 417, 458, 496, 512, 524, 586, 608, 634, 682, 699, 702,
            704, 764, 784, 792, 860, 887]
    Europe = [8, 40, 56, 100, 112, 191, 203, 208, 233, 246, 251, 276, 300, 348, 352, 372,
              380, 428, 440, 442, 470, 499, 528, 579, 616, 620, 642, 643, 688, 703, 705,
              724, 752, 757, 804, 807, 826]
    Oceania = [36, 554, 598]

    continent_map = {
        "Africa": Africa,
        "Americas": Americas,
        "Asia": Asia,
        "Europe": Europe,
        "Oceania": Oceania
    }
    return {code: cont for cont, codes in continent_map.items() for code in codes}


def add_continent(df: pd.DataFrame, reporter_to_continent: dict[int, str]) -> pd.DataFrame:
    """
    Appends a 'continent' column to the DataFrame based on the reporter country code.
    Maps the 'reporterCode' using the provided dictionary and returns a copy of the data.
    """
    out = df.copy()
    out["continent"] = out["reporterCode"].map(reporter_to_continent)
    return out


def compute_annual_continent(df_with_continent: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates trade value by year, continent, flow type, and product.
    Returns a summarized DataFrame with total USD values for each group.
    """
    return (
        df_with_continent.groupby(["refYear", "continent", "flow", "product"], as_index=False)
                         .agg(value_usd=("primaryValue", "sum"))
    )


def plot_continental_trade(annual_cont: pd.DataFrame, product: str, flow: str, start_year=2010, figsize=(10, 5)):
    tmp = annual_cont[
        (annual_cont["product"] == product) &
        (annual_cont["flow"] == flow) &
        (annual_cont["refYear"] >= start_year)
    ].copy()

    fig, ax = plt.subplots(figsize=figsize)
    for cont in sorted(tmp["continent"].dropna().unique()):
        sub = tmp[tmp["continent"] == cont].sort_values("refYear")
        ax.plot(sub["refYear"], sub["value_usd"], label=cont)

    ax.set_title(f"Continental {flow}s — {product} ({start_year} onward)")
    ax.set_xlabel("Year")
    format_axis_billions(ax, axis="y", label="USD (billions)")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_continent_shares_grid(annual_cont: pd.DataFrame, flows, products, figsize=(14, 8)):
    """
    Generates a grid of stacked area charts showing the percentage share of each continent.
    Displays relative continental contributions across multiple trade flows and products.
    """
    fig, axes = plt.subplots(len(flows), len(products), figsize=figsize, sharex=True, sharey=True)

    if len(flows) == 1 and len(products) == 1:
        axes = np.array([[axes]])
    elif len(flows) == 1:
        axes = np.array([axes])
    elif len(products) == 1:
        axes = np.array([[ax] for ax in axes])

    for i, flow in enumerate(flows):
        df_flow = annual_cont[annual_cont["flow"] == flow].copy()
        df_flow["total_value"] = df_flow.groupby(["refYear", "product"])["value_usd"].transform("sum")
        df_flow["share"] = np.where(df_flow["total_value"] > 0, df_flow["value_usd"] / df_flow["total_value"], 0.0)

        for j, prod in enumerate(products):
            ax = axes[i, j]
            tmp = (
                df_flow[df_flow["product"] == prod]
                .pivot(index="refYear", columns="continent", values="share")
                .fillna(0)
                .sort_index()
            )
            tmp.plot.area(ax=ax, legend=False)
            ax.set_title(f"{flow} — {prod}")
            ax.set_xlabel("Year")
            ax.set_ylabel("Share")

    handles, labels = axes[-1, -1].get_legend_handles_labels()
    fig.legend(handles, labels, title="Continent", loc="center right")
    fig.tight_layout(rect=[0, 0, 0.88, 1])
    return fig


#  Country-level analysis

def compute_annual_country(df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarizes trade data by year, product, flow, and reporter country.
    Returns a DataFrame with aggregated 'value_usd' for each unique country-product pairing.
    """
    return (
        df.groupby(["refYear", "product", "flow", "reporterCode", "reporter"], as_index=False)
          .agg(value_usd=("primaryValue", "sum"))
    )


def top_countries(annual_country: pd.DataFrame, year: int, product: str, flow: str, n=20) -> pd.DataFrame:
    """
    Retrieves the top N countries for a specific year, product, and trade flow.
    Calculates rankings based on total trade value and returns a sorted subset of the data.
    """
    tmp = annual_country[
        (annual_country["refYear"] == year) &
        (annual_country["product"] == product) &
        (annual_country["flow"] == flow)
    ].copy()

    tmp = tmp.sort_values("value_usd", ascending=False).head(n).copy()
    tmp["rank"] = range(1, len(tmp) + 1)
    return tmp[["rank", "reporter", "flow", "value_usd"]]


def plot_top_import_export_bars(annual_country: pd.DataFrame, product: str, years, n=10, figsize=(14, 10)):
    """
    Creates a grid of horizontal bar charts showing top importers and exporters for multiple years.
    Useful for comparing the leading global players.
    """
    fig, axes = plt.subplots(nrows=len(years), ncols=2, figsize=figsize, sharex=False)
    if len(years) == 1:
        axes = np.array([axes])

    for i, year in enumerate(years):
        top_imp = top_countries(annual_country, year=year, product=product, flow="Import", n=n).sort_values("value_usd")
        top_exp = top_countries(annual_country, year=year, product=product, flow="Export", n=n).sort_values("value_usd")

        axes[i, 0].barh(top_imp["reporter"], top_imp["value_usd"])
        axes[i, 0].set_title(f"Top {n} {product} Importers — {year}")
        format_axis_billions(axes[i, 0], axis="x", label="Trade value (USD, billions)")

        axes[i, 1].barh(top_exp["reporter"], top_exp["value_usd"])
        axes[i, 1].set_title(f"Top {n} {product} Exporters — {year}")
        format_axis_billions(axes[i, 1], axis="x", label="Trade value (USD, billions)")

    fig.tight_layout()
    return fig


def plot_same_countries_import_export(annual_country: pd.DataFrame, product: str, ref_year: int, compare_years, n=10, figsize=(14, 9)):
    """
    Visualizes trade balances by plotting Import vs Export bars for the same set of top countries.
    The country list is fixed based on top importers from a reference year to highlight relative shifts.
    """
    order = (
        annual_country[
            (annual_country["refYear"] == ref_year) &
            (annual_country["product"] == product) &
            (annual_country["flow"] == "Import")
        ]
        .sort_values("value_usd", ascending=False)
        .head(n)["reporter"]
        .tolist()
    )

    fig, axes = plt.subplots(2, len(compare_years), figsize=figsize, sharey=True)

    for r, flow in enumerate(["Import", "Export"]):
        tmp = annual_country[
            (annual_country["product"] == product) &
            (annual_country["flow"] == flow) &
            (annual_country["refYear"].isin(compare_years)) &
            (annual_country["reporter"].isin(order))
        ]

        mat = (
            tmp.pivot_table(index="reporter", columns="refYear", values="value_usd", fill_value=0)
               .reindex(order)
        )

        for c, y in enumerate(compare_years):
            ax = axes[r, c]
            vals = mat.get(y, pd.Series(0, index=mat.index))
            ax.barh(mat.index[::-1], vals.loc[mat.index[::-1]])
            ax.set_title(f"{flow}s — {y}")
            format_axis_billions(ax, axis="x", label="USD (billions)")
            if c == 0:
                ax.set_ylabel(f"{flow}\n(top {n} importers in {ref_year})")

    fig.suptitle(
        f"{product}: Imports (top) vs Exports (bottom) for SAME countries\n"
        f"Countries = Top {n} Importers in {ref_year} | Years = {compare_years[0]} vs {compare_years[1]}",
        y=0.98
    )
    fig.tight_layout()
    return fig


# Seasonality (monthly imports)

def prepare_monthly_imports(df: pd.DataFrame, value_col="primaryValue") -> pd.DataFrame:
    """
    Extracts and cleans monthly import data by parsing the 'period' column.
    Aggregates total USD value by year, month, and product for seasonality analysis.
    """
    out = df.copy()
    out["month"] = out["period"].dt.month

    out = out[out["flow"] == "Import"].copy()
    out[value_col] = pd.to_numeric(out[value_col], errors="coerce")
    out = out[out[value_col].notna() & (out[value_col] >= 0)].copy()

    monthly = (
        out.groupby(["refYear", "month", "product"], as_index=False)
           .agg(value_usd=(value_col, "sum"))
    )
    return monthly


def add_annual_share(monthly_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates what percentage of the yearly trade total occurred in each individual month.
    Adds 'share' and 'annual_total_usd' columns to the monthly DataFrame for normalized comparisons.
    """
    out = monthly_df.copy()
    out["annual_total_usd"] = out.groupby(["refYear", "product"])["value_usd"].transform("sum")
    out["share"] = np.where(out["annual_total_usd"] > 0, out["value_usd"] / out["annual_total_usd"], np.nan)
    return out


def make_heatmap_matrix(seasonality_df: pd.DataFrame, product: str, value_col="share", year_min=2010, year_max=None) -> pd.DataFrame:
    """
    Pivots seasonal trade data into a year-by-month matrix for a specific product.
    Filters by the specified year range and ensures all 12 months are represented as columns.
    """
    tmp = seasonality_df[seasonality_df["product"] == product].copy()
    tmp = tmp[tmp["refYear"] >= year_min]
    if year_max is not None:
        tmp = tmp[tmp["refYear"] <= year_max]

    mat = (
        tmp.pivot_table(index="refYear", columns="month", values=value_col, aggfunc="mean")
           .reindex(columns=range(1, 13))
           .sort_index()
    )
    return mat


def plot_heatmap(mat: pd.DataFrame, title: str, cmap="viridis", figsize=(12, 6)):
    fig, ax = plt.subplots(figsize=figsize)
    data = mat.to_numpy()
    im = ax.imshow(data, aspect="auto", interpolation="nearest", cmap=cmap)

    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel("Year")
    ax.set_xticks(np.arange(12))
    ax.set_xticklabels(list(range(1, 13)))
    ax.set_yticks(np.arange(len(mat.index)))
    ax.set_yticklabels(mat.index)

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Monthly share of annual imports")

    fig.tight_layout()
    return fig


def label_period(seasonality_df: pd.DataFrame, pre_end_year=2021, post_start_year=2022, post_end_year=2024) -> pd.DataFrame:
    """
    Categorizes years into 'Pre' and 'Post' groups based on defined year thresholds.
    This is useful for comparing historical trade norms against more recent trends.
    """
    out = seasonality_df.copy()

    out["period_group"] = None

    out.loc[out["refYear"] <= pre_end_year, "period_group"] = "Pre"
    out.loc[(out["refYear"] >= post_start_year) & (out["refYear"] <= post_end_year), "period_group"] = "Post"
    return out



def seasonal_profile(seasonality_df: pd.DataFrame, product: str, value_col="share") -> pd.DataFrame:
    """
    Calculates the average monthly trade share for 'Pre' and 'Post' periods.
    """
    tmp = seasonality_df[(seasonality_df["product"] == product) & (seasonality_df["period_group"].notna())].copy()
    prof = (
        tmp.groupby(["period_group", "month"], as_index=False)
           .agg(mean_share=(value_col, "mean"))
           .sort_values(["period_group", "month"])
    )
    return prof


def plot_seasonal_profile(profile_df: pd.DataFrame, title: str, figsize=(10, 4)):
    fig, ax = plt.subplots(figsize=figsize)
    for grp in ["Pre", "Post"]:
        sub = profile_df[profile_df["period_group"] == grp]
        ax.plot(sub["month"], sub["mean_share"], label=grp)

    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel("Average monthly share of annual imports")
    ax.set_xticks(range(1, 13))
    ax.legend()
    fig.tight_layout()
    return fig



# Regime analysis + scenarios

def assign_regime(year: int):
    """
    Categorizes a given year into a specific economic period: 'Pre-COVID', 'COVID', or 'Crisis'.
    Returns the regime name as a string or None if the year falls outside the 2010–2024 range.
    """
    if 2010 <= year <= 2019:
        return "Pre-COVID"
    elif 2020 <= year <= 2021:
        return "COVID"
    elif 2022 <= year <= 2024:
        return "Crisis"
    return None


def add_regime(seasonality: pd.DataFrame, annual_country: pd.DataFrame):
    """
    Applies the regime classification to both seasonality and annual country DataFrames.
    Returns copies of both inputs with a new 'regime' column added for grouped analysis.
    """
    seasonality2 = seasonality.copy()
    annual_country2 = annual_country.copy()
    seasonality2["regime"] = seasonality2["refYear"].apply(assign_regime).astype("object")
    annual_country2["regime"] = annual_country2["refYear"].apply(assign_regime).astype("object")
    return seasonality2, annual_country2


def regime_import_levels(annual_country: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the mean and median import values for each product within each economic regime.
    Useful for observing how total trade volumes shifted during global disruptions.
    """
    tmp = annual_country[(annual_country["flow"] == "Import") & (annual_country["regime"].notna())].copy()
    out = (
        tmp.groupby(["product", "regime"], as_index=False)
           .agg(mean_import_usd=("value_usd", "mean"),
                median_import_usd=("value_usd", "median"))
    )
    return out


def plot_regime_levels(regime_levels: pd.DataFrame, product: str, figsize=(7, 4)):
    tmp = regime_levels[regime_levels["product"] == product].copy()
    order = ["Pre-COVID", "COVID", "Crisis"]
    tmp["regime"] = pd.Categorical(tmp["regime"], categories=order, ordered=True)
    tmp = tmp.sort_values("regime")

    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(tmp["regime"].astype(str), tmp["mean_import_usd"])
    ax.set_title(f"Average Annual Imports by Regime — {product}")
    ax.set_xlabel("Regime")
    format_axis_billions(ax, axis="y", label="Mean annual imports (USD, billions)")
    fig.tight_layout()
    return fig


def regime_winter_intensity(seasonality: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates trade shares to compare 'Winter' (Nov–Mar) vs 'Non-winter' intensity by regime.
    Helps identify if seasonal dependency (like heating demand) has intensified during crisis periods.
    """
    tmp = seasonality[(seasonality["regime"].notna()) & (seasonality["share"].notna())].copy()
    tmp["season"] = np.where(tmp["month"].isin([11, 12, 1, 2, 3]), "Winter", "Non-winter")

    out = (
        tmp.groupby(["product", "regime", "season"], as_index=False)
           .agg(avg_monthly_share=("share", "mean"))
    )
    return out


def plot_winter_vs_nonwinter(winter_tbl: pd.DataFrame, product: str, figsize=(7, 4)):
    """
    Plots the divergence between winter and non-winter trade shares across different regimes.
    Visualizes whether seasonal volatility is increasing or stabilizing over time.
    """
    tmp = winter_tbl[winter_tbl["product"] == product].copy()
    order = ["Pre-COVID", "COVID", "Crisis"]
    tmp["regime"] = pd.Categorical(tmp["regime"], categories=order, ordered=True)
    tmp = tmp.sort_values("regime")
    p = tmp.pivot(index="regime", columns="season", values="avg_monthly_share").reindex(order)

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(p.index.astype(str), p["Winter"], label="Winter (Nov–Mar)")
    ax.plot(p.index.astype(str), p["Non-winter"], label="Non-winter (Apr–Oct)")
    ax.set_title(f"Seasonal Intensity by Regime — {product}")
    ax.set_xlabel("Regime")
    ax.set_ylabel("Avg monthly share of annual imports")
    ax.legend()
    fig.tight_layout()
    return fig


def compute_baseline_seasonal_profile(seasonality_df: pd.DataFrame, product: str, regime="Crisis") -> pd.DataFrame:
    """
    Generates a normalized average monthly share for a specific product and regime.
    This serves as the 'standard' profile used for applying stress tests or diversifications scenarios.
    """
    tmp = seasonality_df[(seasonality_df["product"] == product) & (seasonality_df["regime"] == regime)].copy()
    baseline = (
        tmp.groupby("month", as_index=False)
           .agg(mean_share=("share", "mean"))
           .sort_values("month")
    )
    baseline["mean_share"] = baseline["mean_share"] / baseline["mean_share"].sum()
    return baseline


def plot_seasonal_profiles(dfs, labels, title, figsize=(9, 4)):
    fig, ax = plt.subplots(figsize=figsize)
    for df, label in zip(dfs, labels):
        ax.plot(df["month"], df["mean_share"], marker="o", label=label)
    ax.set_xlabel("Month")
    ax.set_ylabel("Share of annual imports")
    ax.set_xticks(range(1, 13))
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    return fig


def apply_winter_stress(baseline_df: pd.DataFrame, stress_pct=0.20, winter_months=frozenset({11, 12, 1, 2})):
    """
    Simulates a supply shock by increasing the trade share for specific winter months.
    Re-normalizes the total annual share to 1.0 to show how peaks would shift under pressure.
    """
    stressed = baseline_df.copy()
    is_winter = stressed["month"].isin(list(winter_months))
    stressed.loc[is_winter, "mean_share"] *= (1 + stress_pct)
    stressed["mean_share"] = stressed["mean_share"] / stressed["mean_share"].sum()
    return stressed


def plot_winter_stress_side_by_side(baseline_lng, stress_lng, baseline_gas, stress_gas, figsize=(14, 4)):
    """
    Compares baseline and winter-stressed profiles for both LNG and Gaseous Natural Gas.
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize, sharey=True)

    axes[0].plot(baseline_lng["month"], baseline_lng["mean_share"], marker="o", label="Baseline")
    axes[0].plot(stress_lng["month"], stress_lng["mean_share"], marker="o", linestyle="--", label="Winter-stress")
    axes[0].set_title("LNG (271111)")
    axes[0].set_xlabel("Month")
    axes[0].set_ylabel("Share of annual imports")
    axes[0].set_xticks(range(1, 13))
    axes[0].legend()

    axes[1].plot(baseline_gas["month"], baseline_gas["mean_share"], marker="o", label="Baseline")
    axes[1].plot(stress_gas["month"], stress_gas["mean_share"], marker="o", linestyle="--", label="Winter-stress")
    axes[1].set_title("Gaseous NG (271121)")
    axes[1].set_xlabel("Month")
    axes[1].set_xticks(range(1, 13))
    axes[1].legend()

    fig.suptitle("Baseline vs Winter-Stress Seasonal Profiles")
    fig.tight_layout()
    return fig


def apply_diversification(baseline_df: pd.DataFrame, alpha=0.30):
    """
    Trying to simulate trade smoothing by blending the baseline profile with a uniform distribution (flat 1/12 share).
    The 'alpha' parameter controls the strength of the smoothing effect toward a perfectly flat profile.
    """
    diversified = baseline_df.copy()
    uniform_share = 1.0 / 12.0
    diversified["mean_share"] = (1 - alpha) * diversified["mean_share"] + alpha * uniform_share
    diversified["mean_share"] = diversified["mean_share"] / diversified["mean_share"].sum()
    return diversified


def plot_diversification_side_by_side(baseline_lng, div_lng, baseline_gas, div_gas, figsize=(14, 4)):
    fig, axes = plt.subplots(1, 2, figsize=figsize, sharey=True)

    axes[0].plot(baseline_lng["month"], baseline_lng["mean_share"], marker="o", label="Baseline")
    axes[0].plot(div_lng["month"], div_lng["mean_share"], marker="o", linestyle="--", label="Diversification")
    axes[0].set_title("LNG (271111)")
    axes[0].set_xlabel("Month")
    axes[0].set_ylabel("Share of annual imports")
    axes[0].set_xticks(range(1, 13))
    axes[0].legend()

    axes[1].plot(baseline_gas["month"], baseline_gas["mean_share"], marker="o", label="Baseline")
    axes[1].plot(div_gas["month"], div_gas["mean_share"], marker="o", linestyle="--", label="Diversification")
    axes[1].set_title("Gaseous NG (271121)")
    axes[1].set_xlabel("Month")
    axes[1].set_xticks(range(1, 13))
    axes[1].legend()

    fig.suptitle("Baseline vs Diversification Seasonal Profiles")
    fig.tight_layout()
    return fig



# Diagnostic (seasonal naive)

def seasonal_naive_forecast(series: pd.Series) -> pd.Series:
    """
    Implements a simple seasonal naive model by shifting data by a 12-month lag.
    Used as a baseline to see how well past seasonal patterns predict current trade values.
    Note: The intention is not to repliate a ML model, but rather to prove the structural break.
    """
    return series.shift(12)


def plot_diagnostic_seasonal_forecast(monthly_imports: pd.DataFrame, product: str, figsize=(12, 5)):
    s = (
        monthly_imports[monthly_imports["product"] == product]
        .set_index("period")["value_usd"]
        .sort_index()
    )
    pred = seasonal_naive_forecast(s)

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(s.index, s.values, label="Actual", linewidth=2)
    ax.plot(pred.index, pred.values, label="Seasonal naive (t-12)", linestyle="--")

    ax.axvline(pd.to_datetime("2020-01-01"), linestyle=":", alpha=0.7)
    ax.axvline(pd.to_datetime("2022-01-01"), linestyle=":", alpha=0.7)

    ax.set_title(f"Diagnostic Seasonal Forecast — {product} Imports")
    format_axis_billions(ax, axis="y", label="Monthly imports (USD, billions)")
    ax.set_xlabel("Year")
    ax.legend()
    fig.tight_layout()
    return fig


#  Required combined functions

def run_analysis_bundle(df: pd.DataFrame) -> dict:
    """
    Returns:
      {"tables": {<filename.csv>: DataFrame, ...},
       "figures": {<filename.png>: matplotlib Figure, ...}}

    Assumes df has already been prepared by load_and_prepare_processed():
      - standardized dtypes
      - valid trade filtered
      - year filtered
      - product column exists
    """
    tables: dict[str, pd.DataFrame] = {}
    figures: dict[str, plt.Figure] = {}

    #  Global annual trade
    annual_val_piv = comp_annual_trade(df)
    add_table(tables, "annual_trade_global_by_product.csv", annual_val_piv)

    for prod in ["LNG (271111)", "Gaseous NG (271121)"]:
        add_figure(
            figures,
            f"global_trade_value_{safe_filename_key(prod)}.png",
            plot_trade_by_product(annual_val_piv, product=prod, start_year=2010),
        )

    #  Continent analysis
    reporter_to_continent = build_default_continent_map()
    df_cont = add_continent(df, reporter_to_continent)

    cov = df_cont["continent"].value_counts(dropna=False).rename_axis("continent").reset_index(name="rows")
    add_table(tables, "continent_coverage_counts.csv", cov)

    annual_cont = compute_annual_continent(df_cont)
    add_table(tables, "annual_continent_trade.csv", annual_cont)

    for prod in ["LNG (271111)", "Gaseous NG (271121)"]:
        add_figure(
            figures,
            f"continental_imports_{safe_filename_key(prod)}.png",
            plot_continental_trade(annual_cont, product=prod, flow="Import", start_year=2010),
        )
        add_figure(
            figures,
            f"continental_exports_{safe_filename_key(prod)}.png",
            plot_continental_trade(annual_cont, product=prod, flow="Export", start_year=2010),
        )

    add_figure(
        figures,
        "continent_shares_grid_import_export.png",
        plot_continent_shares_grid(
            annual_cont,
            flows=["Import", "Export"],
            products=["LNG (271111)", "Gaseous NG (271121)"],
        ),
    )

    #  Country level
    annual_country = compute_annual_country(df_cont)
    add_table(tables, "annual_country_trade.csv", annual_country)

    years = [2020, 2024]
    add_figure(
        figures,
        "top_countries_import_export_lng_2020_2024.png",
        plot_top_import_export_bars(annual_country, product="LNG (271111)", years=years, n=10),
    )
    add_figure(
        figures,
        "top_countries_import_export_gas_2020_2024.png",
        plot_top_import_export_bars(annual_country, product="Gaseous NG (271121)", years=years, n=10),
    )

    ref_year = 2024
    compare_years = [2019, 2024]
    add_figure(
        figures,
        "same_countries_import_export_gas_top10importers_2024_2019vs2024.png",
        plot_same_countries_import_export(
            annual_country,
            product="Gaseous NG (271121)",
            ref_year=ref_year,
            compare_years=compare_years,
            n=10,
        ),
    )
    add_figure(
        figures,
        "same_countries_import_export_lng_top10importers_2024_2019vs2024.png",
        plot_same_countries_import_export(
            annual_country,
            product="LNG (271111)",
            ref_year=ref_year,
            compare_years=compare_years,
            n=10,
        ),
    )

    #  Seasonality (imports)
    monthly = prepare_monthly_imports(df_cont, value_col="primaryValue")
    seasonality = add_annual_share(monthly)
    add_table(tables, "monthly_imports_by_year_month_product.csv", monthly)
    add_table(tables, "seasonality_monthly_share.csv", seasonality)

    for prod in ["LNG (271111)", "Gaseous NG (271121)"]:
        mat = make_heatmap_matrix(seasonality, product=prod, value_col="share", year_min=2010)
        add_table(
            tables,
            f"heatmap_matrix_{safe_filename_key(prod)}.csv",
            mat.reset_index().rename(columns={"refYear": "year"}),
        )
        add_figure(
            figures,
            f"seasonality_heatmap_{safe_filename_key(prod)}.png",
            plot_heatmap(mat, title=f"Seasonality Heatmap (Imports) — {prod} | Monthly share of annual imports"),
        )

    seasonality_pp = label_period(seasonality, pre_end_year=2021, post_start_year=2022, post_end_year=2024)
    add_table(tables, "seasonality_with_pre_post_flag.csv", seasonality_pp)

    for prod in ["LNG (271111)", "Gaseous NG (271121)"]:
        prof = seasonal_profile(seasonality_pp, product=prod, value_col="share")
        add_table(tables, f"seasonal_profile_pre_post_{safe_filename_key(prod)}.csv", prof)
        add_figure(
            figures,
            f"seasonal_profile_pre_post_{safe_filename_key(prod)}.png",
            plot_seasonal_profile(
                prof,
                title=f"Average Seasonal Profile (Imports) — {prod}\nPre-2022 (2010–2021) vs Post-2022 (2022–2024)",
            ),
        )

    #  Regime + scenarios
    seasonality_r, annual_country_r = add_regime(seasonality, annual_country)
    add_table(tables, "annual_country_trade_with_regime.csv", annual_country_r)
    add_table(tables, "seasonality_with_regime.csv", seasonality_r)

    regime_levels = regime_import_levels(annual_country_r)
    add_table(tables, "regime_import_levels.csv", regime_levels)

    for prod in ["LNG (271111)", "Gaseous NG (271121)"]:
        add_figure(
            figures,
            f"regime_levels_{safe_filename_key(prod)}.png",
            plot_regime_levels(regime_levels, product=prod),
        )

    # winter_tbl = regime_winter_intensity(seasonality_r)
    # add_table(tables, "winter_vs_nonwinter_by_regime.csv", winter_tbl)

    # for prod in ["LNG (271111)", "Gaseous NG (271121)"]:
    #     add_figure(
    #         figures,
    #         f"winter_vs_nonwinter_{safe_filename_key(prod)}.png",
    #         plot_winter_vs_nonwinter(winter_tbl, product=prod),
    #     )

    baseline_lng = compute_baseline_seasonal_profile(seasonality_r, product="LNG (271111)", regime="Crisis")
    baseline_gas = compute_baseline_seasonal_profile(seasonality_r, product="Gaseous NG (271121)", regime="Crisis")
    add_table(tables, "baseline_seasonal_profile_crisis_lng.csv", baseline_lng)
    add_table(tables, "baseline_seasonal_profile_crisis_gas.csv", baseline_gas)

    add_figure(
        figures,
        "baseline_seasonal_profiles_crisis_lng_vs_gas.png",
        plot_seasonal_profiles(
            dfs=[baseline_lng, baseline_gas],
            labels=["LNG (271111)", "Gaseous NG (271121)"],
            title="Baseline Seasonal Profiles (Crisis Regime, 2022–2024)",
        ),
    )

    stress_lng = apply_winter_stress(baseline_lng, stress_pct=0.20)
    stress_gas = apply_winter_stress(baseline_gas, stress_pct=0.20)
    add_table(tables, "winter_stress_profile_lng.csv", stress_lng)
    add_table(tables, "winter_stress_profile_gas.csv", stress_gas)
    add_figure(
        figures,
        "winter_stress_baseline_vs_stressed_side_by_side.png",
        plot_winter_stress_side_by_side(baseline_lng, stress_lng, baseline_gas, stress_gas),
    )

    div_lng = apply_diversification(baseline_lng, alpha=0.30)
    div_gas = apply_diversification(baseline_gas, alpha=0.30)
    add_table(tables, "diversification_profile_lng.csv", div_lng)
    add_table(tables, "diversification_profile_gas.csv", div_gas)
    add_figure(
        figures,
        "diversification_baseline_vs_diversified_side_by_side.png",
        plot_diversification_side_by_side(baseline_lng, div_lng, baseline_gas, div_gas),
    )

    #  Diagnostic seasonal naive
    monthly_imports = (
        df_cont[df_cont["flow"] == "Import"]
        .groupby(["period", "product"], as_index=False)
        .agg(value_usd=("primaryValue", "sum"))
        .sort_values("period")
    )
    add_table(tables, "monthly_imports_global_timeseries.csv", monthly_imports)

    add_figure(
        figures,
        "diagnostic_seasonal_naive_forecast_lng.png",
        plot_diagnostic_seasonal_forecast(monthly_imports, product="LNG (271111)"),
    )
    add_figure(
        figures,
        "diagnostic_seasonal_naive_forecast_gas.png",
        plot_diagnostic_seasonal_forecast(monthly_imports, product="Gaseous NG (271121)"),
    )

    return {"tables": tables, "figures": figures}



def save_analysis_outputs(results: dict, tables_dir: str | Path, figures_dir: str | Path, figure_dpi: int = 200,) -> None:
    """
    Saves all tables and figures produced by run_analysis_bundle() and
    safely closes all matplotlib figures to prevent memory leaks.

    Parameters
    ----------
    results : dict
        Output of run_analysis_bundle()
    tables_dir : str or Path
        Directory where CSV tables will be written
    figures_dir : str or Path
        Directory where figures will be written
    figure_dpi : int
        DPI for saved figures
    """
    tables_dir = Path(tables_dir)
    figures_dir = Path(figures_dir)

    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Save tables
    for name, df in results.get("tables", {}).items():
        df.to_csv(tables_dir / name, index=False)

    # Save figures and CLOSE them
    for name, fig in results.get("figures", {}).items():
        fig.savefig(figures_dir / name, dpi=figure_dpi, bbox_inches="tight")
        plt.close(fig)


def close_figures(figures: dict[str, plt.Figure]) -> None:
    """
    Closes all matplotlib figures in a dictionary.
    Useful if figures are generated but not saved.
    """
    for fig in figures.values():
        plt.close(fig)
