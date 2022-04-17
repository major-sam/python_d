# -*- coding: utf-8 -*-

import my_core
from astrobox.core import Drone


class RebiachikhDrone(Drone):
    my_team = []
    my_team_routes = []

    def build_route(self, start_pos):
        my_route = my_core.build_route(drone=self,
                                       start_pos=start_pos,
                                       end_pos=self.my_mothership,
                                       my_asteroids=self.asteroids,
                                       my_team_routes=self.my_team_routes)
        if my_route:
            _targets = my_route['asteroids']
            self.my_targets = sorted(_targets, key=lambda item: item['asteroid'].payload, reverse=True)
            return True
        else:
            return False

    def check_route(self, start_pos):
        route = self.build_route(start_pos)
        if route:
            self.get_next_target()
        else:
            self.target = self.my_mothership

    def get_next_target(self):
        if self.my_targets:
            self.target = self.my_targets.pop(0)['asteroid']
            self.check_next_target()
        elif any(asteroid.payload > 0 for asteroid in self.asteroids):
            self.check_route(start_pos=self)
        else:
            self.target = self.my_mothership

    def check_next_target(self):
        if self.target.payload == 0:
            self.check_route(start_pos=self)
        path_coefficient = (self.distance_to(self.my_mothership) * 2) / \
                           (self.distance_to(self.target) + self.target.distance_to(self.my_mothership))
        if 0 < path_coefficient < self.fullness:
            self.my_targets = []
            self.target = self.my_mothership

    def remove_asteroid_from_routes(self, asteroid):
        items_to_remove = []
        for item in self.my_team_routes:
            if item['asteroid'] == asteroid:
                items_to_remove.append(item)
        for item_to_remove in items_to_remove:
            self.my_team_routes.remove(item_to_remove)

    def on_born(self):
        self.my_targets = []
        self.my_team.append(self)
        self.build_route(self)
        self.get_next_target()

    def on_stop_at_asteroid(self, asteroid):
        self.load_from(asteroid)
        if self.my_targets:
            self.turn_to(self.my_targets[0]['asteroid'])
        elif asteroid.payload > self.free_space:
            self.turn_to(self.my_mothership)

    def on_load_complete(self):
        self.remove_asteroid_from_routes(self.target)
        if self.is_full:
            self.move_at(self.my_mothership)
        elif self.my_targets:
            self.get_next_target()
        else:
            self.get_next_route()

    def get_next_route(self):
        if self.build_route(start_pos=self):
            self.get_next_target()
        else:
            self.move_at(self.my_mothership)

    def on_stop_at_mothership(self, mothership):
        self.unload_to(mothership)
        self.turn_to(self.asteroids[0])
        if all(asteroid.payload <= 0 for asteroid in self.asteroids):
            self.target = self.my_mothership

    def on_unload_complete(self):
        self.build_route(start_pos=self.my_mothership)
        self.get_next_target()
        self.move_at(self.target)

    def on_wake_up(self):
        if self.target:
            self.move_at(self.target)
