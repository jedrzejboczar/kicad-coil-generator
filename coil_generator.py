#!/usr/bin/env python3

"""
This is a script for generating coil footprints (spiral/rectangular) for PcbNew.
"""

import sys
import numpy as np
import argparse

import KicadModTree as kmt


import rectangle


class CoilParameters:
    def __init__(self, r_inner, r_outer, n_turns, line_width):
        self.r_inner = r_inner
        self.r_outer = r_outer
        self.n_turns = n_turns
        self.line_width = line_width

    @staticmethod
    def from_args(args):
        return CoilParameters(
            r_inner=args.r_inner,
            r_outer=args.r_outer,
            n_turns=args.n_turns,
            line_width=args.line_width,
        )


def coil_footprint(name, description, tags, other_parts):
    fp = kmt.Footprint(name)
    fp.setDescription(description)
    fp.setTags(tags)

    # add some text: reference and value
    fp.append(kmt.Text(type='reference', text='REF**', at=[0, -2], layer='F.SilkS'))
    fp.append(kmt.Text(type='value', text=name, at=[1.5, 2], layer='F.Fab'))

    for part in other_parts:
        fp.append(part)

    return fp


def coil_pads(start_point, end_point, line_width, drill, pad_type, pad_shape):
    if pad_type == 'SMT':
        pad_type = kmt.Pad.TYPE_THT
        pad_layer = kmt.Pad.LAYERS_THT
        drill_kw = dict(drill=drill)
    elif pad_type == 'THT':
        pad_type = kmt.Pad.TYPE_THT
        pad_layer = kmt.Pad.LAYERS_THT
        drill_kw = dict(drill=drill)
    elif pad_type == 'CONNECT':
        pad_type = kmt.Pad.TYPE_CONNECT
        pad_layer = kmt.Pad.LAYERS_THT
        drill_kw = dict()
    else:
        raise Exception('pad_type must be one of "SMT","THT" or "CONNECT"')
    if pad_shape == 'RECTANGLE':
        pad_shape = kmt.Pad.SHAPE_RECT
    elif pad_shape == 'CIRCLE':
        pad_shape = kmt.Pad.SHAPE_CIRCLE
    else:
        raise Exception('pad_type must be one of "RECTANGLE" or "CIRCLE"')
    if line_width - drill < 0.25:
        raise Exception('The width of the ring has to be greater than 0.25mm')
    pads = []
    for i, pos in enumerate([start_point, end_point]):
        pad = kmt.Pad(number=i + 1, type=pad_type, shape=pad_shape,
                      at=pos, size=[line_width, line_width], layers=pad_layer, **drill_kw)
        pads.append(pad)
    return pads


def save_footprint(footprint, file_name):
    if not file_name.endswith('.kicad_mod'):
        file_name = file_name + '.kicad_mod'

    file_handler = kmt.KicadFileHandler(footprint)
    file_handler.writeFile(file_name)


if __name__ == '__main__':

    winding_direction = 1 # don't change  
    drill_diameter = 1 #args.drill_ratio * coil_params.line_width
    pad_OD = drill_diameter + 0.5

    width = 8 #mm
    height = 500 #mm
    thickness = 3 #mm
    line_width = 0.2 #mm
    line_spacing = 0.2

    n_turns = np.floor((thickness + line_spacing)/(line_width + line_spacing)) # - THICKNESS FROM LINE TO LINE (round down)
    # n_turns = np.floor(thickness/(line_width + line_spacing)) # - THICKNESS INCLUDING LAST PAD POSITION (round down)

    coil_params = [width, height, thickness, line_width, line_spacing, n_turns]

    segments, start_point, end_point = rectangle.coil_lines(coil_params, winding_direction)
    pads = coil_pads(start_point, end_point, pad_OD, drill_diameter, 'CONNECT', 'RECTANGLE')



    fp = coil_footprint('Coil', 'One-layer coil', 'coil', segments + pads)
    save_footprint(fp, 'test_footprint.kicad_mod')

