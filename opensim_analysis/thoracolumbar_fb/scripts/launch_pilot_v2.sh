#!/bin/bash
# launch_pilot_v2.sh — nohup + setsid + disown triple-anchor background launch
# Usage: bash launch_pilot_v2.sh
# 2026-04-29

set -euo pipefail

PYTHON=/home/sysop/miniconda3/envs/opensim/bin/python
SCRIPT=/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/run_box_mocotrack_pilot_v2.py
OUT_DIR=/data/opensim_results/box_mocotrack_v1/B_suit0
LOG=$OUT_DIR/pilot_v2.log
PID_FILE=$OUT_DIR/pilot_v2.pid

# Ensure output directory exists
mkdir -p "$OUT_DIR"

# Archive previous failed log (v1) if exists and no solution yet
if [ -f "$OUT_DIR/pilot_run.log" ] && [ ! -f "$OUT_DIR/pilot_verdict.txt" ]; then
    mv "$OUT_DIR/pilot_run.log" "$OUT_DIR/pilot_v1_failed.log.bak" 2>/dev/null || true
    echo "[launch_pilot_v2] Archived v1 failed log -> pilot_v1_failed.log.bak"
fi

# Kill any stale Python pilot processes (from v1)
if [ -f "$OUT_DIR/pilot_v1.pid" ]; then
    OLD_PID=$(cat "$OUT_DIR/pilot_v1.pid" 2>/dev/null || true)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[launch_pilot_v2] Killing stale v1 PID=$OLD_PID"
        kill "$OLD_PID" 2>/dev/null || true
    fi
fi

echo "[launch_pilot_v2] Launch start: $(date)"
echo "[launch_pilot_v2] Script: $SCRIPT"
echo "[launch_pilot_v2] Log: $LOG"

# Triple-anchor background: nohup + setsid + disown
# - nohup:  ignore SIGHUP (terminal close)
# - setsid: create new session (no controlling terminal)
# - disown: remove from shell job table (bash-specific)
# - </dev/null: detach stdin completely
nohup setsid \
    env OMP_NUM_THREADS=28 OPENBLAS_NUM_THREADS=28 MKL_NUM_THREADS=28 \
        OPENSIM_USE_VISUALIZER=0 \
    "$PYTHON" -u "$SCRIPT" \
    >> "$LOG" 2>&1 \
    < /dev/null &

PID=$!
echo $PID > "$PID_FILE"
disown $PID

echo "[launch_pilot_v2] Pilot launched PID=$PID"
echo "[launch_pilot_v2] PID file: $PID_FILE"
echo "[launch_pilot_v2] Start time: $(date)"
echo "[launch_pilot_v2] Monitor: python /data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/monitor_pilot_v2.py"
echo ""
echo "  To tail log in real-time:"
echo "    tail -f $LOG"
echo "  To check PID:"
echo "    kill -0 $PID && echo ALIVE || echo DEAD"
