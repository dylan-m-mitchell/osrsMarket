import requests
from datetime import datetime, timezone, timedelta
import streamlit as st
# import numpy as np
import pandas as pd

headers = {
    'User-Agent': 'osrsMarket app',
    'From': 'dlnmtchll@gmail.com' 
}



def printChart(d):
    print(d)
    timeList = list()
    highPrice = list()
    lowPrice = list()
    highVol = list()
    lowVol = list()
    
    for value in d:
        highPrice.append(value.get('avgHighPrice'))
        lowPrice.append(value.get('avgLowPrice'))
        highVol.append(value.get('highPriceVolume'))
        lowVol.append(value.get('lowPriceVolume'))
        time = datetime.fromtimestamp(value.get('timestamp'))
        #time = time.strftime("%H:%M")
        timeList.append(time)
    
    df = pd.DataFrame({
        'avgLowPrice': lowPrice,
        'avgHighPrice': highPrice,
        'timestamp':timeList
    })
    st.line_chart(df, x='timestamp')
def get5minData():
    test = requests.get('https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=24h&id=21975', headers=headers)
    test = test.json()
    test = test['data']
    printChart(test)

get5minData()