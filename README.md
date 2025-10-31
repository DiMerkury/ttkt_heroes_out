# TTKT Heroes Out — backend (starter)

## Quick start (local)
1. create venv, install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. start redis (docker):
   docker run -p 6379:6379 -d redis:7

3. run app:
   uvicorn app.main:app --reload

4. API docs:
   http://127.0.0.1:8000/docs