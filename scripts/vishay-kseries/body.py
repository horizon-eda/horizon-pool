from solid import *
from solid.utils import *


def create_pins(spacing=5.0, diameter=0.5, length=6.0):
    # Create the pins (spacing along the length side)
    #  ____________
    # |            |
    # |            |
    # |____________|
    #   ||      ||
    #   ||      || ← Pins

    pin1 = translate([(spacing/-2.0)-(diameter/2.0), diameter/-2.0, length*-1.0])(cube([diameter, diameter, length]))
    pin2 = translate([(spacing/2.0)-(diameter/2.0), diameter/-2.0, length*-1.0])(cube([diameter, diameter, length]))

    bow_z = 0.35
    if spacing == 5.0:
        x_offset = 2.85

        pinext1 = translate([x_offset, 0, 0.3+bow_z])(rotate([0, 45, 0])(translate([(spacing/-2.0)-(diameter/2.0), diameter/-2.0, length*-1.0])(cube([diameter, diameter, length]))))
        pinext2 = translate([-x_offset, 0, 0.3+bow_z])(rotate([0, -45, 0])(translate([(spacing/2.0)-(diameter/2.0), diameter/-2.0, length*-1.0])(cube([diameter, diameter, length]))))
        
        # Cut away
        pincut1 = translate([x_offset, -diameter/2.0, 0.51+diameter+bow_z])(rotate([0, 45, 0])(translate([(spacing/-2.0)-(diameter/2.0), diameter/-2.0, length*-2.0])(cube([diameter, 2*diameter, 2*length]))))
        pincut2 = translate([-x_offset, -diameter/2.0, 0.51+diameter+bow_z])(rotate([0, -45, 0])(translate([(spacing/2.0)-(diameter/2.0), diameter/-2.0, length*-2.0])(cube([diameter, 2*diameter, 2*length]))))
        pincut3 = translate([x_offset, -diameter/2.0, 0.51+diameter+bow_z+diameter])(rotate([0, 45, 0])(translate([(spacing/-2.0)-(diameter/2.0), diameter/-2.0, length*-2.0])(cube([diameter, 2*diameter, 2*length]))))
        pincut4 = translate([-x_offset, -diameter/2.0, 0.51+diameter+bow_z+diameter])(rotate([0, -45, 0])(translate([(spacing/2.0)-(diameter/2.0), diameter/-2.0, length*-2.0])(cube([diameter, 2*diameter, 2*length]))))
    pins = pin1 + pin2

    if spacing == 5.0:
        pins = pins + pinext1 + pinext2
        pins = pins - (pincut1 + pincut2 + pincut3 + pincut4)

    pins = translate([0, 0, 2.5])(pins)
    pins = color([0.82, 0.64, 0.2,1.0])( pins )
    return pins


def create_body(length, width, height):
    bdy = translate([0, 0, height])(scale([length, width, height])(sphere(r=1.0)))
    return bdy


def construct_part(length, width, height, spacing=5, lead_diameter=0.5):
    body = create_body(length, width, height)
    body = color([0.7,0.1,0.1,1.0])( body )
    pins = create_pins(spacing, lead_diameter, 5.0)
    return body + pins


def write_scadfile(path, element):
    with open(path, "w+") as f:
        f.write(element)
