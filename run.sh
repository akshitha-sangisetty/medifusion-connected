#!/usr/bin/env bash
set -e
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Starting MEDIFUSION - backend on :8000 and frontend static server on :3000"

# Create venv
cd "$BASE_DIR/backend"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

# Install requirements
if [ -f requirements.txt ]; then
  pip install --upgrade pip
  pip install -r requirements.txt
fi

# Start backend
echo "Starting backend (uvicorn)..."
# Run uvicorn in background
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &

# Start frontend static server
cd "$BASE_DIR/frontend"
echo "Serving frontend at http://localhost:3000"
python3 -m http.server 3000 > ../frontend.log 2>&1 &

echo "Both servers started. Open http://localhost:3000/doctor_dashboard.html"
echo "To stop them: pkill -f uvicorn; pkill -f http.server"
