from datetime import date

import pandas as pd
import polygon


def get_ticker_data(
    tickers: list[str], start: date, end: date, key: str
) -> pd.DataFrame:
    client = polygon.RESTClient(api_key=key)

    # collect price data
    data: dict[str, list[float]] = {}
    dates: list[date] = list()
    for ticker in tickers:
        data[ticker] = list()
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
    df = df.pct_change().dropna()

    return df
