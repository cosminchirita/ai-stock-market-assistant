import streamlit as st
from textblob import TextBlob
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Market Analysis Dashboard", layout="wide")

st.title("📈 AI Stock Market Assistant")

st.write(
    "Interactive stock market dashboard with technical indicators, risk scoring "
    "and historical performance analysis."
)

st.info("Examples: AAPL, TSLA, NVDA, MSFT, SAP.DE, BMW.DE, BP.L, ASML.AS, AIR.PA")

ticker = st.text_input("Enter stock ticker:", "AAPL").upper()

period = st.selectbox(
    "Select period:",
    ["3mo", "6mo", "1y", "2y", "5y", "max"],
    index=2
)

show_all = st.checkbox("Show full stock history")

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

def calculate_rsi(data, window=14):
    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

def calculate_macd(data):
    ema12 = data["Close"].ewm(span=12, adjust=False).mean()
    ema26 = data["Close"].ewm(span=26, adjust=False).mean()

    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal

    return macd, signal, histogram

def get_signal(current_price, ma50, ma200, rsi, macd, macd_signal):
    score = 0

    if current_price > ma50:
        score += 1
    else:
        score -= 1

    if current_price > ma200:
        score += 1
    else:
        score -= 1

    if rsi < 30:
        score += 1
    elif rsi > 70:
        score -= 1

    if macd > macd_signal:
        score += 1
    else:
        score -= 1

    if score >= 2:
        return "BUY"
    elif score <= -2:
        return "SELL"
    else:
        return "HOLD"

def get_risk_score(hist):
    daily_returns = hist["Close"].pct_change()
    volatility = daily_returns.std() * 100

    if volatility < 1.5:
        return "Low", volatility
    elif volatility < 3:
        return "Medium", volatility
    else:
        return "High", volatility

if ticker:
    stock = yf.Ticker(ticker)

    try:
        info = stock.info
        hist = stock.history(period="max" if show_all else period)

        if hist.empty:
            st.error(f"No data returned for ticker: {ticker}")
        else:
            company_name = info.get("longName", ticker)

            hist["MA50"] = hist["Close"].rolling(window=50).mean()
            hist["MA200"] = hist["Close"].rolling(window=200).mean()
            hist["RSI"] = calculate_rsi(hist)
            hist["MACD"], hist["MACD_Signal"], hist["MACD_Histogram"] = calculate_macd(hist)

            current_price = hist["Close"].iloc[-1]
            start_price = hist["Close"].iloc[0]
            return_pct = ((current_price - start_price) / start_price) * 100

            ma50 = hist["MA50"].iloc[-1]
            ma200 = hist["MA200"].iloc[-1]
            rsi = hist["RSI"].iloc[-1]
            macd = hist["MACD"].iloc[-1]
            macd_signal = hist["MACD_Signal"].iloc[-1]

            signal = get_signal(current_price, ma50, ma200, rsi, macd, macd_signal)
            risk_level, volatility = get_risk_score(hist)

            market_cap = info.get("marketCap", None)
            volume = info.get("volume", None)
            avg_volume = info.get("averageVolume", None)
            pe_ratio = info.get("trailingPE", None)
            week_high = info.get("fiftyTwoWeekHigh", None)
            week_low = info.get("fiftyTwoWeekLow", None)

            st.subheader(f"{company_name} ({ticker})")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Current Price", format_price(current_price))
            col2.metric("Period Return", f"{return_pct:.2f}%")
            col3.metric("Signal", signal)
            col4.metric("Risk Level", risk_level)

            col5, col6, col7, col8 = st.columns(4)
            col5.metric("RSI", f"{rsi:.2f}")
            col6.metric("Volatility", f"{volatility:.2f}%")
            col7.metric("52 Week High", format_price(week_high))
            col8.metric("52 Week Low", format_price(week_low))

            col9, col10, col11, col12 = st.columns(4)
            col9.metric("Market Cap", format_large_number(market_cap))
            col10.metric("Volume", format_large_number(volume))
            col11.metric("Average Volume", format_large_number(avg_volume))
            col12.metric("P/E Ratio", f"{pe_ratio:.2f}" if pe_ratio else "N/A")

            st.write(f"Data available from: {hist.index.min().date()}")
            st.write(f"Latest date: {hist.index.max().date()}")
            st.write(f"Total trading days: {len(hist):,}")

            st.subheader("Price History with Moving Averages")

            price_fig = go.Figure()

            price_fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist["Close"],
                mode="lines",
                name="Close Price"
            ))

            price_fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist["MA50"],
                mode="lines",
                name="50-Day Moving Average"
            ))

            price_fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist["MA200"],
                mode="lines",
                name="200-Day Moving Average"
            ))

            price_fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Price",
                hovermode="x unified",
                height=550
            )

            st.plotly_chart(price_fig, use_container_width=True)

            st.subheader("RSI Indicator")

            rsi_fig = go.Figure()

            rsi_fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist["RSI"],
                mode="lines",
                name="RSI"
            ))

            rsi_fig.add_hline(y=70, line_dash="dash", annotation_text="Overbought")
            rsi_fig.add_hline(y=30, line_dash="dash", annotation_text="Oversold")

            rsi_fig.update_layout(
                xaxis_title="Date",
                yaxis_title="RSI",
                height=350
            )

            st.plotly_chart(rsi_fig, use_container_width=True)

            st.subheader("MACD Indicator")

            macd_fig = go.Figure()

            macd_fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist["MACD"],
                mode="lines",
                name="MACD"
            ))

            macd_fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist["MACD_Signal"],
                mode="lines",
                name="Signal Line"
            ))

            macd_fig.add_trace(go.Bar(
                x=hist.index,
                y=hist["MACD_Histogram"],
                name="Histogram"
            ))

            macd_fig.update_layout(
                xaxis_title="Date",
                yaxis_title="MACD",
                height=350
            )

            st.plotly_chart(macd_fig, use_container_width=True)

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
            st.dataframe(
                hist[[
                    "Open", "High", "Low", "Close", "Volume",
                    "MA50", "MA200", "RSI", "MACD", "MACD_Signal"
                ]].tail(10)
            )            
            st.subheader("Financial News Sentiment")

            try:
                news = stock.news

                if news:
                    for article in news[:5]:
                        content = article.get("content", article)

                        title = content.get("title", "No title")
                        publisher = content.get("provider", {}).get("displayName", "Unknown publisher")
                        link = content.get("canonicalUrl", {}).get("url", "")

                        sentiment_score = TextBlob(title).sentiment.polarity

                        if sentiment_score > 0.1:
                            sentiment = "Bullish 🟢"
                        elif sentiment_score < -0.1:
                            sentiment = "Bearish 🔴"
                        else:
                            sentiment = "Neutral 🟡"

                        st.markdown(f"**{title}**")
                        st.write(f"Publisher: {publisher}")
                        st.write(f"Sentiment: {sentiment}")

                        if link:
                            st.markdown(f"[Read article]({link})")

                        st.divider()
                else:
                    st.info("No recent news found for this ticker.")

            except Exception:
                st.info("News data is currently unavailable for this ticker.")
                 
            st.subheader("Portfolio Tracker")

            portfolio_input = st.text_input(
                "Enter portfolio tickers separated by commas:",
                "AAPL, MSFT, NVDA"
            )

            if portfolio_input:
                portfolio_tickers = [
                    item.strip().upper()
                    for item in portfolio_input.split(",")
                    if item.strip()
                ]

                portfolio_data = []

                for symbol in portfolio_tickers:
                    try:
                        portfolio_stock = yf.Ticker(symbol)
                        portfolio_hist = portfolio_stock.history(period="1y")

                        if not portfolio_hist.empty:
                            first_price = portfolio_hist["Close"].iloc[0]
                            last_price = portfolio_hist["Close"].iloc[-1]
                            yearly_return = ((last_price - first_price) / first_price) * 100

                            portfolio_data.append({
                                "Ticker": symbol,
                                "Current Price": round(last_price, 2),
                                "1Y Return %": round(yearly_return, 2)
                            })

                    except Exception:
                        pass

                if portfolio_data:
                    st.dataframe(portfolio_data)

                    portfolio_fig = go.Figure()

                    for symbol in portfolio_tickers:
                        portfolio_stock = yf.Ticker(symbol)
                        portfolio_hist = portfolio_stock.history(period="1y")

                        if not portfolio_hist.empty:
                            normalized = (
                                portfolio_hist["Close"] / portfolio_hist["Close"].iloc[0]
                            ) * 100

                            portfolio_fig.add_trace(go.Scatter(
                                x=portfolio_hist.index,
                                y=normalized,
                                mode="lines",
                                name=symbol
                            ))

                    portfolio_fig.update_layout(
                        title="Portfolio Performance Comparison",
                        xaxis_title="Date",
                        yaxis_title="Normalized Performance",
                        hovermode="x unified",
                        height=500
                    )

                    st.plotly_chart(portfolio_fig, use_container_width=True)
                else:
                    st.info("No portfolio data found.")
    except Exception as e:
        st.error(f"Error loading data: {e}")