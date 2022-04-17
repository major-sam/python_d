# -*- coding: utf-8 -*-

from astrobox.core import Drone
from robogame_engine.geometry import Point
from robogame_engine.theme import theme
import my_utils
# import pygame
# from pygame.draw import circle as pg_circle
# from robogame_engine.user_interface import RoboSprite as rs
# import robogame_engine.user_interface as ui

CIRCLE_STEP = 30
ATTACK_RADIUS = 550
SWITCH = -1
_BOTTOM = 'b'
_TOP = 't'
_LEFT = 'l'
_RIGHT = 'r'



class RArcTracer(Drone):
    my_team = []
    MSH_POS = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shift = None
        self.my_trace_points = []
        self.my_trace_points_back = []
        self.my_target = None

    def on_born(self):
        if not self.MSH_POS:
            self.MSH_POS = self.get_mothership_position()
        self.shift = my_utils.get_shifter(self.my_team)
        self.my_team.append(self)
        self.my_target = Point(500, 400)
        self.build_arc(target=self.my_target, left_position=_LEFT in self.MSH_POS)
        self.my_trace_points_back = self.my_trace_points[::-1]
        # for point in self.my_trace_points:
        #     pg_circle(surface=ui.UserInterface.sprites_by_layer, color=(153, 40, 40), center=point, radius=1)
        self.move_at(self.my_trace_points.pop(0))

    def build_arc(self, target, left_position):
        k, b = my_utils.get_route_line(self.coord, target)
        trace_circle = my_utils.get_arc_circle(k, self.distance_to(target), CIRCLE_STEP, self.coord, target,
                                               left_position, theme.FIELD_WIDTH, theme.FIELD_HEIGHT)
        shifted_circle = my_utils.shift_circle(trace_circle, self.get_nearest_circle_point_index(trace_circle))
        self.my_trace_points = my_utils.get_arc_trace(k, b, shifted_circle, left_position)
        self.my_trace_points.append(target)


    def get_mothership_position(self):
        return (_BOTTOM if self.my_mothership.y < theme.FIELD_HEIGHT / 2 else _TOP,
                _LEFT if self.my_mothership.x < theme.FIELD_WIDTH / 2 else _RIGHT)

    def on_stop_at_asteroid(self, asteroid):
        pass

    def on_stop_at_target(self, target):
        if self.near(self.my_target):
            if self.my_target == self.my_mothership:
                self.do_mothership_operation()
            else:
                self.do_target_operation()
        elif self.my_trace_points:
            self.move_at(self.my_trace_points.pop(0))
        else:
            self.move_at(self.my_target)

    def do_target_operation(self):
        print(f'{self} is on target {type(self.my_target).__name__} at coord {self.my_target}')
        print('do_action')
        self.my_trace_points = self.my_trace_points_back
        self.my_target = self.my_mothership
        self.my_trace_points.append(self.my_target)
        self.move_at(self.my_trace_points.pop(0))

    def do_mothership_operation(self):
        print(f'{self} is on target {type(self.my_target).__name__} at coord {self.my_target}')
        print('do_action')
        self.my_trace_points = []
        self.my_trace_points_back = []
        self.my_target = Point(500, 400)
        self.build_arc(target=self.my_target, left_position=_LEFT in self.MSH_POS)
        self.my_trace_points_back = self.my_trace_points[::-1]
        self.move_at(self.my_trace_points.pop(0))

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
        if self.my_trace_points:
            self.move_at(self.my_trace_points.pop(0))
        else:
            print('end POinst')

    def on_load_complete(self):
        pass

    def on_stop_at_mothership(self, mothership):
        pass

    def on_unload_complete(self):
        self.move_at(self.target)

    def on_wake_up(self):
        if self.my_trace_points:
            temp_target = self.my_trace_points.pop(0)
            self.move_at(temp_target)
        else:
            print('end points')
