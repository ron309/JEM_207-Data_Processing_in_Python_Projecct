from __future__ import annotations
import streamlit as st

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from pathlib import Path
import matplotlib
matplotlib.use("Agg") 

from src.Final_Data_Loading import load_and_prepare_processed
import src.network as nt
import src.analysis as al
import prophet

############
# To run the app: after cloning the rep and setting up run:     pip install -r app_requirements.txt
# Then run:     streamlit run app.py
############


#Functions

def top_year_routes(df: pd.DataFrame, year: int, measure: str) -> pd.DataFrame:
    """
    This function returns a df with top trade routes for a given measure (dollars or kilograms) starting from a given year.
    """
    top_transport = df[
        (df["refYear"]  == year)
        & (df["flow"] == "Import")
    ].groupby(["refYear", "type", "transport"])[measure].sum()/10**9
    top_transport = pd.DataFrame(top_transport)
    top_transport = top_transport.rename(columns={measure: f"{measure}, billions"})
    top_transport = top_transport.groupby(["refYear", "type"])[f"{measure}, billions"].nlargest(4)
    top_transport = top_transport.droplevel([0, 1]).reset_index()
    return top_transport

def compute_annual_country(df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarizes trade data by year, product, flow, and reporter country.
    Returns a DataFrame with aggregated 'value_usd' for each unique country-product pairing.
    """
    return (
        df.groupby(["refYear", "type", "flow", "reporterCode", "reporter"], as_index=False)
          .agg(value_usd=("primaryValue", "sum"))
    )

def compute_mirror_exports(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mirror exports = partner-reported imports grouped by partner (exporter).
    Fixes exporter non-reporting (e.g., Russia).
    """
    mirror = (
        df[df["flow"] == "Import"]
        .groupby(["refYear", "type", "partnerCode", "partner"], as_index=False)
        .agg(value_usd=("primaryValue", "sum"))
        .rename(columns={"partnerCode": "reporterCode", "partner": "reporter"})
    )
    mirror["flow"] = "Export"
    return mirror


def top_countries(annual_country: pd.DataFrame, year: int, gas_type: str, flow: str, n=20) -> pd.DataFrame:
    """
    Retrieves the top N countries for a specific year, product, and trade flow.
    Calculates rankings based on total trade value and returns a sorted subset of the data.
    """
    tmp = annual_country[
        (annual_country["refYear"] == year) &
        (annual_country["type"] == gas_type) &
        (annual_country["flow"] == flow)
    ].copy()

    tmp = tmp.sort_values("value_usd", ascending=False).head(n).copy()
    tmp["rank"] = range(1, len(tmp) + 1)
    return tmp[["rank", "reporter", "flow", "value_usd"]]


def plot_top_import_export_bars(annual_country: pd.DataFrame, gas_type: str, years, n=10, figsize=(14, 10)):
    """
    Creates a grid of horizontal bar charts showing top importers and exporters for multiple years.
    Useful for comparing the leading global players.
    """
    fig, axes = plt.subplots(nrows=len(years), ncols=2, figsize=figsize, sharex=False)
    if len(years) == 1:
        axes = np.array([axes])

    for i, year in enumerate(years):
        top_imp = top_countries(annual_country, year=year, gas_type=gas_type, flow="Import", n=n).sort_values("value_usd")
        top_exp = top_countries(annual_country, year=year, gas_type=gas_type, flow="Export", n=n).sort_values("value_usd")

        axes[i, 0].barh(top_imp["reporter"], top_imp["value_usd"])
        axes[i, 0].set_title(f"Top {n} {gas_type} Importers — {year}")
        al.format_axis_billions(axes[i, 0], axis="x", label="Trade value (USD, billions)")

        axes[i, 1].barh(top_exp["reporter"], top_exp["value_usd"])
        axes[i, 1].set_title(f"Top {n} {gas_type} Exporters — {year}")
        al.format_axis_billions(axes[i, 1], axis="x", label="Trade value (USD, billions)")

    fig.tight_layout()
    return fig


def flow_data(df: pd.DataFrame, country: str, flow: str, gas_type: str) -> pd.DataFrame:
    "Returns a df with required trade flows for a given gas type to the inserted country."

    if flow == "Import":
        country_data = df[( (df["reporter"] == country) & (df["type"] == gas_type) & (df["flow"] == "Import") )]
        if country_data.empty: 
            country_data = df[(df["partner"] == country) & (df["type"] == gas_type) & (df["flow"] == "Export")]
    elif flow == "Export":
        country_data = df[(df["partner"] == country) & (df["type"] == gas_type) & (df["flow"] == "Import")]
        if country_data.empty: 
            country_data = df[(df["partner"] == country) & (df["type"] == gas_type) & (df["flow"] == "Export")]

    return country_data


def country_plot(df_doll: pd.DataFrame, df_kg: pd.DataFrame, country: str, flow: str) -> plt.Figure | None:
    """
    This function plots 4 graphs of evolution of trade for different transport routes 
    for 2 types of trade and 2 types of measures for a given country.
    """
    dfs_cols = {"primaryValue": df_doll, "netWgt": df_kg}
    gas_types = list(df_kg["type"].dropna().unique())
    countries_list = set(list(dfr.partner.unique()) + list(dfr.reporter.unique()))
    countries_list = list(countries_list)

    if country not in countries_list:
        return f"[WARN] '{country}' not found in reporter list."

    fig, axes = plt.subplots(2, 2, figsize=(20, 11))
    axes_flat = axes.flatten()
    axes_ind = 0

    for gas_type in gas_types:
        for col, dfx in dfs_cols.items():

            country_data = flow_data(df=dfx, country=country, flow=flow, gas_type=gas_type)

            if country_data.empty:
                return f"No trade information for {country}"
            ax = axes_flat[axes_ind]
            sns.pointplot(
                data=country_data,
                y=nt.to_billions(dfx, col),
                x="refYear",
                hue="transport",
                errorbar=None,
                ax=ax,
                estimator="sum",
            )
            ax.set_ylabel(f"{col}, billions", size=13)
            ax.set_xlabel("Year", size=12)
            ax.legend(ncol=3, loc="upper left")
            ax.set_title(f"Total {flow} for {country}, {gas_type} gas, {col}", size=12)
            ax.grid(alpha=0.5)
            axes_ind += 1

    plt.tight_layout()
    plt.close(fig)
    return fig

def main_partners(df_doll: pd.DataFrame, country: str, flow: str, year: int, gas_type: str):
    "Returns a df for up to 5 top (by dollar trade) partners of the country in thea given year for a given flow"

    countries_list = set(list(dfr.partner.unique()) + list(dfr.reporter.unique()))
    countries_list = list(countries_list)

    if country not in countries_list:
        return f"[WARN] '{country}' not found in reporter list."
    dfx = df_doll[(df_doll.refYear == year)]

    country_data = flow_data(df=dfx, country=country, flow=flow, gas_type=gas_type)
        
    if country_data.empty:
        return f"No trade information for {country}"
    country_pars = country_data.groupby(["reporter", "partner"])[["primaryValue", "netWgt"]].sum().reset_index()
    reporters = country_pars[country_pars.partner == country][["reporter", "primaryValue", "netWgt"]]
    partners = country_pars[country_pars.reporter == country][["partner", "primaryValue", "netWgt"]]

    reporters.columns = ["partner", "primaryValue", "netWgt"]
    partner_trades = pd.concat([reporters, partners], ignore_index=True)
    main_partners = partner_trades.groupby("partner")[["primaryValue", "netWgt"]].sum().reset_index()
    main_partners.set_index("partner", inplace=True)

    main_partners["primaryValue, billions ($)"] = nt.to_billions(main_partners, "primaryValue")
    main_partners["netWgt, billions (kg)"] = nt.to_billions(main_partners, "netWgt")
    main_partners = main_partners.loc[main_partners["primaryValue"].nlargest(3).index, 
                                      ["primaryValue, billions ($)", "netWgt, billions (kg)"] ]
    return main_partners
                
            

def prepare_monthly_imports(df: pd.DataFrame, year: int, value_col="primaryValue") -> pd.DataFrame:
    """
    Extracts and cleans monthly import data by parsing the 'period' column.
    Aggregates total USD value by year, month, and product for seasonality analysis.
    """
    out = df.copy()
    out["month"] = out["period"].dt.month
    out = out[out.refYear == year]
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
    out["share"] = np.where(out["annual_total_usd"] > 0, (out["value_usd"] / out["annual_total_usd"])*100, np.nan)
    return out


def plot_annual_shares(annual_shares_df: pd.DataFrame, measure: str, year: int) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data = annual_shares_df, x = "month", y="share", hue="product")
    ax.set_title(f"Annual share of each month in the year trade by {measure}, {year}", size=15)
    ax.set_ylabel("share, %")
    ax.set_xlabel("Month, number")
    ax.grid(True, alpha=0.5)
    plt.close(fig)
    return fig


def monthly_prices(df: pd.DataFrame, gas_type: str, max_year: int) -> pd.DataFrame:
    "Creates a df with prices in each month of each year of the given df"

    seas_df = df[(df.refYear <= max_year) & (df.type == gas_type)].copy()

    seas_df = seas_df.groupby(["refYear", "refMonth"])[["primaryValue", "netWgt"]].sum().reset_index()


    seas_df["price"] = np.where(seas_df.netWgt > 0, seas_df.primaryValue / seas_df.netWgt, np.nan)

    total_years = seas_df.groupby("refYear").price.transform("mean").reset_index()
    seas_df["year_price"] = total_years["price"]
    seas_df["seasonal_index"] = seas_df.price / seas_df.year_price

    return seas_df


def plot_seasonal_prices(monthly_prices: pd.DataFrame, gas_type: str) -> plt.Figure:
    """Plotes average seasonal index of a given df. 
    The higher index - the higher price for this month (where 1 is yearly average)"""

    seasonal_prices = monthly_prices.groupby("refMonth")["seasonal_index"].agg("mean").reset_index()
    fig, ax = plt.subplots(figsize=(12,6))
    sns.pointplot(data = seasonal_prices, x = "refMonth", y = "seasonal_index", ax=ax)
    ax.set_title(f"Seasonal prices index for {gas_type} gas")
    ax.set_xlabel("Month, number")
    ax.set_ylabel("Seasonal prices index")
    ax.grid(True)
    return fig


def compare_seasonal_prof(monthly_prices: pd.DataFrame, gas_type: str, year: int) -> plt.Figure:
    seasonal_prices = monthly_prices.groupby("refMonth")["seasonal_index"].agg("mean").reset_index()
    year_prices = monthly_prices[monthly_prices.refYear == year].copy()
    year_prices.rename(columns={"seasonal_index": f"seasonal_index_{year}"}, inplace=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.pointplot(data = seasonal_prices, x = "refMonth", y = "seasonal_index", ax=ax)
    sns.pointplot(data = year_prices, x = "refMonth", y = f"seasonal_index_{year}", ax=ax)

    ax.set_title(f"Comparison of {gas_type} gas seasonal profile and seasonal index for {year}")
    ax.set_xlabel("Month")
    ax.set_ylabel("Seasonal index")
    ax.grid(True)
    plt.legend([f"seasonal_index_{year}", "Seasonal index"])
    plt.close(fig)
    return fig


def train_prophet(monthly_prices: pd.DataFrame, changepoint_value = 0.05, seasonality_value = 4.85) -> list:
    
    df_prophet = monthly_prices.copy()
    df_prophet['ds'] = pd.to_datetime(
        df_prophet['refYear'].astype(str) + '-' + df_prophet['refMonth'].astype(str) + '-01'
    ) #ds are dates for prophet
    # what we want to predict should be renamed to "y" for prophet
    df_prophet = df_prophet.rename(columns={'price': 'y'})[['ds', 'y']]
    # Crisis time breaks the model so it must be deleted
    crisis_mask = (df_prophet['ds'] >= '2022-01-01') & (df_prophet['ds'] <= '2023-01-01')
    df_prophet.loc[crisis_mask, 'y'] = None  # Prophet ignores None values during fit
    model = prophet.Prophet(seasonality_mode='additive', 
                    changepoint_prior_scale=changepoint_value, 
                    seasonality_prior_scale=seasonality_value,
                    yearly_seasonality = False)

    model.add_seasonality(name="yearly seasonality", period=365.25, fourier_order = 3)
    model.fit(df_prophet)


    future = model.make_future_dataframe(periods=12, freq='MS') #MS - month start

    forecast = model.predict(future)

    fig1 = model.plot(forecast)
    plt.title("Seasonal model prediction of prices")
    plt.legend(["Actual prices", "Model's prediction", "Model's prediction range"])
    plt.xlabel("Period, years")
    plt.ylabel("Price, dollars per kilogram")
    plt.close(fig1)

    fig2 = model.plot_components(forecast)
    axes = fig2.get_axes()

    axes[0].set_title("Trend over the years")
    axes[0].set_xlabel("Period, years")
    axes[0].set_ylabel("Price")

    axes[1].set_title("Seasonality over the year")
    axes[1].set_xlabel("Period, months")
    axes[1].set_ylabel("Deviation")
    plt.tight_layout()
    plt.close(fig2)

    return [model, fig1, fig2]

def check_model(model):
    """This function tests how well the model predicts 12 months ahead using past data.
    Returns Mean Absolute Percentage Error - the lower, the better. THe function was used in loops to tune hyperparameters."""
    df_cv = prophet.diagnostics.cross_validation(model=model, initial='730 days', period='180 days', horizon='365 days')
    df_p = prophet.diagnostics.performance_metrics(df_cv)
    return df_p['mape'].mean()





#calling everything




PROCESSED_CSV = Path("data/processed/comtrade_natural_gas_clean.csv")

dfr = load_and_prepare_processed(
    processed_csv_path=str(PROCESSED_CSV),
    year_min=2010,
    year_max=2025,
)
dfr_kg = nt.get_df_for_kg(dfr)
graphs = nt.build_graphs(df_dol=dfr, df_kg=dfr_kg)
gas_types = list(dfr_kg.type.unique())
products = ["LNG (271111)", "Gaseous NG (271121)"]

df_list=[dfr, dfr_kg]
dfs_dict = {"primaryValue": dfr, "netWgt": dfr_kg}



st.title("Global Natural Gas Trade Analysis")

st.sidebar.header("Settings")
sel_year = st.sidebar.slider("Select Year:", 2010, 2025)
st.write(f"Showing results for {sel_year}")

st.header(f"Top yearly routes for {sel_year}", width="content")
for measure, df in dfs_dict.items():
    st.write(top_year_routes(df=df, year=sel_year, measure=measure))

st.header("Network analysis")
st.write(f"Choose the type and measure to see the network and top countries for the selected year. \
Exporters are red, importers are green.")

gas_type = st.selectbox("Choose the gas type:", ["liquefied", "gaseous"])
measure = st.selectbox("Choose the measure (dollars or kilograms):", ["primaryValue", "netWgt"])
st.write(nt.draw_graph(graphs, gas_type=gas_type, measure=measure, year=sel_year))
st.write(f"Top countries by centralities for {gas_type} gas in {sel_year} by {measure}:")
st.write(nt.build_centralities_df(graphs=graphs, gas_type=gas_type, measure=measure, year=sel_year))


annual_country_reported = compute_annual_country(dfr)

annual_country = pd.concat(
    [
        annual_country_reported[annual_country_reported["flow"] == "Import"].copy(),
        compute_mirror_exports(dfr),
    ],
ignore_index=True
)
st.header("Continent-level analysis:")
sel_flow = st.selectbox("Choose the flow:", ["Export", "Import"])

reporter_to_continent = al.build_default_continent_map()
df_cont = al.add_continent(df, reporter_to_continent)
cov = df_cont["continent"].value_counts(dropna=False).rename_axis("continent").reset_index(name="rows")
annual_cont = al.compute_annual_continent(df_cont)

for prod in products:
    st.write(al.plot_continental_trade(annual_cont, product=prod, flow=sel_flow, start_year=2010))

st.write("Relative continental contributions in global gas trade")
continent_shares = al.plot_continent_shares_grid(
    annual_cont,
    flows=["Import", "Export"],
    products=["LNG (271111)", "Gaseous NG (271121)"])
st.write(continent_shares)

st.header("Country-level analysis")
st.write("Top importers and exporters of NG")
st.write(plot_top_import_export_bars(annual_country=annual_country, gas_type="liquefied", years=[sel_year]))
st.write(plot_top_import_export_bars(annual_country=annual_country, gas_type="gaseous", years=[sel_year]))

countries_list = set(list(dfr.partner.unique()) + list(dfr.reporter.unique()))
countries_list = list(countries_list)
sel_country = st.selectbox("Print the name of country:", countries_list)
flow_sel = st.selectbox("Choose the trade flow", ["Import", "Export"])
st.write(country_plot(df_doll = dfr, df_kg = dfr_kg, country = sel_country, flow = flow_sel))

st.write(f"Main partners of {sel_country} in {sel_year} for each type of gas:")
for gas_type in gas_types:
    st.write(gas_type)
    st.write(main_partners(df_doll = dfr, country = sel_country, flow = flow_sel, year=sel_year, gas_type=gas_type))

st.header("Seasonal analysis")

for measure, df in dfs_dict.items():
    monthly = prepare_monthly_imports(df=df, year=sel_year, value_col=measure)
    seasonality = add_annual_share(monthly)
    st.write(plot_annual_shares(annual_shares_df = seasonality, measure=measure, year=sel_year))

st.write("Seasonal prices (maximum year is 2024)")
for gas_type in gas_types:
    st.write(f"{gas_type} gas seasonal profile:")
    monthly_df= monthly_prices(dfr_kg, gas_type=gas_type, max_year=2024)
    st.write(plot_seasonal_prices(monthly_prices=monthly_df, gas_type=gas_type))
    st.write(f"Comparison of {sel_year} with the seasonal profile:")
    st.write(compare_seasonal_prof(monthly_prices=monthly_df, gas_type=gas_type, year=sel_year ))


st.header("Seasonal ML model")
data = monthly_prices(dfr_kg, "gaseous", max_year=2024)
model = train_prophet(data)
st.write(model[1])
st.write("""This model is called Prophet. 2022 was deleted from training as the crisis year badly influenced fitting.
         Model is purely seasonal - it is trained only on dates. Other metrics were not used to see the pure seasonal profile.""")
st.write(f"Model's Mean Absolute Percentage Error: {check_model(model[0]):.4f}")
st.write(model[2])
st.write("Seasonality looks similar to average, but in January values fall, which was impossible to tune by adjusting hyperparameters.")

st.header("Thank You for Your attention!")