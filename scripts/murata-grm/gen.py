import json
import uuid
import os
from os.path import join as pj
import sys
sys.path.append("..")
import util
import copy
import csv

tmpl = json.loads("""
{
    "MPN": [
        false,
        "GRM???"
    ],
    "base": "xxx",
    "datasheet": [
        true,
        ""
    ],
    "orderable_MPNs" : {},
    "description": [
        false,
        "MLCC General Purpose ? F, ?V, ?"
    ],
    "inherit_model": true,
    "inherit_tags": true,
    "manufacturer": [
        true,
        ""
    ],
    "model": "96c366ee-a963-41a0-9cc8-54c646979695",
    "parametric": {
        "table": "capacitors"
    },
    "tags": [],
    "type": "part",
    "uuid": "9cb3c59c-1e26-45e3-a77d-1aecf23802b4",
    "value": [
        false,
        "? F"
    ]
}
""")

bases = {
    "15": "18d5b7ae-d01a-4a38-9142-71c03eb0cde1", # 0402
    "18": "cab72b27-6d92-47d2-9694-d5f2b4b74d91", # 0603
    "21": "25c6bdc4-a874-4ace-8e9c-1f7a3ca96c82", # 0805
    "31": "7bb37d2c-745b-4f9f-abb5-5485b58e86e5", # 1206
    "32": "e747f155-6606-4a43-b5fd-69c43dc541fd", # 1210
}

def check_size(part, package):
    sizes = {
        "15": ("1.0", "0.5"),
        "18": ("1.6", "0.8"),
        "21": ("2.0", "1.25"),
        "31": ("3.2", "1.6"),
        "32": ("3.2", "2.5")
    }[package]
    
    if not part["Length"].startswith(sizes[0]):
        print(f"Part {part['Part Number']} failed length check {sizes[0]} != {part['Length']}")
    
    if not part["Width"].startswith(sizes[1]):
        print(f"Part {part['Part Number']} failed width check {sizes[1]} != {part['Width']}")

temp_characteristics = {
    "1X": "SL",
    "2C": "CH",
    "3C": "CJ",
    "3U": "UJ",
    "4C": "CK",
    "5C": "C0G",
    "6C": "C0H",
    "7U": "U2J",
    "B1": "B",
    "B3": "B",
    "C6": "X5S",
    "C7": "X7S",
    "C8": "X6S",
    "D7": "X7T",
    "D8": "X6T",
    "E7": "X7U",
    "R1": "R",
    "R6": "X5R",
    "R7": "X7R"
}

def decode_temp(part, temp_code):
    try:
        temp_characteristic = temp_characteristics[temp_code]
    except KeyError:
        # print("Unknown: ", temp_code, part["Temperature characteristics"])
        return None
        
    if not part["Temperature characteristics"].startswith(temp_characteristic + "("):
        print(f"Part {part['Part Number']} failed tempco check {temp_characteristic} != {part['Temperature characteristics']}")

    if temp_characteristic == "C0G":
        temp_characteristic = "C0G/NP0"

    return temp_characteristic

rated_voltages = {
    "0E": 2.5,
    "0G": 4,
    "0J": 6.3,
    "1A": 10,
    "1C": 16,
    "1D": 20,
    "1E": 25,
    "1H": 50,
    "1J": 63,
    "1K": 80,
    "2A": 100,
    "2D": 200,
    "2E": 250,
    "2W": 450,
    "2H": 500,
    "2J": 630,
    "3A": 1000,
    "3D": 2000,
    "3F": 3150,
    "YA": 35,
}

def decode_voltage(part, volt_code):
    try:
        rated_voltage = rated_voltages[volt_code]    
    except KeyError:
        print("Unknown: ", volt_code, part["Rated Voltage"])
        return None
    
    if not part["Rated Voltage"] == f"{rated_voltage}Vdc":
        print(f"Part {part['Part Number']} failed voltage check {rated_voltage} != {part['Rated Voltage']}")

    return rated_voltage

def decode_cap(part, cap_code, cap_mul):
    if "R" in cap_code:
        cap_code = cap_code.replace("R", ".")
        cap_pf = float(cap_code + cap_mul)
    else:
        cap_pf = float(cap_code) * (10 ** int(cap_mul))

    def format_float(n):
        if n.is_integer():
            return int(n)
        else:
            return n

    if cap_pf >= 100e3:
        cap_uf = cap_pf / 1e6
        cap_text = f"{format_float(cap_uf)}μF"
    else:
        cap_text = f"{format_float(cap_pf)}pF"
        
    if not part["Capacitance"] == cap_text:
        print(f"Part {part['Part Number']} failed capacitance check {cap_text} != {part['Capacitance']}")

    return cap_pf / 1e12

cap_tolerances = {
    "B": None,
    "C": None,
    "D": None,
    "F": 1,
    "G": 2,
    "J": 5,
    "K": 10,
    "M": 20,
    "W": None,
}

def decode_cap_tol(part, cap_tol_code):
    try:
        cap_tol = cap_tolerances[cap_tol_code]
    except KeyError:
        print("Unknown: ", cap_tol_code, part["Tolerance of capacitance"])
        return None

    if cap_tol == None:
        return None
    
    if not part["Tolerance of capacitance"] == f"±{cap_tol}%":
        print(f"Part {part['Part Number']} failed tolerance check {cap_tol} != {part['Tolerance of capacitance']}")

    return cap_tol

pool_path = os.getenv("HORIZON_POOL")
if pool_path is None :
	raise IOError("need HORIZON_POOL")

base_path = pj(pool_path, "parts", "passive", "capacitor", "murata")

gen = util.UUIDGenerator("uu.txt")

def process(part):
    # print(part)
    part_number = part["Part Number"]

    series = part_number[0:3]
    package = part_number[3:5]
    temp_code = part_number[6:8]
    volt_code = part_number[8:10]
    cap_code = part_number[10:12]
    cap_mul = part_number[12]
    cap_tol = part_number[13]

    if series != "GRM":
        print(f"Non-GRM part! {part_number}")
        return

    if not package in bases.keys():
        return

    check_size(part, package)
    temp_characteristic = decode_temp(part, temp_code)
    rated_voltage = decode_voltage(part, volt_code)
    capacitance = decode_cap(part, cap_code, cap_mul)
    tolerance = decode_cap_tol(part, cap_tol)

    if temp_characteristic == None:
        return

    if not part_number[-1] == "#":
        print("Oops!")
    part_number = part_number[0:-1]
    datasheet = f"https://www.murata.com/en-us/products/productdetail.aspx?partno={part_number}%23"
    capacitance_format = util.format_si(capacitance, 1) + "F"

    tmpl["base"] = bases[package]
    tmpl["MPN"] = [False, part_number]
    tmpl["value"] = [False, capacitance_format]
    tmpl["description"] = [False, f"MLCC General Purpose {capacitance_format}, {util.format_si(rated_voltage, 1)}V, {temp_characteristic}"]
    tmpl["datasheet"] = [False, datasheet]
    tmpl["uuid"] = str(gen.get(part_number))
    tmpl["parametric"]["wvdc"] = str(rated_voltage)
    tmpl["parametric"]["value"] = "%.4e" % capacitance
    tmpl["parametric"]["type"] = temp_characteristic
    if tolerance is not None:
        tmpl["parametric"]["tolerance"] = str(tolerance)
    else:
        tmpl["parametric"].pop("tolerance", None)

    path = pj(base_path, f"grm{package}")
    os.makedirs(path, exist_ok = True)
    with open(pj(path, f"{part_number}.json"), "w") as f:
        json.dump(tmpl, f, sort_keys=True, indent=4)
    
# https://www.murata.com/en-global/products/capacitor/ceramiccapacitor/smd/grm -> Download CSV
# https://www.murata.com/en-global/search/CsvStandby?stype=1&lang=en&partno=GRM&cate=luCeramicCapacitorsSMD
with open("grm.csv", newline='', encoding="utf-8-sig") as csvfile:
    csv = csv.DictReader(csvfile)
    for part in csv:
        process(part)
    
