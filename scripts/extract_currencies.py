import rjsonc
import json

DATA = """
AF_initDataCallback({key: 'ds:4', hash: '3', data:[[["ALL","Albanian Lek","ALL",0],["DZD","Algerian Dinar","DZD",0],["ARS","Argentine Peso","ARS",0],["AMD","Armenian Dram","AMD",0],["AWG","Aruban Florin","AWG",0],["AUD","Australian Dollar","A$",0],["AZN","Azerbaijani Manat","AZN",0],["BSD","Bahamian Dollar","BSD",0],["BHD","Bahraini Dinar","BHD",0],["BYN","Belarusian Ruble","BYN",0],["BMD","Bermudan Dollar","BMD",0],["BAM","Bosnia-Herzegovina Convertible Mark","BAM",0],["BRL","Brazilian Real","R$",0],["GBP","British Pound","£",1],["BGN","Bulgarian Lev","BGN",0],["CAD","Canadian Dollar","CA$",0],["XPF","CFP Franc","CFPF",0],["CLP","Chilean Peso","CLP",0],["CNY","Chinese Yuan","CN¥",0],["COP","Colombian Peso","COP",0],["CRC","Costa Rican Colón","CRC",0],["CUP","Cuban Peso","CUP",0],["CZK","Czech Koruna","CZK",0],["DKK","Danish Krone","DKK",0],["DOP","Dominican Peso","DOP",0],["EGP","Egyptian Pound","EGP",0],["EUR","Euro","€",1],["GEL","Georgian Lari","GEL",0],["HKD","Hong Kong Dollar","HK$",0],["HUF","Hungarian Forint","HUF",0],["ISK","Icelandic Króna","ISK",0],["INR","Indian Rupee","₹",0],["IDR","Indonesian Rupiah","IDR",0],["IRR","Iranian Rial","IRR",0],["ILS","Israeli New Shekel","₪",0],["JMD","Jamaican Dollar","JMD",0],["JPY","Japanese Yen","¥",1],["JOD","Jordanian Dinar","JOD",0],["KZT","Kazakhstani Tenge","KZT",0],["KWD","Kuwaiti Dinar","KWD",0],["LBP","Lebanese Pound","LBP",0],["MKD","Macedonian Denar","MKD",0],["MYR","Malaysian Ringgit","MYR",0],["MXN","Mexican Peso","MX$",0],["MDL","Moldovan Leu","MDL",0],["MAD","Moroccan Dirham","MAD",0],["TWD","New Taiwan Dollar","NT$",1],["NZD","New Zealand Dollar","NZ$",0],["NOK","Norwegian Krone","NOK",0],["OMR","Omani Rial","OMR",0],["PKR","Pakistani Rupee","PKR",0],["PAB","Panamanian Balboa","PAB",0],["PEN","Peruvian Sol","PEN",0],["PHP","Philippine Peso","₱",0],["PLN","Polish Zloty","PLN",0],["QAR","Qatari Riyal","QAR",0],["RON","Romanian Leu","RON",0],["RUB","Russian Ruble","RUB",0],["SAR","Saudi Riyal","SAR",0],["RSD","Serbian Dinar","RSD",0],["SGD","Singapore Dollar","SGD",0],["ZAR","South African Rand","ZAR",0],["KRW","South Korean Won","₩",0],["SEK","Swedish Krona","SEK",0],["CHF","Swiss Franc","CHF",0],["THB","Thai Baht","THB",0],["TRY","Turkish Lira","TRY",0],["UAH","Ukrainian Hryvnia","UAH",0],["AED","United Arab Emirates Dirham","AED",0],["USD","US Dollar","$",1],["VND","Vietnamese Dong","₫",0]]], sideChannel: {}});
"""

script_data = DATA.strip().split("(", 1)[1].strip("); ")
currencies = rjsonc.loads(script_data)["data"][0]

items = []
for code, name, _, _ in currencies:
    print(name, end=" ")
    items.append(json.dumps(code))

print()
print(f"Literal[{', '.join(items)}]")
