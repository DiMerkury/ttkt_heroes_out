import random
from common.logger import log_event

class ActionExecutor:
    def __init__(self, state, ws):
        self.state = state
        self.ws = ws

    async def execute_move(self, hero, dest):
        hero['hall'] = dest
        log_event(self.state, "move", f"Hero {hero['id']} moved to {dest}")
        await self.ws.broadcast(self.state['id'], {"event":"move","hero":hero['id'],"to":dest})

    async def execute_attack(self, hero, hall_id):
        hall = next((h for h in self.state['halls'] if h['id']==hall_id), None)
        if not hall or not hall.get('monsters'):
            return
        target = random.choice(hall['monsters'])
        target['hp'] = target.get('hp',1)-1
        log_event(self.state, "attack", f"Hero {hero['id']} attacked {target['id']} in {hall_id}")
        if target['hp'] <=0:
            hall['monsters'] = [m for m in hall['monsters'] if m['id']!=target['id']]
            log_event(self.state, "monster_dead", f"Monster {target['id']} removed")
        await self.ws.broadcast(self.state['id'], {"event":"attack","hero":hero['id'],"target":target['id']})

    async def take_resource(self, hero, hall_id):
        hall = next((h for h in self.state['halls'] if h['id']==hall_id), None)
        if not hall:
            return
        resources = [t for t in hall.get('tokens',[]) if t in ('coin','book','frog','bone','trap')]
        if not resources:
            return
        r = random.choice(resources)
        hall['tokens'].remove(r)
        hero.setdefault('resources',[]).append(r)
        log_event(self.state, "take_resource", f"Hero {hero['id']} picked {r} in {hall_id}")
