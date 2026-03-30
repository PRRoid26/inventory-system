#!/bin/bash
# Make job_name and check_out_date nullable in work_logs table

export DATABASE_URL="${DATABASE_URL:-postgresql://admin:admin123@localhost:5432/fugro}"

psql "$DATABASE_URL" << EOF
ALTER TABLE work_logs ALTER COLUMN job_name DROP NOT NULL;
ALTER TABLE work_logs ALTER COLUMN check_out_date DROP NOT NULL;
EOF

echo "✅ Migration complete - job_name and check_out_date are now nullable"
