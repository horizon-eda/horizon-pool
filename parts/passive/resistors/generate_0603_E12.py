#!/bin/python
import framework

size = "0603"
r_values = [ 1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2 ]
r_exponents = [0, 1, 2, 3, 4, 5, 6, 7]
pmax = "0.1"

default = {
        "MPN": [ False, "ADD_DATA" ],
        "base": "cbeda48c-7fb0-4cfb-a4de-d9672e8cc190",
        "inherit_tags": True,
        "manufacturer": [ False, "GEN" ],
        "parametric": {
            "pmax": pmax,
            "table": "resistors",
            "value": "ADD_DATA",
            "tolerance": "0.01"
            },
        "tags": [ "gen" ],
        "type": "part",
        "uuid": "ADD_DATA",
        "value": [ False, "ADD DATA" ]
        }

framework.gen_files(r_values, r_exponents, size, pmax, default)

