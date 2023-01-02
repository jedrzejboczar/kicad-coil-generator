#!/usr/bin/env python3

"""
This is a script for generating coil footprints (spiral/rectangular) for PcbNew.
"""

import sys
import argparse

import KicadModTree as kmt

import spiral
import square


def cmdline_args():
    desc = "Generates KiCad footprints of spiral/square coils."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "file_name",
        help="path to the file in which to save the footprint;"
        " will overwrite previous file (this program cannot addmultiple footprints"
        " to the same file, so files have to be concatenated manually)",
    )
    parser.add_argument(
        "coil_type", choices=["spiral", "square"], help="type of the coil created"
    )

    inner_group = parser.add_mutually_exclusive_group(required=True)
    inner_group.add_argument(
        "-r", "--r_inner", type=float, help="inner radius of the coil [mm]"
    )
    inner_group.add_argument(
        "-d", "--d_inner", type=float, help="inner diameter of the coil [mm]"
    )

    outer_group = parser.add_mutually_exclusive_group(required=True)
    outer_group.add_argument(
        "-R", "--r_outer", type=float, help="outer radius of the coil [mm]"
    )
    outer_group.add_argument(
        "-D", "--d_outer", type=float, help="outer diameter of the coil [mm]"
    )

    parser.add_argument(
        "-w",
        "--line_width",
        required=True,
        type=float,
        help="width of the copper path used [mm]",
    )

    parser.add_argument(
        "--direction",
        "--dir",
        choices=["counter_clockwise", "clockwise"],
        default="counter_clockwise",
        help="direction in which the coil turns (starting from outer part)",
    )

    parser.add_argument(
        "-p",
        "--pad_type",
        choices=["SMT", "THT", "CONNECT"],
        default="CONNECT",
        help="type of the pads drawn at the ends of coil's path",
    )
    parser.add_argument(
        "-x",
        "--drill_ratio",
        type=float,
        default=0.6,
        help="ratio of the drill in pad to line width (only for SMT/THT pads)",
    )
    parser.add_argument(
        "-a",
        "--ring_width",
        type=float,
        default=0.25,
        help="Width of the ring around the drill",
    )

    # spiral coil only
    parser.add_argument(
        "--points_per_turn",
        default=4,
        type=float,
        help="(spiral only) number of arcs used for each full turn of the coil",
    )

    parser.add_argument(
        "-n",
        "--n_turns",
        required=False,
        type=float,
        help="number of turns of the coil",
    )
    parser.add_argument(
        "-s",
        "--spacing",
        type=float,
        default=0.5,
        required=False,
        help="spacing between turns [mm]",
    )

    args = parser.parse_args()

    if args.n_turns is None and args.spacing is None:
        raise Exception("Either n_turns or spacing must be specified")

    if args.direction == "counter_clockwise":
        args.direction = 1
    elif args.direction == "clockwise":
        args.direction = -1

    if args.d_inner:
        args.r_inner = args.d_inner / 2
    else:
        args.d_inner = args.r_inner * 2
    if args.d_outer:
        args.r_outer = args.d_outer / 2
    else:
        args.d_outer = args.r_outer * 2

    return args


# this is probably anti-pattern, but functions in submodules
# (spiral.py, square.py) assume that objects of type
#  CoilParameters are passed as 'params'
# "If it quacks like a duck, it is a duck."
DRILL_RATIO_DEFAULT = 0.6
RING_WIDTH_DEFAULT = 0.25
POINTS_PER_TURN_DEFAULT = 4
DIRECTION_DEFAULT = 1
PAD_TYPE_DEFAULT = "CONNECT"


class CoilParameters:
    def __init__(
        self,
        r_inner,
        r_outer,
        n_turns,
        spacing,
        line_width,
        coil_type,
        drill_ratio=DRILL_RATIO_DEFAULT,
        ring_width=RING_WIDTH_DEFAULT,
        points_per_turn=POINTS_PER_TURN_DEFAULT,
        direction=DIRECTION_DEFAULT,
        pad_type=PAD_TYPE_DEFAULT,
    ):
        self.r_inner = r_inner
        self.r_outer = r_outer
        self.n_turns = n_turns
        self.spacing = spacing
        self.line_width = line_width
        self.coil_type = coil_type
        self.drill_ratio = drill_ratio
        self.ring_width = ring_width
        self.points_per_turn = points_per_turn
        self.direction = direction
        self.pad_type = pad_type

    @staticmethod
    def from_args(args):
        return CoilParameters(
            r_inner=args.r_inner,
            r_outer=args.r_outer,
            n_turns=args.n_turns,
            spacing=args.spacing,
            line_width=args.line_width,
            coil_type=args.coil_type,
            direction=args.direction,
            drill_ratio=args.drill_ratio if args.drill_ratio else DRILL_RATIO_DEFAULT,
            ring_width=args.ring_width if args.ring_width else RING_WIDTH_DEFAULT,
            points_per_turn=args.points_per_turn
            if args.points_per_turn
            else POINTS_PER_TURN_DEFAULT,
            pad_type=args.pad_type if args.pad_type else PAD_TYPE_DEFAULT,
        )


def coil_footrpint(name, description, tags, other_parts):
    fp = kmt.Footprint(name)
    fp.setDescription(description)
    fp.setTags(tags)

    # add some text: reference and value
    fp.append(kmt.Text(type="reference", text="REF**", at=[0, -2], layer="F.SilkS"))
    fp.append(kmt.Text(type="value", text=name, at=[1.5, 2], layer="F.Fab"))

    for part in other_parts:
        fp.append(part)

    return fp


def coil_pads(start_point, end_point, line_width, drill, pad_type, pad_shape):
    if pad_type == "SMT":
        pad_type = kmt.Pad.TYPE_THT
        pad_layer = kmt.Pad.LAYERS_THT
        drill_kw = dict(drill=drill)
    elif pad_type == "THT":
        pad_type = kmt.Pad.TYPE_THT
        pad_layer = kmt.Pad.LAYERS_THT
        drill_kw = dict(drill=drill)
    elif pad_type == "CONNECT":
        pad_type = kmt.Pad.TYPE_CONNECT
        pad_layer = kmt.Pad.LAYERS_THT
        drill_kw = dict()
    else:
        raise Exception('pad_type must be one of "SMT","THT" or "CONNECT"')
    if pad_shape == "RECTANGLE":
        pad_shape = kmt.Pad.SHAPE_RECT
    elif pad_shape == "CIRCLE":
        pad_shape = kmt.Pad.SHAPE_CIRCLE
    else:
        raise Exception('pad_type must be one of "RECTANGLE" or "CIRCLE"')
    if line_width - drill < 0.25:
        raise Exception("The width of the ring has to be greater than 0.25mm")
    pads = []
    for i, pos in enumerate([start_point, end_point]):
        pad = kmt.Pad(
            number=i + 1,
            type=pad_type,
            shape=pad_shape,
            at=pos,
            size=[line_width, line_width],
            layers=pad_layer,
            **drill_kw
        )
        pads.append(pad)
    return pads


def save_footprint(footprint, file_name):
    if not file_name.endswith(".kicad_mod"):
        file_name = file_name + ".kicad_mod"

    file_handler = kmt.KicadFileHandler(footprint)
    file_handler.writeFile(file_name)


def construct_coil(coil_params, silent=False):
    drill_diameter = coil_params.drill_ratio * coil_params.line_width

    spacing, segments, pads = (
        -1,
        [],
        [],
    )  # just to put things in this scope, keep our linters happy, will be overwritten
    if coil_params.coil_type == "spiral":
        segments, start_point, end_point = spiral.coil_arcs(
            coil_params,
        )
        spacing = spiral.line_spacing(coil_params)
        pads = coil_pads(
            start_point,
            end_point,
            drill_diameter + coil_params.ring_width,
            drill_diameter,
            coil_params.pad_type,
            "CIRCLE",
        )
    elif coil_params.coil_type == "square":
        segments, start_point, end_point = square.coil_lines(coil_params)
        spacing = square.line_spacing(coil_params)
        pads = coil_pads(
            start_point,
            end_point,
            drill_diameter + coil_params.ring_width,
            drill_diameter,
            coil_params.pad_type,
            "RECTANGLE",
        )

    if not silent:
        if spacing <= 0:
            print("[WARNING] line spacing <= 0", file=sys.stderr)
        else:
            print("Line spacing = %.3f mm" % spacing)

    fp = coil_footrpint("Coil", "One-layer coil", "coil", segments + pads)
    return fp


def main():
    args = cmdline_args()
    coil_params = CoilParameters.from_args(args)
    fp = construct_coil(coil_params)
    save_footprint(fp, args.file_name)


if __name__ == "__main__":
    main()
