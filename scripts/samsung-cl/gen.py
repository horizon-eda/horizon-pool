import json
import uuid
import os
from os.path import join as pj
import sys
sys.path.append("..")
import util
import copy

with open("cl_fmt.json", "r") as fi :
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
        "table": "capacitors"
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
	"uF": 1e-6,
	"nF": 1e-9,
	"pF": 1e-12,
}

bases = {
"1206": "c4c17049-251e-4159-99de-1d8203300811",
"0603": "80ca3c5b-c9cd-4412-bd87-cde4b7bf0b7f",
"0402": "5f11876f-0433-45dc-a306-8f7d0f24e00c",
"0805": "b00f7f9a-540d-4440-a73a-32732a8a8027",
"1210": "6ec346b2-29c6-4bc8-a5dd-a584dc7ad3e9"
}

def xlat_type(ty) :
	if ty == "C0G":
		return "C0G/NP0"
	else :
		return ty

pool_path = os.getenv("HORIZON_POOL")
if pool_path is None :
	raise IOError("need HORIOZN_POOL")

base_path = pj(pool_path, "parts", "passive", "capacitor", "samsung", "cl")

gen = util.UUIDGenerator("uu.txt")


tols = set()

parts = {}

for row in j_raw["rows"] :
	full_mpn = row["parnum"]
	vmax = float(row["ratvol"])
	pkg = row["sizcd_eia"]
	tc = row["tc"]
	tol = None
	if row["toluni"] == "%" :
		rtol = row["tol"]
		if "±" in rtol  :
			tol = int(rtol[2:])
		
	tols.add(tol)
	value = row["cap"]*muls[row["capuni"]]
	ds = "http://www.samsungsem.com/kr/support/product-search/mlcc/%s.jsp"%full_mpn
	tcs.add(tc)
	pkgs.add(pkg)
	mpn = full_mpn[:-1]
	print(mpn, full_mpn)
	if mpn in parts.keys() :
		parts[mpn][1]["orderable_MPNs"][str(gen.get(full_mpn))] = full_mpn
	else :
		print(mpn, tol)
		if pkg in bases :
			tmpl["base"] = bases[pkg]
			tmpl["MPN"] = [False, mpn]
			tmpl["value"] = [False, util.format_si(value, 1) + "F"]
			tmpl["description"] = [False, "Ceramic Capacitor %sF %sV %s"%(util.format_si(value, 1), util.format_si(vmax, 1), tc)]
			tmpl["datasheet"] = [False, ds]
			tmpl["uuid"] = str(gen.get(mpn))
			tmpl["parametric"]["wvdc"] = str(vmax)
			tmpl["parametric"]["value"] = "%.4e"%value
			tmpl["parametric"]["type"] = xlat_type(tc)
			tmpl["orderable_MPNs"] = {}
			tmpl["orderable_MPNs"][str(gen.get(full_mpn))] = full_mpn
			if tol is not None :
				tmpl["parametric"]["tolerance"] = str(tol)
			parts[mpn] = pkg, copy.deepcopy(tmpl)
			""""path = pj(base_path, pkg)
			os.makedirs(path, exist_ok = True)
			with open(pj(path, mpn+".json"), "w") as fi:
				json.dump(tmpl, fi, sort_keys=True, indent=4)"""


for mpn, (pkg, part) in parts.items() :
	print("write", mpn)
	path = pj(base_path, pkg)
	os.makedirs(path, exist_ok = True)
	with open(pj(path, mpn+".json"), "w") as fi:
		json.dump(part, fi, sort_keys=True, indent=4)
