import requests
from datetime import datetime
import streamlit as st
import pandas as pd


headers = {
    'User-Agent': 'osrsMarket app',
    'From': 'dlnmtchll@gmail.com' 
}

response = requests.get("https://www.osrsbox.com/osrsbox-db/items-summary.json")
itemList = response.json()

def itemSearch(d, name):
    for key in d:
        for value in d[key]:
            if itemList[key][value] == name:
                return key
    return

def avgHigh(d):
    sum = 0
    counter = 0
    for key in d:
        low = key['avgHighPrice']
        if low != None:
            sum += low
            counter += 1
    return sum//counter

def avgLow(d):
    sum = 0
    counter = 0
    for key in d:
        high = key['avgLowPrice']
        if high != None:
            sum += high
            counter += 1
    return sum//counter

def get5minData():
    test = requests.get('https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=5m&id='+itemNumber, headers=headers)
    test = test.json()
    test = test['data']
    low = avgLow(test)
    high = avgHigh(test)
    tax = (high*.01)//1
    margin = high - low - tax
    print(f'Average High: {high}\nAverage low: {low}\nMargin: {margin}')

def getLatestData():
    req = requests.get("https://prices.runescape.wiki/api/v1/osrs/latest?id="+itemNumber, headers=headers).json()
    print(req['data'][itemNumber]['highTime'])
    time = datetime.fromtimestamp(req['data'][itemNumber]['highTime'])
    now = datetime.now()
    nowMin = now.minute
    
    print(f'Last sold {nowMin - time.minute} minute(s) ago.')

# def printChart(d):
#     df = pd.DataFrame(d)
#     st.line_chart(df)
    

loop = True
while loop:
    
    itemName = input('Type item name: ')
    #print(itemList['25672'])
    itemName = itemName.lower()
    itemName = itemName.capitalize()
    
    itemNumber = itemSearch(itemList, itemName)
    try:
        num = int(itemNumber)
    except TypeError:
        print('Please make sure item is spelled and spaced correctly.')
        continue
    break
            
get5minData()