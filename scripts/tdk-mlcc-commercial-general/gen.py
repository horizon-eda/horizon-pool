import json
import uuid
import os
from os.path import join as pj
import sys
sys.path.append("..")
import util
import csv


pkgs=set()
tcs=set()

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


bases = {
"1206": "289abc10-f180-4b00-b24e-fa80c8f5f7d3",
"0603": "1f7d1953-3796-4530-951b-ed671d8d36a0",
"0402": "58b92388-cb19-4e12-9c56-4cb3bf795304",
"0805": "2ab89a61-3fb8-442a-b49d-30b8d28da391",
"1210": "83d58ab9-876c-4255-93f2-2c7b442de2a0"
}

muls = {
	"μF": 1e-6,
	"nF": 1e-9,
	"pF": 1e-12,
}

def xlat_type(ty) :
	if ty in ("CH", "C0G", "NP0"):
		return "C0G/NP0"
	elif ty == "JB":
		return "X5R"
	else :
		return ty

pool_path = os.getenv("HORIZON_POOL")
if pool_path is None :
	raise IOError("need HORIOZN_POOL")

base_path = pj(pool_path, "parts", "passive", "capacitor", "tdk", "c")

gen = util.UUIDGenerator("uu.txt")
tols = set()

with open("tdk.csv") as fi:
	reader = csv.DictReader(fi)
	for row in reader :
		mpn = row['Part No.']
		vmax = float(row['Rated Voltage [DC] / V'])
		tc = xlat_type(row['Temp. Chara.'])
		tcs.add(tc)
		captxt = row['Capacitance']
		toltxt = row['Tolerance']
		tol = None
		if toltxt.endswith("%") :
			tol = int(toltxt[1:-1])
		value = float(captxt[:-2])*muls[captxt[-2:]]
		ds = row['Catalog / Data Sheet'].split()[-1]
		pkg = row['L x W Size'].split('[')[-1].split()[1][:-1]
		pkgs.add(pkg)
		print(mpn, captxt, value)
		if pkg in bases :
			tmpl["base"] = bases[pkg]
			tmpl["MPN"] = [False, mpn]
			tmpl["value"] = [False, util.format_si(value, 1) + "F"]
			tmpl["description"] = [False, "Ceramic Capacitor %sF %sV %s"%(util.format_si(value, 1), util.format_si(vmax, 1), tc)]
			tmpl["datasheet"] = [False, ds]
			tmpl["uuid"] = str(gen.get(mpn))
			tmpl["parametric"]["wvdc"] = str(vmax)
			tmpl["parametric"]["value"] = "%.4e"%value
			tmpl["parametric"]["type"] = tc
			if tol is not None :
				tmpl["parametric"]["tolerance"] = str(tol)
			path = pj(base_path, pkg)
			os.makedirs(path, exist_ok = True)
			with open(pj(path, mpn+".json"), "w") as fi:
				json.dump(tmpl, fi, sort_keys=True, indent=4)
"""
for row in soup.find('table').find_all('tr')[1:] :
	tds = row.find_all('td')
	mpn = tds[0].contents[0]
	if len(tds[1].contents) :
		pkg = tds[1].contents[0].split("(")[0]
		tc = tds[3].contents[0]
		tcs.add(tc)
		vmax = float(tds[4].contents[0][:-1].strip())
		value = float(tds[5].contents[0].replace(",", ""))*1e-12
		pkgs.add(pkg)
		ds = "http://www.yageo.com/portal/product/productDocs.jsp?YageoPartNumber="+mpn
		print(mpn, pkg, vmax, value)
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
			path = pj(base_path, pkg)
			os.makedirs(path, exist_ok = True)
			with open(pj(path, mpn+".json"), "w") as fi:
				json.dump(tmpl, fi, sort_keys=True, indent=4)
"""
