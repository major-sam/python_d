# -*- coding: utf-8 -*-
import random

from astrobox.core import Drone


def exclude_a_from_b(a, b):
    result = []
    for item in b:
        if item != b:
            result.append(item)
    return result


def sort_by_cost(in_list):
    if in_list:
        return sorted(in_list, key=lambda item: item['cost'] if item is not None else 2 ** 100)
    else:
        return None


def get_sub_map_stats(sorted_super_sub_map, asteroid, _asteroid):
    if sorted_super_sub_map:
        for in_map in sorted_super_sub_map:
            add_route = [_asteroid]
            add_route.extend(in_map['route'])
            add_cost = asteroid.distance_to(_asteroid) + in_map['cost']
            return {'route': add_route,
                    'cost': add_cost}
    else:
        add_route = [_asteroid]
        add_cost = asteroid.distance_to(_asteroid)
        return ({'route': add_route,
                 'cost': add_cost})


def build_cost_sub_map(asteroid, asteroids, diff):
    current_asteroids = exclude_a_from_b(a=asteroid, b=asteroids)
    sub_map = []
    if current_asteroids:
        for _asteroid in current_asteroids:
            if not hasattr(_asteroid, 'new_payload'):
                _asteroid.new_payload = _asteroid.payload
            if _asteroid.new_payload == 0:
                continue
            elif _asteroid.new_payload > diff:
                add_route = _asteroid
                add_cost = asteroid.distance_to(_asteroid)
                sub_map.append({'route': [add_route],
                                'cost': add_cost})
            else:
                sub_diff = diff - asteroid.new_payload
                super_sub_map = build_cost_sub_map(_asteroid, current_asteroids, sub_diff)
                sorted_super_sub_map = sort_by_cost(super_sub_map)
                sub_map.append(get_sub_map_stats(sorted_super_sub_map=sorted_super_sub_map,
                                                 asteroid=asteroid,
                                                 _asteroid=_asteroid))
        return sub_map
    else:
        return None


def build_cost_map(current_position, asteroids, mothership):
    cost_map = []
    for asteroid in asteroids:
        if not hasattr(asteroid, 'new_payload'):
            asteroid.new_payload = asteroid.payload
        if len(cost_map) > 100:
            break
        if asteroid.new_payload == 0:
            continue
        elif asteroid.new_payload >= 100:
            cost = current_position.distance_to(asteroid) * 2
            cost_map.append({'route': [current_position, asteroid, mothership],
                             'cost': cost})
        else:
            diff = 100 - asteroid.new_payload
            sub_map = build_cost_sub_map(asteroid, asteroids, diff)
            cost_map.append(build_route_and_cost(sub_map, current_position, asteroid, mothership))
    return sort_by_cost(cost_map)


def build_route_and_cost(sub_map, current_position, asteroid, mothership):
    for in_map in sub_map:
        route = [current_position, asteroid, mothership]
        route[-1:1] = in_map['route']
        cost = current_position.distance_to(asteroid) + in_map['cost'] + current_position.distance_to(route[-2])
        return ({'route': route,
                 'cost': cost})


def choose_route(my_map):
    diff = 100
    if my_map:
        for asteroid in my_map['route']:
            if hasattr(asteroid, 'new_payload'):
                if asteroid.new_payload - diff < 0:
                    diff = 100 - asteroid.new_payload
                    asteroid.new_payload = 0
                else:
                    asteroid.new_payload -= diff
        return my_map['route']
    else:
        return None


def _upd1ate_asteroids_stats(asteroids):
    for asteroid in asteroids:
        asteroid.new_payload = asteroid.payload


class RebiachikhDrone(Drone):
    my_team = []
    empty_run = 0
    full_run = 0
    not_full_run = 0

    def _build_map(self):
        field_stats = sum(asteroid.payload for asteroid in self.asteroids)
        total_free_space = sum(drone.free_space for drone in self.my_team)
        if total_free_space < field_stats and field_stats > 0:
            self.build_my_map()
        else:
            self.build_map_with_my_team()

    def build_my_map(self):
        self.my_map = build_cost_map(self.my_mothership,
                                     asteroids=self.asteroids,
                                     mothership=self.my_mothership)
        if self.my_map:
            my_route = choose_route(self.my_map[0])
            if my_route:
                self.targets = list(filter(lambda a: a != self.my_mothership, my_route))
                self.target = self.targets.pop(0)
            else:
                self.target = self.my_mothership
        else:
            self.target = self.my_mothership

    def build_map_with_my_team(self):
        free_asteroids = self.get_free_asteroids()
        if free_asteroids:
            self.get_ending_route(free_asteroids)
        else:
            self.update_sleep_state()
            self.target = self.my_mothership
            self.print_stats()

    def get_free_asteroids(self):
        team_targets = self.get_team_targets()
        not_empty_asteroids = self.get_not_empty_asteroids()
        free_asteroids = [asteroid for asteroid in not_empty_asteroids if asteroid not in team_targets
                          and not asteroid.is_empty]
        drones = [drone for drone in self.my_team if drone != self and not drone.near(drone.mothership)]
        for asteroid in free_asteroids:
            if any(drone.near(asteroid) for drone in drones):
                free_asteroids.remove(asteroid)
        return free_asteroids

    def get_ending_route(self, free_asteroids):
        total_payload = 0
        for asteroid in free_asteroids:
            total_payload += asteroid.payload
        if self.free_space < total_payload:
            self.targets = free_asteroids
            self._choose_next_target()
        else:
            self.target = random.choice(free_asteroids)
            self.update_statistic(self.target)

    def on_born(self):
        self.my_team.append(self)
        self._build_map()

    def on_stop_at_asteroid(self, asteroid):
        self.load_from(asteroid)

    def on_load_complete(self):
        if self.is_full:
            self.update_statistic(self.my_mothership)
            self.move_at(self.my_mothership)
        else:
            self._choose_next_target()

    def _choose_next_target(self):
        if self.targets:
            self.target = self.targets.pop(0)
            self.update_statistic(self.target)
        elif any(asteroid.payload > 0 for asteroid in self.asteroids):
            self._build_map()
        else:
            self.update_statistic(self.my_mothership)
            self.move_at(self.my_mothership)

    def on_stop_at_mothership(self, mothership):
        self.unload_to(mothership)
        self._build_map()

    def on_unload_complete(self):
        if self.target:
            self.update_statistic(self.target)
            self.move_at(self.target)

    def on_wake_up(self):
        if self.target:
            self.update_statistic(self.target)
            self.move_at(self.target)

    def update_statistic(self, target):
        if self.is_full:
            self.full_run += self.distance_to(target)
        elif self.is_empty:
            self.empty_run += self.distance_to(target)
        else:
            self.not_full_run += self.distance_to(target)

    def print_stats(self):
        if all(drone.near(drone.mothership) for drone in self.my_team) and \
                sum(asteroid.payload for asteroid in self.asteroids) == 0:
            print(f'Full runs distance:{self.full_run}\n'
                  f'Empty runs distance: {self.empty_run}\n'
                  f'Not full runs distance: {self.not_full_run}')

    def get_team_targets(self):
        targets = []
        for drone in self.my_team:
            if drone.target != drone.mothership:
                targets.append(drone.target)
                targets.extend(drone.my_targets)
            else:
                continue
        return targets

    def get_not_empty_asteroids(self):
        result = []
        for asteroid in self.asteroids:
            if asteroid.payload > 0:
                result.append(asteroid)
        return result
