import csv
import json
import pathlib
import re
import uuid
from decimal import Decimal

from data.data import LEAD_DIAMETER_MM, LEAD_SPACING_MM


ROOT = pathlib.Path(__file__).resolve().parent
POOL_ROOT = ROOT.parent.parent
CSV_PATH = ROOT / "data" / "nichicon-ues.csv"
PACKAGE_OUTDIR = POOL_ROOT / "packages" / "passive" / "th" / "capacitor" / "nichicon" / "ues"
PART_OUTDIR = POOL_ROOT / "parts" / "passive" / "capacitor" / "nichicon" / "ues"
MODEL_OUTDIR = POOL_ROOT / "3d_models" / "passive" / "capacitor" / "th" / "bipolar" / "nichicon" / "ues"
SCAD_OUTDIR = ROOT / "3D"

DATASHEET_URL = "https://www.nichicon.co.jp/english/series_items/catalog_pdf/e-ues.pdf"
ENTITY_UUID = "ca83a84f-6183-4088-84b6-5d79b2a119d4"
GATE_UUID = "9bfcf213-2a7e-444e-8312-ce57209fc9ec"
PIN_A_UUID = "852f1fe6-06dc-4661-8a14-61a9a6ebb26a"
PIN_B_UUID = "29995253-b4b1-4c7c-a049-b6db2713ca7c"
ZERO_UUID = "00000000-0000-0000-0000-000000000000"
PADSTACK_UUID = "296cf69b-9d53-45e4-aaab-4aedf4087d3a"


def slugify(value):
    value = value.replace("⌀", "").replace("µ", "u").replace(".", "_")
    value = re.sub(r"[^A-Za-z0-9_]+", "_", value)
    return value.strip("_")


def format_decimal(value):
    normalized = value.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def parse_capacitance(capacitance):
    text = capacitance.replace("µ", "u").strip()
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*([um])F", text, re.IGNORECASE)
    if not match:
        raise ValueError(f"Unsupported capacitance string: {capacitance}")
    value = Decimal(match.group(1))
    unit = match.group(2).lower()
    if unit == "m":
        uf = value * Decimal("1000")
    else:
        uf = value
    farads = uf * Decimal("1e-6")
    return uf, farads


def parse_size(size):
    match = re.fullmatch(r"φ([0-9]+(?:\.[0-9]+)?)x([0-9]+(?:\.[0-9]+)?)L mm", size.strip())
    if not match:
        raise ValueError(f"Unsupported size string: {size}")
    diameter = Decimal(match.group(1))
    height = Decimal(match.group(2))
    return diameter, height


def package_identity(diameter, height, lead_spacing):
    return (
        f"Nichicon UES bipolar capacitor, ⌀ {format_decimal(diameter)} mm, "
        f"height {format_decimal(height)} mm, lead spacing {format_decimal(lead_spacing)} mm"
    )


def mm_to_nm(value):
    return int((value * Decimal("1000000")).to_integral_value())


def model_basename(diameter, height, lead_spacing):
    return (
        "nichicon_ues_"
        f"{format_decimal(diameter)}mm_diameter_"
        f"{format_decimal(height)}mm_height_"
        f"{format_decimal(lead_spacing)}mm_lead_spacing"
    )


def circle_polygon(radius_mm, layer, parameter_class="", close=False):
    radius = mm_to_nm(radius_mm)
    vertices = [
        {
            "arc_center": [0, 0],
            "arc_reverse": False,
            "position": [-radius, 0],
            "type": "arc",
        },
        {
            "arc_center": [0, 0],
            "arc_reverse": False,
            "position": [radius, 0],
            "type": "arc",
        },
    ]
    if close:
        vertices.append(
            {
                "arc_center": [0, 0],
                "arc_reverse": False,
                "position": [-radius, 0],
                "type": "line",
            }
        )
    return {
        "layer": layer,
        "parameter_class": parameter_class,
        "vertices": vertices,
    }


def lead_hole_diameter(lead_diameter):
    return lead_diameter + Decimal("0.25")


def pad_diameter(hole_diameter):
    return hole_diameter + Decimal("0.50")


def render_scad_model(diameter, height, lead_spacing, lead_diameter):
    radius = diameter / Decimal("2")
    lead_length_below = Decimal("3.5")
    body_lift = Decimal("1.0")
    lead_stub = max(body_lift, Decimal("0.8"))
    top_chamfer = min(Decimal("0.6"), max(height * Decimal("0.08"), Decimal("0.3")))

    return f"""$fn = 64;

body_diameter = {format_decimal(diameter)};
body_height = {format_decimal(height)};
lead_spacing = {format_decimal(lead_spacing)};
lead_diameter = {format_decimal(lead_diameter)};
lead_length_below = {format_decimal(lead_length_below)};
body_lift = {format_decimal(body_lift)};
lead_stub = {format_decimal(lead_stub)};
top_chamfer = {format_decimal(top_chamfer)};

module lead(x) {{
    color([0.75, 0.75, 0.75])
    translate([x, 0, -lead_length_below])
        cylinder(h = lead_length_below + body_lift + lead_stub, d = lead_diameter);
}}

module capacitor_body() {{
    color([0.16, 0.18, 0.19])
    union() {{
        translate([0, 0, body_lift])
            cylinder(h = body_height - top_chamfer, d = body_diameter);
        translate([0, 0, body_lift + body_height - top_chamfer])
            cylinder(h = top_chamfer, d1 = body_diameter, d2 = body_diameter * 0.92);
    }}
}}

module top_vent() {{
    color([0.78, 0.78, 0.78])
    translate([0, 0, body_lift + body_height - 0.05])
    linear_extrude(height = 0.12)
    union() {{
        square([body_diameter * 0.42, body_diameter * 0.08], center = true);
        square([body_diameter * 0.08, body_diameter * 0.42], center = true);
    }}
}}

lead(-lead_spacing / 2);
lead( lead_spacing / 2);
capacitor_body();
top_vent();
"""


def write_scad_model(diameter, height, lead_spacing, lead_diameter):
    basename = model_basename(diameter, height, lead_spacing)
    SCAD_OUTDIR.mkdir(parents=True, exist_ok=True)
    scad_path = SCAD_OUTDIR / f"{basename}.scad"
    with open(scad_path, "w", encoding="utf-8") as f:
        f.write(render_scad_model(diameter, height, lead_spacing, lead_diameter))
    return basename


def build_package(diameter, height):
    lead_spacing = Decimal(str(LEAD_SPACING_MM[float(diameter)]))
    lead_diameter = Decimal(str(LEAD_DIAMETER_MM[float(diameter)]))
    model_name = model_basename(diameter, height, lead_spacing)
    model_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"atoav-pool/model/{model_name}"))

    name = package_identity(diameter, height, lead_spacing)
    package_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"atoav-pool/package/{name}"))
    pad_a_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{package_uuid}/pad/A"))
    pad_b_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{package_uuid}/pad/B"))
    hole_diameter = lead_hole_diameter(lead_diameter)
    copper_diameter = pad_diameter(hole_diameter)
    half_pitch = mm_to_nm(lead_spacing / Decimal("2"))
    body_radius = diameter / Decimal("2")
    silk_radius = body_radius
    courtyard_radius = body_radius + Decimal("0.25")
    text_radius = mm_to_nm(body_radius + Decimal("0.45"))
    outline_radius = mm_to_nm(body_radius + Decimal("0.30"))
    center_junction = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{package_uuid}/junction/center"))
    left_junction = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{package_uuid}/junction/left"))
    right_junction = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{package_uuid}/junction/right"))
    arc_a_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{package_uuid}/arc/a"))
    arc_b_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{package_uuid}/arc/b"))

    package = {
        "arcs": {
            arc_a_uuid: {
                "center": center_junction,
                "from": left_junction,
                "layer": 20,
                "to": right_junction,
                "width": 150000,
            },
            arc_b_uuid: {
                "center": center_junction,
                "from": right_junction,
                "layer": 20,
                "to": left_junction,
                "width": 150000,
            },
        },
        "default_model": model_uuid,
        "dimensions": {},
        "grid_settings": {
            "current": {
                "mode": "square",
                "name": "",
                "origin": [0, 0],
                "spacing_rect": [1000000, 1000000],
                "spacing_square": max(outline_radius, 1000000),
            },
            "grids": {},
        },
        "junctions": {
            center_junction: {"position": [0, 0]},
            left_junction: {"position": [-outline_radius, 0]},
            right_junction: {"position": [outline_radius, 0]},
        },
        "keepouts": {},
        "lines": {},
        "manufacturer": "Nichicon",
        "models": {
            model_uuid: {
                "filename": f"3d_models/passive/capacitor/th/bipolar/nichicon/ues/{model_name}.step",
                "pitch": 0,
                "roll": 0,
                "x": 0,
                "y": 0,
                "yaw": 0,
                "z": 0,
            }
        },
        "name": name,
        "pads": {
            pad_a_uuid: {
                "name": "A",
                "padstack": PADSTACK_UUID,
                "parameter_set": {
                    "hole_diameter": mm_to_nm(hole_diameter),
                    "pad_diameter": mm_to_nm(copper_diameter),
                },
                "placement": {
                    "angle": 0,
                    "mirror": False,
                    "shift": [-half_pitch, 0],
                },
            },
            pad_b_uuid: {
                "name": "B",
                "padstack": PADSTACK_UUID,
                "parameter_set": {
                    "hole_diameter": mm_to_nm(hole_diameter),
                    "pad_diameter": mm_to_nm(copper_diameter),
                },
                "placement": {
                    "angle": 0,
                    "mirror": False,
                    "shift": [half_pitch, 0],
                },
            },
        },
        "parameter_program": (
            f"{format_decimal(diameter)}mm {format_decimal(diameter)}mm\n"
            "get-parameter [ courtyard_expansion ]\n"
            "2 * +xy\n"
            "set-polygon [ courtyard circle 0.000mm 0.000mm ]"
        ),
        "parameter_set": {
            "courtyard_expansion": 250000,
        },
        "polygons": {
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{package_uuid}/polygon/assembly")): circle_polygon(body_radius, 50),
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{package_uuid}/polygon/silkscreen")): circle_polygon(silk_radius, 40),
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{package_uuid}/polygon/courtyard")): circle_polygon(courtyard_radius, 60, "courtyard", close=True),
        },
        "rules": {
            "clearance_package": {
                "clearance_silkscreen_cu": 200000,
                "clearance_silkscreen_pkg": 200000,
                "enabled": True,
                "order": -1,
            },
            "package_checks": {
                "enabled": True,
                "order": -1,
            },
        },
        "tags": [
            "bipolar",
            "capacitor",
            "nichicon",
            "radial",
            "th",
            "ues",
        ],
        "texts": {
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{package_uuid}/text/assembly")): {
                "font": "simplex",
                "from_smash": False,
                "layer": 50,
                "origin": "center",
                "placement": {
                    "angle": 0,
                    "mirror": False,
                    "shift": [-mm_to_nm(body_radius), 0],
                },
                "size": 1000000,
                "text": "$RD",
                "width": 0,
            },
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{package_uuid}/text/body")): {
                "font": "simplex",
                "from_smash": False,
                "layer": 20,
                "origin": "center",
                "placement": {
                    "angle": 0,
                    "mirror": False,
                    "shift": [text_radius, 0],
                },
                "size": 1000000,
                "text": "$RD",
                "width": 150000,
            },
        },
        "type": "package",
        "uuid": package_uuid,
    }

    dirname = slugify(name)
    outdir = PACKAGE_OUTDIR / dirname
    outdir.mkdir(parents=True, exist_ok=True)
    with open(outdir / "package.json", "w", encoding="utf-8") as f:
        json.dump(package, f, indent=4, sort_keys=True)
        f.write("\n")
    write_scad_model(diameter, height, lead_spacing, lead_diameter)

    return {
        "uuid": package_uuid,
        "pad_a_uuid": pad_a_uuid,
        "pad_b_uuid": pad_b_uuid,
        "lead_spacing": lead_spacing,
        "diameter": diameter,
        "height": height,
    }


def build_part(row, package_meta):
    mpn = row["Part Number"].strip()
    uf, farads = parse_capacitance(row["Capacitance"])
    voltage = Decimal(row["Voltage"].split()[0])
    status = row["Status"].strip().lower().replace(" ", "-")
    package_label = (
        f"{format_decimal(package_meta['diameter'])} mm diameter, "
        f"{format_decimal(package_meta['height'])} mm height, "
        f"{format_decimal(package_meta['lead_spacing'])} mm lead spacing"
    )

    description = (
        f"{row['Capacitance']} {row['Voltage']} bi-polar aluminum electrolytic capacitor, "
        f"radial lead, Nichicon UES ({package_label})"
    )
    value_display = row["Capacitance"].replace("u", "µ")
    part = {
        "MPN": [False, mpn],
        "datasheet": [False, DATASHEET_URL],
        "description": [False, description],
        "entity": ENTITY_UUID,
        "inherit_tags": False,
        "manufacturer": [False, "Nichicon"],
        "package": package_meta["uuid"],
        "pad_map": {
            package_meta["pad_a_uuid"]: {
                "gate": GATE_UUID,
                "pin": PIN_A_UUID,
            },
            package_meta["pad_b_uuid"]: {
                "gate": GATE_UUID,
                "pin": PIN_B_UUID,
            },
        },
        "parametric": {
            "table": "capacitors",
            "type": "Electrolytic",
            "value": f"{farads:.6e}",
            "wvdc": f"{voltage:.1f}",
        },
        "tags": [
            "audio",
            "bipolar",
            "capacitor",
            "passive",
            status,
            "th",
        ],
        "type": "part",
        "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, f"atoav-pool/part/{mpn}")),
        "value": [False, value_display],
    }

    PART_OUTDIR.mkdir(parents=True, exist_ok=True)
    with open(PART_OUTDIR / f"{mpn}.json", "w", encoding="utf-8") as f:
        json.dump(part, f, indent=4, sort_keys=True)
        f.write("\n")


def main():
    packages = {}

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        diameter, height = parse_size(row["Size"])
        lead_spacing = Decimal(str(LEAD_SPACING_MM[float(diameter)]))
        package_key = (diameter, height, lead_spacing)
        if package_key not in packages:
            packages[package_key] = build_package(diameter, height)
        build_part(row, packages[package_key])

    print(f"Generated {len(packages)} packages, {len(rows)} parts, and {len(packages)} SCAD models.")
    print(f"SCAD models written to {SCAD_OUTDIR}")
    print(f"Convert them to STEP and place the files in {MODEL_OUTDIR}")


if __name__ == "__main__":
    main()
