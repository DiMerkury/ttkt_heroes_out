import random
from common.logger import log_event

TREASURE_EFFECTS = {
    1: ['robbery','curse'],
    2: ['curse','heal'],
    3: ['heal','prisoner'],
    4: ['defeat']
}

async def apply_treasure_effect(state, ws, hall_id, treasure_token):
    hall = next((h for h in state['halls'] if h['id']==hall_id), None)
    if not hall:
        return
    value = int(treasure_token.split('_')[1])
    effect = random.choice(TREASURE_EFFECTS.get(value, ['robbery']))
    log_event(state, "treasure_effect_chosen", f"Effect {effect} for {treasure_token} in {hall_id}", effect=effect)
    if effect == 'robbery':
        resources = [t for t in hall.get('tokens',[]) if t in ('coin','book','frog','bone')]
        if resources:
            removed = random.choice(resources)
            hall['tokens'].remove(removed)
            log_event(state, "robbery", f"Removed resource {removed} from {hall_id}")
    elif effect == 'curse':
        for p in state.get('players',[]):
            if p.get('hand'):
                await ws.broadcast(state['id'], {"event":"choose_discard","player":p['id'],"hand":p['hand']})
                card = p['hand'].pop(0)
                p.setdefault('discard',[]).append(card)
                log_event(state, "curse_discard", f"Player {p['id']} discarded {card}")
            else:
                log_event(state, "curse_skip", f"Player {p['id']} had no cards to discard")
    elif effect == 'heal':
        for h in state.get('heroes',[]):
            if h['hall']==hall_id:
                h['active'] = True
                h['exhausted'] = False
        log_event(state, "heal", f"Heroes in {hall_id} healed/activated")
    elif effect == 'prisoner':
        if state.get('guild_deck'):
            card = state['guild_deck'].pop(0)
            new_hero = {"id":"pr_"+card['id'],"type":card['heroes'][0]['type'],"hall":"hall_prison","active":False,"hp":2,"exhausted":True}
            state.setdefault('heroes',[]).append(new_hero)
            log_event(state, "prisoner", f"New prisoner hero {new_hero['id']} placed in hall_prison")
    elif effect == 'defeat':
        state['status']='defeat'
        log_event(state, "defeat", "Treasure 4 stolen - players lose")
        await ws.broadcast(state['id'], {"event":"game_over","result":"defeat"})
    await ws.broadcast(state['id'], {"event":"treasure_effect","effect":effect,"hall":hall_id})
