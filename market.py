import requests
from datetime import datetime
import streamlit as st
import pandas as pd

st.title("OSRS Grand Exchange Data")

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

def get24hrData():
    test = requests.get('https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=5m&id='+itemNumber, headers=headers)
    test = test.json()
    test = test['data']
    low = avgLow(test)
    high = avgHigh(test)
    st.write(f"Average High: {high}\n\nAverage low: {low}")
    st.write("Use Scroll Wheel to Zoom in on the Chart")
    printChart(test)

def getLatestData():
    req = requests.get("https://prices.runescape.wiki/api/v1/osrs/latest?id="+itemNumber, headers=headers).json()
    #print(req['data'][itemNumber]['highTime'])
    time = datetime.fromtimestamp(req['data'][itemNumber]['highTime'])
    now = datetime.now()
    nowMin = now.minute
    high = req['data'][itemNumber]['high']
    low = req['data'][itemNumber]['low']
    tax = (high*.01)//1
    margin = high - low - tax
    st.write(f"Insta Buy Price: {high}\n\nInsta Sell Price: {low}\n\nMargin: {margin}")
    st.write(f'Last sold {nowMin - time.minute} minute(s) ago.')

def printChart(d):
    
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
        time = time.strftime("%H:%M")
        timeList.append(time)
    
    df = pd.DataFrame({
        'avgLowPrice': lowPrice,
        'avgHighPrice': highPrice,
        'timestamp':timeList
    })
    st.line_chart(df, x='timestamp')
    
try:
    itemName = st.text_input('Type item name: ')
    #print(itemList['25672'])
    
    itemName = itemName.lower()
    itemName = itemName.capitalize()
    
    itemNumber = itemSearch(itemList, itemName)
    
    num = int(itemNumber)
except(TypeError, NameError):
    st.write('Please make sure item is spelled and spaced correctly.')

st.write('The current item is:', itemName)

options = {
    "Latest Data":getLatestData,
    "24 Hour History":get24hrData,
}

try:
    selected_option = st.selectbox("Select Option...", list(options.keys()), index=None)
    options[selected_option]()
except KeyError:
    st.write()
    


# st.selectbox(
#     "What information would you like to see?",
#     ("Latest Data", "24 Hour History"),
#     index=None,
#     placeholder="Select option...",
# )











# loop = True

# while loop:
#     try:
#         itemName = st.text_input('Type item name: ')
#     #print(itemList['25672'])
    
#         st.write('The current item is:', itemName)

#         itemName = itemName.lower()
#         itemName = itemName.capitalize()
    
#         itemNumber = itemSearch(itemList, itemName)
    
#         num = int(itemNumber)
#     except(TypeError, NameError):
#         st.write('Please make sure item is spelled and spaced correctly.')
#         continue
#     break

#get5minData()