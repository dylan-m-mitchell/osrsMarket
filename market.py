import requests

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
        low = key['avgLowPrice']
        if low != None:
            sum += low
            counter += 1
    print(f'average low: {sum//counter}')

def avgLow(d):
    sum = 0
    counter = 0
    for key in d:
        high = key['avgHighPrice']
        if high != None:
            sum += high
            counter += 1
    print(f'average high: {sum//counter}')


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
            
test = requests.get('https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=5m&id='+itemNumber, headers=headers)
#print(test.json())
test = test.json()
test = test['data']
avgHigh(test)
avgLow(test)