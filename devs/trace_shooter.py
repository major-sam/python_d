# -*- coding: utf-8 -*-
import math
import random
from robogame_engine.geometry import Point, Vector
import my_utils
from astrobox.core import Drone
from robogame_engine.theme import theme
import devs.ContextTools as ct

SPEED_COEFFICIENT = 3

TRACE_STEP = 5


class TraceShooter(Drone):
    my_team = []
    enemies_target = list()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.enemies = list()

    def on_born(self):
        self.move_at(Point(600, 400))
        self.my_team.append(self)
        self._get_enemies()

    def on_stop_at_point(self, target):
        self.turn_to(Point(self.my_mothership.x + theme.FIELD_WIDTH, self.my_mothership.y))

    def _get_enemies(self):
        for drone in self.scene.drones:
            if drone.__class__ != self.__class__:
                self.enemies.append(drone)

    def _get_enemies_target(self):
        for drone in self.enemies:
            self.enemies_target.append({drone: {
                'target': drone.target}})

    def _choose_attack_target(self):
        pass

    def on_wake_up(self):
        if self.gun.can_shot:
            enemy = self.enemies[0]
            self.turn_to(enemy)
            if enemy.is_moving:
                enemy_target = enemy.target
                shoot_point = self._get_shoot_point(enemy, enemy_target)
                if shoot_point:
                    self.turn_to(shoot_point)
                    print('moving_shot')
                    self.gun.shot(shoot_point)
            else:
                self.turn_to(enemy)
                print('not_moving_shot')
                self.gun.shot(enemy)

    def _get_shoot_point(self, enemy, enemy_target):
        line_points, k, b = my_utils.get_line_points(enemy, enemy_target, TRACE_STEP)
        shoot_point = None
        enemy_pos = enemy.coord
        for point in line_points:
            my_distance = self.distance_to(point)
            next_angle = my_utils.get_angle(self.coord, point)
            angle_diff = math.fabs(self.vector.direction - next_angle)
            rad = self.distance_to(point)
            arc_len = 2 * math.pi * angle_diff * rad / 360

            enemy_distance = ct.get_distance_between(enemy_pos, point)
            if - self.radius / 2 < my_distance - (enemy_distance+2*arc_len) * SPEED_COEFFICIENT < self.radius / 2 \
                    and self.distance_to(point) < 600:
                shoot_point = point
                print(arc_len)
                break
        return shoot_point
