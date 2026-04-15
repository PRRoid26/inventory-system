#!/bin/bash
cd backend
source venv/bin/activate
export DATABASE_URL="postgresql://postgres.ncsklhnqouhduaccqwjc:Fugro-inventory%40123@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-your-secret-key-change-in-production}"
python main.py
