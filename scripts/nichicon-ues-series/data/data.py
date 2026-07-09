
# Dict mapping package diameter to lead spacing
# (sourced from the e-ues series datasheet)
LEAD_SPACING_MM = {
    5.0: 2.0,
    6.3: 2.5,
    8.0: 3.5,
    10.0: 5.0,
    12.5: 5.0,
    16: 7.5,
}

# Dict mapping package diameter to lead diameter
# (sourced from the e-ues series datasheet)
LEAD_DIAMETER_MM = {
    5.0: 0.5,
    6.3: 0.5,
    8.0: 0.6,
    10.0: 0.6,
    12.5: 0.8,
    16.0: 0.8,
}

# Dict mapping the letters of an MPN to voltage ratings
VOLTAGE_READING_CODES = {
    "A": 10,
    "C": 16,
    "D": 20,
    "E": 25,
    "V": 35,
    "H": 50,
}
