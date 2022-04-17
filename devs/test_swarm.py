# -*- coding: utf-8 -*-

from astrobox.space_field import SpaceField
from devs.swarm import Swarm as sw
from devs.rarc_trace import RArcTracer as tgt1
from devs.stupid_target import StupidTarget as tgt2
from stage_04_soldiers.devastator import DevastatorDrone as tgt

if __name__ == '__main__':
    scene = SpaceField(
        speed=3,
        asteroids_count=4,
        can_fight=True
    )
    s = [sw() for _ in range(3)]
    d = [tgt() for _ in range(3)]
    scene.go()

# Первый этап: зачёт!
# Второй этап: зачёт!
