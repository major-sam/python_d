# -*- coding: utf-8 -*-

from astrobox.space_field import SpaceField
from devs.stupid_target import StupidTarget as target
from devs.trace_shooter import TraceShooter as shooter

if __name__ == '__main__':
    scene = SpaceField(
        speed=3,
        asteroids_count=1,
        can_fight=True
    )
    d = [shooter() for _ in range(1)]
    c = [target() for _ in range(1)]
    scene.go()

# Первый этап: зачёт!
# Второй этап: зачёт!
