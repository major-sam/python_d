# -*- coding: utf-8 -*-

from astrobox.space_field import SpaceField
from devs.stupid_target import StupidTarget as drone
from devs.circle_trace import CircleTracer as circle

if __name__ == '__main__':
    scene = SpaceField(
        speed=3,
        asteroids_count=1,
        can_fight=True
    )
    d = [drone() for _ in range(1)]
    c = [circle() for _ in range(2)]
    scene.go()

# Первый этап: зачёт!
# Второй этап: зачёт!
