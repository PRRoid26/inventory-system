#!/bin/bash

# Database Backup Script
# This script creates automated backups of the PostgreSQL database

# Configuration
BACKUP_DIR="/var/backups/inventory"
DB_NAME="${DB_NAME:-inventory_db}"
DB_USER="${DB_USER:-postgres}"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/inventory_backup_$TIMESTAMP.sql"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "Database Backup Script"
echo "=========================================="
echo "Database: $DB_NAME"
echo "Backup location: $BACKUP_FILE"
echo ""

# Perform backup
if docker-compose exec -T db pg_dump -U $DB_USER $DB_NAME > "$BACKUP_FILE" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Backup completed successfully"
    
    # Compress backup
    gzip "$BACKUP_FILE"
    echo -e "${GREEN}✓${NC} Backup compressed: ${BACKUP_FILE}.gz"
    
    # Get file size
    SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
    echo "Backup size: $SIZE"
    
    # Delete old backups
    echo ""
    echo "Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
    find "$BACKUP_DIR" -name "inventory_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    
    REMAINING=$(ls -1 "$BACKUP_DIR"/inventory_backup_*.sql.gz 2>/dev/null | wc -l)
    echo "Remaining backups: $REMAINING"
    
else
    echo -e "${RED}✗${NC} Backup failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "Backup Complete"
echo "=========================================="

# If running in cron, send notification (optional)
if [ -n "$BACKUP_EMAIL" ]; then
    echo "Backup completed at $(date)" | mail -s "Inventory DB Backup Success" "$BACKUP_EMAIL"
fi
