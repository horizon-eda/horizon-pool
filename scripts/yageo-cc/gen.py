import json
import uuid
import os
from os.path import join as pj
import sys
sys.path.append("..")
import util
from bs4 import BeautifulSoup
import copy

with open("yageo.html") as fi:
	soup = BeautifulSoup(fi, 'lxml')

pkgs=set()
tcs=set()

tmpl = json.loads("""
{
    "MPN": [
        false,
        "RC0603DR-071K05L"
    ],
    "orderable_MPNs" : {},
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
"1206": "0c75bc97-bb58-4283-b5e5-0795d24f46e7",
"0603": "6f27eb66-40e7-4dcc-baa1-887f336d41ed",
"0402": "6c8302f6-8c7d-4cb2-b04f-e3ce9fa8b311",
"0805": "35791498-ef97-4a72-9d63-d4468b213ec2",
"1210": "a9067048-3070-4df6-b961-c0d409b7f4d0"
}

def xlat_type(ty) :
	if ty == "NP0":
		return "C0G/NP0"
	else :
		return ty

pool_path = os.getenv("HORIZON_POOL")
if pool_path is None :
	raise IOError("need HORIOZN_POOL")

base_path = pj(pool_path, "parts", "passive", "capacitor", "yageo", "cc")

gen = util.UUIDGenerator("uu.txt")

parts = {}
for row in soup.find('table').find_all('tr')[1:] :
	tds = row.find_all('td')
	full_mpn = str(tds[0].contents[0])
	mpn = full_mpn
	mpn = list(mpn)
	mpn[7] = '_'
	mpn = ''.join(mpn)
	if len(tds[1].contents) :
		pkg = tds[1].contents[0].split("(")[0]
		tc = str(tds[3].contents[0])
		ttol = tds[2].contents
		tol = None
		if len(ttol) :
			ttol = str(ttol[0])
			if ttol.startswith("±") and ttol.endswith("%") :
				tol = int(ttol[1:-1])
		print(mpn)
		tcs.add(tc)
		vmax = float(tds[4].contents[0][:-1].strip())
		value = float(tds[5].contents[0].replace(",", ""))*1e-12
		pkgs.add(pkg)
		ds = "http://www.yageo.com/portal/product/productDocs.jsp?YageoPartNumber="+full_mpn
		if mpn in parts.keys() :
			parts[mpn][1]["orderable_MPNs"][str(gen.get(full_mpn))] = full_mpn
		else :
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
					if tol is not None :
						tmpl["parametric"]["tolerance"] = str(tol)
					tmpl["orderable_MPNs"] = {}
					tmpl["orderable_MPNs"][str(gen.get(full_mpn))] = full_mpn
					parts[mpn] = pkg, copy.deepcopy(tmpl)

for mpn, (pkg, part) in parts.items() :
	path = pj(base_path, pkg)
	os.makedirs(path, exist_ok = True)
	with open(pj(path, mpn+".json"), "w") as fi:
		json.dump(part, fi, sort_keys=True, indent=4)

