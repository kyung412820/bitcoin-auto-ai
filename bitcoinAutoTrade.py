import time
import pyupbit
import datetime
import pandas as pd
import schedule
from fbprophet import Prophet
import datetime as dt
from slacker import Slacker
import requests
import pytz
utc=pytz.UTC

access = "YttVn2BhLicTA5b02xrZc5ydbqYGjvpnhbP9wTdP"
secret = "LtpkDjfN9gNvEtgA6u3AIMqvx86bQ6rBSLzoqJlq"
myToken = "xoxb-3149418271687-3166344806020-x3ttmDoZxutryjJ037pmS1zH"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

predicted_close_price = 0
def predict_price(ticker):
    """Prophet으로 당일 종가 가격 예측"""
    global predicted_close_price
    df = pyupbit.get_ohlcv(ticker, interval="minute60")
    df = df.reset_index()
    df['ds'] = df['index'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['y'] = df['close']
    data = df[['ds','y']]
    data=pd.DataFrame(data)
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
    if len(closeDf) == 0: 
        closeDf = forecast[forecast['ds'] == datetime.datetime.strptime(data.iloc[-1]['ds'], '%Y-%m-%d %H:%M:%S').replace(hour=9)]
    closeValue = closeDf['yhat'].values[0]
    predicted_close_price = closeValue
    
predict_price("KRW-BTC")
schedule.every().hour.do(lambda: predict_price("KRW-BTC"))

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
post_message(myToken,"#bitcoinauto-ai", "autotrade start")

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        now = now.replace(tzinfo=utc)
        start_time = get_start_time("KRW-BTC") #코인은 장이 24시간이라 하루의 시작을 오전 9시로 적용
        end_time = start_time + datetime.timedelta(days=1) # 담날 9시까지
        schedule.run_pending()

        if start_time < now < end_time - datetime.timedelta(seconds=10):#9->9면 계속 돌아가니 9시부터 담날 8시50분까지 자동으로 돌림
            target_price = get_target_price("KRW-BTC", 0.5)#이걸 변경하면 구매전략 변경됨, 변동성 돌파전략을 이용한 목표가 설정
            current_price = get_current_price("KRW-BTC")
            #print(target_price,current_price,predicted_close_price)
            if target_price < current_price and current_price < predicted_close_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    buy_result = upbit.buy_market_order("KRW-BTC", krw*0.9995)#돌파하면 구매
                    post_message(myToken,"#bitcoinauto-ai", "BTC buy : " +str(buy_result))
        else:
            btc = get_balance("BTC")#담날 오전 8시50분에 전량 매도
            if btc > 0.00008:
                sell_result = upbit.sell_market_order("KRW-BTC", btc*0.9995)
                post_message(myToken,"#bitcoinauto-ai", "BTC buy : " +str(sell_result))
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken,"#bitcoinauto-ai", e)
        time.sleep(1)