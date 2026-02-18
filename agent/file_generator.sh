#!/bin/bash
# File Generator - Creates random files to simulate real disk usage growth
# Used inside agent containers to generate test data

set -e

# Configuration via environment variables
MAX_SIZE_MB=${MAX_SIZE_MB:-500}
FILE_GEN_INTERVAL=${FILE_GEN_INTERVAL:-86400}  # Default: once per day (86400s)
DATA_DIR=${DATA_DIR:-/data}
MIN_FILE_KB=${MIN_FILE_KB:-1}
MAX_FILE_KB=${MAX_FILE_KB:-20480}  # 20MB

echo "[FileGen] Starting file generator"
echo "[FileGen] Data dir: ${DATA_DIR}"
echo "[FileGen] Max size: ${MAX_SIZE_MB} MB"
echo "[FileGen] Interval: ${FILE_GEN_INTERVAL}s"
echo "[FileGen] File size range: ${MIN_FILE_KB}KB - ${MAX_FILE_KB}KB"

# Ensure data directory exists
mkdir -p "$DATA_DIR"

while true; do
    # Get current folder size in MB
    current_mb=$(du -sm "$DATA_DIR" 2>/dev/null | cut -f1)
    current_mb=${current_mb:-0}

    if [ "$current_mb" -lt "$MAX_SIZE_MB" ]; then
        # Generate random file size between MIN and MAX KB
        range=$((MAX_FILE_KB - MIN_FILE_KB + 1))
        file_size_kb=$((MIN_FILE_KB + RANDOM % range))

        # Create random file
        filename="file_$(date +%Y%m%d_%H%M%S)_${RANDOM}.bin"
        dd if=/dev/urandom of="${DATA_DIR}/${filename}" bs=1024 count=$file_size_kb 2>/dev/null

        new_mb=$(du -sm "$DATA_DIR" 2>/dev/null | cut -f1)
        echo "[FileGen] $(date '+%Y-%m-%d %H:%M:%S') Created ${filename} (${file_size_kb}KB) | Total: ${new_mb}MB / ${MAX_SIZE_MB}MB"
    else
        echo "[FileGen] $(date '+%Y-%m-%d %H:%M:%S') Max size reached (${current_mb}MB / ${MAX_SIZE_MB}MB) - skipping"
    fi

    sleep "$FILE_GEN_INTERVAL"
done
