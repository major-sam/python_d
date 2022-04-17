import itertools
import math
import time
from datetime import datetime
import logging
from robogame_engine.geometry import Point
from robogame_engine.theme import theme
import devs.ContextTools as ct
import devs.SwarmBrainConst as const

LOG_LEVEL = logging.INFO
logging.basicConfig(format='%(asctime)s - %(message)s', level=LOG_LEVEL)


def get_angle(point1, point2):
    x = point2.x - point1.x
    y = point2.y - point1.y
    if x == 0:
        if y >= 0:
            direction = 90
        else:
            direction = 270
    else:
        direction = math.atan(y / x) * (180 / math.pi)
        if x < 0:
            direction += 180
    return normalise_angle(direction)


def normalise_angle(a):
    """
        Make angle in 0 < x < 360
    """
    return a % 360


def get_line_points(me, target=None, angle=None, distance=const.MAX_ATTACK_RADIUS, trace_step=1):
    assert target is not None or angle is not None
    if hasattr(me, 'coord'):
        my_coord = me.coord
    else:
        my_coord = me
    if hasattr(target, 'coord'):
        my_target = target.coord
    else:
        my_target = target
    if angle:
        rad_angle = angle * math.pi / 180
        k = math.tan(rad_angle)
        b = my_coord.y - my_coord.x * k
        end_point_y = int(my_coord.y + math.sin(rad_angle) * distance)
        end_point_x = int(my_coord.x + math.cos(rad_angle) * distance)
    elif my_target:
        k, b = get_route_line(my_coord, my_target)
        end_point_x = int(my_target.x)
        end_point_y = int(my_target.y)
    else:
        raise Exception("target or angle must be set")
    line_points = []
    if -1.0 < k < 1.0:
        for y in range(int(my_coord.y), end_point_y, trace_step):
            x = (y - b) / k
            line_points.append(Point(x, y))
    elif k == 0:
        for x in range(int(my_coord.x), end_point_x, trace_step):
            y = b
            line_points.append(Point(x, y))
    else:
        for x in range(int(my_coord.x), end_point_x, trace_step):
            y = k * x + b
            line_points.append(Point(x, int(y)))
    return line_points, k, b


def get_sins_circles(start, end, distance, step, left_position, max_width, max_height):
    first_center = Point((3 * start.x + end.x) / 4, (3 * start.y + end.y) / 4)
    second_center = Point((start.x + 3 * end.x) / 4, (start.y + 3 * end.y) / 4)
    radius = distance // 4
    first_circle_points = build_circle_trace(radius, first_center, step, left_position, max_width, max_height)
    second_circle_points = build_circle_trace(radius, second_center, step, left_position, max_width, max_height)
    return first_circle_points, second_circle_points


def build_circle_trace(rad, center_point, step, left_position, max_width, max_height, append_out=True):
    center_x = int(center_point.x)
    center_y = int(center_point.y)
    circle = []
    reverse_circle = []
    rng = range(center_x - int(rad), center_x + int(rad), step)
    if not left_position:
        rng = reversed(rng)
    for x in rng:
        y = math.sqrt((rad - x + center_x) * (rad + x - center_x))
        if y == 0:
            # +0.5\-0.5 rad simplified fix
            if x == center_x - rad:
                append_trace_point(circle, reverse_circle, x, y, center_y, max_width, max_height, append_out)
                side_fix = x + step / 2
                y = math.sqrt((rad - side_fix + center_x) * (rad + side_fix - center_x))
                append_trace_point(circle, reverse_circle, side_fix, y, center_y, max_width, max_height, append_out)
            else:
                side_fix = x - step / 2
                append_trace_point(circle, reverse_circle, side_fix, y, center_y, max_width, max_height, append_out)
                append_trace_point(circle, reverse_circle, x, y, center_y, max_width, max_height, append_out)
        else:
            append_trace_point(circle, reverse_circle, x, y, center_y, max_width, max_height, append_out)
    circle.extend(reversed(reverse_circle))
    return circle


def append_trace_point(circle, reverse_circle, x, y, center_y, max_width, max_height, append_out):
    y_top = center_y + y
    y_bot = center_y - y
    x_not_in_field = x > max_width - const.DRONE_RADIUS
    y_bot_not_in_field = y_bot < const.DRONE_RADIUS
    y_top_not_in_field = y_top > max_height - const.DRONE_RADIUS
    if not append_out and x_not_in_field:
        return
    x = max_width - const.DRONE_RADIUS if x_not_in_field else x
    x = const.DRONE_RADIUS if x < const.DRONE_RADIUS else x
    y_top = max_height - const.DRONE_RADIUS if y_top_not_in_field else y_top
    y_bot = const.DRONE_RADIUS if y_bot_not_in_field else y_bot
    if not append_out and y_top_not_in_field:
        pass
    else:
        circle.append(Point(x=float(x), y=y_top))
    if not append_out and y_bot_not_in_field:
        pass
    else:
        reverse_circle.append(Point(x=float(x), y=y_bot))


def shift_circle(circle, shift):
    result = circle[shift:]
    result.extend(circle[:shift])
    return result


def get_half_circle(cycle):
    cutter = len(cycle) // 4
    half_cycle = cycle[:cutter]
    half_cycle.extend(cycle[:-cutter - 1:-1])
    return half_cycle


def get_shifter(team):
    x = len(team)
    if len(team) % 2 == 0:
        res = x * -1
    else:
        res = x + 1
    return res // 2


def get_arc_circle(k, distance, step, start_coord, end_coord, left_position, max_width, max_height):
    arc_circle_center = get_arc_center_point(k, distance, start_coord, end_coord, left_position)
    rad = distance / (math.sqrt(2))
    arc_circle = build_circle_trace(rad, arc_circle_center, step, left_position, max_width, max_height)
    return arc_circle


def get_sin_trace(k, b, first_circle_points, second_circle_points, left_position, max_height, max_width, drone_size):
    second_circle_points = second_circle_points[::-1]
    sin_trace_to = []
    sin_trace_from = []
    if left_position:
        first_to, first_from = cut_circle_for_sins(k, b, first_circle_points, not left_position, max_height,
                                                   max_width, drone_size)
        second_to, second_from = cut_circle_for_sins(k, b, second_circle_points, left_position, max_height,
                                                     max_width, drone_size)
    else:
        first_to, first_from = cut_circle_for_sins(k, b, first_circle_points, left_position, max_height,
                                                   max_width, drone_size)
        second_to, second_from = cut_circle_for_sins(k, b, second_circle_points, not left_position, max_height,
                                                     max_width, drone_size)
    sin_trace_to.extend(first_to)
    sin_trace_to.extend(second_to)
    sin_trace_from.extend(second_from)
    sin_trace_from.extend(first_from)
    return sin_trace_to, sin_trace_from


def cut_circle_for_sins(k, b, circle, left_position, max_height, max_width, drone_size):
    trace_to = []
    trace_from = []
    for point in circle:
        if point.y <= drone_size or point.y >= max_height - drone_size or point.x <= drone_size \
                or point.x >= max_width - drone_size:
            continue
        elif point.y >= k * point.x + b:
            trace_to.append(point)
        else:
            trace_from.append(point)
    if left_position:
        trace_to, trace_from = trace_from, trace_to
    return trace_to, trace_from


def get_arc_trace(k, b, circle_points, left_position):
    arc_trace = []
    for point in circle_points:
        # if not left_position:
        # if point.y < k * point.x + b:
        #   arc_trace.append(point)
        # else:
        print(point.y)
        print(point.x * k + b)
        if point.y > k * point.x + b:
            arc_trace.append(point)
    return arc_trace


def get_route_line(start, end):
    """get line y=kx+b func args
    :param start - point a
    :param end - point b
    :type start Point
    :type end Point
    :returns k,b
    """
    if start.x != end.x:
        k = (start.y - end.y) / (start.x - end.x)
    else:
        k = 0
    b = start.y - k * start.x
    return k, b


def get_arc_center_point(k, horde_len, start_coord, end_coord, left_position):
    """conflux points of func1 y1 = -1/k*x+b1(90 degree rotated y=kx+b and shifted to middle of distance, which also
     center of func2) and func2 (y-a)^2 + (x-b)^2 = r^2 circle, for Pi/2 arc build
     :param k key k of root func
     :param horde_len distance as horde of Pi/2
     :param left_position position of mothership
     :param start_coord start point
     :param end_coord end point
     :type start_coord Point
     :type end_coord Point
     :type k float
     :type horde_len float
     :type left_position bool
     :returns Point  of Pi/2 arc center
     """
    radius = horde_len // math.sqrt(2)
    mid_point_x = (start_coord.x + end_coord.x) / 2
    mid_point_y = (start_coord.y + end_coord.y) / 2
    if k == 0:
        return Point(mid_point_x, mid_point_y - (horde_len / 2))
    k_90_degree_line = -1 / k
    b_90_degree_line = mid_point_y - mid_point_x * k_90_degree_line
    discr_a = k_90_degree_line ** 2 + 1
    discr_b = 2 * k_90_degree_line * b_90_degree_line - 2 * mid_point_x - 2 * k_90_degree_line * mid_point_y
    discr_c = mid_point_y ** 2 + mid_point_x ** 2 + b_90_degree_line ** 2 - radius ** 2 - 2 * b_90_degree_line * mid_point_y
    discr = discr_b ** 2 - 4 * discr_a * discr_c
    if not left_position:
        arc_x = (-discr_b - math.sqrt(discr)) / (2 * discr_a)
    else:
        arc_x = (-discr_b + math.sqrt(discr)) / (2 * discr_a)
    arc_y = k_90_degree_line * arc_x + b_90_degree_line
    return Point(arc_x, arc_y)


def exclude_item_from_list(item_to_remove, my_list):
    result = []
    for item in my_list:
        if item != item_to_remove:
            result.append(item)
    return result


def sort_by_cost(in_list, cost='cost'):
    return sorted(in_list, key=lambda item: item[cost])


def filter_trace(k, trace, left_pos, bottom_pos, destination_from):
    if -1 < k < 1:
        filter_axis = ['y', bottom_pos]
    else:
        filter_axis = ['x', left_pos]
    filter_by_axis(trace, filter_axis, destination_from)


def prepare_trace_for_filter(trace, pos, dest):
    buffer_trace = []
    if (not pos and dest) or (pos and not dest):
        buffer_trace.extend(trace)
    else:
        buffer_trace.extend(trace[::-1])
    return buffer_trace


def filter_by_axis(trace, axis, destination_from):
    buffer_trace = prepare_trace_for_filter(trace, axis[1], destination_from)
    prev_point = getattr(buffer_trace[0], axis[0])
    for point in buffer_trace:
        if prev_point >= getattr(point, axis[0]):
            trace.remove(point)
        prev_point = getattr(point, axis[0])


def filter_by_y(trace, bottom_pos, destination_from):
    buffer_trace = prepare_trace_for_filter(trace, bottom_pos, destination_from)
    prev_point_y = buffer_trace[0].y
    for point in buffer_trace:
        if prev_point_y >= point.y:
            trace.remove(point)
        prev_point_y = point.y


def get_new_payload(my_team_routes, asteroid):
    root_routes, routes = itertools.tee(my_team_routes)
    for item in routes:
        if item['asteroid'] == asteroid:
            return int(item['new_payload'])
    return 0


def time_track_cost(func):
    def surrogate(*args, **kwargs):
        started_at = time.time()
        readable_time = datetime.fromtimestamp(started_at).strftime('%c')
        logging.debug('func %s started at %s', func.__name__, readable_time)
        result = func(*args, **kwargs)
        ended_at = time.time()
        elapsed = round(ended_at - started_at, 4)
        logging.debug('Функция %s работала %s секунд(ы)', func.__name__, elapsed)
        return result

    return surrogate


def time_track(func):
    def surrogate(*args, **kwargs):
        started_at = time.time()
        readable_time = datetime.fromtimestamp(started_at).strftime('%c')
        drone_id = kwargs['drone'].id
        logging.debug('func %s for drone id %s started at %s', func.__name__, drone_id, readable_time)
        result = func(*args, **kwargs)
        ended_at = time.time()
        elapsed = round(ended_at - started_at, 4)
        logging.debug('Функция %s работала %s секунд(ы) drone id %s', func.__name__, elapsed, drone_id)
        return result

    return surrogate


def get_nearest_circle_point_index(drone, circle):
    res_list = []
    for point in circle:
        res_list.append(
            {
                'point': point,
                'distance': ct.get_distance_between(drone, point)
            }
        )
    nearest_point = sorted(res_list, key=lambda item: item['distance'])[0]
    return res_list.index(nearest_point)


def get_attack_points(shifted_circle, me, my_msh_pos, target):
    k1, b1 = get_route_line(me.coord, target)
    if k1 == 0:
        k = 0
    else:
        k = -1 / k1
    b = target.y - k * target.x
    top, bot = cut_circle_for_sins(k, b, shifted_circle, const.LEFT in my_msh_pos, theme.FIELD_HEIGHT,
                                   theme.FIELD_WIDTH, me.radius)
    if const.LEFT in my_msh_pos:
        return bot
    else:
        return top


def get_turn_angle(me, enemy):
    trace_to_enemy_angle = get_angle(me.coord, enemy.coord)
    my_angle = me.direction
    if my_angle - trace_to_enemy_angle < 180:
        return normalise_angle(my_angle + 10)
    else:
        return normalise_angle(my_angle - 10)


def get_shoot_point(me, enemy, enemy_target):
    line_points, k, b = get_line_points(enemy, enemy_target, 1)
    shoot_point = None
    enemy_pos = enemy.coord
    for point in line_points:
        my_distance = me.distance_to(point)
        next_angle = get_angle(me.coord, point)
        angle_diff = math.fabs(me.vector.direction - next_angle)
        rad = me.distance_to(point)
        arc_len = 2 * math.pi * angle_diff * rad / 360
        enemy_distance = ct.get_distance_between(enemy_pos, point)
        if - me.radius / 2 < my_distance - (enemy_distance + 2 * arc_len) * const.SPEED_COEFFICIENT < me.radius / 2 \
                and me.distance_to(point) < 600:
            shoot_point = point
            break
    return shoot_point


def match_points(p1, p2, rad=0):
    if p1.x == p2.x and p1.y == p2.y:
        return True
    else:
        return ct.get_distance_between(p1, p2) < rad
