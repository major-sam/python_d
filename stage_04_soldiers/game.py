# -*- coding: utf-8 -*-

# pip install -r requirements.txt

from astrobox.space_field import SpaceField
from stage_03_harvesters.driller import DrillerDrone
from stage_04_soldiers.devastator import DevastatorDrone
# TODO тут импортировать своих дронов

NUMBER_OF_DRONES = 5

if __name__ == '__main__':
    scene = SpaceField(
        # field=(900, 900),
        speed=1,
        asteroids_count=7,
        can_fight=True,
    )
    # TODO создать их
    #team_1 = [VaderDrone() for _ in range(NUMBER_OF_DRONES)]
    # TODO и побороть противников!
    #team_2 = [ReaperDrone() for _ in range(NUMBER_OF_DRONES)]
    team_3 = [DrillerDrone() for _ in range(1)]
    team_4 = [DevastatorDrone() for _ in range(NUMBER_OF_DRONES)]
    scene.go()

