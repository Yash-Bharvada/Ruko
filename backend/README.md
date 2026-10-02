# Ruko Backend

Backend API for Ruko — investor-protection assistant for detecting suspicious investment tips before money moves.

## Setup & Running Locally

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate

   pip install -r requirements.txt
   ```

2. Copy environment file:
   ```bash
   cp .env.example .env
   ```

3. Run the development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

4. Check liveness:
   ```bash
   curl http://localhost:8000/health
   ```

## Running Tests

```bash
pytest tests/ -q
```
