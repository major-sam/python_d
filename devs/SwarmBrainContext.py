from __future__ import annotations
from abc import ABC, abstractmethod
import devs.ContextTools as ct
import devs.SwarmBrainConst as const


class Context(ABC):
    _state = None

    def __init__(self, state: State) -> None:
        self.transition_to(state)

    def transition_to(self, state: State):
        self._state = state
        self._state.context = self

    def get_mode(self, me, memory):
        return self._state.get_mode(me, memory)

    def do_target_operation(self, me, memory):
        self._state.do_target_operation(me, memory)

    def make_decision(self, me, memory):
        self._state.make_decision(me, memory)

    def do_i_want_change_decision(self, me, memory):
        self._state.do_i_want_change_decision(me, memory)


class State(ABC):

    def __init__(self):
        self._context = None

    @property
    def context(self) -> Context:
        return self._context

    @context.setter
    def context(self, context: Context) -> None:
        self._context = context

    @abstractmethod
    def do_target_operation(self, me, memory):
        pass

    @abstractmethod
    def get_mode(self, me, prev_data):
        pass

    @abstractmethod
    def make_decision(self, me, memory):
        pass

    @abstractmethod
    def do_i_want_change_decision(self, me, memory):
        pass


class OneOnOne(State):  # todo change to atr or module
    def get_best_target(self, me, prev_data):
        pass

    def get_mode(self, me, prev_data):
        pass


class OneOnMany(State):  # todo change to attr or module
    def get_mode(self, me, prev_data):
        pass

    def get_team_position(self, me, target, drones_count, memory):
        pass

    def get_best_target(self, me, prev_data):
        pass


class AdvantageState(State):

    def make_decision(self, me, memory):
        DestroyEnemies().make_decision(me, memory)

    def do_i_want_change_decision(self, me, memory):
        DestroyEnemies().do_i_want_change_decision(me, memory)

    def do_target_operation(self, me, memory):
        DestroyEnemies().do_target_operation(me, memory)

    def get_mode(self, me, memory):
        my_alive_drones = [drone for drone in me.scene.teams[me.team] if drone.is_alive]
        enemy_alive_drones = [drone for drone in memory[const.MEM_TEAM_TO_DESTROY][const.MEM_DRONES] if drone.is_alive]
        if not any(drone.is_alive for drone in me.scene.drones if drone.team is not me.team):
            ct.set_mode(self.context, EveryBodyDead, memory, me.id, const.MOD_COLLECT)
        elif me.health < 90 - 100 / len(enemy_alive_drones):
            ct.set_mode(self.context, NeedHealth, memory, me.id, const.MOD_HEALS)
        elif len(my_alive_drones) < len(enemy_alive_drones):
            ct.set_mode(self.context, LoosingState, memory, me.id, const.MOD_LOOSING)
        elif len(my_alive_drones) > len(enemy_alive_drones):
            ct.set_mode(self.context, None, memory, me.id, const.MOD_WINNING)
        else:
            ct.set_mode(self.context, DestroyEnemies, memory, me.id, const.MOD_DESTROY)


class NeedHealth(State):
    def do_target_operation(self, me, memory):
        if me.health == 100:
            ct.set_mode(self.context, DestroyEnemies, memory, me.id, const.MOD_DESTROY)

    def make_decision(self, me, memory):
        me.move_at(me.mothership)

    def do_i_want_change_decision(self, me, memory):
        me.move_at(me.mothership)

    def get_best_target(self, me, memory):
        if me.health == 100:
            ct.set_mode(self.context, DestroyEnemies, memory, me.id, const.MOD_DESTROY)

    def get_mode(self, me, memory):
        if me.health == 100:
            ct.set_mode(self.context, DestroyEnemies, memory, me.id, const.MOD_DESTROY)


class NeedBodyBlock(State):

    def do_target_operation(self, me, memory):
        pass

    def get_mode(self, me, prev_data):
        pass

    def make_decision(self, me, memory):
        pass

    def do_i_want_change_decision(self, me, memory):
        pass


class LoosingState(State):

    def do_target_operation(self, me, memory):
        DestroyEnemies().do_target_operation(me, memory)

    def get_mode(self, me, memory):
        DestroyEnemies().get_mode(me, memory)

    def make_decision(self, me, memory):
        DestroyEnemies().make_decision(me, memory)

    def do_i_want_change_decision(self, me, memory):
        DestroyEnemies().do_i_want_change_decision(me, memory)


class EveryBodyDead(State):
    def do_target_operation(self, me, memory):
        pass

    def get_mode(self, me, prev_data):
        pass

    def make_decision(self, me, memory):
        pass

    def do_i_want_change_decision(self, me, memory):
        pass


class DestroyEnemies(State):

    def make_decision(self, me, memory):
        if me.my_brain.have_swarm_decision:
            print(me.id, 'confirm prev decision')
            return
        who_is_alive = ct.get_team_to_destroy(me, memory)
        if not who_is_alive:
            self.context.transition_to(EveryBodyDead())
            return
        ct.audit_enemies(memory, me)
        ct.make_audit_results(memory, me)
        if memory[const.MEM_SWARM_TARGET]:
            ct.get_team_position(me, memory)
            me.my_brain.have_swarm_decision = True
        else:
            pass  # todo add no swarm target decision

    def do_i_want_change_decision(self, me, memory):
        change_conditions = []
        if not memory[const.MEM_SWARM_TARGET]:
            me.my_brain.have_swarm_decision = False
            return
        swarm_target = memory[const.MEM_SWARM_TARGET]
        enemy = swarm_target[const.MEM_ENEMY]
        current_enemy_target = swarm_target[const.MEM_ENEMY].state.target_point
        enemy_is_moving = current_enemy_target is not None
        enemy_in_range = ct.get_distance_between(me.coord, enemy.coord) < const.MAX_ATTACK_RADIUS
        enemy_team = [drone for drone in memory[const.MEM_TEAM_TO_DESTROY][const.MEM_DRONES] if drone.is_alive]

        if not enemy.is_alive:
            ct.n_quick_switch(swarm_target, me, memory, change_conditions)

        if enemy.health < 50 and enemy.is_alive:
            return
        target = swarm_target[const.MEM_SHOOT_TARGET]  # if swarm_target[const.MEM_FIRE_ON_POINT] else enemy

        position_is_ok = all([ct.check_shoot_trace(drone, enemy_team
                                                   , target) for drone in me.my_team])
        if position_is_ok and enemy_in_range:  # todo fix it
            if enemy_is_moving:
                swarm_target[const.MEM_ENEMY_TARGET] = enemy.state.target_point
            else:
                swarm_target[const.MEM_ENEMY_TARGET] = enemy.coord
            return
        elif position_is_ok and swarm_target[const.MEM_AMBUSH_FLAG]:
            pass
        else:
            change_conditions.append(True)
        if enemy_is_moving:
            is_target_changed = not ct.match_points(current_enemy_target,
                                                    swarm_target[const.MEM_ENEMY_TARGET], 10)
            is_target_mothership = enemy.mothership.near(current_enemy_target)
            enemy_distance_is_ok = all([
                is_target_mothership and ct.get_distance_between(
                    enemy.coord, enemy.mothership.coord) < ct.get_distance_between(me.coord,
                                                                                   enemy.mothership.coord),
            ])
            change_conditions.append(is_target_mothership and not enemy_in_range)
            change_conditions.append(all([is_target_changed, not enemy_distance_is_ok]))
        else:
            attack_position_to_far = ct.get_distance_between(me.coord,
                                                             memory[me.id][const.MEM_ATTACK_POSITION]
                                                             ) < ct.get_distance_between(me.coord, enemy.coord)
            if not swarm_target[const.MEM_AMBUSH_FLAG]:
                change_conditions.append(attack_position_to_far)
            enemy_on_mothership = enemy.near(enemy.mothership.coord) if hasattr(enemy, 'mothership') else False
            change_conditions.append(enemy_on_mothership)

        if any(change_conditions):
            me.my_brain.have_swarm_decision = False
            print(me, 'cancel prev decision')

    def get_mode(self, me, memory):
        my_alive_drones = [drone for drone in me.scene.teams[me.team] if drone.is_alive]
        enemy_alive_drones = [drone for drone in memory[const.MEM_TEAM_TO_DESTROY][const.MEM_DRONES] if drone.is_alive]
        if not any(drone.is_alive for drone in me.scene.drones if drone.__class__ is not me.team):
            ct.set_mode(self.context, EveryBodyDead, memory, me.id, const.MOD_COLLECT)
        elif me.health < 110 - 100 / len(enemy_alive_drones):
            ct.set_mode(self.context, NeedHealth, memory, me.id, const.MOD_HEALS)
        elif len(my_alive_drones) < len(enemy_alive_drones):
            ct.set_mode(self.context, LoosingState, memory, me.id, const.MOD_LOOSING)
        elif len(my_alive_drones) > len(enemy_alive_drones):
            ct.set_mode(self.context, AdvantageState, memory, me.id, const.MOD_WINNING)
        else:
            ct.set_mode(self.context, None, memory, me.id, const.MOD_DESTROY)

    def do_target_operation(self, me, memory):
        my_position = memory[me.id][const.MEM_ATTACK_POSITION]
        me_shoot_flag = memory[me.id][const.MEM_SHOOT_FLAG]

        if me_shoot_flag:
            ct.shoot_the_target(memory, me)
        if ct.match_points(me.coord, my_position, 2):

            swarm_target = memory[const.MEM_SWARM_TARGET]
            enemy_target = swarm_target[const.MEM_ENEMY_TARGET]
            enemy = swarm_target[const.MEM_ENEMY]
            shoot_point = swarm_target[const.MEM_SHOOT_TARGET]
            enemy_reach_target = enemy.near(enemy_target)
            enemy_in_range = ct.get_distance_between(me.coord, enemy.coord) <= const.MAX_ATTACK_RADIUS
            distance_to_enemy_target = ct.get_distance_between(me.coord, enemy_target)
            my_shoot_trace, k, b = ct.get_line_points(me=me, angle=me.direction, distance=distance_to_enemy_target)
            enemy_straight_ahead = any([enemy.near(point) for point in my_shoot_trace])
            enemy_near_target = ct.get_distance_between(enemy, enemy_target) < 50
            #  shoot_point = ct.get_pre_fire_point(me, enemy, enemy_target)
            # if shoot_point: # todo possibly need fixes
            #     me.turn_to(shoot_point)
            #     memory[me.id][const.MEM_SHOOT_FLAG] = True
            #     memory[const.MEM_SHOOT_TARGET] = shoot_point
            #     return
            if enemy_in_range:
                me.turn_to(enemy)
                if enemy_reach_target:
                    print('turn to enemy', enemy.coord)
                    memory[me.id][const.MEM_SHOOT_FLAG] = True
                    memory[const.MEM_SHOOT_TARGET] = enemy.coord
                elif enemy_near_target:
                    memory[me.id][const.MEM_SHOOT_FLAG] = True
                elif enemy_straight_ahead:
                    me.gun.shot(enemy)
                    print('shot to enemy', enemy)
                else:
                    print('turn to enemy target', enemy_target)
                    memory[me.id][const.MEM_SHOOT_FLAG] = True
                    memory[const.MEM_SHOOT_TARGET] = enemy
            elif shoot_point:
                me.turn_to(shoot_point)
                print('turn to enemy predicted shoot point', shoot_point)
            else:
                me.turn_to(enemy)
                print('track enemy', enemy, 'outside attack range')

        else:
            me.move_at(my_position)
