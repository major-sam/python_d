# -*- coding: utf-8 -*-

from astrobox.space_field import SpaceField

from devs.sam_v1_1 import RebiachikhDrone as drone


if __name__ == '__main__':
    scene = SpaceField(
        speed=3,
        asteroids_count=17,
    )
    d = [drone() for _ in range(5)]
    # d = SamDrone()
    scene.go()

# Первый этап: зачёт!
# Второй этап: зачёт!
