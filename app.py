import csv
import json
from datetime import date, timedelta
from io import StringIO

import pandas as pd
import requests
import streamlit as st

from dynamic_correlation import get_ticker_data

sectors_and_indices = {
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Financials": "XLF",
    "Healthcare": "XLV",
    "Industrials": "XLI",
    "Technology": "XLK",
    "Media and Telecom": "XLC",
    "Utilities": "XLU",
    "Quant": "SPY",
    "REITS": "XLRE",
}


def calculate_beta_and_treynor(data: pd.DataFrame, index: str) -> pd.DataFrame:
    result = {"Beta": [], "Treynor": [], "Ticker": []}
    corr = data.corr()
    for ticker in data.columns:
        beta = (data[ticker].std() / data[index].std()) * corr[ticker][index]
        total_return = 1
        for daily_return in data[ticker]:
            total_return *= 1 + daily_return
        treynor_ratio = total_return / beta
        result["Ticker"].append(ticker)
        result["Beta"].append(beta)
        result["Treynor"].append(treynor_ratio)

    return pd.DataFrame.from_dict(result).set_index("Ticker")


def get_holdings_by_sector() -> dict[str, list[str]]:
    scsv = requests.get(
        "https://docs.google.com/spreadsheets/d/1hLTHQbxRyILSQg6TP2hSXeBnQ5Km8ifo64fd7tXJ5CM/gviz/tq?tqx=out:csv"
    ).text

    # consumer discretionary is first sector on table
    holdings_by_sector = {"Consumer Discretionary": list()}
    current_sector = "Consumer Discretionary"

    skipped = False
    reader = csv.reader(StringIO(scsv), delimiter=",")
    for row in reader:
        if not skipped:
            skipped = True
            continue

        if row[0] == "":
            holdings_by_sector[current_sector].append(row[1])
        elif row[0] == "Sector Total":
            continue
        else:
            current_sector = row[0]
            holdings_by_sector[current_sector] = list()

    to_remove = list()
    for key in holdings_by_sector.keys():
        if key not in sectors_and_indices.keys():
            to_remove.append(key)
        elif sectors_and_indices[key] not in holdings_by_sector[key]:
            holdings_by_sector[key].append(sectors_and_indices[key])

        if "Cash" in holdings_by_sector[key]:
            holdings_by_sector[key].remove("Cash")

    for key in to_remove:
        holdings_by_sector.pop(key)

    return holdings_by_sector


with open("sp500.json", "r") as f:
    sp500_tickers_and_sectors = json.load(f)

sp500 = [i for i, _ in sp500_tickers_and_sectors]

st.title("Dynamic Correlation")
mode = st.selectbox("Mode", ["Sector Holdings", "Sandbox"])
col1, col2 = st.columns(2)
start_date = col1.date_input("Start Date", date.today() - timedelta(days=365))
end_date = col2.date_input("End Date", value=date.today())
if mode == "Sandbox":
    tickers = st.multiselect("Select tickers", sp500)
    tickers.append("SPY")
    index = "SPY"
    data = get_ticker_data(tickers, start_date, end_date, st.secrets["key"])

else:
    holdings_by_sector = get_holdings_by_sector()
    sector = st.selectbox("Sector", holdings_by_sector.keys())
    assert sector is not None
    tickers = holdings_by_sector[sector]
    index = sectors_and_indices[sector]

data = get_ticker_data(tickers, start_date, end_date, st.secrets["key"])
correlation_df = data.corr()
correlation_df.index.names = ["Ticker"]
beta_treynor = calculate_beta_and_treynor(data, index)
beta_treynor["Correlation"] = ""
st.write(
    pd.concat(
        [
            beta_treynor,
            correlation_df,
        ],
        axis=1,
    )
)
