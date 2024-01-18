# -*- coding: utf-8 -*-
from os import listdir
from os.path import isfile, join
import json, pathlib, uuid
from body import *


# Kseries MPN List is stored here
mpn_dir = "./MPNs" 

# Tolerance Table from the datasheet
tolerances = {
    "J" : 5,
    "K" : 10,
    "M" : 20,
    "Z" : 80
}

# Package codes and the according meassurements
package_codes = {
    "10": {
        "length" : 3.6,
        "height" : 3.6,
        "width" : 2.3
    },
    "15": {
        "length" : 4.0,
        "height" : 4.0,
        "width" : 2.6
    },
    "20": {
        "length" : 5.0,
        "height" : 5.0,
        "width" : 3.2
    }
}

# Seating codes for the different leg variations, I didn't use this one
# because I only did one variant
seating_codes = {
            "L2": 1.6,
            "H5": 2.6,
            "K2": 3.5,
            "K5": 3.5
        }

# Voltage rating codes from the datasheet
voltage_codes = {
    "F": 50,
    "H": 100,
    "K": 200,
    "L": 500
}



def decode_mpn(mpn, dielectric):
    """
    Extracts data from a parts MPN
    """
    parts = []
    if mpn.startswith("K"):
        exponent = 10**(int(mpn[3])+1)
        value = int(mpn[1:3])*exponent
        # Set letter for tolerance
        for tolerance_key, tolerance in tolerances.items():
            # Set tolerance key in MPN
            temp = list(mpn)
            temp[4] = tolerance_key
            mpn = "".join(temp)

            # Get package
            package = package_codes[mpn[5:7]]
            package_code = mpn[5:7]

            # Get voltage
            voltage = voltage_codes[mpn[10]]

            # Set Package to Bulk – no need to overdo this
            temp = list(mpn)
            temp[12] = tolerance_key
            mpn = "".join(temp)

            # Set Lead style to straight (L) – no need to overdo this
            temp = list(mpn)
            temp[12] = "L"
            mpn = "".join(temp)

            for lead_key, lead_space in {"2": 2.5, "5": 5.0}.items():
                # Set lead spacing variant
                temp = list(mpn)
                temp[14] = lead_key
                mpn = "".join(temp)

                # Copy because dicts and memory
                package_copy = package.copy()
                package_copy["lead diameter"] = 0.5
                package_copy["lead spacing"] = lead_space
                package_copy["code"] = package_code

                part = {
                    "mpn" : mpn,
                    "tolerance" : tolerance,
                    "value" : value,
                    "dielectric" : dielectric,
                    "package" : package_copy,
                    "voltage" : voltage
                }

                parts.append(part)
    return parts



def to_unit(value):
    """
    Convert a number to a unit for the Part value string
    """
    if value < 1000:
        s = str(value)+"pF"
    elif value < 1000000:
        s = str(value/1000)+"nF"
    else:
        s = str(value/1000/1000)+"μF"
    return s

class hashabledict(dict):
    """
    Hashable dicts to allow us to create unique sets
    """
    def __hash__(self):
        return hash(tuple(sorted(self.items())))




# ======================== MPN PROCESSING =============================

# Read all files in the mpn_dir
mpn_files = [f for f in listdir(mpn_dir) if isfile(join(mpn_dir, f))]
mpn_list = {}

# Read the raw MPNs from those files
for filename in mpn_files:
    dielectric = filename.split(".")[0]
    mpn_list[dielectric] = []
    with open(join(mpn_dir, filename), "r") as f:
        for mpn in [l.strip() for l in f.readlines()]:
            mpn_list[dielectric].append(mpn)


# =========================== PARTS INFO =============================

# Decode all the information from the MPN and spit out more where Vishay
# used a "#"-wildcard
parts = []
for dielectric, mpns in mpn_list.items():
    print("Found {:3} raw MPNs in {}".format(len(mpns), dielectric))
    for mpn in mpns:
        decoded_parts = decode_mpn(mpn, dielectric)
        for part in decoded_parts:
            parts.append(part)

print("\nDecoded {} parts from the raw MPNs".format(len(parts)))

# Get a list of unique package combinations
unique_packages = set([hashabledict(part["package"]) for part in parts])
print("\nFound {} unique packages: ".format(len(unique_packages)))


# ========================= PACKAGE CREATION ===========================

template_2_5 = {}
template_5_0 = {}

# Load package template files from disk (for 2.5/5.0 mm lead spacing variants)
with open("./templates/2.5/package.json") as json_file:
    template_2_5 = json.load(json_file)

with open("./templates/5.0/package.json") as json_file:
    template_5_0 = json.load(json_file)

used_packages = {}

# Generate packages (Note: .scad to step conversion is done manually    )
for p in unique_packages:
    # Create a 3D model using solidpython and openscad
    body = construct_part(p["length"], p["width"], p["height"], p["lead spacing"], p["lead diameter"])
    # Use a precision of 32
    scad = "$fn = 32;\n\n"+scad_render(body)
    package_path = "3D/vishay_kseries_size_code_{}_{}mm_lead_spacing.scad".format(p["code"], p["lead spacing"])
    model_path = package_path.replace(".scad", ".step")[3:]
    # Write the SCAD file to disk (manual conversion needed! )
    write_scadfile(package_path, scad)

    # Copy the template dicts to avoid memory weirdness
    if p["lead spacing"] == 2.5:
        data = template_2_5.copy()
        model_uuid = "e7eb2860-69cd-4600-9fb0-25578ffc0b09"
    else:
        data = template_5_0.copy()
        model_uuid = "22bc86e8-83da-41aa-8929-b8558cf14bf8"

    # Set 3D Model
    data["models"][model_uuid]["filename"] = join("3d_models/passive/capacitor/", model_path)

    # Set Package Name
    data["name"] = "Vishay kseries Size {} ({} mm lead spacing)".format(p["code"], p["lead spacing"])

    data["manufacturer"] = "Vishay"

    # Add lead spacing to tags
    data["tags"].append("{}mm".format(p["lead spacing"]))
    data["uuid"] = str(uuid.uuid5(uuid.NAMESPACE_DNS, data["name"]))
    used_packages[data["uuid"]] = p


    # Generate paths for the package
    dirname = data["name"].replace(" ", "_")
    outdir = "../../packages/passive/capacitor/vishay/kseries/{}".format(dirname)
    # Create all Dirs on the way
    pathlib.Path(outdir).mkdir(parents=True, exist_ok=True) 
    targetpath = join(outdir, "package.json")
    with open(targetpath, 'w') as outfile:
            print("Writing Package: {}".format(targetpath))  
            json.dump(data, outfile, indent=4, sort_keys=True)

print("Packages Done\n")

for k, p in used_packages.items():
    print("{}: {}".format(k, p))

print()

    
# =========================== PARTS CREATION =================================

part_template = {}

# Open parts template from disk
with open("./templates/part.json") as json_file:
    part_template = json.load(json_file)

# Iterate over the parts
for p in parts:
    # Copy the template each iteration to avoid stale data
    data = part_template.copy()

    # Override all kind of fields
    data["MPN"][1] = p["mpn"].replace("#", "")
    data["uuid"] = str(uuid.uuid5(uuid.NAMESPACE_DNS, data["MPN"][1]))
    data["tags"].append(p["dielectric"])
    data["tags"].append("{}mm".format(p["package"]["lead spacing"]))
    # Make sure the tags are unique
    data["tags"] = list(set(data["tags"]))

    # Get the UUID of the package by comparison
    package_uuid = None
    for u, package_dict in used_packages.items():
        if p["package"] == package_dict:
            package_uuid = u

    data["package"] = package_uuid

    # Rename C0G to make it compatible to the table
    if p["dielectric"] == "C0G":
        p["dielectric"] = "C0G/NP0"

    # Set parametric data
    data["parametric"]["type"] = p["dielectric"]
    data["parametric"]["wvdc"] = str(p["voltage"])
    # value = "{:.2E}".format(int(p["value"])).replace("E+", "e-")
    value = "{}e-12".format(int(p["value"]))    
    data["parametric"]["value"] = value

    # Set the part value
    value = "{} {}%".format(to_unit(p["value"]), p["tolerance"]).replace(".0", "")
    data["value"][1] = value

    # Set the part description
    data["description"][1] = "{} {}V Radial Leaded Multilayer Ceramic Capacitor ({} mm Lead Spacing)".format(value, p["voltage"], p["package"]["lead spacing"])

    # Generate paths for the package
    filename = "{}.json".format(data["MPN"][1])
    outdir = "../../parts/passive/capacitor/vishay/kseries/"
    # Create all Dirs on the way
    pathlib.Path(outdir).mkdir(parents=True, exist_ok=True) 
    targetpath = join(outdir, filename)
    # Write the parts files
    with open(targetpath, 'w') as outfile:
            print("Writing Part: {}".format(targetpath))  
            json.dump(data, outfile, indent=4, sort_keys=True)



print("\nDone. Make sure to manually convert the SCAD files in ./3D to step and move them to the place specified in the parts")