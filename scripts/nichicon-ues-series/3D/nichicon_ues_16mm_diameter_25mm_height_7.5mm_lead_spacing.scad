$fn = 64;

body_diameter = 16;
body_height = 25;
lead_spacing = 7.5;
lead_diameter = 0.8;
lead_length_below = 3.5;
body_lift = 1;
lead_stub = 1;
top_chamfer = 0.6;

module lead(x) {
    color([0.75, 0.75, 0.75])
    translate([x, 0, -lead_length_below])
        cylinder(h = lead_length_below + body_lift + lead_stub, d = lead_diameter);
}

module capacitor_body() {
    color([0.16, 0.18, 0.19])
    union() {
        translate([0, 0, body_lift])
            cylinder(h = body_height - top_chamfer, d = body_diameter);
        translate([0, 0, body_lift + body_height - top_chamfer])
            cylinder(h = top_chamfer, d1 = body_diameter, d2 = body_diameter * 0.92);
    }
}

module top_vent() {
    color([0.78, 0.78, 0.78])
    translate([0, 0, body_lift + body_height - 0.05])
    linear_extrude(height = 0.12)
    union() {
        square([body_diameter * 0.42, body_diameter * 0.08], center = true);
        square([body_diameter * 0.08, body_diameter * 0.42], center = true);
    }
}

lead(-lead_spacing / 2);
lead( lead_spacing / 2);
capacitor_body();
top_vent();
