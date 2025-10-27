import random
from common.logger import log_event

async def check_game_end(state, ws):
    if state.get('status')=='defeat':
        await ws.broadcast(state['id'], {"event":"game_over","result":"defeat"})
        log_event(state,'game_end','Defeat by treasure')
        return state
    if not state.get('guild_deck'):
        wave = state.get('wave',1)
        if wave==1:
            state['wave']=2
            disc = state.get('heroes_discard',[])
            random.shuffle(disc)
            state['guild_deck']=disc
            state['heroes_discard']=[]
            await ws.broadcast(state['id'], {"event":"wave_next","wave":2})
            log_event(state,'wave','Wave 2 started')
        else:
            state['status']='victory'
            await ws.broadcast(state['id'], {"event":"game_over","result":"victory"})
            log_event(state,'game_end','Victory - survived two waves')
    return state
