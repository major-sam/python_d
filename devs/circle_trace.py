# -*- coding: utf-8 -*-
import math

from astrobox.core import Drone
from robogame_engine.geometry import Point
from robogame_engine.theme import theme

CIRCLE_STEP = 10
ATTACK_RADIUS = 220
SWITCH = -1


def build_circle_trace(rad, center_point, step, reverse=False):
    center_x = center_point.x
    center_y = center_point.y
    circle = []
    reverse_circle = []
    rng = range(int(center_x - rad), int(center_x + rad), step)
    if reverse:
        rng = reversed(rng)
    for x in rng:
        y = math.sqrt((rad - x + center_x) * (rad + x - center_x))
        if y == 0:
            if x == center_x - rad:
                append_trace_point(circle, reverse_circle, x, y, center_y)
                side_fix = x + step / 2
                y = math.sqrt((rad - side_fix + center_x) * (rad + side_fix - center_x))
                append_trace_point(circle, reverse_circle, side_fix, y, center_y)
            else:
                side_fix = x - step / 2
                append_trace_point(circle, reverse_circle, side_fix, y, center_y)
                append_trace_point(circle, reverse_circle, x, y, center_y)
        else:
            append_trace_point(circle, reverse_circle, x, y, center_y)
    circle.extend(reversed(reverse_circle))
    return circle


def append_trace_point(circle, reverse_circle, x, y, center_y):
    circle.append(Point(x=float(x), y=y + center_y))
    reverse_circle.append(Point(x=float(x), y=center_y - y))


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


class CircleTracer(Drone):
    my_team = []

    def on_born(self):
        self.target_to_destroy = None
        self.my_circle = None
        self.my_half_circle = []
        self.targets_to_destroy = self.get_targets()
        self.get_wait_point = Point(900, 200)
        self.shift = get_shifter(self.my_team)
        self.my_team.append(self)
        self.move_at(self.get_wait_point)

    def get_targets(self):
        targets = [target for target in self.scene.drones if
                   not isinstance(target, self.__class__) and not isinstance(target, self.mothership.__class__)]
        return targets

    def on_stop_at_asteroid(self, asteroid):
        pass

    def get_nearest_circle_point_index(self, circle):
        res_list = []
        for point in circle:
            res_list.append(
                {
                    'point': point,
                    'distance': self.distance_to(point)
                }
            )
        nearest_point = sorted(res_list, key=lambda item: item['distance'])[0]
        return res_list.index(nearest_point)

    def on_stop_at_point(self, target):
        if target is self.get_wait_point:
            choose_target_to_destroy = self.targets_to_destroy[0]
            self.target_to_destroy = choose_target_to_destroy
            if self.target_to_destroy.target:
                target_coord = self.target_to_destroy.target
            else:
                target_coord = self.target_to_destroy
            center_x = target_coord.x
            center_y = target_coord.y
            cycle_center = Point(center_x, center_y)
            # point_x_center = Point(center_x - ATTACK_RADIUS, center_y)

            # point_center_x = Point(center_x + ATTACK_RADIUS, center_y)
            # reverse = self.distance_to(point_center_x) < self.distance_to(point_x_center)
            if not self.my_circle or not self.target_to_destroy.is_alive:
                circle = build_circle_trace(ATTACK_RADIUS, cycle_center, CIRCLE_STEP)
                nearest_point_index = self.get_nearest_circle_point_index(circle)
                self.my_circle = shift_circle(circle, nearest_point_index)
                self.my_half_circle = get_half_circle(self.my_circle)
                place_step = len(self.my_half_circle) // len(self.my_team)
                self.target = self.my_half_circle[place_step * self.shift]
                #     self.my_circle_iter = iter(self.my_circle)
                # if next(self.my_circle_iter, None):
                #     self.target = (next(self.my_circle_iter))
                self.move_at(self.target)
            else:
                self.my_circle_iter = iter(self.my_circle)
        elif target in self.my_circle and self.target_to_destroy.is_alive:
            self.turn_to(self.target_to_destroy)
            if next(self.my_circle_iter, None):
                self.target = (next(self.my_circle_iter))
            else:
                self.my_circle_iter = iter(self.my_circle)
        elif self.target:
            self.move_at(self.target)

    def on_load_complete(self):
        pass

    def on_stop_at_mothership(self, mothership):
        self.unload_to(mothership)

    def on_unload_complete(self):
        self.move_at(self.target)

    def on_wake_up(self):
        if (self.near(point) for point in self.my_circle) and self.target_to_destroy.is_alive:
            if self.target_to_destroy.target:
                target_coord = self.target_to_destroy.target
            else:
                target_coord = self.target_to_destroy
            center_x = target_coord.x
            center_y = target_coord.y
            cycle_center = Point(center_x, center_y)
            if self.have_gun:
                self.turn_to(cycle_center)
                self.gun.shot(self.target_to_destroy)

            # if self.my_circle:
            #    if next(self.my_circle_iter, None):
            #        self.target = (next(self.my_circle_iter))
            #        # self.turn_to(self.target_to_destroy)
            #        # if self.have_gun and self.target_to_destroy.is_alive:
            #        #     self.gun.shot(self.target_to_destroy)
            #        self.move_at(self.target)
            #    else:
            #        self.my_circle_iter = iter(self.my_circle)
        elif self.target:
            self.move_at(self.target)
