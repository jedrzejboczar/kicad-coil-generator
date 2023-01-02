#!/usr/bin/env python3

"""
This script runs over a set of iterations for the coils, and generates a bulk
set of coils with those parameters. As a result, there's no inputs or anything,
we're basically just calling the coil generator script over and over again...
If you want a specific coil, better to just run the coil generator script
directly. If you want to change the generative parameters, you can do that
by fiddling with these global variables.
"""
from coil_generator import CoilParameters, construct_coil, save_footprint
import os

# fmt: off
MIN_TRACE_WIDTH_MM   = 0.128                # just a hair over 5 mils for rounding-error safety
MIN_TRACE_SPACING_MM = 0.128                # just a hair over 5 mils, again for rounding-error safety
INNER_RADIUS_MM      = 2.0                  # inner radius of the coil. Nothing will be generated within this area.
MIN_OUTER_RADIUS_MM  = 10.0                 # 10mm minimum radius. Our generation will start at this point.
MAX_OUTER_RADIUS_MM  = 100.0                # 100mm maximum radius. Our generation will end at this point.
STEP_RADIUS_MM       = 5.0                  # Our generation will step by this amount.
COIL_TYPES           = ["spiral", "square"] # the different modes to pass into the coil generator.
SIG_FIGS             = 3                    # how many significant figures to use in the filenames/text output.
BULK_OUTPUT_DIR      = "bulk_output"        # where to put the output files.

assert MIN_TRACE_WIDTH_MM   > 0.0
assert MIN_TRACE_SPACING_MM > 0.0
assert MIN_OUTER_RADIUS_MM  > 0.0
assert MAX_OUTER_RADIUS_MM  > 0.0
assert STEP_RADIUS_MM       > 0.0
assert MAX_OUTER_RADIUS_MM  > MIN_OUTER_RADIUS_MM
# fmt: on

# make sure that the BULK_OUTPUT_DIR exists.
if not os.path.exists(BULK_OUTPUT_DIR):
    os.makedirs(BULK_OUTPUT_DIR)

params = []
n = MIN_OUTER_RADIUS_MM
while n <= MAX_OUTER_RADIUS_MM:
    for type_ in COIL_TYPES:
        param = CoilParameters(
            r_inner=INNER_RADIUS_MM,
            r_outer=n,
            n_turns=None,
            spacing=MIN_TRACE_SPACING_MM,
            line_width=MIN_TRACE_WIDTH_MM,
            coil_type=type_,
        )
        params.append(param)
    n += STEP_RADIUS_MM


def param_to_filename(param):
    # return filename for the footprint given the params.
    # outputs might look like: "spiral_r5mm_tw0.128mm.kicad_mod"
    return "coil_{}_r{}mm_tw{}mm.kicad_mod".format(
        param.coil_type,
        round(param.r_outer, SIG_FIGS) if int(param.r_outer) != param.r_outer else int(param.r_outer),
        round(param.line_width, SIG_FIGS),
    )


print(
    "Generated parameters for {} coils. Now let's turn that into some footprints...".format(
        len(params)
    )
)
for param in params:
    coil = construct_coil(param, silent=True)
    print("Saving footprint for {}".format(param_to_filename(param)))
    save_footprint(coil, os.sep.join([BULK_OUTPUT_DIR, param_to_filename(param)]))
