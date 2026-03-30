#!/bin/bash
cd backend
source venv/bin/activate
export DATABASE_URL="${DATABASE_URL}"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-your-secret-key-change-in-production}"
python main.py
