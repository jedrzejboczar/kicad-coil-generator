import math
import collections
from math import pi

import KicadModTree as kmt

def polar2cartesian(r, theta):
    x, y = r * math.cos(theta), r * math.sin(theta)
    return (x, y)

def cartesian2polar(x, y):
    r, theta = math.sqrt(x**2 + y**2), math.atan2(y, x)
    return (r, theta)


def arc_through_3_points(A, B, C):
    """
    Calculate arc through 3 subsequent points (B is between A and B!).
    Algorithm:
        - find slopes of segments AB and BC
        - find slopes of lines perpendicular to AB and BC (slope_perp = -1 / slope)
        - find mid points of segments AB and BC
        - find 'b' of line equations (y = a*x + b) through those mid points
        - solve for the intersection point
    Returns:
        (D, angle_rad)
        D -- center point of the arc (x, y)
        angle_rad -- angle of the arc in radians
    """
    # data type for easier access
    Point = collections.namedtuple('Point', ['x', 'y'])
    A = Point(*A)
    B = Point(*B)
    C = Point(*C)

    # slopes of the segments perpendicular to AB and BC
    slope_AB = (A.y - B.y) / (A.x - B.x)
    slope_BC = (B.y - C.y) / (B.x - C.x)
    slope_perp_AB = -1 / slope_AB
    slope_perp_BC = -1 / slope_BC

    # mid points
    mid_AB = Point(x=(A.x + B.x) / 2, y=(A.y + B.y) / 2)
    mid_BC = Point(x=(B.x + C.x) / 2, y=(B.y + C.y) / 2)

    # calculate line equation b parameters (b = y - a*x)
    b_AB = mid_AB.y - slope_perp_AB * mid_AB.x
    b_BC = mid_BC.y - slope_perp_BC * mid_BC.x

    # solve for intersection (x, y) given the two equations y = a*x + b
    x = (b_AB - b_BC) / (slope_perp_BC - slope_perp_AB)
    y = slope_perp_AB * x + b_AB
    # let's call the center point D
    D = Point(x, y)

    # now find the angle of the arc,
    # this is the difference of angles of segments AD and CD
    angle_AD = math.atan2(A.y - D.y, A.x - D.x)
    angle_CD = math.atan2(C.y - D.y, C.x - D.x)
    angle_rad = angle_CD - angle_AD

    return tuple(D), angle_rad

def coil_arcs(params):
    """
    Approximates Archimedean spiral by a sequence of arcs.
    For each spiral revolution 'points_per_turn' are taken and an arc
    for each pair is drawn.

    The coordinates of start and end points of the line are returned as (x, y).

    Archimedean spiral is defined in polar coordinates by equation:
        r = a + b*theta
    where 'a' is the inner radius.

    We can calculate the outer radius as:
        R = a + b*total_theta
    And solve for b:
        b = (R - a) / total_theta

    We first define the spiral as if it had 0 line width,
    only when generating footprint we draw with the actual width.
    """
    if params.n_turns is None:
        return coil_arcs_by_spacing(params)
    else:
        return coil_arcs_by_turns(params)

def coil_arcs_by_turns(params):
    total_angle = 360 * params.n_turns
    b = (params.r_outer - params.r_inner) / math.radians(total_angle) * params.direction

    # calculate all the angles at which we evaluate points
    angle_increment = 360.0 / params.points_per_turn
    n_increments = int(total_angle / angle_increment)
    angles = [angle_increment * i for i in range(n_increments)]
    if angles[-1] < total_angle:
        angles += [total_angle]

    def cartesian_coords_for_angle(angle_deg):
        theta = math.radians(angle_deg)
        r = params.r_inner + b * theta
        x, y = polar2cartesian(r, theta)
        return x, y

    arcs = []
    for i in range(len(angles) - 1):
        start_angle = angles[i]
        end_angle = angles[i + 1]
        mid_angle = (start_angle + end_angle) / 2

        start = cartesian_coords_for_angle(start_angle)
        mid = cartesian_coords_for_angle(mid_angle)
        end = cartesian_coords_for_angle(end_angle)

        # calculate the center and angle of the arc
        center, angle_rad = arc_through_3_points(start, mid, end)
        if params.direction > 0:
            if angle_rad < 0:
                angle_rad += 2 * pi
        else:
            if angle_rad > 0:
                angle_rad -= 2 * pi

        # just draw everything on front copper layer
        layer = 'F.Cu'

        arcs.append(kmt.Arc(center=center, start=start, angle=math.degrees(angle_rad),
                            layer=layer, width=params.line_width))

    start_point = cartesian_coords_for_angle(angles[0])
    end_point = cartesian_coords_for_angle(angles[-1])

    return arcs, start_point, end_point

def coil_arcs_by_spacing(params):
    # given the inner and outer radius, we know the distance to be covered by the coil.
    # we can calculate the number of turns using the width of each line and the space between each line.
    fill_space = params.r_outer - params.r_inner
    line_space = params.line_width + params.spacing
    n_turns = fill_space / line_space
    params.n_turns = n_turns
    return coil_arcs_by_turns(params)

def line_spacing(params):
    """
    Calculates the space left between subsequent lines of the spiral
    for the given 'line_width'.
    This is effectively the space between copper paths, so it should
    be high enough to avoid electrical interference.
    Negative spacing is...too small.
    """
    if params.spacing is not None:
        return params.spacing
    else:
        total_angle = 360 * params.n_turns
        b = (params.r_outer - params.r_inner) / math.radians(total_angle)
        r0 = params.r_inner + b * 0
        r1 = params.r_inner + b * 2 * pi
        delta_r = abs(r1 - r0)
        spacing = delta_r - params.line_width
        return spacing

