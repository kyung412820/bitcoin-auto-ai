import requests
import pandas as pd
import time
import webbrowser
import pyupbit

tickers = pyupbit.get_tickers(fiat="KRW")

print('Upbit 10 minute RSI')

while True:
    
    def rsiindex(symbol):
        url = "https://api.upbit.com/v1/candles/minutes/10"
    
        querystring = {"market":symbol,"count":"500"}
    
        response = requests.request("GET", url, params=querystring)
    
        data = response.json()
    
        df = pd.DataFrame(data)
    
        df=df.reindex(index=df.index[::-1]).reset_index()
    
        df['close']=df["trade_price"]

    
    
        def rsi(ohlc: pd.DataFrame, period: int = 14):
            ohlc["close"] = ohlc["close"]
            delta = ohlc["close"].diff()
    
            up, down = delta.copy(), delta.copy()
            up[up < 0] = 0
            down[down > 0] = 0
    
            _gain = up.ewm(com=(period - 1), min_periods=period).mean()
            _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    
            RS = _gain / _loss
            return pd.Series(100 - (100 / (1 + RS)), name="RSI")
    
        rsi = rsi(df, 14).iloc[-1]
        if rsi <= 35:
            print(symbol,' ',rsi)
            if rsi <=30:
                print('☆')
        time.sleep(1)
        
    for ticker in tickers:
        rsiindex(ticker)