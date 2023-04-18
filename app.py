import json
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from utils import (
    calculate_beta_and_treynor,
    get_holdings_by_sector,
    get_ticker_data,
    get_upside_downside_capture,
    sectors_and_indices,
)

with open("sp500.json", "r") as f:
    sp500_tickers_and_sectors = json.load(f)

sp500 = [i for i, _ in sp500_tickers_and_sectors]

st.title("Sector Metrics")
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

data, raw = get_ticker_data(tickers, start_date, end_date, st.secrets["key"])
up_down_capture = get_upside_downside_capture(data, index)

correlation_df = data.corr()
correlation_df.index.names = ["Ticker"]
beta_treynor = calculate_beta_and_treynor(data, index)
metrics_df = pd.concat(
    [
        beta_treynor,
        up_down_capture,
    ],
    axis=1,
)
col1, col2 = st.columns(2)
col1.subheader("Metrics")
col1.write(metrics_df)
col2.subheader("Correlation")
col2.write(correlation_df)
st.line_chart(raw)
