import csv
from datetime import date
from io import StringIO

import numpy as np
import pandas as pd
import polygon
import requests

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


def get_upside_downside_capture(ticker_data: pd.DataFrame, index: str) -> pd.DataFrame:
    up, down = buckets(ticker_data, index)
    up_capture = capture(up, index)
    down_capture = capture(down, index)

    return pd.DataFrame({"Up Capture": up_capture, "Down Capture": down_capture})


def buckets(df: pd.DataFrame, index: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    avg = df[index].mean()
    direction = np.where(df[index] >= avg, 1, 0)
    up_data = df.loc[direction == 1]  # grabs up data
    down_data = df.loc[direction == 0]
    return up_data, down_data


def capture(data: pd.DataFrame, index: str) -> dict[str, float]:
    num_rows = len(data.index)
    reference_column = data[index]
    res = {}
    for column in data.columns:
        count = len(data[reference_column * data[column] >= 0])
        res[column] = count / num_rows

    return res


def get_ticker_data(
    tickers: list[str], start: date, end: date, key: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    client = polygon.RESTClient(api_key=key)

    # collect price data
    data: dict[str, list[float]] = {}
    dates: list[date] = []
    for ticker in tickers:
        data[ticker] = []
        dates.clear()
        for agg in client.get_aggs(
            ticker, multiplier=1, timespan="day", from_=start, to=end
        ):
            data[ticker].append(agg.close)
            dates.append(date.fromtimestamp(agg.timestamp // 1000))

    min_length = min([len(v) for k, v in data.items()])
    for ticker in data.keys():
        data[ticker] = data[ticker][-min_length:]

    dates = dates[-min_length:]

    df = pd.DataFrame.from_dict(data)
    df["Dates"] = dates
    df = df.set_index("Dates")

    return df.pct_change().dropna(), df.div(df.iloc[0])


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
    holdings_by_sector = {"Consumer Discretionary": []}
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
            holdings_by_sector[current_sector] = []

    to_remove = []
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
