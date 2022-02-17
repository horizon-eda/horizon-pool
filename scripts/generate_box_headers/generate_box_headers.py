#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import glob
import uuid
from itertools import islice
from typing import Optional, List, Union, Tuple

from generate_step import generate_box_header


PACKAGE_DIRECTORY = "../../packages/connector/header/idc_box/2.54/"
MODEL_DIRECTORY = "../../3d_models/connector/header/idc_box/2.54/"
PART_DIRECTORY = "../../parts/connector/header/idc_box/"


def get_data_from_file(path: str) -> Optional[dict]:
    """Return the json-data from a file"""
    with open(path, "r") as f:
        data = json.loads(f.read())
        return data


def get_uuid_from_file(path: str) -> Optional[str]:
    """Get the UUID from a file"""
    data = get_data_from_file(path)
    if data is not None:
        try:
            return data["uuid"]
        except KeyError:
            return None


def get_entity_for_pins(n: int) -> Optional[str]:
    """Get the entity data of a generic connector entity for a given number of pins"""
    pin_files = glob.glob("../../entities/connector/generic/*.json")
    for path in pin_files:
        try:
            number = int(path.rsplit("/", 1)[1][:-5])
        except:
            continue
        if n == number:
            data = get_data_from_file(path)
            if data is not None:
                return data
    return None


def sliding_window(seq, n=2):
    """Returns a sliding window (of width n) over data from the iterable
    s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ..."""
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


def generate_pin_coordinates(rows, cols, spacing=2.54) -> List[List[int]]:
    pin_list = []
    col_start = ((cols - 1) * spacing) / 2
    for row in range(rows):
        for col in range(cols):
            x = (-spacing / 2) + (spacing * row)
            y = col_start - (col * spacing)
            x = mm_to_horizon(x)
            y = mm_to_horizon(y)
            pin_list.append([x, y])
    return pin_list


def mm_to_horizon(value: Union[int, float]) -> int:
    return int(value * 1_000_000)


def generate_predictable_uuid(value: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, value))


def add_silkscreen_line(
    model: dict,
    start_point: Tuple[int, int],
    end_point: Tuple[int, int],
    layer: int,
    width: int,
    uuid_suffix="silkscreen",
) -> dict:
    start_junction_uuid = generate_predictable_uuid(
        model["uuid"] + f"_start_{uuid_suffix}_junction_at_{str(start_point)}"
    )
    end_junction_uuid = generate_predictable_uuid(
        model["uuid"] + f"_end_{uuid_suffix}_junction_at_{str(end_point)}"
    )
    line_uuid = generate_predictable_uuid(
        model["uuid"]
        + f"_{uuid_suffix}_line_from_{start_junction_uuid}_to_{end_junction_uuid}"
    )

    model["junctions"][start_junction_uuid] = {
        "position": [start_point[0], start_point[1]]
    }

    model["junctions"][end_junction_uuid] = {"position": [end_point[0], end_point[1]]}

    model["lines"][line_uuid] = {
        "from": start_junction_uuid,
        "to": end_junction_uuid,
        "layer": layer,
        "width": width,
    }


def generate_package(
    pin_rows,
    pin_cols,
    spacing,
    package_name,
    package_path,
    package_uuid,
    model_path,
    model_uuid,
) -> dict:
    """Generates a package, returns the generated package"""
    # Generate the coordinates of the pins
    pin_coordinates = generate_pin_coordinates(pin_rows, pin_cols, spacing)

    # Fixup the relativ paths
    model_path = model_path.replace("../../", "")
    package_path = package_path if package_path.endswith("/") else f"{package_path}/"

    # Half the distances from the pin to the outside of the plastic part
    plastic_length_distance = 3.99
    plastic_width_distance = 1.81

    # Calculate the package outline
    package_length = (pin_cols * spacing) + (2 * plastic_length_distance)
    package_width = (pin_rows * spacing) + (2 * plastic_width_distance)

    # Translate to horizon units
    p_x = mm_to_horizon(package_width)
    p_y = mm_to_horizon(package_length)

    # Define the basic package data (some stuff is added afterwards)
    package = {
        "default_model": model_uuid,
        "manufacturer": "",
        "models": {
            model_uuid: {
                "filename": model_path,
                "pitch": 0,
                "roll": 0,
                "x": 0,
                "y": 0,
                "yaw": 49152,
                "z": 0,
            }
        },
        "name": package_name,
        "parameter_program": f"{package_width}mm {package_length}mm\nget-parameter [ courtyard_expansion ]\n2 * +xy\nset-polygon [ courtyard rectangle 0.000mm 0.000mm ]",
        "parameter_set": {"courtyard_expansion": 250000},
        "tags": [
            "box-header",
            "connector",
            "generic",
            "header",
            "idc",
            "shrouded",
            "th",
            "vertical",
            f"{spacing}mm",
            f"{pin_cols}x{pin_rows}",
            f"{pin_cols*pin_rows}-pin",
        ],
        "polygons": {
            generate_predictable_uuid(package_uuid + "_assembly_polygon"): {
                "layer": 50,
                "parameter_class": "",
                "vertices": [
                    {
                        "position": [-p_x / 2, -p_y / 2],
                        "type": "line",
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                    },
                    {
                        "position": [-p_x / 2, p_y / 2],
                        "type": "line",
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                    },
                    {
                        "position": [p_x / 2 - p_x / 3, p_y / 2],
                        "type": "line",
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                    },
                    {
                        "position": [p_x / 2, p_y / 2 - p_x / 3],
                        "type": "line",
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                    },
                    {
                        "position": [p_x / 2, -p_y / 2],
                        "type": "line",
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                    },
                ],
            },
            generate_predictable_uuid(package_uuid + "_courtyard_lines"): {
                "layer": 60,
                "parameter_class": "courtyard",
                "vertices": [
                    {
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                        "position": [-p_x / 2, -p_y / 2],
                        "type": "line",
                    },
                    {
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                        "position": [-p_x / 2, p_y / 2],
                        "type": "line",
                    },
                    {
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                        "position": [p_x / 2, p_y / 2],
                        "type": "line",
                    },
                    {
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                        "position": [p_x / 2, -p_y / 2],
                        "type": "line",
                    },
                ],
            },
            generate_predictable_uuid(package_uuid + "_package_polygon"): {
                "layer": 40,
                "parameter_class": "",
                "vertices": [
                    {
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                        "position": [-p_x / 2, -p_y / 2],
                        "type": "line",
                    },
                    {
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                        "position": [-p_x / 2, p_y / 2],
                        "type": "line",
                    },
                    {
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                        "position": [p_x / 2, p_y / 2],
                        "type": "line",
                    },
                    {
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                        "position": [p_x / 2, 2250000],
                        "type": "line",
                    },
                    {
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                        "position": [p_x / 2 - 1_000_000, 2250000],
                        "type": "line",
                    },
                    {
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                        "position": [p_x / 2 - 1_000_000, -2250000],
                        "type": "line",
                    },
                    {
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                        "position": [p_x / 2, -2250000],
                        "type": "line",
                    },
                    {
                        "arc_center": [0, 0],
                        "arc_reverse": False,
                        "position": [p_x / 2, -p_y / 2],
                        "type": "line",
                    },
                ],
            },
        },
        "pads": {},
        "junctions": {},
        "lines": {},
        "arcs": {},
        "texts": {
            generate_predictable_uuid(package_uuid + "_assembly_text"): {
                "font": "simplex",
                "from_smash": False,
                "layer": 50,
                "origin": "center",
                "placement": {
                    "angle": 16384,
                    "mirror": False,
                    "shift": [0, -p_y / 2 + p_y / 20],
                },
                "size": 1500000,
                "text": "$RD",
                "width": 0,
            },
            generate_predictable_uuid(package_uuid + "_silkscreen_rd_text"): {
                "font": "simplex",
                "from_smash": False,
                "layer": 20,
                "origin": "center",
                "placement": {
                    "angle": 0,
                    "mirror": False,
                    "shift": [-p_x / 2, p_y / 2 + 1_300_000],
                },
                "size": 1_000_000,
                "text": "$RD",
                "width": 150000,
            },
        },
        "type": "package",
        "uuid": package_uuid,
    }

    # Create and add pins
    for i, pin in enumerate(pin_coordinates):
        n = i + 1
        pad_uuid = generate_predictable_uuid(f"{package_uuid}_pad{n}")
        pad = {
            "name": str(n),
            "padstack": "296cf69b-9d53-45e4-aaab-4aedf4087d3a",
            "parameter_set": {"hole_diameter": 1000000, "pad_diameter": 1700000},
            "placement": {"angle": 0, "mirror": False, "shift": [pin[0], pin[1]]},
        }
        package["pads"][pad_uuid] = pad

    # Add Silkscreen outline with offset
    offset = 300_000
    add_silkscreen_line(
        package,
        start_point=(-p_x / 2 - offset, -p_y / 2 - offset),
        end_point=(-p_x / 2 - offset, p_y / 2 + offset),
        layer=20,
        width=130_000,
        uuid_suffix="silkscreen",
    )

    add_silkscreen_line(
        package,
        start_point=(p_x / 2 + offset, -p_y / 2 - offset),
        end_point=(p_x / 2 + offset, p_y / 2 + offset),
        layer=20,
        width=130_000,
        uuid_suffix="silkscreen",
    )

    add_silkscreen_line(
        package,
        start_point=(-p_x / 2 - offset, p_y / 2 + offset),
        end_point=(p_x / 2 + offset, p_y / 2 + offset),
        layer=20,
        width=130_000,
        uuid_suffix="silkscreen",
    )

    add_silkscreen_line(
        package,
        start_point=(-p_x / 2 - offset, -p_y / 2 - offset),
        end_point=(p_x / 2 + offset, -p_y / 2 - offset),
        layer=20,
        width=130_000,
        uuid_suffix="silkscreen",
    )

    # Silkscreen Notch
    add_silkscreen_line(
        package,
        start_point=(p_x / 2 + offset - 1_000_000, 2_250_000),
        end_point=(p_x / 2 + offset - 1_000_000, -2_250_000),
        layer=20,
        width=130_000,
        uuid_suffix="silkscreen",
    )

    add_silkscreen_line(
        package,
        start_point=(p_x / 2 + offset - 1_000_000, 2_250_000),
        end_point=(p_x / 2 + offset, 2_250_000),
        layer=20,
        width=130_000,
        uuid_suffix="silkscreen",
    )

    add_silkscreen_line(
        package,
        start_point=(p_x / 2 + offset - 1_000_000, -2_250_000),
        end_point=(p_x / 2 + offset, -2_250_000),
        layer=20,
        width=130_000,
        uuid_suffix="silkscreen",
    )

    # Create package directory
    os.makedirs(package_path, exist_ok=True)

    # Write to file
    with open(package_path + "/package.json", "w") as f:
        json.dump(package, f, sort_keys=True, indent=4, ensure_ascii=False)
    print(f"Created package at path: {package_path}")

    return package


def generate_part(
    pin_rows: int,
    pin_cols: int,
    spacing: float,
    part_uuid: str,
    PART_DIRECTORY: str,
    entity: dict,
    package: dict,
):

    part = {
        "MPN": [
            False,
            f"Shrouded IDC Box Header {pin_rows}×{pin_cols} {spacing}mm pitch (vertical, throughole)",
        ],
        "datasheet": [False, ""],
        "description": [
            False,
            f"Shrouded IDC Box Header {pin_rows}×{pin_cols} {spacing}mm pitch (vertical, throughole)",
        ],
        "entity": entity["uuid"],
        "inherit_model": False,
        "inherit_tags": False,
        "manufacturer": [False, ""],
        "model": package["default_model"],
        "package": package["uuid"],
        "pad_map": {},
        "parametric": {},
        "tags": ["box-header", "connector", "generic", "header", "idc", "shrouded"],
        "type": "part",
        "uuid": part_uuid,
        "value": [False, ""],
    }
    gate_uuid = list(entity["gates"].keys())[0]
    unit_uuid = list(entity["gates"].values())[0]["unit"]
    unit_path = (
        f"../../units/connector/generic/{str(pin_rows * pin_cols).zfill(3)}.json"
    )
    unit = get_data_from_file(unit_path)

    for pad_uuid, pad in package["pads"].items():
        for pin_uuid, pin in unit["pins"].items():
            if pad["name"] == pin["primary_name"]:
                part["pad_map"][pad_uuid] = {"gate": gate_uuid, "pin": pin_uuid}

    # Create parts directory if it doesn't exist
    os.makedirs(f"{PART_DIRECTORY}{spacing}/", exist_ok=True)

    # Create a path for the part
    part_name = f"{pin_rows}x{pin_cols}_{spacing}mm_pitch_idc_box_header_shrouded_vertical_th.json"
    part_path = f"{PART_DIRECTORY}{spacing}/{part_name}"

    # Write to file
    with open(part_path, "w") as f:
        json.dump(part, f, sort_keys=True, indent=4, ensure_ascii=False)
    print(f"Created part at path: {part_path}")


if __name__ == "__main__":
    for pin_cols in range(3, 51):
        pin_rows = 2
        spacing = 2.54
        pin_count = pin_cols * pin_rows

        # Get the fitting connector entity if possible
        entity = get_entity_for_pins(pin_count)
        if entity is None:
            print(
                f"Error: Could not find a fitting entity for a connector with {pin_count}!"
            )
            print(f"Exiting...")
            exit(1)

        # Create some shared variables, uuids, paths etc.
        package_name = f"{pin_rows}×{pin_cols} {spacing}mm pitch IDC Box Header (shrouded, vertical, throughole)"
        package_filename = f"{pin_rows}x{pin_cols}_{spacing}mm_pitch_idc_box_header_shrouded_vertical_th"
        package_path = f"{PACKAGE_DIRECTORY}{package_filename}"
        package_uuid = generate_predictable_uuid(f"{package_name}_package")
        model_filename = f"{package_filename}.step"
        model_path = f"{MODEL_DIRECTORY}{model_filename}"
        model_uuid = generate_predictable_uuid(f"{model_filename}_3d_model")
        part_uuid = generate_predictable_uuid(f"{package_name}_part")

        # Generate the package
        package = generate_package(
            pin_rows,
            pin_cols,
            spacing,
            package_name,
            package_path,
            package_uuid,
            model_path,
            model_uuid,
        )

        # Generate the part
        generate_part(
            pin_rows, pin_cols, spacing, part_uuid, PART_DIRECTORY, entity, package
        )

        # Generate 3D-Model
        os.makedirs(MODEL_DIRECTORY, exist_ok=True)
        # generate_box_header(
        #     rows=pin_rows, cols=pin_cols, spacing=spacing, output_path=model_path
        # )
