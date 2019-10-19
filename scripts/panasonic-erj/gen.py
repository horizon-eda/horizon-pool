import json
import uuid
import os
from os.path import join as pj
import sys
sys.path.append("..")
import util
import copy

#https://mf2ap002.marsflag.com/product-search-api/1.0/panasonic_device/RDA0000_WW?start=0&rows=2000000&_=1569774971900
with open("erj.json", "r") as fi :
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
    "orderable_MPNs" : {},
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

bases = {
"0402": "7f3cde91-d80e-4fd9-9053-b6cbe78f31fd",
"0603": "25f985ce-3357-4a0f-b19d-4866ef892436",
"0805": "3b6ec949-50f9-4ac5-a9d6-fa2ae04a8869",
"1206": "3cfc0897-cdc4-462f-ade4-f41bdf2bac54",
}

def xlat_tol(tol) :
	if tol == 'Not specified' :
		return 1
	elif tol == 'Other' :
		return 1
	else :
		return float(tol)

pool_path = os.getenv("HORIZON_POOL")
if pool_path is None :
	raise IOError("need HORIOZN_POOL")

base_path = pj(pool_path, "parts", "passive", "resistor", "panasonic", "erj")

gen = util.UUIDGenerator("uu.txt")
pmaxs=set()

pmax_pkg = {
	"0402":.1,
	"0603":.1,
	"0805":.125,
	"1206":.25,
}


parts = {}

for row in j_raw["response"]["docs"] :
	pkg = row["spec_item_code_001"]["raw"]
	if 'EIA' in pkg :
		pkg = pkg.split(":")[1][:-1]
		value = float(row["spec_item_code_005"]["raw"])
		
		tol = xlat_tol(row["spec_item_code_004"]["raw"])
		datasheet_url = row["catalog_url"]["raw"]
		pmax = pmax_pkg.get(pkg, 0)
		if "spec_item_code_006" in row :
			pmax = float(row["spec_item_code_006"]["raw"])
		pmaxs.add(pmax)
		full_mpn = row["item_id"]["raw"]
		mpn = full_mpn[:-1]
		print(mpn, full_mpn)
		if mpn in parts.keys() :
			parts[mpn][1]["orderable_MPNs"][str(gen.get(full_mpn))] = full_mpn.replace("ERJ", "ERJ-")
		else :
			if pkg in bases :
				tmpl["base"] = bases[pkg]
				tmpl["MPN"] = [False, mpn.replace("ERJ", "ERJ-")]
				tmpl["datasheet"] = [False, datasheet_url]
				tmpl["value"] = [False, util.format_si(value, 2) + "Ω"]
				tmpl["description"] = [False, "Chip Resistor %sΩ %d%% %gW"%(util.format_si(value, 2), tol, pmax)]
				tmpl["uuid"] = str(gen.get(mpn))
				tmpl["parametric"]["pmax"] = str(pmax)
				tmpl["parametric"]["value"] = str(value)
				tmpl["parametric"]["tolerance"] = str(tol)
				tmpl["orderable_MPNs"] = {}
				tmpl["orderable_MPNs"][str(gen.get(full_mpn))] = full_mpn.replace("ERJ", "ERJ-")
				parts[mpn] = pkg, copy.deepcopy(tmpl)

for mpn, (pkg, part) in parts.items() :
	print("write", mpn)
	path = pj(base_path, pkg)
	os.makedirs(path, exist_ok = True)
	with open(pj(path, mpn.replace("ERJ", "ERJ-")+".json"), "w") as fi:
		json.dump(part, fi, sort_keys=True, indent=4)
