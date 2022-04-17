# -*- coding: utf-8 -*-
import random

from astrobox.core import Drone
from robogame_engine.geometry import Point


class StupidTarget(Drone):
    my_team = []

    def on_born(self):
        # p = Point(random.randint(200, 500), random.randint(100, 600))
        # self.move_at(p)
        self.my_team.append(self)

    def on_stop_at_asteroid(self, asteroid):
        self.load_from(asteroid)

    # def on_stop_at_target(self, target):
    #    p = Point(random.randint(200, 900), random.randint(100, 900))
    #    self.target = p

    def on_load_complete(self):
        self.move_at(self.my_mothership)

    def on_stop_at_mothership(self, mothership):
        self.unload_to(mothership)

    def on_unload_complete(self):
        self.move_at(self.target)

    def on_wake_up(self):
        a = 200
        b = 300
        srand = Point(random.randint(100, 1200), random.randint(100, 500))
        s = random.choice(self.asteroids)
        self.target = s
        if self.target:
            self.move_at(s)
