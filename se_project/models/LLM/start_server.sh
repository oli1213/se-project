#!/bin/bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
