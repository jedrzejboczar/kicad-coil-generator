import numpy as np

import KicadModTree as kmt



def coil_lines(coil_params, direction):


    width = coil_params[0]
    height = coil_params[1]
    thickness = coil_params[2]
    line_width = coil_params[3]
    line_spacing = coil_params[4]
    n_turns = int(coil_params[5])

    points = []

    #start at lower-left corner
    points.append((-width/2, -height/2))

    # points.append((params.r_outer, - params.r_outer))
    for i in np.arange(n_turns):
        x = width/2 - i * (line_width + line_spacing)
        y = height/2 - i * (line_width + line_spacing)

        next_x = x - (line_width + line_spacing)

        if direction > 0:
            turn_points = [
                (-x, y),
                (x, y),
                (x, -y),
                (-next_x, -y),
            ]
        else: print('NOT DONE YET')
            # turn_points = [
            #     (-x, -y),
            #     (-x, y),
            #     (x, y),
            #     (x, -next_y),
            # ]
        points.extend(turn_points)


    lines = []
    for i in range(len(points) - 1):
        lines.append(kmt.Line(start=points[i], end=points[i + 1],
                              width=line_width, layer='F.Cu'))

    start_point = points[0]
    end_point = points[-1]

    return lines, start_point, end_point



