#!/bin/bash
# File Generator - Creates random files to simulate real disk usage growth
# Used inside agent containers to generate test data

set -e

# Configuration via environment variables
MAX_SIZE_MB=${MAX_SIZE_MB:-500}
FILE_GEN_INTERVAL=${FILE_GEN_INTERVAL:-86400}  # Default: once per day (86400s)
DATA_DIR=${DATA_DIR:-/data}
MIN_FILE_KB=${MIN_FILE_KB:-1}       # Minimum file size in KB
MAX_FILE_KB=${MAX_FILE_KB:-1024}    # Maximum file size in KB (default: 1MB)
LARGE_FILE_PROB=${LARGE_FILE_PROB:-30}  # Probability (%) of generating a "large" file

echo "[FileGen] Starting file generator"
echo "[FileGen] Data dir: ${DATA_DIR}"
echo "[FileGen] Max size: ${MAX_SIZE_MB} MB"
echo "[FileGen] Interval: ${FILE_GEN_INTERVAL}s"
echo "[FileGen] File size range: ${MIN_FILE_KB}KB - ${MAX_FILE_KB}KB"
echo "[FileGen] Large file probability: ${LARGE_FILE_PROB}%"

# Ensure data directory exists
mkdir -p "$DATA_DIR"

# Weighted random file size generator
# Small files (MIN ~ midpoint): probability = 100 - LARGE_FILE_PROB
# Large files (midpoint ~ MAX): probability = LARGE_FILE_PROB
get_random_size_kb() {
    local mid
    mid=$(( (MIN_FILE_KB + MAX_FILE_KB) / 2 ))
    local roll
    roll=$(( RANDOM % 100 ))

    if [ "$roll" -lt "$LARGE_FILE_PROB" ]; then
        # Large file: midpoint ~ MAX
        local range
        range=$(( MAX_FILE_KB - mid + 1 ))
        echo $(( mid + RANDOM % range ))
    else
        # Small file: MIN ~ midpoint
        local range
        range=$(( mid - MIN_FILE_KB + 1 ))
        echo $(( MIN_FILE_KB + RANDOM % range ))
    fi
}

while true; do
    # Get current folder size in MB
    current_mb=$(du -sm "$DATA_DIR" 2>/dev/null | cut -f1)
    current_mb=${current_mb:-0}

    if [ "$current_mb" -lt "$MAX_SIZE_MB" ]; then
        file_size_kb=$(get_random_size_kb)

        # Create random file
        filename="file_$(date +%Y%m%d_%H%M%S)_${RANDOM}.bin"
        dd if=/dev/urandom of="${DATA_DIR}/${filename}" bs=1024 count="$file_size_kb" 2>/dev/null

        new_mb=$(du -sm "$DATA_DIR" 2>/dev/null | cut -f1)
        echo "[FileGen] $(date '+%Y-%m-%d %H:%M:%S') Created ${filename} (${file_size_kb}KB) | Total: ${new_mb}MB / ${MAX_SIZE_MB}MB"
    else
        echo "[FileGen] $(date '+%Y-%m-%d %H:%M:%S') Max size reached (${current_mb}MB / ${MAX_SIZE_MB}MB) - skipping"
    fi

    sleep "$FILE_GEN_INTERVAL"
done
