import json
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from dynamic_correlation import get_ticker_data

with open("sp500.json", "r") as f:
    sp500_tickers_and_sectors = json.load(f)

sp500 = [i for i, _ in sp500_tickers_and_sectors]

st.title("Dynamic Correlation")
tickers = st.multiselect("Select tickers", sp500)
col1, col2 = st.columns(2)
start_date = col1.date_input("Start Date", date.today() - timedelta(days=365))
end_date = col2.date_input("End Date", value=date.today())
data = get_ticker_data(tickers, start_date, end_date, KEY)
st.write(data.corr())
