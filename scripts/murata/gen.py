# Q: Why does this script parse the part number instead of looking at the
#    other CSV columns in the download?
# A: Two reasons.  First, the MPN components for Murata apply over a broad
#    range of products.  Second, this serves as a built-in consistency check
#    rejecting invalid values rather than feeding garbage into the parametric
#    DB.

import json, zipfile, csv
from lxml import etree
from collections import namedtuple, OrderedDict
import uuid
import os
from os.path import join as pj
import sys

self_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(self_path))

import util

# main references:
#
# https://search.murata.co.jp/Ceramy/image/img/A01X/partnumbering_e_01.pdf
# http://www.mouser.com/ds/2/281/K23e5-462343.pdf

# fields for taking the MPN apart into its components
fields = OrderedDict([
    ('product_id', 3),   # (1), (2)
    ('dimensions', 2),   # (3)
    ('height', 1),       # (4)
    ('tempchar', 2),     # (5)
    ('voltage', 2),      # (6)
    ('capacitance', 3),  # (7)
    ('captolerance', 1), # (8)
    ('speccode', 3),     # (9)
])

CapacitorData = namedtuple('CapacitorData', ['mpn'] + list(fields.keys()))

total_len = 0
for k in fields.keys():
    fields[k] = (total_len, fields[k])
    total_len += fields[k][1]

# output
tmpl = json.loads("""
{
    "MPN": [
        false,
        "GRM011R60G103KE01"
    ],
    "base": "9954497f-10af-4158-934b-3b53068f6de4",
    "datasheet": [
        true,
        ""
    ],
    "description": [
        false,
        ""
    ],
    "inherit_model": true,
    "inherit_tags": true,
    "manufacturer": [true, ""],
    "parametric": {
        "table": "capacitors"
    },
    "tags": [],
    "type": "part",
    "uuid": "",
    "value": [
        false,
        ""
    ]
}
""")

# data tables for the various MPN parts

datasheets = {
    'GRM': 'https://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx',
    'KRM': 'https://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx',
}

# NOT VALID FOR ZRA...
# EIA
c_dims = {
    '01': '008004',
    '02':  '01005',
    '0D': '015015',
    'MD': '015008',
    '03':  '0201',
    '05':  '0202',
    '08':  '0303',
    '1U': '02404',
    '11':  '0504',  # only in mouser doc
    '15':  '0402',
    '18':  '0603',
    'JN':  '0704',
    '21':  '0805',
    '22':  '1111',
    '31':  '1206',
    '32':  '1210',
    '42':  '1808',
    '43':  '1812',
    '52':  '2211',
    '55':  '2220',
}
def get_dim(data):
    if data.product_id != 'ZRA':
        return c_dims.get(data.dimensions)
    else:
        return None

# NOT VALID FOR KR...
# (mm)
c_height = {
    '1': 0.125,
    '2': 0.2,
    '3': 0.3,
    '4': 0.4,
#   '4': 4-array type (CONFLICTING DATA in mouser doc)
    '5': 0.5,
    '6': 0.6,
    '7': 0.7,
    '8': 0.8,
    '9': 0.85,
    'A': 1.0,
    'B': 1.25,
    'C': 1.6,
    'D': 2.0,
    'E': 2.5,
    'M': 1.15,
    'N': 1.35,  # only in mouser doc
    'Q': 1.5,
    'R': 1.8,   # only in mouser doc
    'S': 2.8,
    'X': False, # unspecified -- different from None
}

c_height_kr = {
    'E': 1.8,
    'F': 1.9,
    'K': 2.7,
    'L': 2.8,
    'R': 3.6,
    'Q': 3.7,
    'T': 4.8,
    'V': 6.2,
    'W': 6.4,
}

def get_height(data):
    if not data.product_id.startswith('KR'):
        return c_height.get(data.height)
    else:
        return c_height_kr.get(data.height)

c_tempchar = {
    '1C': 'JIS CG',
    '1X': 'JIS SL',
    '2C': 'JIS CH',
    '3C': 'JIS CJ',
    '3U': 'JIS UJ',
    '4C': 'JIS CK',
    'B1': 'JIS B half-voltage',
    'B3': 'JIS B',
    'R1': 'JIS R half-voltage',
    'R3': 'JIS R',              # only in mouser doc
    'R8': 'JIS R half-voltage',

    '5G': 'muRata X8G',

    '5C': 'C0G/NP0',
    '6C': 'C0H', # only in mouser doc
    '6P': 'P2H', # only in mouser doc
    '6R': 'R2H', # only in mouser doc
    '6S': 'S2H', # only in mouser doc
    '6T': 'T2H', # only in mouser doc
    '7U': 'U2J',
    'C6': 'X5S',
    'C7': 'X7S',
    'C8': 'X6S',
    'D7': 'X7T',
    'D8': 'X6T',
    'E4': 'Z5U', # only in mouser doc
    'E7': 'X7U',
    'F5': 'Y5V', # only in mouser doc
    'R6': 'X5R',
    'R7': 'X7R',
    'Z7': 'X7R',
    '9E': 'ZLM', # only in mouser doc
}

c_voltage = {
    '0E': ('DC', 2.5),
    '0G': ('DC', 4.0),
    '0J': ('DC', 6.3),
    '1A': ('DC', 10.),
    '1C': ('DC', 16.),
    '1D': ('DC', 20.), # https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM21BR61D106KE15-01.pdf
    '1E': ('DC', 25.),
    'YA': ('DC', 35.),
    '1H': ('DC', 50.),
    '1J': ('DC', 63.),
    '1K': ('DC', 80.), # https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM32ER71K475KE14-01.pdf
    '2A': ('DC', 100.),
    '2D': ('DC', 200.),
    '2E': ('DC', 250.),
    '2W': ('DC', 450.),
    '2H': ('DC', 500.),
    '2J': ('DC', 630.),
    '3A': ('DC', 1000.),
    '3D': ('DC', 2000.),
    '3F': ('DC', 3150.),
    'E2': ('AC', 250., None),
    'GB': ('AC', 250., 'X2'),
    'GC': ('AC', 250., 'X1,Y2'), # only in mouser doc
    'GD': ('AC', 250., 'Y3'),
    'GF': ('AC', 250., 'Y2,X1/Y2'),
}

# this is not included in the CSV; getting it would require accessing each
# part's HTML detail page... so we just grab it for each SMD base footprint
# + height combo, in the hopes that same footprint/height = same packaging
# availability...
c_packaging = {
}

def get_packaging(cap):
    key = '%s%s%s' % (cap.product_id, cap.dimensions, cap.height)
    if key in c_packaging:
        return c_packaging[key]

    cache = util.CachedURL('https://psearch.en.murata.com/capacitor/product/%s%%23.html' % cap.mpn, urlcache)
    tree = etree.HTML(cache())

    pkgtab = tree.xpath('//table[@class="product-table package-table"]/tbody')
    if len(pkgtab) == 0:
        print('could not get packaging options for %r' % cap)
        options = []
    else:
        options = pkgtab[0].xpath('tr/td[1]/text()')

    c_packaging[key] = options
    return options

def iter_zipfile(zipfilename):
    '''
    iterate MPNs from a model .zip file downloaded from murata website

    Note: the models / ZIP files are incomplete, so this is here mostly for
    reference/posterity.  it's not currently used.
    '''
    zf = zipfile.ZipFile(zipfilename)
    for fileinfo in zf.filelist:
        if fileinfo.is_dir():
            continue
        filename = fileinfo.filename.split('/')[-1]
        filename = filename.replace('.s2p', '')

        yield filename

def iter_parse(itr):
    '''
    dissect MPN into a parsed CapacitorData namedtuple
    '''
    for mpn in itr:
        if len(mpn) != total_len:
            print('invalid part number "%s" (length %d chars, expected %d)' %
                    (mpn, len(mpn), total_len))
            continue

        vals = [mpn]
        vals.extend([mpn[i[0]:i[0]+i[1]] for i in fields.values()])
        data = CapacitorData(*vals)
        yield data

urlcache = pj(self_path, 'urlcache.json')

sources = []
sources.append(util.CachedURL('https://psearch.en.murata.com/capacitor/lineup/download/grm_g1', urlcache))
sources.append(util.CachedURL('https://psearch.en.murata.com/capacitor/lineup/download/krm_1', urlcache))

class csvattrs(csv.Dialect):
    delimiter = ','
    quotechar = '"'
    escapechar = None
    doublequote = True
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_MINIMAL

def iter_websearch():
    for source in sources:
        for row in csv.DictReader(source().splitlines(), dialect=csvattrs):
            yield row['Part number (#:Packing code)'].replace('#', '')


if __name__ == '__main__':
    base_path = pj(util.pool_path, "parts", "passive", "capacitor", "murata")

    gen = util.UUIDGenerator(pj(self_path, "uu.txt"))
    bpm = util.VendorSubBasepartMaker('passive/capacitor', gen)

    with open(pj(util.pool_path, 'tables.json'), 'r') as tablesfd:
        tables = json.load(tablesfd)
    param_cols = tables['tables']['capacitors']['columns']
    param_types = [col for col in param_cols if col['name'] == 'type'][0]
    param_tempchars = param_types['items']

    # for cap in iter_parse(iter_zipfile(sys.argv[1])):
    for cap in sorted(iter_parse(iter_websearch())):
        dim = get_dim(cap)
        if dim is None:
            print('%s: could not determine dimension' % cap.mpn)
            continue

        height = get_height(cap)
        if height is None:
            print('%s: could not determine height' % cap.mpn)
            continue

        try:
            attrs = {
                'description': [False, '%s%s (%s) base' % (cap.product_id, cap.dimensions, dim)],
                'manufacturer': [False, 'muRata'],
                'model': '96c366ee-a963-41a0-9cc8-54c646979695',
            }
            if cap.product_id in datasheets:
                attrs['datasheet'] = [False, datasheets[cap.product_id]]

            # KR* = stacked, metal bonded capacitors... 3d model is far off
            # need to set up actual proper models for these
            if cap.product_id.startswith('KR'):
                del attrs['model']

            baseuuid = bpm.find_or_make_pkg(
                'murata/%s' % cap.product_id.lower(),
                '%s%s' % (cap.product_id, cap.dimensions),
                'C%s' % dim,
                attrs)

            attrs = {
                'description': [False, '%s%s%s (%s, %rmm height) base' % (cap.product_id, cap.dimensions, cap.height, dim, height)],
            }
            baseuuid = bpm.find_or_make(
                'murata/%s' % cap.product_id.lower(),
                '%s%s%s' % (cap.product_id, cap.dimensions, cap.height),
                baseuuid,
                attrs)
        except IndexError as e:
            print('%s: no base part available for EIA size code %s' % (cap.mpn, dim))
            continue

        packaging_opts = get_packaging(cap)

        tempchar = c_tempchar.get(cap.tempchar)
        if tempchar is None:
            print('%s: could not determine temperature characteristic' % cap.mpn)
            continue
        if tempchar not in param_tempchars:
            print('%s: skipping temperature characteristic %s (not in parametrics database)' % (cap.mpn, tempchar))
            continue

        voltage = c_voltage.get(cap.voltage)
        if voltage is None:
            print('%s: could not determine voltage rating' % cap.mpn)
            continue

        exp = int(cap.capacitance[2])
        nom = float(cap.capacitance[0:2].replace('R', '.'))
        value = nom * (10 ** (-12 + exp))

        itempath = pj(base_path, cap.product_id.lower(), dim, '%s.json' % (cap.mpn))
        print(os.path.relpath(itempath, base_path), cap)

        tmpl["base"] = baseuuid
        tmpl["MPN"] = [False, cap.mpn]
        if len(packaging_opts) > 0:
            tmpl['orderable_MPNs'] = dict([
                (str(gen.get(cap.mpn + opt)), cap.mpn + opt) for opt in packaging_opts
            ])
        else:
            del tmpl['orderable_MPNs']
        tmpl["value"] = [False, util.format_si(value, 1) + "F"]
        tmpl["description"] = [False, "Ceramic Capacitor %sF %sV%s %s" % (util.format_si(value, 1), util.format_si(voltage[1], 1), voltage[0], tempchar)]
        tmpl["uuid"] = str(gen.get(cap.mpn))
        if voltage[0] == 'DC':
            tmpl["parametric"]["wvdc"] = str(voltage[1])
        else:
            tmpl["parametric"]["wvdc"] = None
        tmpl["parametric"]["value"] = "%.4e" % value
        tmpl["parametric"]["type"] = tempchar

        os.makedirs(os.path.dirname(itempath), exist_ok = True)
        with open(itempath, "w") as fi:
            json.dump(tmpl, fi, sort_keys=True, indent=4)
