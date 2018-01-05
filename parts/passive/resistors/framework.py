#!/bin/python
import os, json, uuid

def check_comma(value):
    i = "%.1f" % (value - round(value))
    if float(i) != 0:
        return "%.1f" % value
    else:
        return "%d" % value

def with_si_name(value):
    if value < 1000:
        return "%s" % check_comma(value)
    if value < 1000000:
        return "%sK" % check_comma(value/1000)
    if value >= 1000000:
        return "%sM" % check_comma(value/1000000)
    if value >= 1000000000:
        return "%sG" % check_comma(value/1000000000)

def with_si(value):
    if value < 1000:
        return "%s " % check_comma(value)
    if value < 1000000:
        return "%s k" % check_comma(value/1000)
    if value >= 1000000:
        return "%s M" % check_comma(value/1000000)
    if value >= 1000000000:
        return "%s G" % check_comma(value/1000000000)

def gen_data(default, part_name, value):
    default["MPN"][1] = part_name
    default["parametric"]["value"] = "%.1f" % value
    default["value"][1] = "%s\u03a9" % with_si(value)
    default["uuid"] = str(uuid.uuid4())
    return default

def gen_files(E_row_data, exponents, size, pmax, default):
    for i in exponents:
        r_ = 10**i
        for r in E_row_data:
            val = r_*r
            part_name = "RES-%s-%s-%sW" % (size, with_si_name(val), pmax)
            file_name = "gen/%s.json" % part_name
            print(file_name)
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            with open(file_name, "w+") as outfile:
                json.dump(gen_data(default, part_name, val), outfile)


