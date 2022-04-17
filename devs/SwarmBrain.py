from collections import OrderedDict

import devs.SwarmBrainContext as sbc
import devs.ContextTools as ct
import devs.SwarmBrainConst as const
import my_core as core


class SwarmMemory:

    def __init__(self):
        # todo move dict to memory
        print("i am new empty memory, please code and fill me")
        pass


class SwarmBrain:

    def __init__(self):
        self.start_position = None
        self.my_team = None
        self.drones_to_destroy = None
        self.team_to_destroy = None
        self.initialised = False
        self.have_decision = False
        self.have_swarm_decision = False
        self.my_mothership_position = None
        self.my_team_name = None
        self.teams_count = None
        self.drones_count = None
        self.teams = None
        self.my_team_health = None
        self.my_team_name = list()
        self.enemy_teams = dict()
        self.brain_memory = dict()
        self.memory = SwarmMemory()
        self.msh_to_destroy = None
        self.context = None
        self.init_context = sbc.Context(sbc.DestroyEnemies())

    def on_born_init(self, me):
        if not self.initialised:
            self.init_brain(me)
        return self.start_position

    def init_brain(self, me):
        teams = OrderedDict(me.scene.teams)
        self.my_team_name = me.team
        self.my_mothership_position = core.get_mothership_position(me.my_mothership)
        self.enemy_teams = teams
        self.teams_count = len(teams)
        self.my_team = teams[self.my_team_name]
        self.drones_count = len(teams[self.my_team_name])
        self.team_to_destroy, self.drones_to_destroy, self.msh_to_destroy = \
            ct.get_team_to_destroy(me=me, memory=self.brain_memory)
        for drone in self.my_team:
            self.brain_memory.update({drone.id: {const.MEM_CONTEXT: self.init_context,
                                                 const.MEM_SHOOT_FLAG: False,
                                                 const.MEM_ATTACK_POSITION: None,
                                                 }
                                      })
        msh_to_destroy_position = core.get_mothership_position(self.msh_to_destroy)
        self.start_position = ct.get_start_position(self.my_mothership_position, msh_to_destroy_position)
        self.initialised = True

    def make_decision(self, me):
        self.context = self.brain_memory[me.id][const.MEM_CONTEXT]
        self.context.get_mode(me, self.brain_memory)
        self.context.make_decision(me=me, memory=self.brain_memory)

    def do_i_want_change_decision(self, me):
        self.context = self.brain_memory[me.id][const.MEM_CONTEXT]
        self.context.get_mode(me, self.brain_memory)
        self.context.do_i_want_change_decision(me=me, memory=self.brain_memory)
