import KicadModTree as kmt


def delta_r(params):
    # the change of radius at each step
    if params.n_turns > 1:
        delta_r = (params.r_outer - params.r_inner) / (params.n_turns - 1)
    else:  # for one turn this is needed not to close the square
        delta_r = 2 * params.line_width
    return delta_r


def coil_lines(params):
    if params.n_turns is None:
        return coil_lines_by_spacing(params)
    else:
        return coil_lines_by_turns(params)


def coil_lines_by_turns(params):
    """
    Creates a square spiral coil.

    It is assumed that we want to fill as much space as possible,
    and so the length of line is shortened only after full turn.
    The coil starts at corner of the square and ends in "previous"
    corner.
    """
    n_turns = int(params.n_turns)
    if abs(n_turns - params.n_turns) > 0.01:
        print(
            "[WARNING] square coil can only have integer number of turns;"
            " reducing n_turns to %d" % n_turns
        )

    points = []
    points.append((params.r_outer, -params.r_outer))
    for i in range(n_turns):
        r = params.r_outer - i * delta_r(params)
        next_r = r - delta_r(params)
        if params.direction > 0:
            turn_points = [
                (-r, -r),
                (-r, r),
                (r, r),
                (r, -next_r),
            ]
        else:
            turn_points = [
                (r, r),
                (-r, r),
                (-r, -r),
                (next_r, -r),
            ]
        points.extend(turn_points)

    lines = []
    for i in range(len(points) - 1):
        lines.append(
            kmt.Line(
                start=points[i],
                end=points[i + 1],
                width=params.line_width,
                layer="F.Cu",
            )
        )

    start_point = points[0]
    end_point = points[-1]

    return lines, start_point, end_point


def coil_lines_by_spacing(params):
    fill_space = params.r_outer - params.r_inner
    line_space = params.line_width + params.spacing
    n_turns = int(fill_space / line_space)
    params.n_turns = n_turns
    return coil_lines_by_turns(params)


def line_spacing(params):
    """
    Calculates the space left between subsequent lines of the coil.
    This is effectively the space between copper paths, so it should
    be high enough to avoid electrical interference.
    Negative spacing is...too small.
    """
    if params.spacing is not None:
        return params.spacing
    else:
        return delta_r(params) - params.line_width
