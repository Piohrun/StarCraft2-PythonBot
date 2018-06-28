import sc2

from sc2 import run_game,maps,Race,Difficulty
from sc2.player import Bot,Computer
from sc2.constants import NEXUS,PROBE,PYLON,ASSIMILATOR,GATEWAY,CYBERNETICSCORE
from sc2.constants import ZEALOT,STALKER,EFFECT_CHRONOBOOST,AbilityId,BuffId
from sc2.constants import STARGATE,VOIDRAY

class Gregbot(sc2.BotAI):
    async def on_step(self,iteration):

        params = {}
        if self.state.game_loop < 10000:
            params['max_nx'] = 5
            params['attack_grp'] = 7
            params['geysers'] = 2
            params['void'] = False
        elif 12000 > self.state.game_loop > 8000:
            params['max_nx'] = 5
            params['attack_grp'] = 12
            params['geysers'] = 4
            params['void'] = True
        else:
            params['max_nx'] = 6
            params['attack_grp'] = 16
            params['geysers'] = 6
            params['void'] = True

        await self.distribute_workers()
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators(params)
        await self.expand(params)
        await self.build_army_factory(params)
        await self.build_army(params)
        await self.command_army(params)
        await self.try_chronoboosting()

        if self.state.game_loop % 100 ==0:
            print(self.state.game_loop)

    async def build_workers(self):
        for base in self.units(NEXUS).ready.noqueue:
            if self.can_afford(PROBE) and self.units(PROBE).amount < (self.units(NEXUS).amount * 14):
                await self.do(base.train(PROBE))

    async def build_pylons(self):
        if self.supply_left < 5 and not self.already_pending(PYLON):
            nexuses = self.units(NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON):
                    await self.build(PYLON,near=nexuses.first)
    
    async def expand(self,params):
        if self.units(NEXUS).amount < params['max_nx'] and self.can_afford(NEXUS):
            await self.expand_now()
            
    async def build_assimilators(self,params):
        if self.units(ASSIMILATOR).amount < params['geysers']:
            for nexus in self.units(NEXUS).ready:
                vaspenes = self.state.vespene_geyser.closer_than(15.0, nexus)
                for vaspene in vaspenes:
                    if not self.can_afford(ASSIMILATOR):
                        break
                    worker = self.select_build_worker(vaspene.position)
                    if worker is None:
                        break
                    if not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists:
                        await self.do(worker.build(ASSIMILATOR, vaspene))

    async def build_army_factory(self,params):
        if self.units(PYLON).ready.exists:
            pylon = self.units(PYLON).ready.random
            if self.units(GATEWAY).amount < (self.units(NEXUS).amount * 1.5) and self.can_afford(GATEWAY):
                await self.build(GATEWAY,near=pylon)
            if self.units(CYBERNETICSCORE).amount ==0 and not self.already_pending(CYBERNETICSCORE) and self.can_afford(CYBERNETICSCORE):
                await self.build(CYBERNETICSCORE,near=pylon)
            if params['void']:
                if self.units(STARGATE).amount < (self.units(NEXUS).amount * 0.4) and self.can_afford(STARGATE):
                    await self.build(STARGATE,near=pylon)


    async def build_army(self,params):
        for gateway in self.units(GATEWAY).ready.noqueue:
            if not self.units(CYBERNETICSCORE).ready.exists:
                if self.can_afford(ZEALOT):
                    await self.do(gateway.train(ZEALOT))
            else:
                if self.units(ZEALOT).amount < (self.units(STALKER).amount *2):
                    if self.can_afford(ZEALOT):
                        await self.do(gateway.train(ZEALOT))
                else:
                    if self.can_afford(STALKER):
                        await self.do(gateway.train(STALKER))

        if params['void']:
            for star in self.units(STARGATE).ready.noqueue:
                if self.can_afford(VOIDRAY):
                    await self.do(star.train(VOIDRAY))

    async def command_army(self,params):           
        if (self.units(ZEALOT).idle.amount + self.units(STALKER).idle.amount )> params['attack_grp']:
            for u in self.units(ZEALOT).idle + self.units(STALKER).idle + self.units(VOIDRAY).idle:
                if len(self.known_enemy_units) == 0:
                    await self.do(u.attack(self.enemy_start_locations[0]))
                else:
                    await self.do(u.attack(self.known_enemy_units.prefer_close_to(u.position)[0].position))
        elif any([len(self.known_enemy_units.closer_than(15.0,nx)) > 0 for nx in self.units(NEXUS)]):
            for u in self.units(ZEALOT).idle + self.units(STALKER).idle + self.units(VOIDRAY).idle:
                await self.do(u.attack(self.known_enemy_units.prefer_close_to(u.position)[0].position))

    async def try_chronoboosting(self):
        for nx in self.units(NEXUS).ready:
            if nx.energy >=50:
                if self.units(GATEWAY).ready.amount ==0:
                    if not nx.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                        await self.do(nx(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nx))
                else:
                    for gt in self.units(GATEWAY).ready:
                        if len(gt.orders)>0 and not gt.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                            await self.do(nx(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, gt))




run_game(maps.get('AbyssalReefLE'),[Bot(Race.Protoss,Gregbot()),Computer(Race.Protoss,Difficulty.Hard)],realtime=False)