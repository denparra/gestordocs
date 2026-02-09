#!/bin/bash

# Dual startup: FastAPI (background) + Streamlit (foreground)
# Both share the same src/ modules without interference.

# 1. Start API in background
echo "Starting FastAPI on port 8000..."
uvicorn api:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# 2. Wait for API to be ready
sleep 2
echo "API started (PID: $API_PID)"

# 3. Start Streamlit in foreground (Railway monitors this process)
echo "Starting Streamlit on port ${PORT:-8501}..."
streamlit run app.py --server.port ${PORT:-8501} --server.address 0.0.0.0

# If Streamlit exits, stop the API process
kill $API_PID 2>/dev/null
