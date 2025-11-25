#!/bin/bash
# Cron wrapper script for monthly updates
# This ensures proper environment and logging

# Set working directory
cd /Users/savantlab/mental-rotation-research

# Activate virtual environment
source venv/bin/activate

# Create logs directory if it doesn't exist
mkdir -p logs

# Run update script with logging
LOG_FILE="logs/update_$(date +%Y%m%d_%H%M%S).log"

echo "========================================" >> "$LOG_FILE"
echo "Update started: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

python scripts/update_current_year.py >> "$LOG_FILE" 2>&1

echo "========================================" >> "$LOG_FILE"
echo "Update completed: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Keep only last 12 months of logs
find logs/ -name "update_*.log" -mtime +365 -delete
