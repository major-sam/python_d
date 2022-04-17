import math
from collections import OrderedDict

from robogame_engine.geometry import Point
from robogame_engine.theme import theme
from devs import SwarmBrainConst as const


def get_distance_between(p1, p2):
    if hasattr(p1, 'coord'):
        a = p1.coord
    else:
        a = p1
    if hasattr(p2, 'coord'):
        b = p2.coord
    else:
        b = p2

    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def get_enemy_target_points(drones_to_destroy):
    """
    func for getting enemies targets
    :param drones_to_destroy:  list of drones
    :return: list of dict (drone,target)
    """
    targets = []
    for drone in drones_to_destroy:
        s = drone.state.target_point
        if s:
            targets.append(
                {
                    'drone': drone,
                    'target': s
                }
            )
    return targets


def get_nearest_enemy(source_point, team_to_destroy):
    """
    func for gets nearest enemy drone
    :param source_point: source point
    :type source_point Point
    :param team_to_destroy: list of drones
    :type team_to_destroy list
    :return: nearest drone
    :rtype Drone
    """
    distance = None
    target = None
    for drone in team_to_destroy:
        if distance is None:
            distance = get_distance_between(source_point, drone.coord)
            target = drone
        else:
            next_distance = get_distance_between(source_point, drone.coord)
            target = drone if next_distance < distance else target
            distance = next_distance
    return target


def get_nearest_enemy_for_whole_team(team, team_to_destroy):
    """
    func for summarize distance to each enemy and gets minimal distance
    :param team: list of drones
    :type team list
    :param team_to_destroy: list of enemy drones
    :type team_to_destroy list
    :return: nearest drone for whole team
    :rtype Drone
    """
    all_dist = {}
    for enemy in team_to_destroy:
        all_dist.update({enemy: sum(get_distance_between(enemy.coord, drone.coord) for drone in team)})
    return min(all_dist, key=all_dist.get)


def get_team_to_destroy(me, memory):
    """
    check current target team in memory and returns team enemy drones if any one is alive
    :param me: drone which init change decision
    :param memory: swarm brain rewritable memory
    :return: first no dead enemy team
    """

    if len(memory) != 0:
        mem = memory[const.MEM_TEAM_TO_DESTROY]
        if any(drone.is_alive for drone in mem[const.MEM_DRONES]):
            return mem['name'], mem[const.MEM_DRONES], mem['mshp']
    teams = OrderedDict(me.scene.teams)
    teams.pop(me.team)
    for name, drones in teams.items():
        if not any(drone.is_alive for drone in drones):
            continue
        memory.update(
            {
                const.MEM_TEAM_TO_DESTROY:
                    {
                        "name": name,
                        const.MEM_DRONES: drones,
                        "mshp": drones[0].mothership,
                        const.MEM_OFFENCIVE_DRONES: [],
                        const.STAT: {}
                    }
            }
        )
        return name, drones, drones[0].mothership
    else:
        return None


def get_nearest_enemies_target(me, drones_to_destroy):
    """
    func for getting nearest target of enemies targets
    :param me: drone which init change decision
    :param drones_to_destroy: enemy drones team
    :return: enemies target
    :rtype Point
    """
    targets = get_enemy_target_points(drones_to_destroy)
    if len(targets) == 0:
        return None
    distance = None
    target = None
    for tgt in targets:
        if distance is None:
            distance = get_distance_between(me.coord, tgt['target'])
            target = tgt
        else:
            next_distance = get_distance_between(me.coord, tgt['target'])
            target = tgt if next_distance < distance else target
            distance = next_distance
    return target


def choose_target(me, nearest_enemy, nearest_enemies_target, nearest_enemy_for_whole_team, memory):
    """
    func for choosing target in input params
    :param me: drone which init new decision
    :param nearest_enemy: nearest target for drone
    :param nearest_enemies_target: nearest target of enemies drones for drone
    :param nearest_enemy_for_whole_team: nearest target for whole team
    :param memory: brain rewritable stats
    :return: one of input args
    :rtype Point
    """
    targets_coef = {'nearest_enemy': 0,
                    'nearest_enemy_for_whole_team': 0,
                    "nearest_enemies_target['target']": 0}
    if nearest_enemies_target == memory[const.N_ENEMY_TGT]:
        targets_coef["nearest_enemies_target['target']"] += 10
    if nearest_enemies_target:
        targets_coef["nearest_enemies_target['target']"] += 10
        if get_distance_between(me.coord, nearest_enemy.coord) > \
                get_distance_between(me.coord, nearest_enemies_target['target']):
            targets_coef['nearest_enemy'] += 10
        else:
            targets_coef["nearest_enemies_target['target']"] += 10
    else:
        targets_coef['nearest_enemy'] += 50
    if get_distance_between(nearest_enemy.coord, nearest_enemy_for_whole_team.coord) > 100:
        targets_coef[nearest_enemy_for_whole_team] += 30
    result = max(targets_coef, key=targets_coef.get)
    return eval(result)


def get_nearest_point_index(start_point, circle):
    """
    func for getting nearest point in list of points
    :param start_point: source point
    :type start_point Point
    :param circle: list of points
    :type circle list
    :return: index of nearest point
    :rtype int
    """
    res_list = []
    for point in circle:
        res_list.append(
            {
                'point': point,
                'distance': get_distance_between(start_point, point)
            }
        )
    nearest_point = sorted(res_list, key=lambda item: item['distance'])[0]
    return res_list.index(nearest_point)


def get_drones_attack_points(attack_points, safe_radius, me, target):
    """ func gets drones attack position points
    :param target:
    :param me:
    :param attack_points attack formation points
    :type attack_points list of Points
    :param safe_radius radius of safe positioning
    :type safe_radius int
    :returns drones points on attack_points split by distance eq radius and drones with no position count """
    result = []
    prev_point = attack_points[0]
    for point in attack_points:
        shot_trace = get_line_points(me=point, target=target)[0]
        conditions = [get_distance_between(point, prev_point) >= safe_radius,
                      get_distance_between(me.mothership, point) > me.mothership.radius + me.radius,
                      not any(me.mothership.near(p) for p in shot_trace)]
        if all(conditions):
            result.append(point)
            prev_point = point
    return result


def get_attack_arc(me, rad, target, my_msh_pos):
    """
    func for build attack arc for target
    :param me: drone which init build
    :type me astrobox.core.Drone
    :param rad: attack radius
    :type rad float
    :param target: target for attack
    :type target astrobox.core.Object
    :param my_msh_pos: drone mother ship position
    :type my_msh_pos list
    :return: result of get_drones_attack_points func
    :rtype tuple of list of Points and total count of drone without position
    """
    attack_circle = build_circle_trace(rad, target, 10, const.LEFT in my_msh_pos, theme.FIELD_WIDTH,
                                       theme.FIELD_HEIGHT)
    shifted_circle = shift_circle(attack_circle, get_nearest_circle_point_index(me, attack_circle))
    clear_circle_zeroes(shifted_circle)
    attack_points = get_attack_points(shifted_circle, me, my_msh_pos, target)
    return get_drones_attack_points(attack_points, me.radius, me, target)


def get_nearest_circle_point_index(drone, circle):
    res_list = []
    for point in circle:
        res_list.append(
            {
                'point': point,
                'distance': get_distance_between(drone, point)
            }
        )
    nearest_point = sorted(res_list, key=lambda item: item['distance'])[0]
    return res_list.index(nearest_point)


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


def clear_circle_zeroes(circle):
    for point in circle:
        if point.x in [0, 0.0] or point.y in [0, 0.0]:
            circle.remove(point)


def shift_circle(circle, shift):
    result = circle[shift:]
    result.extend(circle[:shift])
    return result


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


def get_start_position(my_msh_pos, msh_to_destroy):
    """
    func for getting start point
    :param my_msh_pos: mother ship position
    :type my_msh_pos tuple,list
    :param msh_to_destroy: enemy mother ship position
    :type msh_to_destroy: tuple,list
    :return: wait point
    :rtype Point
    """
    basic_shift = const.MAX_ATTACK_RADIUS - 300
    matcher = -1
    for elem in my_msh_pos:
        if elem in msh_to_destroy:
            matcher = my_msh_pos.index(elem)
    if matcher == 0:
        return Point(100, basic_shift)
    elif matcher == 1:
        return Point(basic_shift, 100)
    else:
        return Point(basic_shift, basic_shift)


def degrees_to_rad(angle):
    """
    func for convert degree to radian
    :param angle: angle in degrees
    :return: angle in radians
    """
    return angle * math.pi / 180


def get_intersection_point_of_lines(k1, b1, k2, b2):
    """
    func for getting intersection of 2 lines y=k1*x+b1 , y=k2*x+b2
    :param k1: k of func1
    :param b1: b of func1
    :param k2: k of func2
    :param b2: b of func2
    :return: Point of intersection
    """
    if k1 == k2 and b1 == b2:
        return True
    elif k1 == k2:
        return False
    else:
        x = (b2 - b1) / (k1 - k2)
        y = k1 * x + b1
        return Point(x=x, y=y)


def check_fire_points_useless(me, my_k, my_b, enemy, accuracity_coef):  # todo TO REMOVE
    enemy_k = math.tan(degrees_to_rad(enemy.direction))
    enemy_b = enemy.coord.y - enemy.coord.x * enemy_k
    intersection = get_intersection_point_of_lines(my_k, my_b, enemy_k, enemy_b)
    if type(intersection) == bool:
        return False
    else:
        dist_1 = get_distance_between(me.coord, intersection)
        dist_2 = get_distance_between(enemy.coord, intersection)
        return True if (1 - accuracity_coef) <= dist_1 / (dist_2 * 3) <= (1 + accuracity_coef) else False


def normalise_coord(x, y):
    x = x if x > 0 else 0
    x = x if x < theme.FIELD_WIDTH else theme.FIELD_WIDTH
    y = y if y > 0 else 0
    y = y if y < theme.FIELD_HEIGHT else theme.FIELD_HEIGHT


def build_drone_stats(me, enemy_drone, enemy_mothership):
    """
    func for enemy team cost build
    :param me: init drone
    :param enemy_drone: enemy drone
    :param enemy_mothership: enemy mothership
    :return: dict of enemy stats with cost
    """
    drone_state = {
        const.MEM_ENEMY: enemy_drone,
        const.MEM_ENEMY_COST: 0,
        # 'enemy_state': None,
        # 'enemy_pos': enemy_drone.coord,
        const.MEM_ENEMY_TARGET: None,
        const.MEM_ATTACK_RADIUS: 0,
    }
    if enemy_drone.is_moving:
        target_point_x = enemy_drone.state.target_point.x
        target_point_y = enemy_drone.state.target_point.y
        normalise_coord(target_point_x, target_point_y)
        drone_state[const.MEM_ENEMY_TARGET] = Point(target_point_x, target_point_y)
        drone_state[const.MEM_SHOOT_TARGET] = Point(target_point_x, target_point_y)
        if enemy_mothership.near(drone_state[const.MEM_ENEMY_TARGET]):
            drone_state[const.MEM_ENEMY_COST] += 90
        else:
            drone_state[const.MEM_ENEMY_COST] -= 10
    else:
        drone_state[const.MEM_ENEMY_TARGET] = enemy_drone.coord
        drone_state[const.MEM_ENEMY_COST] += 10
        drone_state[const.MEM_SHOOT_TARGET] = enemy_drone.coord
        enemy_in_msh_radius = get_distance_between(enemy_drone.coord,
                                                   me.mothership.coord) < const.MAX_ATTACK_RADIUS + me.mothership.radius + me.radius + 10
        team_distance = sum(get_distance_between(drone.coord, me.mothership.coord) for drone in me.my_team)
        if all([team_distance / (len(me.my_team) + 1) < const.MAX_ATTACK_RADIUS, enemy_in_msh_radius]):
            drone_state[const.MEM_ENEMY_COST] -= 50
    me_to_enemy = get_distance_between(me.coord, enemy_drone.coord)
    me_to_enemy_tgt = get_distance_between(me.coord, drone_state[const.MEM_ENEMY_TARGET])
    enemy_to_enemy_tgt = get_distance_between(enemy_drone.coord, drone_state[const.MEM_ENEMY_TARGET])
    enemy_target_to_enemy_mshp = get_distance_between(enemy_mothership.coord, drone_state[const.MEM_ENEMY_TARGET])
    if me_to_enemy < const.MAX_ATTACK_RADIUS:
        drone_state[const.MEM_ENEMY_COST] -= 5
    else:
        drone_state[const.MEM_ENEMY_COST] += 5
    if me_to_enemy < const.MAX_ATTACK_RADIUS / 2:
        drone_state[const.MEM_ENEMY_COST] -= 5
    if me_to_enemy_tgt < enemy_to_enemy_tgt:
        drone_state[const.MEM_ENEMY_COST] -= 10
    if me_to_enemy_tgt < enemy_to_enemy_tgt + const.MAX_ATTACK_RADIUS / 2:
        drone_state[const.MEM_ENEMY_COST] -= 10
    if me_to_enemy_tgt < const.MAX_ATTACK_RADIUS:
        drone_state[const.MEM_ENEMY_COST] -= 5
        if me_to_enemy_tgt > 120:
            drone_state[const.MEM_ATTACK_RADIUS] = me_to_enemy_tgt
        else:
            drone_state[const.MEM_ATTACK_RADIUS] = 120
    else:
        drone_state[const.MEM_ENEMY_COST] += 5
        # if enemy_target_to_enemy_mshp > me_to_enemy_tgt:
        drone_state[const.MEM_ATTACK_RADIUS] = const.MAX_ATTACK_RADIUS
        # else:
        #   drone_state[const.MEM_ATTACK_RADIUS] = const.MAX_ATTACK_RADIUS / 2
    if me_to_enemy_tgt < const.MAX_ATTACK_RADIUS / 2:
        drone_state[const.MEM_ENEMY_COST] -= 10
    return drone_state


def n_quick_switch(swarm_target, me, memory, change_conditions):
    """
    func for quick switch on prev target death
    :param change_conditions:
    :param swarm_target: dead target
    :param me: init drone
    :param memory: brain memory
    :return: None
    """
    dead_drone = swarm_target[const.MEM_ENEMY]
    if dead_drone in memory[const.MEM_TEAM_TO_DESTROY][const.MEM_DRONES]:
        memory[const.MEM_TEAM_TO_DESTROY][const.MEM_DRONES].remove(dead_drone)
    for drone in memory[const.MEM_TEAM_TO_DESTROY][const.MEM_DRONES]:
        if drone.near(dead_drone):
            swarm_target[const.MEM_ENEMY] = drone
            break
        elif drone.health < 100:
            swarm_target[const.MEM_ENEMY] = drone
            break
        elif get_distance_between(me, drone) < const.MAX_ATTACK_RADIUS:
            swarm_target[const.MEM_ENEMY] = drone
            break
    else:
        change_conditions.append(True)
    return


def quick_switch(swarm_target, me, memory):
    """
    func for quick switch on prev target death
    :param swarm_target: dead target
    :param me: init drone
    :param memory: brain memory
    :return: None
    """
    dead_drone = swarm_target[const.MEM_ENEMY]
    if dead_drone in memory[const.MEM_TEAM_TO_DESTROY][const.MEM_DRONES]:
        memory[const.MEM_TEAM_TO_DESTROY][const.MEM_DRONES].remove(dead_drone)
    for drone in memory[const.MEM_TEAM_TO_DESTROY][const.MEM_DRONES]:
        if drone.near(dead_drone):
            swarm_target[const.MEM_ENEMY] = drone
            break
        elif drone.health < 100:
            swarm_target[const.MEM_ENEMY] = drone
            break
        elif get_distance_between(me, drone) < const.MAX_ATTACK_RADIUS:
            swarm_target[const.MEM_ENEMY] = drone
            break
    else:
        me.my_brain.have_swarm_decision = False
    return


def get_team_position(me, memory, hold_points=None, hold_position=False):
    """
    func for getting team positions
    :param hold_position: hold current positions for all drones
    :param hold_points: points witch must be attack positions
    :type hold_points: dict
    :param me: init drone
    :param memory: team brain memory
    :return:
    """
    target = memory[const.MEM_SWARM_TARGET]
    recursion_breaker = 10
    if hold_position:
        return
    while True:
        recursion_breaker -= 1
        rad = target[const.MEM_ATTACK_RADIUS]
        circle = build_circle_trace(rad, target[const.MEM_ENEMY_TARGET], 1, True,
                                    max_height=theme.FIELD_HEIGHT, max_width=theme.FIELD_WIDTH, append_out=False)
        points = get_drones_attack_points(circle, me.radius * 2 + 1, me,
                                          target[const.MEM_ENEMY])
        if hold_points:
            for drone_id, hold_point in hold_points.items():
                [points.pop(p) for p in points if get_distance_between(p, hold_point) < me.radius * 2]
        if len(points) >= len(me.my_team):
            break
        rad += 50 if rad < const.MAX_ATTACK_RADIUS else rad - 50
        if recursion_breaker < 0:
            print('bad position!')
            break
    for drone in me.my_team:
        nearest_point_index = get_nearest_point_index(drone.coord, points)
        # if memory[drone.id][const.MEM_ATTACK_POSITION]:
        memory[drone.id][const.MEM_ATTACK_POSITION] = points.pop(nearest_point_index)
        # else:
        #    print("NO ATTACK POSITION!!!!")
    if hold_points:
        for drone_id, hold_point in hold_points.items():
            memory[drone_id][const.MEM_ATTACK_POSITION] = hold_point
    memory[const.MEM_ADDITIONAL_POSITIONS] = points


def set_mode(context, tr_to, mem, drone_id, context_string):
    """
    mod setter for SwarmBrainContext get_mode func
    :param context: current context
    :param tr_to: transition target context
    :param mem: current brain memory
    :param drone_id: current drone id
    :param context_string: human readable mod string
    """
    mem[drone_id][const.MEM_CONTEXT_STR] = context_string
    if tr_to:
        tr_str = 'switch brain'
        context.transition_to(tr_to())
        mem[drone_id][const.MEM_CONTEXT] = context
    else:
        tr_str = 'stay on'
    print('drone', drone_id, tr_str, mem[drone_id][const.MEM_CONTEXT_STR])


def get_best_target(me, who_is_alive):
    team_to_destroy, drones_to_destroy, msh_to_destroy = who_is_alive
    cost_list = []
    for drone in drones_to_destroy:
        drone_stats = build_drone_stats(me, drone, msh_to_destroy)
        cost_list.append(drone_stats)
    result = sort_by_cost(cost_list, const.MEM_ENEMY_COST)[0]
    return result


def sort_by_cost(in_list, cost='cost'):
    return sorted(in_list, key=lambda item: item[cost])


def match_points(p1, p2, rad=0):
    if p1.x == p2.x and p1.y == p2.y:
        return True
    else:
        return get_distance_between(p1, p2) < rad


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


def get_pre_fire_point(me, enemy, enemy_target, accuracity_coef=1):
    enemy_target_distance = get_distance_between(enemy.coord, enemy_target)
    enemy_trace = get_line_points(enemy, angle=enemy.direction, distance=enemy_target_distance)[0]
    for point in enemy_trace:
        me_to_point = get_distance_between(me.coord, point)
        if me_to_point > const.MAX_ATTACK_RADIUS:
            continue
        me_point_direction = get_angle(me.coord, point)
        direction_diff = math.fabs(me_point_direction - me.direction)
        arc_len = math.pi * me_to_point * direction_diff / 180
        predicted_dist = (me_to_point + arc_len) / const.SPEED_COEFFICIENT
        enemy_to_point = get_distance_between(enemy.coord, point)
        if accuracity_coef * -1 < enemy_to_point - predicted_dist < accuracity_coef:
            return point
    return False


def get_angle(source_point, target_point):
    """
    func for getting vector angle
    :param source_point: vector start
    :type source_point Point
    :param target_point: vector end
    :type target_point Point
    :return: angle in degrees
    """
    x = target_point.x - source_point.x
    y = target_point.y - source_point.y
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


def shoot_the_target(memory, me):
    target = memory[const.MEM_SHOOT_TARGET]
    enemy = memory[const.MEM_SWARM_TARGET][const.MEM_ENEMY]
    enemies = memory[const.MEM_TEAM_TO_DESTROY][const.MEM_DRONES]
    if check_shoot_trace(me, enemies, target):
        me.gun.shot(target)
        if not enemy.is_alive:
            memory[me.id][const.MEM_SHOOT_FLAG] = False
    else:
        if memory[const.MEM_ADDITIONAL_POSITIONS]:
            memory[me.id][const.MEM_ATTACK_POSITION] = memory[const.MEM_ADDITIONAL_POSITIONS].pop(
                get_nearest_point_index(me, memory[const.MEM_ADDITIONAL_POSITIONS]))
        else:
            me.my_brain.have_swarm_decision = False


def check_shoot_trace(me, enemies, target):
    points = get_line_points(me, target)[0]

    for point in points:
        if any(match_points(drone.coord, point, drone.radius) for drone in enemies):
            return True
        if any(match_points(drone.coord, point, drone.radius) for drone in me.my_team if drone is not me):
            return False
        if me.mothership.near(point):
            return False
    else:
        return True


def get_shoot_point(my_team, enemy_drone, enemy_target, memory):
    if hasattr(enemy_target, 'coord'):
        enemy_target_point = enemy_target.coord
    else:
        enemy_target_point = enemy_target
    for drone in my_team:
        if any([drone.coord == enemy_target_point, get_distance_between(drone, enemy_target) < 20,
                drone.near(enemy_target_point)]):
            target_drone = drone
            break
    else:
        print('target is None')
        return None
    target_drone_to_enemy_drone = get_distance_between(target_drone, enemy_drone)
    if target_drone_to_enemy_drone <= const.MAX_ATTACK_RADIUS + 30:
        target = enemy_drone
    else:
        to_enemy_trace = get_line_points(target_drone, enemy_drone,
                                         distance=get_distance_between(target_drone, enemy_drone))[0]
        # move_distance = (target_drone_to_enemy_drone - const.MAX_ATTACK_RADIUS - delta) / 2
        center_point = None
        for point in to_enemy_trace:
            if not center_point:
                center_point = point if get_distance_between(target_drone,
                                                             point) >= const.MAX_ATTACK_RADIUS else None
            if center_point:
                break
        else:
            center_point = enemy_drone
        target = center_point
    return target


def audit_moving_target(me, memory, enemy_drone, enemy_target):
    stats = memory[const.MEM_TEAM_TO_DESTROY][const.STAT]
    if any(aster.near(enemy_target) for aster in me.asteroids):  # todo may be bad decision for aster
        # todo count 10+ need to  use match_points func
        stats[const.MEM_ENEMY_STATE_COLLECTOR] += 1
    if any(get_distance_between(dr, enemy_target) <= const.MAX_ATTACK_RADIUS for dr in
           me.my_team):
        memory[const.MEM_TEAM_TO_DESTROY][const.MEM_OFFENCIVE_DRONES].append(enemy_drone)
        stats[const.MEM_ENEMY_STATE_OFFENCIVE] += 1
    else:
        stats[const.MEM_ENEMY_STATE_ON_WAIT] += 1


def audit_waiting_target(me, memory, enemy_drone):
    enemy_team_stat = memory[const.MEM_TEAM_TO_DESTROY][const.STAT]
    if enemy_drone.near(enemy_drone.mothership):
        enemy_team_stat[const.MEM_ENEMY_STATE_ON_WAIT] = +1
    elif any(aster.near(enemy_drone) for aster in me.asteroids):
        enemy_team_stat[const.MEM_ENEMY_STATE_COLLECTOR] = +1
    elif get_distance_between(enemy_drone, enemy_drone.mothership) < 250:
        enemy_team_stat[const.MEM_ENEMY_STATE_DEFENCIVE] = +1
    elif any(get_distance_between(dr, enemy_drone) <= const.MAX_ATTACK_RADIUS for dr in
             me.my_team):
        enemy_team_stat[const.MEM_ENEMY_STATE_OFFENCIVE] = +1
        memory[const.MEM_TEAM_TO_DESTROY][const.MEM_OFFENCIVE_DRONES].append(enemy_drone)
    else:
        enemy_team_stat[const.MEM_ENEMY_STATE_ON_WAIT] = +1


def audit_enemies(memory, me):
    enemy_team_stat = memory[const.MEM_TEAM_TO_DESTROY][const.STAT]
    enemy_team_stat.update({
        const.MEM_ENEMY_STATE_COLLECTOR: 0,
        const.MEM_ENEMY_STATE_DEFENCIVE: 0,
        const.MEM_ENEMY_STATE_OFFENCIVE: 0,
        const.MEM_ENEMY_STATE_ON_WAIT: 0
    })
    enemy_team = memory[const.MEM_TEAM_TO_DESTROY][const.MEM_DRONES]
    for enemy_drone in enemy_team:
        enemy_target = enemy_drone.state.target_point
        if enemy_target:
            audit_moving_target(me, memory, enemy_drone, enemy_target)
        else:
            audit_waiting_target(me, memory, enemy_drone)


def make_audit_results(memory, me):
    enemy_team = memory[const.MEM_TEAM_TO_DESTROY][const.MEM_DRONES]
    enemy_team_stat = memory[const.MEM_TEAM_TO_DESTROY][const.STAT]
    if enemy_team_stat[const.MEM_ENEMY_STATE_OFFENCIVE] > 0:
        print('need ambush')
        offencive_drones = memory[const.MEM_TEAM_TO_DESTROY][const.MEM_OFFENCIVE_DRONES]
        # todo choose best ambush_target
        #      todo check offencive drone target
        #      todo attack radius get radius = max_radius
        # todo set Swarm target
        for enemy_drone in offencive_drones:
            enemy_target = enemy_drone.state.target_point
            enemy_to_target = get_distance_between(enemy_target, enemy_drone)
            me_to_enemy_target = get_distance_between(enemy_target, me)
            my_drone_is_target = any([
                get_distance_between(my_drone, enemy_target) <= 40 for my_drone in me.my_team])
            if my_drone_is_target:
                pass
            else:
                pass
            pass
        # me_to_enemy_target = get_distance_between(enemy_target, me)
        # my_drone_is_target = any([
        #     get_distance_between(my_drone, enemy_target) < 50 for my_drone in my_team])
        # if my_drone_is_target:
        #     rad = const.MAX_ATTACK_RADIUS - 50  # todo -50 fix to step

        #     shoot_point = get_shoot_point(my_team, enemy_drone, enemy_target, memory)
        # else:
        #     rad = min(me_to_enemy_target, const.MAX_ATTACK_RADIUS)
        #     shoot_point = enemy_target
        # if shoot_point:
        #     offencive_enemy_pos.append({  # todo MUST BE NOT EMPTY
        #         const.MEM_ENEMY: enemy_drone,
        #         const.MEM_ATTACK_RADIUS: rad,
        #         const.MEM_ENEMY_TARGET: enemy_target,
        #         const.MEM_AMBUSH_FLAG: True,
        #         const.MEM_SHOOT_TARGET: shoot_point  # todo MUST BE REAL
        #     })
        # else:
        #     print(' shoot_point is none')

        #        memory[const.MEM_SWARM_TARGET] = offencive_enemy_pos.pop()
        # hold_pos = True
        # todo check current attack positions is ok and handle it with get_team_position(hold_position=True)
    elif enemy_team_stat[const.MEM_ENEMY_STATE_ON_WAIT] >= len(enemy_team):
        print('need sneaky trace, with stats refresh')
        # TODO  rad fix to minimum  team distance - 20
        memory[const.MEM_SWARM_TARGET] = {
            const.MEM_ENEMY: enemy_team[0].mothership,
            const.MEM_ATTACK_RADIUS: get_distance_between(me, enemy_team[0].mothership) - 50,
            const.MEM_ENEMY_TARGET: enemy_team[0].mothership,
            const.MEM_AMBUSH_FLAG: False,
            const.MEM_SHOOT_TARGET: enemy_team[0].mothership  # todo MUST BE REAL
        }
    elif all([enemy_team_stat[const.MEM_ENEMY_STATE_DEFENCIVE] > 0,
              enemy_team_stat[const.MEM_ENEMY_STATE_ON_WAIT] > 0]):
        print('turret on board, and somebody wait something', 'need short sneaky trace')
        print('need to replace')
        memory[const.MEM_SWARM_TARGET] = None
        # {
        #     const.MEM_ENEMY: enemy_team[0].mothership,
        #     const.MEM_ATTACK_RADIUS: ct.get_distance_between(me, enemy_team[0].mothership),
        #     const.MEM_ENEMY_TARGET: enemy_team[0].mothership,
        #     const.MEM_AMBUSH_FLAG: False,
        #     const.MEM_SHOOT_TARGET: enemy_team[0].mothership  # todo MUST BE REAL
        # }
    elif all([enemy_team_stat[const.MEM_ENEMY_STATE_COLLECTOR] > 0,
              enemy_team_stat[const.MEM_ENEMY_STATE_ON_WAIT] == 0]):
        print('collectors on board')
        memory[const.MEM_SWARM_TARGET] = None
    elif all([enemy_team_stat[const.MEM_ENEMY_STATE_COLLECTOR] > 0,
              enemy_team_stat[const.MEM_ENEMY_STATE_ON_WAIT] > 0]):
        print('collectors on board, and somebody wait something')
        memory[const.MEM_SWARM_TARGET] = None
    else:
        memory[const.MEM_SWARM_TARGET] = None
        print('strange complex enemy')
