# -*- coding: utf-8 -*-

from astrobox.space_field import SpaceField
from devs.speed_test import SpeedTester as drone
from devs.rotate_test import Rotator as rt
if __name__ == '__main__':
    scene = SpaceField(
        speed=3,
        asteroids_count=1,
        can_fight=True
    )
    d = [drone() for _ in range(2)]
    r = [rt() for _ in range(1)]
    scene.go()

# Первый этап: зачёт!
# Второй этап: зачёт!
