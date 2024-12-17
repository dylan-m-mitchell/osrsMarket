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
            
print(requests.get('https://prices.runescape.wiki/api/v1/osrs/latest?id='+itemNumber, headers=headers).json())
#https://services.runescape.com/m=itemdb_rs/api/catalogue/detail.json?item=X

# itemNum = input("Enter item number: ")
# #itemLookup = "https://services.runescape.com/m=itemdb_rs/api/catalogue/detail.json?item=" + str(itemNum)
# itemLookup = requests.get("https://services.runescape.com/m=itemdb_rs/api/catalogue/detail.json?item=" + str(itemNum))
# print(itemLookup.json())
