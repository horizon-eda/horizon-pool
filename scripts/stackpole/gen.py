import json
from lxml import etree
import os
from os.path import join as pj
import sys

self_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(self_path))

import util
from util import CachedURL, pool_path

# not sure if the TokenID in the url expires after some time... I tried a few
# days after initially using it and, er, the website was down.  If you get a
# 404, 403, 500 or something... open the webpage in a browser and get a new
# token.

urlcache = pj(self_path, 'urlcache.json')
token = 'D2T1B8O19C261'

sources = []
sources.append(CachedURL('http://www.seielect.com/CommonFunctions/XMLProxyFetch.asp?remoteurl='
        + 'https://xmlserve.seielect.com/PartSearchXML.asp&TokenID=%s&XMLUtilMethod=ParametricPartSearch&IMTypeID=13&IMOhmVal1=&IMOhmVal2=&IMObjID=11&IMObjVal_11=0402&IMObjID=5&IMObjVal_5=T&R' % token, urlcache))
sources.append(CachedURL('http://www.seielect.com/CommonFunctions/XMLProxyFetch.asp?remoteurl='
        + 'https://xmlserve.seielect.com/PartSearchXML.asp&TokenID=%s&XMLUtilMethod=ParametricPartSearch&IMTypeID=13&IMOhmVal1=&IMOhmVal2=&IMObjID=11&IMObjVal_11=0402&IMObjID=5&IMObjVal_5=T&R - 10,000 pcs/reel' % token, urlcache))
sources.append(CachedURL('http://www.seielect.com/CommonFunctions/XMLProxyFetch.asp?remoteurl='
        + 'https://xmlserve.seielect.com/PartSearchXML.asp&TokenID=%s&XMLUtilMethod=ParametricPartSearch&IMTypeID=13&IMOhmVal1=&IMOhmVal2=&IMObjID=11&IMObjVal_11=0603&IMObjID=5&IMObjVal_5=T&R' % token, urlcache))
sources.append(CachedURL('http://www.seielect.com/CommonFunctions/XMLProxyFetch.asp?remoteurl='
        + 'https://xmlserve.seielect.com/PartSearchXML.asp&TokenID=%s&XMLUtilMethod=ParametricPartSearch&IMTypeID=13&IMOhmVal1=&IMOhmVal2=&IMObjID=11&IMObjVal_11=0603&IMObjID=5&IMObjVal_5=T&R - 10,000 pcs/reel' % token, urlcache))
sources.append(CachedURL('http://www.seielect.com/CommonFunctions/XMLProxyFetch.asp?remoteurl='
        + 'https://xmlserve.seielect.com/PartSearchXML.asp&TokenID=%s&XMLUtilMethod=ParametricPartSearch&IMTypeID=13&IMOhmVal1=&IMOhmVal2=&IMObjID=11&IMObjVal_11=0805&IMObjID=5&IMObjVal_5=T&R' % token, urlcache))
sources.append(CachedURL('http://www.seielect.com/CommonFunctions/XMLProxyFetch.asp?remoteurl='
        + 'https://xmlserve.seielect.com/PartSearchXML.asp&TokenID=%s&XMLUtilMethod=ParametricPartSearch&IMTypeID=13&IMOhmVal1=&IMOhmVal2=&IMObjID=11&IMObjVal_11=0805&IMObjID=5&IMObjVal_5=T&R - 10,000 pcs/reel' % token, urlcache))
sources.append(CachedURL('http://www.seielect.com/CommonFunctions/XMLProxyFetch.asp?remoteurl='
        + 'https://xmlserve.seielect.com/PartSearchXML.asp&TokenID=%s&XMLUtilMethod=ParametricPartSearch&IMTypeID=13&IMOhmVal1=&IMOhmVal2=&IMObjID=11&IMObjVal_11=1206&IMObjID=5&IMObjVal_5=T&R' % token, urlcache))
sources.append(CachedURL('http://www.seielect.com/CommonFunctions/XMLProxyFetch.asp?remoteurl='
        + 'https://xmlserve.seielect.com/PartSearchXML.asp&TokenID=%s&XMLUtilMethod=ParametricPartSearch&IMTypeID=13&IMOhmVal1=&IMOhmVal2=&IMObjID=11&IMObjVal_11=1206&IMObjID=5&IMObjVal_5=T&R - 10,000 pcs/reel' % token, urlcache))

pkgs = {
    "0402": "3f5268a0-f33b-4443-bec7-aa7e3b285c6a",
    "0603": "7e7a7e7e-4697-48a7-9bc9-36190b557ac9",
    "0805": "bf3fe998-9412-4076-b25c-e12d8d712527",
    "1206": "18abe45f-715b-4d6c-b6fb-53c8cb4104ac",
}

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

if __name__ == '__main__':
    base_path = pj(pool_path, "parts", "passive", "resistor", "stackpole")

    gen = util.UUIDGenerator(pj(self_path, "uu.txt"))

    with open(pj(pool_path, 'tables.json'), 'r') as tablesfd:
        tables = json.load(tablesfd)
    param_cols = tables['tables']['capacitors']['columns']
    param_types = [col for col in param_cols if col['name'] == 'type'][0]
    param_tempchars = param_types['items']

    for s in sources:
        xmltree = etree.fromstring(s())
        types = xmltree.xpath('//Commodity/Type')

        for typ in types:
            typedesc = (typ.xpath('TypeDesc/text()') + [None])[0]
            typefull = (typ.xpath('TypeFullDesc/text()') + [None])[0]
            typepdf = (typ.xpath('TypeWebPdf/text()') + [None])[0]

            for part in typ.xpath('.//Part'):
                mpn  = part.xpath('PartDesc/text()')[0]
                desc = part.xpath('PartGenericDesc/text()')[0]

                def getvalue(label, use_desc=False):
                    val  = (part.xpath('PartObject[PartObjectDesc/text() = "%s"]/PartObjectValue/text()' % label) + [None])[0]
                    if use_desc:
                        desc = (part.xpath('PartObject[PartObjectDesc/text() = "%s"]/PartObjectValueDesc/text()' % label) + [None])[0]
                        if desc.strip() == '':
                            desc = None
                    else:
                        desc = None
                    return desc or val

                size      = getvalue('Size')
                powerrate = getvalue('Power Rating (watts)', True)
                value     = util.parse_si(getvalue('Ohmic Value', True).replace('K', 'k'))
                tolerance = getvalue('Tolerance', True)
                voltrate  = getvalue('Max Working Voltage')

                itempath = pj(base_path, size, '%s.json' % (mpn))

                print('%-15s %6s %4s %.3e ±%-6s %-5s %-40s %s' % (mpn, size, powerrate + 'W', value, tolerance, voltrate + 'V', '"%s"' % desc, itempath))

                if size not in pkgs:
                    sys.stderr.write('size %s not available in Horizon\n' % size)
                    continue

                tmpl["base"] = pkgs[size]
                tmpl["MPN"] = [False, mpn]
                tmpl['datasheet'] = [False, 'http://www.seielect.com/catalog/%s' % typepdf]
                tmpl["value"] = [False, util.format_si(value, 2) + "Ω"]
                tmpl["description"] = [False, "SMD Resistor %s (%s)" % (desc.replace('RES, ', ''), typedesc)]
                tmpl["manufacturer"] = [False, "Stackpole"]
                tmpl["uuid"] = str(gen.get(mpn))
                tmpl["parametric"]["pmax"] = powerrate
                tmpl["parametric"]["value"] = str(value)
                if tolerance.startswith('< 0.05'):
                    tmpl["parametric"]["tolerance"] = '0'
                else:
                    tmpl["parametric"]["tolerance"] = str(float(tolerance.replace('%', '')))

                os.makedirs(os.path.dirname(itempath), exist_ok = True)
                with open(itempath, "w") as fi:
                    json.dump(tmpl, fi, sort_keys=True, indent=4)
