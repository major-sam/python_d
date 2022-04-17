# -*- coding: utf-8 -*-
import itertools
import random

from astrobox.core import Drone
from robogame_engine.geometry import Point


class Rotator(Drone):
    my_team = []
    self_targets = itertools.cycle([Point(410, 200), Point(400, 210), Point(390, 200), Point(400, 190)])

    def on_born(self):
        self.target = Point(400, 200)
        self.move_at(self.target)
        self.my_team.append(self)
        self.i = 0

    def on_wake_up(self):
        self.turn_to(next(self.self_targets))

