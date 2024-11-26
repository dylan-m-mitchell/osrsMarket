import requests

response = requests.get("https://secure.runescape.com/m=itemdb_oldschool/api/info.json")
print(response.json())

#https://services.runescape.com/m=itemdb_rs/api/catalogue/detail.json?item=X

itemNum = input("Enter item number: ")
#itemLookup = "https://services.runescape.com/m=itemdb_rs/api/catalogue/detail.json?item=" + str(itemNum)
itemLookup = requests.get("https://services.runescape.com/m=itemdb_rs/api/catalogue/detail.json?item=" + str(itemNum))
print(itemLookup.json())