MEDIFUSION - Connected package
================================

This package contains a backend (FastAPI) and a static frontend (doctor dashboard).
Files:
 - backend/   : FastAPI application (run on port 8000)
 - frontend/  : Static HTML/JS files (doctor dashboard) — served on port 3000
 - run.sh     : Convenience script to create venv, install deps, and start both servers

Quick start (Linux/macOS):
1. Open terminal and run:
   ./run.sh
2. Wait a little while (pip install may take some minutes).
3. Open your browser:
   http://localhost:3000/doctor_dashboard.html

Notes:
 - Backend already has CORS enabled (allow all origins).
 - Frontend API base is set to http://localhost:8000 in frontend/api.js
 - To stop servers: pkill -f uvicorn; pkill -f http.server

If you want the frontend served from the backend (single origin), I can modify FastAPI to serve static files and update instructions — tell me and I will patch it.
