# -*- coding: utf-8 -*-

from astrobox.space_field import SpaceField
from devs.stupid_target import StupidTarget as drone
from devs.circle_trace import CircleTracer as circle
from devs.arc_trace import ArcTracer as arc
from devs.rarc_trace import RArcTracer as rarc
from devs.sin_trace import SinTracer as sin_tr
from devs.rsin_trace import RSinTracer as rsin_tr
if __name__ == '__main__':
    scene = SpaceField(
        speed=3,
        asteroids_count=1,
        can_fight=True
    )
    s = [sin_tr() for _ in range(1)]
    d = [rsin_tr() for _ in range(1)]
    scene.go()

# Первый этап: зачёт!
# Второй этап: зачёт!
