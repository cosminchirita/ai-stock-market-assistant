import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(
    page_title="Stock Market Analysis Dashboard",
    layout="wide"
)

st.title("📈 Stock Market Analysis Dashboard")

st.write(
    "Interactive stock market dashboard with real-time data, technical indicators "
    "and historical performance analysis."
)

st.info(
    "Examples: AAPL, TSLA, NVDA, MSFT, SAP.DE, BMW.DE, BP.L, ASML.AS, AIR.PA"
)

ticker = st.text_input("Enter stock ticker:", "AAPL").upper()

period = st.selectbox(
    "Select period:",
    ["1mo", "3mo", "6mo", "1y", "5y", "max"],
    index=3
)

show_all = st.checkbox("Show full stock history")

if ticker:
    stock = yf.Ticker(ticker)

    try:
        info = stock.info
        hist = stock.history(period="max" if show_all else period)

        if hist.empty:
            st.error(f"No data returned for ticker: {ticker}")
        else:
            company_name = info.get("longName", ticker)

            current_price = hist["Close"].iloc[-1]
            start_price = hist["Close"].iloc[0]
            return_pct = ((current_price - start_price) / start_price) * 100

            previous_close = info.get("previousClose", None)
            daily_change_pct = (
                ((current_price - previous_close) / previous_close) * 100
                if previous_close
                else 0
            )

            market_cap = info.get("marketCap", None)
            volume = info.get("volume", None)
            avg_volume = info.get("averageVolume", None)
            pe_ratio = info.get("trailingPE", None)
            week_high = info.get("fiftyTwoWeekHigh", None)
            week_low = info.get("fiftyTwoWeekLow", None)

            def format_large_number(value):
                if value is None:
                    return "N/A"
                if value >= 1_000_000_000_000:
                    return f"{value / 1_000_000_000_000:.2f} T"
                if value >= 1_000_000_000:
                    return f"{value / 1_000_000_000:.2f} B"
                if value >= 1_000_000:
                    return f"{value / 1_000_000:.2f} M"
                return f"{value:,}"

            def format_price(value):
                return f"${value:.2f}" if value is not None else "N/A"

            def format_ratio(value):
                return f"{value:.2f}" if value is not None else "N/A"

            st.subheader(f"{company_name} ({ticker})")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Current Price",
                format_price(current_price),
                f"{daily_change_pct:.2f}%"
            )

            col2.metric(
                "Period Return",
                f"{return_pct:.2f}%"
            )

            col3.metric(
                "52 Week High",
                format_price(week_high)
            )

            col4.metric(
                "52 Week Low",
                format_price(week_low)
            )

            col5, col6, col7, col8 = st.columns(4)

            col5.metric(
                "Market Cap",
                format_large_number(market_cap)
            )

            col6.metric(
                "Volume",
                format_large_number(volume)
            )

            col7.metric(
                "Average Volume",
                format_large_number(avg_volume)
            )

            col8.metric(
                "P/E Ratio",
                format_ratio(pe_ratio)
            )

            st.write(f"Data available from: {hist.index.min().date()}")
            st.write(f"Latest date: {hist.index.max().date()}")
            st.write(f"Total trading days: {len(hist):,}")

            hist["MA50"] = hist["Close"].rolling(window=50).mean()
            hist["MA200"] = hist["Close"].rolling(window=200).mean()

            st.subheader(f"{ticker} Price History with Moving Averages")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist["Close"],
                mode="lines",
                name="Close Price"
            ))

            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist["MA50"],
                mode="lines",
                name="50-Day Moving Average"
            ))

            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist["MA200"],
                mode="lines",
                name="200-Day Moving Average"
            ))

            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Price",
                hovermode="x unified",
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Volume Analysis")

            volume_fig = go.Figure()

            volume_fig.add_trace(go.Bar(
                x=hist.index,
                y=hist["Volume"],
                name="Volume"
            ))

            volume_fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Volume",
                height=350
            )

            st.plotly_chart(volume_fig, use_container_width=True)

            st.subheader("Recent Price Data")
            st.dataframe(hist.tail(10))

    except Exception as e:
        st.error(f"Error loading data: {e}")