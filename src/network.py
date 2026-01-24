# src/network.py
from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import seaborn as sns
import networkx as nx



# Helper function


def to_billions(df: pd.DataFrame, col: str) -> pd.Series:
    "Function that divides all values in a given column on 10**9 to represent values in billions"
    return pd.to_numeric(df[col], errors="coerce") / 10**9


def column_explanations() -> dict:
    """Function that prints explanations to each column in the df for the observer to understand the roles of different columns"""
    return {
        "period": "YYYYMM of trade",
        "refYear": "year of trade",
        "refMonth": "month of trade",
        "reporterCode": "code of country who reported the trade",
        "flowCode": "code of trade flow, usually 'M' for 'Import' and 'X' for 'Export' ",
        "partnerCode": "code of country who is a counterparty in the trade reported by reporter country ",
        "classificationCode": "type of Harmonized System (HS) classification used for this trade. It has changed throughout the years",
        "cmdCode": "code of commodity traded",
        "customsCode": "defines how the goods entered or left the economic territory",
        "motCode": "code of transport used to deliver the trade",
        "qtyUnitCode": "defines the unit of measurement of commodity traded",
        "qty": "quantity of commodity traded measured in a way specified in qtyUnitCode",
        "isQtyEstimated": "Is quantity Estimated - boolean",
        "altQtyUnitCode": "alternative unit of measurement of commodity traded",
        "altQty": "quantity of commodity traded measured in altQtyUnitCode units",
        "isAltQtyEstimated": "Is alternative quantity Estimated - boolean",
        "netWgt": "net weight of commodity traded in kilograms",
        "isNetWgtEstimated": "Is net weight Estimated - boolean",
        "primaryValue": "value of trade in dollars",
        "isAggregate": "is value aggregated - True or False",
        "transport": "mode of transport (already decoded)",
        "qty_type": "decoded unit for qty",
        "alt_qty_type": "decoded unit for altQty",
        "customs_type": "decoded customs category"
    }


def add_gas_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'type' column expected by teammate code:
      - liquefied for LNG (271111)
      - gaseous for gaseous NG (271121)
    """
    out = df.copy()


    if "cmdCode" in out.columns:
        cmd = out["cmdCode"].astype(str)
        out["type"] = np.where(cmd == "271111", "liquefied",
                        np.where(cmd == "271121", "gaseous", None))
    else:
        # In case of error fallback
        prod = out.get("product", "").astype(str)
        out["type"] = np.where(prod.str.contains("271111", na=False), "liquefied",
                        np.where(prod.str.contains("271121", na=False), "gaseous", None))

    return out



# Data prep for KG analysis


def get_df_for_kg(df: pd.DataFrame) -> pd.DataFrame:
    """
        The df is now read from main.py .
    """
    dfr_kg = df.copy()
    dfr_kg = dfr_kg[
        ~(
            (dfr_kg["refYear"] >= 2015)
            & (dfr_kg["reporter"] == "Mexico")
            & (dfr_kg["flow"] == "Import")
            & (dfr_kg["partner"] == "United States of America")
        )
    ]
    dfr_kg = dfr_kg[dfr_kg["netWgt"] > 0].copy()
    dfr_kg["kg_price"] = dfr_kg["primaryValue"] / dfr_kg["netWgt"]

    low_lim = dfr_kg["kg_price"].quantile(0.01)
    high_lim = dfr_kg["kg_price"].quantile(0.99)
    dfr_kg = dfr_kg[(dfr_kg["kg_price"] > low_lim) & (dfr_kg["kg_price"] < high_lim)].copy()
    return dfr_kg




def observe_discrepancies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Function that compare total import and export for each year and type of gas to see inconsistencies in data.
    """
    cols = ["primaryValue", "netWgt"]
    data = df.groupby(["refYear", "flow", "type"], as_index=False)[cols].sum()

    for col in cols:
        data[col] = data[col] / 10**9

    return data.sort_values(["refYear", "type", "flow"]).tail(20)


def see_problems(df: pd.DataFrame) -> pd.DataFrame:
    """
    Show top suspicious netWgt rows for Import >= 2015.
    """
    needed_cols = [
        "type", "period", "reporter", "flow", "partner", "cmdCode",
        "primaryValue", "qty", "qty_type", "netWgt", "altQty", "alt_qty_type",
        "transport"
    ]
    tmp = df[(df["flow"] == "Import") & (df["refYear"] >= 2015)].copy()
    tmp["netWgt"] = pd.to_numeric(tmp["netWgt"], errors="coerce")
    tmp = tmp[tmp["netWgt"].notna()]

    # take 4 largest netWgt per year
    idx = tmp.groupby("refYear")["netWgt"].nlargest(4).index
    bad_indexes = [i[1] for i in idx]
    bad_indexes = bad_indexes[:10]

    cols_present = [c for c in needed_cols if c in df.columns]
    return df.loc[bad_indexes, cols_present].copy()



# Prices & transport


def plot_trades(column: str, df: pd.DataFrame) -> plt.Figure:
    """
     The function returns a plot of total import and export for each type of gas for each year.
    Column argument accept only 'netWgt' or 'primaryValue.
    """
    gas_types = list(df["type"].dropna().unique())
    measure = "dollars" if column == "primaryValue" else "kilograms"

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(15, 10))
    axes_flat = axes.flatten()
    axes_index = 0

    for gas_type in gas_types:
        for fl in ["Export", "Import"]:
            ax = axes_flat[axes_index]
            data = (
                df[(df["flow"] == fl) & (df["type"] == gas_type)]
                .groupby("refYear")[column]
                .sum() / 10**9
            )
            data.plot.bar(ax=ax)
            ax.set_title(f"{gas_type} natural gas; {column}, Total {fl}")
            ax.set_xlabel("Years")
            ax.set_ylabel(f"Total {fl}, billions of {measure}")
            ax.grid(True, alpha=0.5)
            axes_index += 1

    plt.tight_layout()
    plt.close(fig)
    return fig


def plot_transport_trades(df_doll: pd.DataFrame, df_kg: pd.DataFrame) -> plt.Figure:
    """
    Plot total import for different transport routes for each type of gas and measure.
    """
    dfs_cols = {"primaryValue": df_doll, "netWgt": df_kg}
    gas_types = list(df_doll["type"].dropna().unique())

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(21, 13))
    axes_flat = axes.flatten()
    axes_index = 0

    for gas in gas_types:
        for col, dfx in dfs_cols.items():
            ax = axes_flat[axes_index]
            sns.lineplot(
                data=dfx[(dfx["flow"] == "Import") & (dfx["type"] == gas)],
                y=to_billions(dfx, col),
                x="refYear",
                hue="transport",
                errorbar=None,
                estimator="sum",
                ax=ax,
            )
            ax.set_ylabel(f"{col}, billions", size=16)
            ax.set_xlabel("Year", size=14)
            ax.legend(ncol=3, loc="upper left")
            ax.set_title(f"Total import for {gas} gas, {col}", size=14)
            ax.grid(alpha=0.5)
            axes_index += 1

    plt.tight_layout()
    plt.close(fig)
    return fig


def top_year_routes(df: pd.DataFrame, start_year: int, measure: str) -> pd.DataFrame:
    """
    This function returns a df with top trade routes for a given measure (dollars or kilograms) starting from a given year.
    """
    top_transport = df[
        (df["refYear"] > start_year)
        & (df["flow"] == "Import")
        & ~df["transport"].isin(["Total Modes of Transport", "Other"])
    ].groupby(["refYear", "type", "transport"])[measure].sum()

    top_transport = top_transport.groupby(["refYear", "type"]).nlargest(2)
    top_transport = top_transport.droplevel([0, 1]).reset_index()
    return top_transport


def top_historical_routes(df: pd.DataFrame, measure: str) -> pd.DataFrame:
    """Top routes over whole period."""
    routes_df = df.groupby(["type", "transport"])[measure].sum()
    routes_df = routes_df.groupby("type").nlargest(7).droplevel(0).reset_index()
    return routes_df


def country_plot(df_doll: pd.DataFrame, df_kg: pd.DataFrame, country: str) -> plt.Figure | None:
    """
    This function plots 4 graphs of evolution of trade for different transport routes 
    for 2 types of trade and 2 types of measures for a given country.
    """
    dfs_cols = {"primaryValue": df_doll, "netWgt": df_kg}
    gas_types = list(df_kg["type"].dropna().unique())
    countries_list = set(df_kg["reporter"].dropna().unique())

    if country not in countries_list:
        print(f"[WARN] '{country}' not found in reporter list.")
        return None

    fig, axes = plt.subplots(2, 2, figsize=(20, 11))
    axes_flat = axes.flatten()
    axes_ind = 0

    for gas in gas_types:
        for col, dfx in dfs_cols.items():
            ax = axes_flat[axes_ind]
            sns.lineplot(
                data=dfx[(dfx["reporter"] == country) & (dfx["type"] == gas)],
                y=to_billions(dfx, col),
                x="refYear",
                hue="transport",
                errorbar=None,
                ax=ax,
                estimator="sum",
            )
            ax.set_ylabel(f"{col}, billions", size=13)
            ax.set_xlabel("Year", size=12)
            ax.legend(ncol=3, loc="upper left")
            ax.set_title(f"Total import for {country}, {gas} gas, {col}", size=12)
            ax.grid(alpha=0.5)
            axes_ind += 1

    plt.tight_layout()
    plt.close(fig)
    return fig


def route_prices(df_kg: pd.DataFrame) -> pd.DataFrame:
    """
    Average prices (USD/kg) by type, flow, transport route.
    """
    prices = (
        df_kg.groupby(["type", "flow", "transport"], as_index=False)[["primaryValue", "netWgt"]]
        .sum()
    )
    prices["price"] = prices["primaryValue"] / prices["netWgt"]

    prices = prices[
        (prices["netWgt"] > 10**6)
        & (prices["transport"] != "Postal consignments, mail or courier shipment")
    ].copy()

    return prices


def plot_route_prices(df_kg: pd.DataFrame) -> plt.Figure:
    """
    This function plots price differences between differen routes for export and import
    and for each type of gas.
    """
    prices = route_prices(df_kg)
    gas_types = list(df_kg["type"].dropna().unique())

    fig, axes = plt.subplots(1, 2, figsize=(18, 6))
    axes_flat = axes.flatten()

    for i, gas in enumerate(gas_types[:2]):
        ax = axes_flat[i]
        sns.barplot(
            data=prices[prices["type"] == gas],
            x="transport",
            y="price",
            errorbar=None,
            hue="flow",
            ax=ax,
        )
        ax.set_ylabel("Price, dollars per kilogram", size=12)
        ax.set_title(f"{gas} gas, price by mode of transport", size=12)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        ax.grid(alpha=0.5)

    plt.tight_layout()
    plt.close(fig)
    return fig


def routes_saldo(df_kg: pd.DataFrame) -> plt.Figure:
    """This function plotes saldo (export - import) of average prices for export and import
      for each route for both types of gas."""
    prices = route_prices(df_kg)

    saldo = prices.pivot(index=["type", "transport"], columns="flow", values="price")
    saldo["diff"] = saldo.get("Export", np.nan) - saldo.get("Import", np.nan)
    saldo = saldo.reset_index()

    fig, ax = plt.subplots(figsize=(12, 4))
    sns.barplot(data=saldo, x="transport", y="diff", errorbar=None, hue="type", ax=ax)
    ax.set_ylabel("Export price - Import price (USD/kg)", size=12)
    ax.set_xlabel("Transport", size=12)
    ax.set_title("Difference between avg export and import prices by route", size=12)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    ax.grid(alpha=0.5)

    plt.tight_layout()
    plt.close(fig)
    return fig


def price_evolution(df_kg: pd.DataFrame) -> plt.Figure:
    """This function plots price evolution throughout the year for each type of gas."""
    price_evol = df_kg.groupby(["type", "refYear"], as_index=False)[["primaryValue", "netWgt"]].sum()
    price_evol["price"] = price_evol["primaryValue"] / price_evol["netWgt"]

    fig, ax = plt.subplots(figsize=(12, 4))
    sns.pointplot(data=price_evol, x="refYear", y="price", hue="type", errorbar=None, ax=ax)
    ax.set_title("Price evolution (USD/kg) for gaseous vs liquefied")
    ax.set_ylabel("USD/kg")
    ax.set_xlabel("Year")
    ax.grid(alpha=0.6)

    plt.tight_layout()
    plt.close(fig)
    return fig


def route_price_evol(df_kg: pd.DataFrame) -> Dict[str, plt.Figure]:
    """
    Creates one figure per gas type and returns a dict of figures.
    """
    rp = (
        df_kg.groupby(["type", "refYear", "transport"], as_index=False)[["primaryValue", "netWgt"]]
        .sum()
    )
    rp["price"] = rp["primaryValue"] / rp["netWgt"]
    rp = rp[rp["netWgt"] > 10**8].copy()  # only significant routes

    figs: Dict[str, plt.Figure] = {}
    for gas_type in sorted(rp["type"].dropna().unique()):
        fig, ax = plt.subplots(figsize=(12, 4))
        sns.pointplot(
            data=rp[rp["type"] == gas_type],
            x="refYear",
            y="price",
            hue="transport",
            errorbar=None,
            ax=ax,
        )
        ax.set_title(f"Evolution of prices by transport route — {gas_type}")
        ax.set_ylabel("USD/kg")
        ax.set_xlabel("Year")
        ax.legend(ncol=3)
        ax.grid(alpha=0.6)
        plt.tight_layout()
        plt.close(fig)

        figs[f"transport_route_price_evolution_{gas_type}.png"] = fig

    return figs


#  Network analysis


def build_graphs(df_dol: pd.DataFrame, df_kg: pd.DataFrame) -> dict:
    """
    This function builds a network for each type of gas, each measure, and each year
    and returns dictionary with all the graphs that can be called in the above described order.
    """
    # Use only years in df to avoid building empty graphs up to current year
    year_list = sorted(set(df_dol["refYear"].dropna().astype(int).unique().tolist()))

    dfs_cols = {"primaryValue": df_dol.copy(), "netWgt": df_kg.copy()}

    # Prepare directed graph fields
    for dfx in dfs_cols.values():
        dfx["source"] = np.where(dfx["flow"] == "Export", dfx["reporter"], dfx["partner"])
        dfx["target"] = np.where(dfx["flow"] == "Export", dfx["partner"], dfx["reporter"])

    gas_types = sorted(df_kg["type"].dropna().unique())
    graphs = {gas: {"primaryValue": {}, "netWgt": {}} for gas in gas_types}

    for gas_type in gas_types:
        for col, dfx in dfs_cols.items():
            dfg = dfx[dfx["type"] == gas_type]
            for year in year_list:
                dfgy = dfg[dfg["refYear"] == year]

                G = nx.from_pandas_edgelist(
                    df=dfgy,
                    source="source",
                    target="target",
                    edge_attr=True,
                    create_using=nx.DiGraph,
                )
                graphs[gas_type][col][f"G_{year}"] = G

    return graphs


def get_layout(G: nx.DiGraph):
    "Function to create nice layout for a given graph"
    return nx.spring_layout(G, k=1.4, scale=2)


def get_sizes(G: nx.DiGraph, col: str, scale=100):
    "Function to adjust size of nodes to their weighted degree"
    weighted_degrees = dict(G.degree(weight=col))
    degrees = np.array(list(weighted_degrees.values())) if weighted_degrees else np.array([0.0])
    sizes = np.sqrt(degrees) / scale
    return sizes


def get_width(G: nx.DiGraph, measure: str, scale=10000):
    "Function to adjust size of nodes to their weighted degree"
    edges = list(G.edges())
    if not edges:
        return np.array([])
    weight = np.array([G[u][v].get(measure, 0.0) for u, v in edges])
    return np.sqrt(weight) / scale


def get_color(G: nx.DiGraph, weight: str):
    import_weights = {}
    export_weights = {}

    for node in G.nodes():
        import_weights[node] = sum(d.get(weight, 0.0) for _, _, d in G.in_edges(node, data=True))
        export_weights[node] = sum(d.get(weight, 0.0) for _, _, d in G.out_edges(node, data=True))

    colors = []
    for node in G.nodes():
        colors.append("green" if import_weights[node] > export_weights[node] else "red")

    return colors


def draw_graph(graphs: dict, gas_type: str, measure: str, year: int) -> plt.Figure:
    """
    Function that draws final graw with all settings given by previous functions
    """
    G = graphs[gas_type][measure].get(f"G_{year}")
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_title(f"Network of {gas_type} natural gas; {measure}, {year}", size=10)

    if G is None or G.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "Empty graph for this year/type", ha="center", va="center")
        ax.axis("off")
        plt.close(fig)
        return fig

    pos = get_layout(G)
    nx.draw(
        G,
        pos,
        ax=ax,
        node_size=get_sizes(G, measure),
        width=get_width(G, measure=measure),
        edge_color="grey",
        node_color=get_color(G, measure),
        with_labels=True,
        font_size=8,
    )

    plt.tight_layout()
    plt.close(fig)
    return fig


def global_efficiency(G: nx.DiGraph, weight: str) -> float:
    
    """
    Function that returns the efficiency of the graph. It appeared that the efficiency metric in networkx is pretty limited and does not
    work with directed and weighted graphs. This metric, based on the same principle, adjusts for weight.
    Inputs: graph, its weight attribute.
    Output: efficiency of the graph.
    Note: for the inverted graph, it was required to invert weights as more trade is better, not worse, as the shortest path treats it.
    """
    num_nodes = G.number_of_nodes()
    if num_nodes < 2:
        return np.nan

    all_pairs = num_nodes * (num_nodes - 1)
    efficiency_sum = 0.0

    for source, targets in nx.shortest_path_length(G, weight=weight):
        for target, distance in targets.items():
            if source != target and distance and distance > 0:
                efficiency_sum += 1 / distance

    return efficiency_sum / all_pairs


def global_efficiency_log_normalized(G: nx.DiGraph, weight: str) -> float:
    """
    Global_efficiency above gives extremely small values, which appeared because 
    1. the shortest path is inverted, not the weights, and 2. the distribution of weights in natgas is catastrophically heavy-tailed:
    plenty of small trades with a few enormous. This function fixes the first effects and smoothes the second.
    """
    if G.number_of_edges() == 0 or G.number_of_nodes() < 2:
        return np.nan

    G_cost = G.copy()
    max_weight = max(d.get(weight, 0.0) for _, _, d in G_cost.edges(data=True))
    if max_weight <= 0:
        return np.nan

    log_max = np.log2(max_weight)

    to_remove = []
    for u, v, data in G_cost.edges(data=True):
        trade_vol = data.get(weight, 0.0)
        if trade_vol > 0:
            log_weight = np.log2(trade_vol + 1)
            data["cost"] = log_max / log_weight
        else:
            to_remove.append((u, v))
    for e in to_remove:
        G_cost.remove_edge(*e)

    num_nodes = G_cost.number_of_nodes()
    if num_nodes < 2:
        return np.nan

    all_pairs = num_nodes * (num_nodes - 1)
    efficiency_sum = 0.0

    for source, targets in nx.shortest_path_length(G_cost, weight="cost"):
        for target, distance in targets.items():
            if source != target and distance and distance > 0:
                efficiency_sum += 1 / distance

    return efficiency_sum / all_pairs


def get_metrics(graphs: dict, func, weights: bool) -> pd.DataFrame:
    """
    This function calculates some metrics of the graph based on the given function to store it in comfortable df.
    Input: function; whether it takes weight.
    Output: DataFrame 
    """
    years = None
    gas_types = sorted(graphs.keys())
    measures = ["primaryValue", "netWgt"]

    rows = []
    for gas_type in gas_types:
        for col in measures:
            if years is None:
                years = sorted(int(k.split("_")[1]) for k in graphs[gas_type][col].keys())
            for year in years:
                G = graphs[gas_type][col].get(f"G_{year}")
                if G is None:
                    val = np.nan
                else:
                    if weights:
                        val = func(G, weight=col)
                    else:
                        val = func(G)
                rows.append(
                    {
                        "type": gas_type,
                        "measure": col,
                        "year": year,
                        "function": func.__name__,
                        "value": val,
                    }
                )

    return pd.DataFrame(rows)


def build_metrics_df(graphs: dict) -> pd.DataFrame:
    """
    This function uses the function above to calculate all metrics from the functions list
    and returns a dataframe with name of the functions as the columns and corresponding to each graph values.
    """
    functions_list = {
        nx.average_clustering: True,
        nx.degree_assortativity_coefficient: True,
        nx.reciprocity: False,
        nx.density: False,
        global_efficiency: True,
        global_efficiency_log_normalized: True,
    }

    dfs_list = []
    for function, need_weight in functions_list.items():
        dfs_list.append(get_metrics(graphs=graphs, func=function, weights=need_weight))

    df_metrics = pd.concat(dfs_list, ignore_index=True)
    df_metrics = df_metrics.pivot(
        columns="function", index=["type", "measure", "year"], values="value"
    ).reset_index()

    df_metrics["type_measure"] = df_metrics["type"].astype(str) + ", " + df_metrics["measure"].astype(str)
    return df_metrics


def plot_metric(metric: str, df_metrics: pd.DataFrame) -> plt.Figure:
    "This function creates a lineplot for a given metric with 4 hues based on the type of gas and measurement"
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.pointplot(
        data=df_metrics,
        x="year",
        y=metric,
        errorbar=None,
        hue="type_measure",
        ax=ax,
    )
    ax.set_ylabel("Value", size=12)
    ax.set_xlabel("Year", size=12)
    ax.grid(True)
    ax.set_title(f"Evolution of {metric} for all years")
    plt.tight_layout()
    plt.close(fig)
    return fig


def get_metrics_corr(df_metrics: pd.DataFrame) -> pd.DataFrame:
    "The function returns adf with correlations between its metrics"
    metric_cols = [c for c in df_metrics.columns if c not in ("type", "measure", "year", "type_measure")]
    return df_metrics[metric_cols].corr()



#  Function to be used for main.py


def run_network_bundle(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Entry point expected by main.py

    Returns:
      {"tables": {filename.csv: DataFrame, ...},
       "figures": {filename.png: Figure, ...}}
    """
    tables: Dict[str, pd.DataFrame] = {}
    figures: Dict[str, plt.Figure] = {}

    # Check numeric
    df0 = df.copy()
    df0["primaryValue"] = pd.to_numeric(df0["primaryValue"], errors="coerce")
    df0["netWgt"] = pd.to_numeric(df0["netWgt"], errors="coerce")

    # df for kg analysis (price-based + network-based)
    df0 = add_gas_type(df)
    dfr_kg = get_df_for_kg(df0)
    tables["df_for_kg_analysis.csv"] = dfr_kg

    # diagnostics tables
    tables["discrepancies_in_kg_trade.csv"] = observe_discrepancies(df=df0)
    tables["problematic_kg_trades.csv"] = see_problems(df=df0)

    # plots: trade evolution
    figures["evolution_of_trade_for_gas_kg.png"] = plot_trades(column="netWgt", df=dfr_kg)
    figures["evolution_of_trade_for_gas_doll.png"] = plot_trades(column="primaryValue", df=df0)

    # plots: transport
    figures["evolution_of_transport_trades.png"] = plot_transport_trades(df_doll=df0, df_kg=dfr_kg)

    # top routes tables
    tables["top_yearly_trade_routes_from_2022_doll.csv"] = top_year_routes(df=df0, start_year=2022, measure="primaryValue")
    tables["top_yearly_trade_routes_from_2022_kg.csv"] = top_year_routes(df=dfr_kg, start_year=2022, measure="netWgt")
    tables["top_all_time_routes_doll.csv"] = top_historical_routes(df=df0, measure="primaryValue")
    tables["top_all_time_routes_kg.csv"] = top_historical_routes(df=dfr_kg, measure="netWgt")

    # country plots (skip if None)
    for country, fname in [
        ("Czechia", "czechia_trade_by_transport.png"),
        ("United States of America", "us_trade_by_transport.png"),
        ("China", "china_trade_by_transport.png"),
    ]:
        fig = country_plot(df_doll=df0, df_kg=dfr_kg, country=country)
        if fig is not None:
            figures[fname] = fig

    # price plots
    figures["prices_for_transport_routes.png"] = plot_route_prices(df_kg=dfr_kg)
    figures["saldo_for_transport_routes.png"] = routes_saldo(df_kg=dfr_kg)
    figures["evolution_of_gas_prices.png"] = price_evolution(df_kg=dfr_kg)

    # route price evolution returns multiple figs flatten into dict
    figures.update(route_price_evol(df_kg=dfr_kg))

    # network: graphs + sample graph draw
    graphs = build_graphs(df_dol=df0, df_kg=dfr_kg)

    # choose a safe latest year present
    latest_year = int(max(df0["refYear"].dropna().astype(int).unique()))
    # sample graphs
    # teammate uses "liquefied"/"gaseous" in 'type' — keep consistent
    if "liquefied" in graphs and "primaryValue" in graphs["liquefied"]:
        figures[f"graph_liquefied_{latest_year}_doll.png"] = draw_graph(graphs=graphs, gas_type="liquefied", measure="primaryValue", year=latest_year)
    if "gaseous" in graphs and "primaryValue" in graphs["gaseous"]:
        figures[f"graph_gaseous_{latest_year}_doll.png"] = draw_graph(graphs=graphs, gas_type="gaseous", measure="primaryValue", year=latest_year)

    # metrics
    df_metrics = build_metrics_df(graphs=graphs)
    tables["network_metrics_all_graphs.csv"] = df_metrics

    # metric plots
    metric_cols = [c for c in df_metrics.columns if c not in ("type", "measure", "year", "type_measure")]
    for metric in metric_cols:
        figures[f"{metric}_all_year_evol.png"] = plot_metric(metric=metric, df_metrics=df_metrics)

    tables["corr_between_graph_metrics.csv"] = get_metrics_corr(df_metrics=df_metrics)

    return {"tables": tables, "figures": figures}


