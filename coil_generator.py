#!/usr/bin/env python3

"""
This is a script for generating coil footprints (spiral/rectangular) for PcbNew.
"""


import numpy as np
import KicadModTree as kmt




def main():

#INPUT PARAMETERS
	winding_direction = -1 # +1 or -1  
	
	width = 15 #mm
	height = 200 #mm
	line_width = 0.153 #mm
	line_spacing = 0.153
	n_turns = 20
	coil_params = [width, height, line_width, line_spacing, n_turns]


	if ((n_turns*(line_width + line_spacing) - line_spacing) > np.min((width, height))):
		print('Error: too many turns for specified dimensions')
		return

#Pad parameters
	drill_diameter = 0.35 #args.drill_ratio * coil_params.line_width
	pad_OD = 0.7
	via_offset = 0.6


#CREATE COIL
	segments, start_point, end_point = rectangle_coil_lines(coil_params, via_offset, winding_direction)
	pads = coil_pads(start_point, end_point, pad_OD, drill_diameter, 'CONNECT')

	fp = coil_footprint('Coil', 'One-layer coil', 'coil', segments + pads)
	save_footprint(fp, 'test_footprint.kicad_mod')





def rectangle_coil_lines(coil_params, via_offset, direction):


	width = coil_params[0]
	height = coil_params[1]
	line_width = coil_params[2]
	line_spacing = coil_params[3]
	n_turns = int(coil_params[4])

	points = []

	#start at lower-left corner

	#For the first point, add an offset for the Via 
	points.append((-width/2, height/2 + via_offset))
	points.append((-width/2, height/2))

	# points.append((params.r_outer, - params.r_outer))
	for i in np.arange(n_turns):

		x = width/2 - i * (line_width + line_spacing)
		y = height/2 - i * (line_width + line_spacing)

		if direction == 1: #counter-clockwise
			next_y = y - (line_width + line_spacing)
			turn_points = [
				(x, y),
				(x, -y),
				(-x, -y),
				(-x, next_y),
			]
		elif direction  == -1: #clockwise
			next_x = x - (line_width + line_spacing)
			turn_points = [
				(-x, -y),
				(x, -y),
				(x, y),
				(-next_x, y),
			]

		points.extend(turn_points)



	#For the last point, add an offset for the Via 
	if direction == 1:
		points.append((0, next_y))
		next_y = y - via_offset
		points.append((0, next_y))

	elif direction  == -1: 
		next_y = height/2 - (n_turns) * (line_width + line_spacing) #next_y not defined for direction == -1
		next_y = y - via_offset
		points.append((-next_x, next_y))
		next_x = next_x - via_offset
		points.append((-next_x, next_y))




	lines = []
	for i in np.arange(len(points) - 1):
		lines.append(kmt.Line(start=points[i], end=points[i + 1], width=line_width, layer='F.Cu'))

	start_point = points[0]
	end_point = points[-1]

	return lines, start_point, end_point





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


def coil_pads(start_point, end_point, line_width, drill, pad_type):

	pad_type = kmt.Pad.TYPE_THT
	pad_layer = kmt.Pad.LAYERS_THT
	drill_kw = dict(drill=drill)

	pad_shape = kmt.Pad.SHAPE_CIRCLE
	

	pads = []
	for i, pos in enumerate([start_point, end_point]):
		pad = kmt.Pad(number=i + 1, type=pad_type, shape=pad_shape, at=pos, size=[line_width, line_width], layers=pad_layer, **drill_kw)
		pads.append(pad)
	return pads


def save_footprint(footprint, file_name):
	if not file_name.endswith('.kicad_mod'):
		file_name = file_name + '.kicad_mod'

	file_handler = kmt.KicadFileHandler(footprint)
	file_handler.writeFile(file_name)





if __name__ == '__main__': main()


