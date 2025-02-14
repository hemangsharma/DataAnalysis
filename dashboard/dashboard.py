import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set up the Streamlit page configuration
st.set_page_config(page_title="Enhanced NASDAQ Stock Dashboard", layout="wide")

# Cache metadata and data loading functions to speed up subsequent runs
@st.cache_data
def load_metadata():
    meta_path = os.path.join("../dataset", "symbols_valid_meta.csv")
    meta_df = pd.read_csv(meta_path)
    return meta_df

@st.cache_data
def load_stock_data(ticker, etf_flag):
    # Determine folder based on ETF flag: "etfs" if ETF flag is "Y", otherwise "stocks"
    folder = "etfs" if str(etf_flag).strip().upper() == "Y" else "stocks"
    file_path = os.path.join("../dataset", folder, f"{ticker}.csv")
    df = pd.read_csv(file_path)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df.sort_values("Date", inplace=True)
    return df

# Load metadata
meta_df = load_metadata()

# Build dropdown options using 'Symbol' and 'Security Name'
ticker_options = meta_df.apply(lambda row: f"{row['Symbol']} - {row['Security Name']}", axis=1).tolist()
ticker_symbol_mapping = {
    f"{row['Symbol']} - {row['Security Name']}": (row['Symbol'], row['ETF'])
    for _, row in meta_df.iterrows()
}

st.title("Enhanced NASDAQ Stock Dashboard")

# Ticker selection
selected_option = st.selectbox("Choose a stock/ETF:", ticker_options)
ticker, etf_flag = ticker_symbol_mapping[selected_option]
type_str = "ETF" if str(etf_flag).strip().upper() == "Y" else "Stock"

st.subheader(f"{ticker} Price Data")

# Sidebar analysis options
st.sidebar.header("Analysis Options")
ma_short = st.sidebar.number_input("Short Moving Average Window (days)", min_value=1, value=20, step=1)
ma_long = st.sidebar.number_input("Long Moving Average Window (days)", min_value=1, value=50, step=1)
date_range = st.sidebar.date_input("Select Date Range", [])

# Load selected ticker data
with st.spinner(f"Loading {ticker} data..."):
    df = load_stock_data(ticker, etf_flag)

# Filter by date range if selected
if date_range and len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)
    df = df.loc[mask]

# Calculate additional metrics
df['Return'] = df['Close'].pct_change()
df['Cumulative Return'] = (1 + df['Return']).cumprod() - 1
df['MA_short'] = df['Close'].rolling(window=ma_short).mean()
df['MA_long'] = df['Close'].rolling(window=ma_long).mean()

# Create tabs for different analyses
tab1, tab2, tab3, tab4 = st.tabs([
    "Price & Moving Averages", 
    "Candlestick Chart", 
    "Returns Analysis", 
    "Summary Statistics"
])

with tab1:
    st.markdown("### Price & Moving Averages")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df["Date"], y=df["Close"],
                              mode="lines",
                              name="Close Price",
                              line=dict(color="steelblue")))
    fig1.add_trace(go.Scatter(x=df["Date"], y=df["MA_short"],
                              mode="lines",
                              name=f"MA ({ma_short} days)",
                              line=dict(color="orange")))
    fig1.add_trace(go.Scatter(x=df["Date"], y=df["MA_long"],
                              mode="lines",
                              name=f"MA ({ma_long} days)",
                              line=dict(color="green")))
    fig1.update_layout(title=f"{ticker} Price with Moving Averages",
                       xaxis_title="Date", yaxis_title="Price")
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.markdown("### Candlestick Chart")
    # Check if OHLC data is available
    if {'Open', 'High', 'Low', 'Close'}.issubset(df.columns):
        fig2 = go.Figure(data=[go.Candlestick(
            x=df["Date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC"
        )])
        fig2.update_layout(title=f"{ticker} Candlestick Chart",
                           xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.write("OHLC data is not available for this ticker.")

with tab3:
    st.markdown("### Returns Analysis")
    # Daily returns histogram
    fig3 = go.Figure()
    fig3.add_trace(go.Histogram(x=df["Return"],
                                nbinsx=50,
                                name="Daily Returns",
                                marker_color="purple",
                                opacity=0.75))
    fig3.update_layout(title=f"{ticker} Daily Returns Histogram",
                       xaxis_title="Daily Return", yaxis_title="Frequency")
    st.plotly_chart(fig3, use_container_width=True)
    
    # Cumulative return line chart
    fig3b = go.Figure()
    fig3b.add_trace(go.Scatter(x=df["Date"], y=df["Cumulative Return"],
                               mode="lines",
                               name="Cumulative Return",
                               line=dict(color="red")))
    fig3b.update_layout(title=f"{ticker} Cumulative Return",
                        xaxis_title="Date", yaxis_title="Cumulative Return")
    st.plotly_chart(fig3b, use_container_width=True)

with tab4:
    st.markdown("### Summary Statistics")
    latest_close = df["Close"].iloc[-1]
    mean_return = df["Return"].mean()
    volatility = df["Return"].std()
    cumulative_return = df["Cumulative Return"].iloc[-1]
    stats = {
        "Latest Close Price": latest_close,
        "Mean Daily Return": mean_return,
        "Daily Return Std Dev (Volatility)": volatility,
        "Cumulative Return": cumulative_return
    }
    stats_df = pd.DataFrame(stats, index=[0]).T
    stats_df.columns = ["Value"]
    st.table(stats_df)
    st.markdown("These statistics provide a quick overview of the ticker's recent performance.")

st.markdown("### Data Sample")
st.write(df.head())