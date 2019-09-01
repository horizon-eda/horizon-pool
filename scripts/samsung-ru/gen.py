import json
import uuid
import os
from os.path import join as pj
import sys
sys.path.append("..")
import util

tmpl = json.loads("""
{
    "MPN": [
        false,
        "RC0603DR-071K05L"
    ],
    "base": "9954497f-10af-4158-934b-3b53068f6de4",
    "datasheet": [
        true,
        ""
    ],
    "description": [
        false,
        "SMD Resistor General Purpose 1.05 kΩ 0.5% 0.1W"
    ],
    "inherit_model": true,
    "inherit_tags": true,
    "manufacturer": [
        true,
        ""
    ],
    "model": "96c366ee-a963-41a0-9cc8-54c646979695",
    "parametric": {
        "pmax": "0.1",
        "table": "resistors",
        "tolerance": "0.5",
        "value": "1050"
    },
    "tags": [],
    "type": "part",
    "uuid": "9cb3c59c-1e26-45e3-a77d-1aecf23802b4",
    "value": [
        false,
        "1.05 kΩ"
    ]
}
""")


with open("ru.txt") as fi:
	l = [x.strip().split("\t") for x in fi.readlines()]

bases = {
"1206": "18abe45f-715b-4d6c-b6fb-53c8cb4104ac",
"0603": "7e7a7e7e-4697-48a7-9bc9-36190b557ac9",
"0402": "3f5268a0-f33b-4443-bec7-aa7e3b285c6a",
"0805": "bf3fe998-9412-4076-b25c-e12d8d712527"
}

pool_path = os.getenv("HORIZON_POOL")
if pool_path is None :
	raise IOError("need HORIOZN_POOL")

base_path = pj(pool_path, "parts", "passive", "resistor", "samsung", "ru")

gen = util.UUIDGenerator("uu.txt")

for mpn, a, value, pmax, b, pkg, c, tol, *_ in l :
	pkg = pkg.split("(")[1][:-1]
	tol = int(tol[1])
	pmax = float(pmax.split("(")[1][:-2])
	value = int(value[:-2])/1e3
	print(mpn, value, pmax, pkg, tol)
	if pkg in bases :
		tmpl["base"] = bases[pkg]
		tmpl["MPN"] = [False, mpn]
		tmpl["value"] = [False, str(int(value*1e3)) + " mΩ"]
		tmpl["description"] = [False, "SMD Resistor Current Sensing %d mΩ %d%% %sW"%(value*1e3, tol, str(pmax))]
		tmpl["uuid"] = str(gen.get(mpn))
		tmpl["parametric"]["pmax"] = str(pmax)
		tmpl["parametric"]["value"] = str(value)
		tmpl["parametric"]["tolerance"] = str(tol)
		path = pj(base_path, pkg)
		os.makedirs(path, exist_ok = True)
		with open(pj(path, mpn+".json"), "w") as fi:
			json.dump(tmpl, fi, sort_keys=True, indent=4)
