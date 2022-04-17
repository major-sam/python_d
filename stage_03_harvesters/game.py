# -*- coding: utf-8 -*-

# pip install -r requirements.txt

from astrobox.space_field import SpaceField

from rebiachikh_drone import RebiachikhDrone as drone
from stage_03_harvesters.reaper import ReaperDrone as enemy1
from stage_03_harvesters.driller import DrillerDrone as enemy

NUMBER_OF_DRONES = 5

if __name__ == '__main__':
    scene = SpaceField(
        speed=3,
        asteroids_count=15,
    )
    team_1 = [drone() for _ in range(NUMBER_OF_DRONES)]
    team_2 = [enemy() for _ in range(NUMBER_OF_DRONES)]
    scene.go()

# зачёт!
