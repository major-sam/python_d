import itertools
import random

from robogame_engine.theme import theme

import my_utils
from devs import SwarmBrainConst as const


@my_utils.time_track_cost
def build_cost(route, routes_w_new_payload):
    cost = 0
    for i, item in enumerate(route, start=1):
        if i < len(route):
            target = route[i]
            target_new_payload = my_utils.get_new_payload(my_team_routes=routes_w_new_payload, asteroid=target)
            if target.payload < 50:
                cost += const.PAYLOAD_PENALTY + 100
            if target.payload > 130:
                cost -= const.PAYLOAD_PENALTY

            if target_new_payload and target_new_payload <= 0:
                cost_payload_changer = 0.9
            else:
                cost_payload_changer = 1
            cost += my_utils.get_distance_between(item, target)
            cost *= cost_payload_changer
    return cost


@my_utils.time_track
def build_route(drone, start_pos, end_pos, my_asteroids, my_team_routes):
    routes = []
    root_asteroids, asteroids = itertools.tee(my_asteroids)
    my_team_targets = []
    for item in my_team_routes:
        my_team_targets.append(item['asteroid'])
    for asteroid in asteroids:
        new_payload = int(asteroid.payload)
        if len(routes) > 100:
            break
        if asteroid.payload <= 0:
            continue
        if asteroid in my_team_targets:
            new_payload = my_utils.get_new_payload(my_team_routes, asteroid)
        if new_payload == 0:
            continue
        results = route_build_step(drone, asteroid, asteroids, my_team_targets, my_team_routes, new_payload)
        if results:
            res = merge_results(results, drone, start_pos, end_pos)
            routes.extend(res)
    sort_routes = my_utils.sort_by_cost(routes)
    if sort_routes:
        best_route = check_best_route(my_team_targets, sort_routes, routes, drone)
        update_team_routes_stats(best_route, my_team_targets, my_team_routes)
    else:
        best_route = None
    return best_route


def update_team_routes_stats(best_route, my_team_targets, my_team_routes):
    for item in best_route['asteroids']:
        if item['asteroid'] in my_team_targets:
            for route_dict in my_team_routes:
                if route_dict['asteroid'] == item['asteroid']:
                    route_dict['new_payload'] = item['new_payload']
        else:
            my_team_routes.extend(best_route['asteroids'])


@my_utils.time_track_cost
def check_best_route(my_team_targets, sort_routes, routes, drone):
    best_route = dict()
    is_best_route = False
    iter_count = 0
    while not is_best_route:
        iter_count += 1
        if iter_count > const.MAX_ITER:
            # pass
            best_route = handle_max_iter_excess(routes, drone)
            break
        exp_best_route = sort_routes[0]
        for item in exp_best_route['asteroids']:
            if item['asteroid'] in my_team_targets:
                exp_best_route['cost'] += const.TEAM_PENALTY
                sort_routes = my_utils.sort_by_cost(sort_routes)
                best_route = sort_routes[0]
                is_best_route = best_route['route'] == exp_best_route['route']
            else:
                best_route = exp_best_route
                is_best_route = True
    return best_route


def handle_max_iter_excess(routes, drone):
    best_routes = my_utils.sort_by_cost(routes)
    drone_count = len(drone.my_team_name)
    best_routes_count = len(best_routes)
    if drone_count > best_routes_count:
        list_len = best_routes_count
    else:
        list_len = drone_count
    return random.choice(best_routes[0:list_len])


def merge_results(results, drone, start_pos, end_pos):
    r = []
    for result in results:
        route = {
            'drone': drone,
            'asteroids': [],
            'route': [start_pos],
            'my_targets': []
        }
        route['asteroids'].extend(result['asteroids'])
        route['my_targets'].extend(result['my_targets'])
        route['route'].extend(result['route'])
        route['route'].append(end_pos)
        route['cost'] = build_cost(route=route['route'], routes_w_new_payload=route['asteroids'])
        r.append(route)
    return r


def route_build_step(drone, asteroid, asteroids, my_team_targets, my_team_routes, new_payload):
    routes = []
    single_route = {
        'asteroids': [
            {
                'asteroid': asteroid,
                'new_payload': asteroid.payload - drone.free_space
            }
        ],
        'route': [asteroid],
        'my_targets': [asteroid]
    }
    if new_payload <= 0:
        return None
    elif new_payload < drone.free_space:
        free_space_diff = drone.free_space - new_payload
        sub_routes = build_sub_route(asteroid, asteroids, free_space_diff, my_team_targets, my_team_routes)
        if sub_routes:
            routes.extend(update_sub_route(sub_routes, asteroid))
        else:
            routes.append(single_route)
    else:
        routes.append(single_route)
    return routes


def update_sub_route(_routes, _asteroid):
    res = []
    for sub_route in _routes:
        _route = {
            'asteroids': [
                {
                    'asteroid': _asteroid,
                    'new_payload': 0
                }
            ],
            'route': [_asteroid],
            'my_targets': [_asteroid]
        }
        if sub_route:
            _route['asteroids'].extend(sub_route['asteroids'])
            _route['route'].extend(sub_route['route'])
            _route['my_targets'].extend(sub_route['my_targets'])
            res.append(_route)
    return res


def build_sub_route(asteroid, asteroids, free_space_diff, my_team_targets, my_team_routes):
    root_asteroids, sub_asteroids = itertools.tee(asteroids)
    sub_asteroids = my_utils.exclude_item_from_list(item_to_remove=asteroid, my_list=sub_asteroids)
    routes = []
    for sub_asteroid in sub_asteroids:
        new_payload = int(sub_asteroid.payload)
        if len(routes) > 100:
            break
        if sub_asteroid.is_empty:
            sub_asteroids.remove(sub_asteroid)
            continue
        if sub_asteroid in my_team_targets:
            new_payload = my_utils.get_new_payload(my_team_routes, asteroid)
        if new_payload <= 0:
            continue
        sub_routes = sub_route_build_step(sub_asteroid, sub_asteroids, free_space_diff, my_team_targets,
                                          my_team_routes, new_payload)
        if sub_routes:
            for sub_route in sub_routes:
                if sub_route:
                    routes.append(sub_route)
        else:
            return None
    if routes:
        return routes
    else:
        return None


def sub_route_build_step(sub_asteroid, asteroids, free_space_diff, sub_team_targets, my_team_routes, new_payload):
    sub_routes = []
    end_point = {
        'asteroids': [
            {
                'asteroid': sub_asteroid,
                'new_payload': sub_asteroid.payload - free_space_diff
            }
        ],
        'route': [sub_asteroid],
        'my_targets': [sub_asteroid]
    }
    if new_payload <= 0:
        return None
    elif new_payload < free_space_diff:
        super_sub_diff = free_space_diff - new_payload
        super_sub_routes = build_sub_route(sub_asteroid, asteroids, super_sub_diff, sub_team_targets, my_team_routes)
        if super_sub_routes:
            sub_routes.extend(update_sub_route(super_sub_routes, sub_asteroid))
        else:
            sub_routes.append(end_point)
    else:
        sub_routes.append(end_point)
    return sub_routes


def get_mothership_position(mother_ship):
    return (const.BOTTOM if mother_ship.y < theme.FIELD_HEIGHT / 2 else const.TOP,
            const.LEFT if mother_ship.x < theme.FIELD_WIDTH / 2 else const.RIGHT)
