# KTHO Backend - Full Backup

This backup contains the server side code discussed in the chat:
- FastAPI server with WebSockets
- Redis-backed asynchronous storage (RedisStorage)
- GameService, HeroAIService, RuleEngine, ActionExecutor
- Deck and event handling (treasure effects)
- Sample data (scenarios, clans, shop cards)

## Quick start
1. Start Redis on localhost (or set REDIS_URL env var)
2. Install requirements: pip install -r requirements.txt
3. Run: uvicorn main:app --reload
4. Open: http://127.0.0.1:8000/docs

## Redis keys
- `game:{game_id}:state` — JSON of full game state
