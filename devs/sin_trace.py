# -*- coding: utf-8 -*-

from astrobox.core import Drone
from robogame_engine.geometry import Point
from robogame_engine.theme import theme
import my_utils
import logging

LOG_LEVEL = logging.INFO
logging.basicConfig(format='%(asctime)s - %(message)s', level=LOG_LEVEL)

CIRCLE_STEP = 10  # bug on 5 with default field size and disabled trace filter
ATTACK_RADIUS = 550
SWITCH = -1
_BOTTOM = 'b'
_TOP = 't'
_LEFT = 'l'
_RIGHT = 'r'


class SinTracer(Drone):
    my_team = []
    MSH_POS = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shift = None
        self.my_trace_points = []
        self.my_trace_points_to = []
        self.my_target = None
        self.my_trace_points_from = []

    def on_born(self):
        if not self.MSH_POS:
            self.MSH_POS = self.get_mothership_position()
        self.shift = my_utils.get_shifter(self.my_team)
        self.my_team.append(self)
        self.my_target = Point(500, 400)
        self.my_trace_points_to, self.my_trace_points_from = self.build_sin(self.my_target)
        self.my_trace_points = self.my_trace_points_to
        self.move_at(self.my_trace_points.pop())

    def build_sin(self, target):
        k, b = my_utils.get_route_line(self.coord, target)
        first_circle, second_circle = my_utils.get_sins_circles(self.coord, target, self.distance_to(target),
                                                                CIRCLE_STEP,
                                                                left_position=_LEFT in self.MSH_POS,
                                                                max_height=theme.FIELD_HEIGHT,
                                                                max_width=theme.FIELD_WIDTH)
        first_circle = my_utils.shift_circle(first_circle, self.get_nearest_circle_point_index(first_circle))
        second_circle = my_utils.shift_circle(second_circle, self.get_nearest_circle_point_index(second_circle))
        trace_to, trace_from = my_utils.get_sin_trace(k, b, first_circle, second_circle,
                                                      left_position=_LEFT in self.MSH_POS,
                                                      max_height=theme.FIELD_HEIGHT,
                                                      max_width=theme.FIELD_WIDTH,
                                                      drone_size=self.radius)
        my_utils.filter_trace(k, trace_to, _LEFT in self.MSH_POS, _BOTTOM in self.MSH_POS, destination_from=False)
        my_utils.filter_trace(k, trace_from, _LEFT in self.MSH_POS, _BOTTOM in self.MSH_POS, destination_from=True)
        return trace_to[::-1], trace_from[::-1]

    def get_mothership_position(self):
        return (_BOTTOM if self.my_mothership.y < theme.FIELD_HEIGHT / 2 else _TOP,
                _LEFT if self.my_mothership.x < theme.FIELD_WIDTH / 2 else _RIGHT)

    def on_stop_at_target(self, target):
        if self.near(self.my_target):
            if self.my_target == self.my_mothership:
                self.do_mothership_operation()
            else:
                self.do_target_operation()
        elif self.my_trace_points:
            logging.debug(f'me {self} go to {self.my_trace_points[-1]}')
            self.move_at(self.my_trace_points.pop())
        else:
            self.move_at(self.my_target)
            self.my_trace_points = self.my_trace_points_from

    def do_mothership_operation(self):
        logging.debug(f'me {self} is on target {type(self.my_target).__name__} at coord {self.my_target}')
        logging.debug('do_action')
        self.my_target = Point(604, 345)
        self.my_trace_points_to, self.my_trace_points_from = self.build_sin(self.my_target)
        self.my_trace_points = self.my_trace_points_to
        self.move_at(self.my_trace_points.pop())

    def do_target_operation(self):
        self.my_trace_points = self.my_trace_points_from
        logging.debug(f'me {self} is on target {type(self.my_target).__name__} at coord {self.my_target}')
        logging.debug('do_action')
        self.my_target = self.my_mothership
        # self.my_trace_points.extend(self.my_target)
        self.move_at(self.my_trace_points.pop())

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
        logging.debug('i am on point')
        pass
        # if self.my_trace_points:
        #    self.move_at(self.my_trace_points.pop(0))
        # else:
        #    logging.debug('end Point')

    def on_load_complete(self):
        pass

    def on_stop_at_mothership(self, mothership):
        if self.my_trace_points:
            self.move_at(self.my_trace_points.pop())
        else:
            logging.debug('end points')

    def on_unload_complete(self):
        self.move_at(self.target)

    def on_wake_up(self):
        if self.my_trace_points:
            self.move_at(self.my_trace_points.pop())
        else:
            logging.debug("WTF!!!&!&!&??!?!?!")
