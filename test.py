from fflights import parse
from primp import Client

client = Client()
res = client.get(
    "https://www.google.com/travel/flights/search?tfs=CBwQAhooEgoyMDI1LTA5LTEwagwIAhIIL20vMGZ0a3hyDAgDEggvbS8wMTU2cRooEgoyMDI1LTA5LTEyagwIAxIIL20vMDE1NnFyDAgCEggvbS8wZnRreEABSAFwAYIBCwj___________8BmAEB"
)

with open(".html", "wb") as f:
    f.write(res.content)

parse(res.text)
