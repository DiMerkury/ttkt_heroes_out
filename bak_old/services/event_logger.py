import time
import uuid

class EventLogger:
    def __init__(self, store, ws_manager=None):
        self.store = store
        self.ws_manager = ws_manager

    async def add_event(self, game_state, event_type, actor=None, target=None,
                        hall=None, payload=None, message=None, broadcast=True):
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "type": event_type,
            "actor": actor,
            "target": target,
            "hall": hall,
            "payload": payload or {},
            "message": message or "",
        }

        game_state.setdefault("log", []).append(event)
        await self.store.set_json(f"game:{game_state['id']}:state", game_state)

        if broadcast and self.ws_manager:
            await self.ws_manager.broadcast(game_state["id"], {"event": "log_update", "data": event})

        return event
