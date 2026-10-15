import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title='ART Market Monitor',page_icon='📈',layout='wide')
st.title('ART Investment & Global Market Monitor')
st.caption('Real published ART performance + delayed market-price proxies. Not connected to your private ART account.')
weights={'International Shares Hedged Index':.35,'International Shares Unhedged Index':.35,'Bonds Index':.20,'Cash':.10}
initial=st.number_input('Illustrative portfolio starting value (AUD)',min_value=0.,value=1000000.,step=10000.,format='%.0f')
st.subheader('Your target allocation')
st.dataframe(pd.DataFrame([{'ART option':k,'Weight':f'{v:.0%}','Illustrative starting amount':f'${initial*v:,.0f}'} for k,v in weights.items()]),hide_index=True,use_container_width=True)

@st.cache_data(ttl=3600,show_spinner=False)
def art_returns():
    url='https://www.australianretirementtrust.com.au/investments/performance'
    tables=pd.read_html(url)
    for table in tables:
        flat=table.copy()
        flat.columns=[' '.join(map(str,c)) if isinstance(c,tuple) else str(c) for c in flat.columns]
        if flat.astype(str).apply(lambda c:c.str.contains('International Shares Hedged Index',regex=False)).any().any():
            return flat
    raise ValueError('ART table not found; website format may have changed.')
st.subheader('A — Official ART published performance')
st.markdown('[Open ART official performance page](https://www.australianretirementtrust.com.au/investments/performance) · [ART unit prices](https://www.australianretirementtrust.com.au/investments/performance/unit-prices)')
try:
    t=art_returns()
    mask=t.astype(str).apply(lambda col:col.str.contains('International Shares Hedged Index|International Shares Unhedged Index|Bonds Index|Cash',regex=True)).any(axis=1)
    st.dataframe(t.loc[mask],hide_index=True,use_container_width=True)
    st.caption('Official published return periods, not daily account valuations. Confirm the “as at” date on ART’s linked page. Data may lag.')
except Exception as e:
    st.warning('Automatic extraction of ART’s published table is unavailable right now. Open the official ART links above for current figures.')

st.subheader('B — Global market early-warning indicators')
st.caption('ETFs are imperfect benchmark proxies, NOT ART investments. USD/AUD currency exposure and hedging differ. Quotes can be delayed.')
proxies={'Global equities (ACWI, USD)':'ACWI','Developed equities (VEA, USD)':'VEA','US equities (SPY, USD)':'SPY','AUD/USD currency':'AUDUSD=X','Global bonds (BNDW, USD)':'BNDW'}
@st.cache_data(ttl=3600,show_spinner=False)
def history(ticker):
    df=yf.Ticker(ticker).history(period='2y',auto_adjust=True)
    if df.empty or 'Close' not in df: raise ValueError('No price history')
    return df['Close'].dropna()
for label,ticker in proxies.items():
    try:
        series=history(ticker)
        peak=series.cummax().iloc[-1]
        last=series.iloc[-1]
        drawdown=(last/peak-1)*100
        st.markdown(f'**{label}** · {last:.4f} · drawdown from 2-year high: **{drawdown:.1f}%** · data through {series.index[-1].date()}')
        if ticker!='AUDUSD=X':
            if drawdown<=-30: st.error('30% correction threshold reached')
            elif drawdown<=-20: st.warning('20% correction threshold reached')
            elif drawdown<=-10: st.warning('10% correction threshold reached')
        with st.expander(f'Price history — {ticker}'):
            st.line_chart(series)
    except Exception:
        st.info(f'{label}: data unavailable from the free market provider. Try again later.')
st.divider()
st.info('This dashboard refreshes its sources when opened, caching data for up to 1 hour. It does NOT send push notifications or run continuously. Your separate ChatGPT scheduled market watch handles daily checks. No trades are executed.')
st.caption(f'Dashboard loaded: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} (server time). Market data source: Yahoo Finance via yfinance, subject to availability.')
