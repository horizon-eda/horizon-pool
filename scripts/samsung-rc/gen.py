import json
import uuid
import os
from os.path import join as pj
import sys
sys.path.append("..")
import util

with open("rc.json", "r") as fi :
	j_raw = json.load(fi)

pkgs = set()
tcs = set()

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

muls = {
	"k": 1e3,
	"M": 1e6,
}

bases = {
"0402": "fcd01937-22a6-4569-bec7-78cf999d3bb3",
"0603": "7d6fb163-8671-4026-91b0-5137e70ff04b",
"0805": "4783cd85-1010-4602-8fe2-459f0e0c26e9",
"1206": "c8ca9ff5-d694-4549-adef-4a8c45463d83",
}

def xlat_tol(tol) :
	if tol == '0.05ohm Max' :
		return 1
	else :
		return int(tol[-1])

def xlat_pmax(pmax) :
	if '/' in pmax :
		a = [float(x) for x in pmax.split("/")]
		return a[0]/a[1]
	else :
		return float(pmax)

pool_path = os.getenv("HORIZON_POOL")
if pool_path is None :
	raise IOError("need HORIOZN_POOL")

base_path = pj(pool_path, "parts", "passive", "resistor", "samsung", "rc")

gen = util.UUIDGenerator("uu.txt")


pmaxs = set()
for row in j_raw["rows"] :
	mpn = row["parnum"]
	pkg = row["sizcd_eia"]
	rval = row["rval"][:-1]
	if rval[-1] in muls :
		value = float(rval[:-1])*muls[rval[-1]]
	else :
		value = float(rval)
	tol = xlat_tol(row['tol'])
	
	pmax = row['ratpow']
	pmax = xlat_pmax(pmax.split("W")[0])
	
	if pkg in bases :
		pmaxs.add(row['ratpow'])
		tmpl["base"] = bases[pkg]
		tmpl["MPN"] = [False, mpn]
		tmpl["value"] = [False, util.format_si(value, 2) + "Ω"]
		tmpl["description"] = [False, "Chip Resistor %sΩ %d%% %gW"%(util.format_si(value, 2), tol, pmax)]
		tmpl["uuid"] = str(gen.get(mpn))
		tmpl["parametric"]["pmax"] = str(pmax)
		tmpl["parametric"]["value"] = str(value)
		tmpl["parametric"]["tolerance"] = str(tol)
		path = pj(base_path, pkg)
		os.makedirs(path, exist_ok = True)
		with open(pj(path, mpn+".json"), "w") as fi:
			json.dump(tmpl, fi, sort_keys=True, indent=4)
