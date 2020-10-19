#!/usr/bin/env python3

"""
This is a script for generating coil footprints (spiral/rectangular) for PcbNew.
"""


import numpy as np
import KicadModTree as kmt




def main():

	run_create_component('F.Cu', 1)
	run_create_component('B.Cu', 1)
	# run_create_component('F.Cu', -1)
	# run_create_component('B.Cu', -1)
		
	return



def run_create_component(board_layer, winding_direction):


	if (board_layer == 'F.Cu') and (winding_direction == 1):
		component_name = 'front_pos'
	elif (board_layer == 'B.Cu') and (winding_direction == 1):
		component_name = 'back_pos'
	elif (board_layer == 'F.Cu') and (winding_direction == -1):
		component_name = 'front_neg'
	elif (board_layer == 'B.Cu') and (winding_direction == -1):
		component_name = 'back_neg'



#INPUT PARAMETERS

	width = 15.284 #mm - from solidworks
	height = 675 #mm - from solidworks (acoustic length - 602 mm, total mandrel length - 711.2 mm)
	line_width = 0.153 #mm - recommended minimum from oshpark
	line_spacing = 0.153
	n_turns = 24
	coil_params = [width, height, line_width, line_spacing, n_turns]


	if ((n_turns*(line_width + line_spacing) - line_spacing) > np.min((width, height))):
		print('Error: too many turns for specified dimensions')
		return

#Pad parameters
	drill_diameter = 0.35 #args.drill_ratio * coil_params.line_width
	pad_OD = 0.6
	via_offset = 1


#CREATE COIL
	
	#Top layer
	segments, start_point, end_point = rectangle_coil_lines(coil_params, board_layer, via_offset, winding_direction)
	pads = coil_pads(start_point, end_point, pad_OD, drill_diameter)


	fp = coil_footprint('Coil', 'One-layer coil', 'coil', segments + pads)
	save_footprint(fp, component_name + '.kicad_mod')


	return


def rectangle_coil_lines(coil_params, board_layer, via_offset, winding_direction):


	width = coil_params[0]
	height = coil_params[1]
	line_width = coil_params[2]
	line_spacing = coil_params[3]
	n_turns = int(coil_params[4])

	points = []


#####################
## FRONT POSITIVE
	if (board_layer == 'F.Cu') and (winding_direction == 1):
		points.append((-width/2, height/2 + via_offset))
		points.append((-width/2, height/2))

		for i in np.arange(n_turns):
			x = width/2 - i * (line_width + line_spacing)
			y = height/2 - i * (line_width + line_spacing)
			next_y = y - (line_width + line_spacing)
			turn_points = [(x, y),(x, -y),(-x, -y),(-x, next_y)]
			points.extend(turn_points)

		#For the last point, add an offset for the Via 
		points.append((0, next_y))
		next_y = y - via_offset
		points.append((0, next_y))



#####################
## BACK POSITIVE
	elif (board_layer == 'B.Cu') and (winding_direction == 1):
		points.append((width/2, height/2 + via_offset))
		points.append((width/2, height/2))


		for i in np.arange(n_turns):
			x = width/2 - i * (line_width + line_spacing)
			y = height/2 - i * (line_width + line_spacing)
			next_y = y - (line_width + line_spacing)
			# turn_points = [(x, -y),(x, -y),(-x, -y),(-x, next_y)]

			turn_points = [(-x, y),(-x, -y),(x, -y),(x, next_y)]

			points.extend(turn_points)

		#For the last point, add an offset for the Via 
		points.append((0, next_y))
		next_y = y - via_offset
		points.append((0, next_y))




#####################
## FRONT NEGATIVE
	elif (board_layer == 'F.Cu') and (winding_direction == -1):
		points.append((-width/2, height/2 + via_offset))
		points.append((-width/2, height/2))

		for i in np.arange(n_turns):
			x = width/2 - i * (line_width + line_spacing)
			y = height/2 - i * (line_width + line_spacing)
			next_x = x - (line_width + line_spacing)
			turn_points = [(-x, -y),(x, -y),(x, y),(-next_x, y)]
			points.extend(turn_points)

		#For the last point, add an offset for the Via 
		next_y = height/2 - (n_turns) * (line_width + line_spacing) #next_y not defined for direction == -1
		next_y = y - via_offset
		points.append((-next_x, next_y))
		next_x = next_x - via_offset
		points.append((-next_x, next_y))


#####################
## BACK NEGATIVE
	elif (board_layer == 'B.Cu') and (winding_direction == -1):
		points.append((-width/2, height/2 + via_offset))
		points.append((-width/2, height/2))

		for i in np.arange(n_turns):
			x = width/2 - i * (line_width + line_spacing)
			y = height/2 - i * (line_width + line_spacing)
			next_x = x - (line_width + line_spacing)
			turn_points = [(-x, -y),(x, -y),(x, y),(-next_x, y)]
			points.extend(turn_points)

		#For the last point, add an offset for the Via 
		next_y = height/2 - (n_turns) * (line_width + line_spacing) #next_y not defined for direction == -1
		next_y = y - via_offset
		points.append((-next_x, next_y))
		next_x = next_x - via_offset
		points.append((-next_x, next_y))


	lines = []
	for i in np.arange(len(points) - 1):
		lines.append(kmt.Line(start=points[i], end=points[i + 1], width=line_width, layer=board_layer))

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


def coil_pads(start_point, end_point, line_width, drill):

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


