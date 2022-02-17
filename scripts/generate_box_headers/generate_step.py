#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cadquery as cq


def generate_box_header(rows, cols, spacing=2.54, output_path="./"):
    pin_rows = rows
    pin_cols = cols
    pin_space = spacing
    pin_thickness = 0.7
    pin_height_top = 6.1
    pin_height_bottom = 3.2

    # Spacing between pin and plastic
    plastic_length_distance = 3.99
    plastic_width_distance = 1.81
    plastic_height = 9.1

    # Material thickness of the plastic
    plastic_thickness = 1.0
    plastic_fillet_radius = 0.25

    # Actual dimensions of the plastic part
    plastic_length = (pin_cols * pin_space) + (2 * plastic_length_distance)
    plastic_width = (pin_rows * pin_space) + (2 * plastic_width_distance)

    # Create some selectors
    s = cq.selectors.StringSyntaxSelector
    b = cq.selectors.BoxSelector

    # Create the outer plastic shell
    outer_shell = (
        cq.Workplane("XY")
        .rect(plastic_length, plastic_width)
        .extrude(plastic_height)
        .edges("|Z")
        .fillet(plastic_fillet_radius)
    )

    inner_shell = (
        cq.Workplane("XY")
        .rect(
            plastic_length - 2 * plastic_thickness,
            plastic_width - 2 * plastic_thickness,
        )
        .extrude(plastic_height)
        .translate([0.0, 0.0, plastic_thickness])
    )

    box = outer_shell.cut(inner_shell)
    outer_shell = None
    inner_shell = None

    # Add inner Chamfer
    box = (
        box.edges((s(">Z") - s("<Z")))
        .edges(
            b(
                (
                    -plastic_length / 2 + plastic_thickness / 3,
                    -plastic_width / 2 + plastic_thickness / 3,
                    plastic_height + plastic_thickness / 3,
                ),
                (
                    plastic_length / 2 - plastic_thickness / 3,
                    plastic_width / 2 - plastic_thickness / 3,
                    0.0,
                ),
            )
        )
        .chamfer(0.75)
    )

    # Remove the key hole
    key_cutout = (
        cq.Workplane("XY")
        .rect(4.5, plastic_thickness * 2)
        .extrude(plastic_height)
        .translate([0.0, -plastic_width / 2, 2.3])
    )
    box = box.cut(key_cutout)
    key_cutout = None

    # Remove the side holes
    side_cutouts = (
        cq.Workplane("XY")
        .rect(plastic_thickness, 3.5)
        .extrude(6.4)
        .translate([-plastic_length / 2 + plastic_thickness / 2, 0.0, 0.0])
    )
    box = box.cut(side_cutouts)
    box = box.cut(side_cutouts.mirror("YZ", (0, 0)))
    side_cutouts = None

    # Add threads (on the other side of the key hole)
    threadcount = int((plastic_length - 2) // 11.4) + 1
    threads = (
        cq.Workplane("XY")
        .rarray(11.4, 1, threadcount, 1, center=True)
        .circle(0.5)
        .extrude(plastic_height - 1.5)
        .edges(">Z")
        .fillet(0.3)
        .translate([0, plastic_width / 2 - plastic_thickness / 4, 0])
    )
    box = box.union(threads)
    threads = None

    # Generate the actual pins
    pins = (
        cq.Workplane("XY")
        .rarray(pin_space, pin_space, pin_cols, pin_rows, center=True)
        .rect(pin_thickness, pin_thickness)
        .extrude(pin_height_top + pin_height_bottom + plastic_thickness)
        .edges("|Z")
        .fillet(pin_thickness * 0.25)
        .edges(">Z")
        .chamfer(0.8, 0.2)
        .edges("<Z")
        .chamfer(0.1, 0.1)
        .translate([0, 0, -pin_height_bottom])
    )

    # Cut the pins from the plastic part
    box = box.cut(pins)

    # Split the pins in top and bottom parts
    (pins_top, pins_bottom) = (
        pins.workplane().split(keepTop=True, keepBottom=True).all()
    )
    pins = None

    # Create an assembly
    assembly = (
        cq.Assembly(box, name="plastic", color=cq.Color(0.1, 0.1, 0.1, 1))
        .add(pins_bottom, name="pins-bottom", color=cq.Color(0.8, 0.8, 0.8, 1))
        .add(pins_top, name="pins-top", color=cq.Color(0.87, 0.75, 0.43, 1))
    )

    # Create a filename and store the result
    if not output_path.lower().endswith(".step"):
        filename = (
            f"{pin_rows}x{pin_cols}_{pin_space}_mm_idc_box_header_vertical_th.step"
        )
        assembly.save(f"{output_path}{filename}")
    else:
        assembly.save(output_path)


if __name__ == "__main__":
    generate_box_header(2, 8)
