#!/bin/bash
# Add designation column to work_logs table

export DATABASE_URL="${DATABASE_URL:-postgresql://admin:admin123@localhost:5432/fugro}"

psql "$DATABASE_URL" -c "ALTER TABLE work_logs ADD COLUMN IF NOT EXISTS designation VARCHAR(100);"

echo "✅ Migration complete - designation column added"
