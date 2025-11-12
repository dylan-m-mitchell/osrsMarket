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

def get24hrData(hours=24):
    test = requests.get('https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=5m&id='+itemNumber, headers=headers)
    test = test.json()
    test = test['data']
    
    # Filter data based on selected hours
    # With 5-minute intervals, we have 12 data points per hour
    data_points_per_hour = 12
    num_data_points = int(hours * data_points_per_hour)
    
    # Get the most recent data points
    filtered_data = test[-num_data_points:] if len(test) > num_data_points else test
    
    low = avgLow(filtered_data)
    high = avgHigh(filtered_data)
    st.write(f"Average High: {high}\n\nAverage low: {low}")
    st.write("Use Scroll Wheel to Zoom in on the Chart")
    printChart(filtered_data)

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

# Time range slider for filtering the 24-hour data
time_range_hours = st.slider(
    "Select time range (hours):",
    min_value=1,
    max_value=24,
    value=24,
    step=1,
    help="Adjust the time window to view data from the last N hours"
)

try:
    get24hrData(time_range_hours)
except Exception as e:
    st.write(f"Error loading data: {e}")
    