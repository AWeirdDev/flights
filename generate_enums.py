# i forgot how to use pandas lol

with open("./airports.csv", "r", encoding="utf-8") as file:
    lines = file.readlines()[1:]

t = """from enum import Enum

class Airport(Enum):
"""

for line in lines:
    columns = line.split(",")
    name = "_".join(
        columns[2]
        .replace("-", " ")
        .replace(".", " ")
        .replace("/", " ")
        .replace("'", "")
        .replace("(", " ")
        .replace(")", " ")
        .replace("–", " ")
        .split()
    ).upper()

    if "AIRPORT" not in name:
        continue

    if name in t:
        continue

    generated = " " * 4 + name + " = '" + columns[0] + "'\n"
    t += generated
    print(generated[:-1])


with open("./_generated_enum.py", "wb") as f:
    f.write(t.encode("utf-8"))
