# -*- coding: utf-8 -*-
"""
Created on Mon May 31 11:24:24 2021
Streaming real time stock price data for ITC(less than 1 sec);
Support and Resistance alert using historical Value at risk and
simulated one with monte carlo technique. Supported with real time notification alert
using telegram
@author: Priyanka Choudhary
"""
import requests
import time
import numpy as np
import pandas as pd
import yfinance as yf
#import plotly.graph_objs as go
import datetime
from scipy.stats import norm
from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import pandas as pd
import os

cwd = os.chdir("D:\Algorithmic Trading_internship")

# global variables
bot_token = '############################################'
chat_id = '##########'
# fn to send_message through telegram
def send_message(chat_id, msg):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={msg}"

    # send the msg
    requests.get(url) 

#To calculate the VAR for last 14 days
data=yf.download(tickers='ITC.NS', period='14d', interval='1h')
p=data['Close']
y=data['Close'][len(data)-1]
returns=p.pct_change()
avg_rets = np.mean(returns)
std_rets = np.std(returns)
Z_95 = norm.ppf(0.05, avg_rets, std_rets)
k=Z_95
Paramatric VAR = y*k*std_rets
HistVAR = y*np.percentile(returns.dropna(), 1)
print('Historic VAR is', HistVAR)

#VaR using Monte Carlo Technique for 100000 simulations
np.random.seed(4)
n_sims = 10000000
sim_returns = np.random.normal(avg_rets, std_rets, n_sims)
SimVAR = y*np.percentile(sim_returns, 1)
print('Simulated VAR is ', SimVAR)

#defining resistance and support levels as resistance=last closing price + VAR Level
#Support= Last Closing price - VAR Level
data['Resistance Alert']= data['Close'][len(data)-2]+abs(HistVAR)*0.01*data['Close'][len(data)-2]
data['Support Alert']=data['Close'][len(data)-2]-abs(HistVAR)*0.01*data['Close'][len(data)-2]

## Function to send a msg when the resistance and support levels are activated
def msg_sralert(ticks):
    for tick in ticks:
        print(ticks)
        try:
            while True:
                if tick['last_price']>data['Resistance Alert'][len(data)-1]:
                    send_message(chat_id=chat_id, msg=f'ITC Resistance Alert is activated')
                    #Execute sell order
                elif tick['last_price']<data['Support Alert'][len(data)-1]:
                    send_message(chat_id=chat_id, msg=f'ITC Support Alert is activated')
                    #Execute buy order
        except Exception as e:
            print(e)
            pass 
        
#generate trading session using access token
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

#get all NSE instruments
instrument_dump = kite.instruments("NSE")
instrument_df = pd.DataFrame(instrument_dump)

#function to find the symbols for the ticker from the instrument token
def tokenLookup(instrument_df,symbol_list):
    """Looks up instrument token for a given script from instrument dump"""
    token_list = []
    for symbol in symbol_list:
        token_list.append(int(instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]))
    return token_list

#using ITC to proceed
tickers = ["ITC"]
#create KiteTicker object
kws = KiteTicker(key_secret[0],kite.access_token)
tokens = tokenLookup(instrument_df,tickers)

# function which takes the ticks and sends alerts based on the msg_sralert function
def on_ticks(ws,ticks):
    msg_sralert(ticks)
    print(ticks)

def on_connect(ws,response):
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_LTP,tokens)
kws.on_ticks=on_ticks
kws.on_connect=on_connect
kws.connect()

#Source: 1. https://www.udemy.com/course/algorithmic-trading-on-zerodha-kiteconnect-platform/ 
#2. https://thecodingpie.com/post/lets-build-a-real-time-bitcoin-price-notification-python-project
#3.Kiteconnect documentation