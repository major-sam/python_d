# -*- coding: utf-8 -*-
from astrobox.core import Drone
from devs.SwarmBrain import SwarmBrain
import logging
import devs.SwarmBrainConst as const

LOG_LEVEL = logging.INFO
logging.basicConfig(format='%(asctime)s - %(message)s', level=LOG_LEVEL)


class Swarm(Drone):
    my_team = []
    my_brain = SwarmBrain()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next_target = None
        self.my_mode, self.my_trace, self.my_target, self.my_attack_position = [None] * 4

    def on_born(self):
        self.my_team.append(self)
        self.move_at(self.my_brain.on_born_init(me=self))

    def on_wake_up(self):
        self.my_brain.do_i_want_change_decision(self)
        self.my_brain.make_decision(me=self)
        context = self.my_brain.brain_memory[self.id][const.MEM_CONTEXT]
        context.do_target_operation(me=self, memory=self.my_brain.brain_memory)

    def on_stop_at_target(self, target):
        self.my_brain.make_decision(me=self)
        context = self.my_brain.brain_memory[self.id][const.MEM_CONTEXT]
        context.do_target_operation(me=self, memory=self.my_brain.brain_memory)

    def on_stop_at_asteroid(self, asteroid):
        self.do_asteroid_operation(asteroid)

    def do_asteroid_operation(self, asteroid):  # todo to context
        self.load_from(asteroid)
        if self.next_target:
            self.turn_to(self.next_target)
        else:
            self.turn_to(self.mothership)

    def do_mothership_operation(self):
        pass
