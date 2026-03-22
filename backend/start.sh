#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo ""
echo "Your Mac IP: $(ipconfig getifaddr en0)"
echo "API docs:    http://$(ipconfig getifaddr en0):8000/docs"
echo ""
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
