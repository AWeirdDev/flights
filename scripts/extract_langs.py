import rjsonc
import json

DATA = """
AF_initDataCallback({key: 'ds:5', hash: '4', data:[[["af","Afrikaans"],["bs","Bosanski"],["ca","Català"],["cs","Čeština"],["da","Dansk"],["de","Deutsch"],["et","Eesti"],["en-GB","English (United Kingdom)"],["en-US","English (United States)"],["es","Español (España)"],["es-419","Español (Latinoamérica)"],["eu","Euskara"],["fil","Filipino"],["fr","Français"],["gl","Galego"],["hr","Hrvatski"],["id","Indonesia"],["is","Íslenska"],["it","Italiano"],["sw","Kiswahili"],["lv","Latviešu"],["lt","Lietuvių"],["hu","Magyar"],["ms","Melayu"],["nl","Nederlands"],["no","Norsk"],["pl","Polski"],["pt-BR","Português (Brasil)"],["pt-PT","Português (Portugal)"],["ro","Română"],["sq","Shqip"],["sk","Slovenčina"],["sl","Slovenščina"],["sr-Latn","Srpski (latinica)"],["fi","Suomi"],["sv","Svenska"],["vi","Tiếng Việt"],["tr","Türkçe"],["el","Ελληνικά"],["bg","Български"],["mk","Македонски"],["mn","Монгол"],["ru","Русский"],["sr","Српски (ћирилица)"],["uk","Українська"],["ka","Ქართული"],["iw","עברית"],["ur","اردو"],["ar","العربية"],["fa","فارسی"],["am","አማርኛ"],["ne","नेपाली"],["mr","मराठी"],["hi","हिन्दी"],["bn","বাংলা"],["pa","ਪੰਜਾਬੀ"],["gu","ગુજરાતી"],["ta","தமிழ்"],["te","తెలుగు"],["kn","ಕನ್ನಡ"],["ml","മലയാളം"],["si","සිංහල"],["th","ไทย"],["lo","ລາວ"],["km","ខ្មែរ"],["ko","한국어"],["ja","日本語"],["zh-CN","简体中文"],["zh-TW","繁體中文"]]], sideChannel: {}});
"""

script_data = DATA.strip().split("(", 1)[1].strip("); ")
langs = rjsonc.loads(script_data)["data"][0]

items = []
for code, name in langs:
    items.append(json.dumps(code))
    print(name, end=" ")

print()
print(f"Literal[{', '.join(items)}]")
