# -*- coding: utf-8 -*-
import random

from astrobox.core import Drone
from robogame_engine.geometry import Point


class SpeedTester(Drone):
    my_team = []
    start_points = [Point(30, 400), Point(30, 500)]
    end_points = [Point(1200, 400), Point(1200, 500)]

    def on_born(self):
        self.target = self.start_points.pop()
        self.end_point = self.end_points.pop()
        self.move_at(self.target)
        self.my_team.append(self)
        self.in_position = False
        return random.choice(self.asteroids)

    def on_stop_at_target(self, target):
        self.turn_to(self.end_point)
        self.in_position = True

    def on_stop_at_point(self, target):

        self.turn_to(self.end_point)
        self.in_position = True

    def on_load_complete(self):
        self.move_at(self.my_mothership)

    def on_stop_at_mothership(self, mothership):
        self.unload_to(mothership)

    def on_unload_complete(self):
        self.move_at(self.target)


    def on_wake_up(self):
        self.turn_to(self.end_point)
        if all(drone.vector.direction < 5 for drone in self.my_team):
            if self.my_team.index(self) == 0:
                self.gun.shot(self.end_point)
            else:
                self.move_at(self.end_point)
