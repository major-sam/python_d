# -*- coding: utf-8 -*-

from astrobox.space_field import SpaceField
from devs.arc_trace import ArcTracer as arc
from devs.rarc_trace import RArcTracer as rarc
if __name__ == '__main__':
    scene = SpaceField(
        speed=3,
        asteroids_count=1,
        can_fight=True
    )
    s = [arc() for _ in range(1)]
    d = [rarc() for _ in range(1)]
    scene.go()

# Первый этап: зачёт!
# Второй этап: зачёт!
