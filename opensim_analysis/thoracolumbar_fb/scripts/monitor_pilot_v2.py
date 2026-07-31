"""
monitor_pilot_v2.py — 5-minute cycle monitor for B_suit0 Pilot v2.

Checks every 5 minutes:
    1. PID alive check
    2. Log tail (last 20 lines)
    3. IPOPT iteration extraction (iter, inf_pr, inf_du, objective)
    4. OOM detection (dmesg + available memory)
    5. Stagnation check (< 5 iter progress in 30 min)
    6. NaN/Inf objective detection
    7. inf_pr divergence detection (10x increase)

Fail-fast triggers (auto-kill):
    - 5 min elapsed, no IPOPT first iteration -> kill + diagnose
    - OOM detected -> kill + report
    - NaN/Inf objective -> kill + report
    - inf_pr 10x increase -> kill + report
    - 2 hour wall time -> kill + report

Non-kill triggers (report only, user decides):
    - 30 min stagnation (iter change < 5)

Usage:
    python monitor_pilot_v2.py              # run once (single report)
    python monitor_pilot_v2.py --loop       # run every 5 minutes indefinitely
    python monitor_pilot_v2.py --loop --cycles 6  # run 6 cycles (30 min)

2026-04-29
"""
from __future__ import annotations

import os
import re
import sys
import time
import signal
import subprocess
import argparse
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

OUT_DIR   = Path('/data/opensim_results/box_mocotrack_v1/B_suit0')
LOG_PATH  = OUT_DIR / 'pilot_v2.log'
PID_FILE  = OUT_DIR / 'pilot_v2.pid'
VERDICT   = OUT_DIR / 'pilot_verdict.txt'

MONITOR_INTERVAL_S = 300        # 5 minutes
FIRST_ITER_TIMEOUT_S = 1200     # kill if no IPOPT iter in 20 min from start
                                # Rationale: MocoTrack+contact CasADi codegen
                                # takes 10-15 min (vs MocoInverse ~1 min)
STAGNATION_WINDOW_S  = 1800     # 30 min stagnation check
STAGNATION_ITER_MIN  = 5        # minimum iter progress in stagnation window
WALL_TIME_LIMIT_S    = 7200     # 2 hour hard kill

# IPOPT output patterns
# Standard IPOPT iter line: "  47r  1.23e+02  4.56e-03  ..."
# or restored iter: " 47r 1.23e+02 ..."
ITER_RE = re.compile(
    r'^\s*(\d+)r?\s+([\d\.\-eE\+]+)\s+([\d\.\-eE\+]+)\s+([\d\.\-eE\+]+)',
    re.MULTILINE,
)
# NaN/Inf in objective field
NANINF_RE = re.compile(r'\b(nan|inf|NaN|Inf)\b')


# ── Helpers ───────────────────────────────────────────────────────────────────

def read_pid() -> int | None:
    try:
        return int(PID_FILE.read_text().strip())
    except Exception:
        return None


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def kill_process(pid: int, reason: str) -> None:
    print(f'[monitor] AUTO-KILL PID={pid}: {reason}', flush=True)
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(3)
        if pid_alive(pid):
            os.kill(pid, signal.SIGKILL)
        print(f'[monitor] PID={pid} killed.', flush=True)
    except Exception as e:
        print(f'[monitor] Kill failed: {e}', flush=True)


def read_log_tail(n: int = 30) -> str:
    """Read last n lines of pilot log."""
    try:
        lines = LOG_PATH.read_text(errors='replace').splitlines()
        return '\n'.join(lines[-n:])
    except Exception as e:
        return f'[log read error: {e}]'


def parse_ipopt_iters(log_text: str) -> list[tuple[int, float, float, float]]:
    """
    Return list of (iter, inf_pr, inf_du, objective) from log text.
    Each element is one IPOPT iteration line.
    """
    results = []
    for m in ITER_RE.finditer(log_text):
        try:
            iter_n  = int(m.group(1))
            inf_pr  = float(m.group(2))
            inf_du  = float(m.group(3))
            obj     = float(m.group(4))
            results.append((iter_n, inf_pr, inf_du, obj))
        except ValueError:
            continue
    return results


def check_oom() -> tuple[bool, str]:
    """Check dmesg for OOM events related to Python."""
    try:
        out = subprocess.run(
            ['dmesg', '--level=err,crit,emerg'],
            capture_output=True, text=True, timeout=5
        ).stdout
        oom_lines = [l for l in out.splitlines()
                     if re.search(r'oom|killed.*python|out of memory', l, re.I)]
        if oom_lines:
            return True, '\n'.join(oom_lines[-3:])
        return False, ''
    except Exception as e:
        return False, f'dmesg check failed: {e}'


def available_memory_mb() -> int:
    """Return available memory in MB from /proc/meminfo."""
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemAvailable:'):
                return int(line.split()[1]) // 1024
    except Exception:
        pass
    return -1


def get_launch_time() -> float | None:
    """Estimate launch time from first line of pilot_v2.log."""
    try:
        first_line = LOG_PATH.read_text(errors='replace').splitlines()[0]
        # format: [HH:MM:SS] ...
        m = re.search(r'\[(\d{2}:\d{2}:\d{2})\]', first_line)
        if m:
            today = time.strftime('%Y-%m-%d')
            t_str = f'{today} {m.group(1)}'
            return time.mktime(time.strptime(t_str, '%Y-%m-%d %H:%M:%S'))
    except Exception:
        pass
    return None


# ── Single monitor cycle ──────────────────────────────────────────────────────

def run_monitor_cycle(
    cycle_num: int,
    start_wall: float,
    prev_iters: list,
    prev_check_time: float,
) -> tuple[bool, list, float]:
    """
    Execute one monitor cycle.

    Returns:
        should_continue (bool): False if pilot is done or killed
        updated_iters (list): last parsed IPOPT iters
        check_time (float): time.time() of this check
    """
    now        = time.time()
    elapsed    = now - start_wall
    check_time = now

    sep = '=' * 60
    print(f'\n{sep}', flush=True)
    print(f'[Monitor cycle={cycle_num}  t=+{elapsed/60:.1f}min  {time.strftime("%H:%M:%S")}]',
          flush=True)
    print(sep, flush=True)

    # 0. Check if verdict already written (pilot already done)
    if VERDICT.exists():
        print('[monitor] pilot_verdict.txt found -> pilot completed', flush=True)
        print(VERDICT.read_text(), flush=True)
        return False, prev_iters, check_time

    # 1. PID alive check
    pid = read_pid()
    if pid is None:
        print('[monitor] PID file not found — pilot may not have launched', flush=True)
        log_tail = read_log_tail(30)
        print(f'[monitor] Log tail:\n{log_tail}', flush=True)
        return False, prev_iters, check_time

    alive = pid_alive(pid)
    print(f'[monitor] PID: {pid} — {"ALIVE" if alive else "DEAD"}', flush=True)

    if not alive:
        print('[monitor] Process dead — checking for verdict...', flush=True)
        log_tail = read_log_tail(40)
        print(f'[monitor] Log tail:\n{log_tail}', flush=True)
        return False, prev_iters, check_time

    # 2. Read full log for iteration parsing
    try:
        log_text = LOG_PATH.read_text(errors='replace')
    except Exception as e:
        log_text = ''
        print(f'[monitor] Cannot read log: {e}', flush=True)

    # 3. IPOPT iteration extraction
    all_iters = parse_ipopt_iters(log_text)
    last_iter = all_iters[-1] if all_iters else None

    if last_iter:
        iter_n, inf_pr, inf_du, obj = last_iter
        print(f'[monitor] IPOPT last iter: {iter_n}  inf_pr={inf_pr:.3e}  '
              f'inf_du={inf_du:.3e}  obj={obj:.4f}', flush=True)
    else:
        print('[monitor] IPOPT: no iterations recorded yet', flush=True)

    # 4. Memory + OOM check
    avail_mb = available_memory_mb()
    total_mb = None
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemTotal:'):
                total_mb = int(line.split()[1]) // 1024
                break
    except Exception:
        pass

    if total_mb and avail_mb >= 0:
        used_pct = 100 * (total_mb - avail_mb) / total_mb
        print(f'[monitor] Memory: {avail_mb:,} MB available '
              f'/ {total_mb:,} MB total  ({used_pct:.1f}% used)', flush=True)
    else:
        print(f'[monitor] Memory: {avail_mb:,} MB available', flush=True)

    oom_detected, oom_msg = check_oom()
    if oom_detected:
        print(f'[monitor] OOM DETECTED:\n{oom_msg}', flush=True)
        kill_process(pid, 'OOM detected in dmesg')
        return False, prev_iters, check_time

    # 5. Log tail (last 20 lines)
    log_lines = log_text.splitlines()
    tail_lines = log_lines[-20:] if len(log_lines) >= 20 else log_lines
    print(f'[monitor] Log tail (last 20 lines):')
    for line in tail_lines:
        print(f'  {line}', flush=True)

    # ── Fail-fast trigger checks ──────────────────────────────────────────────

    # Trigger A: 5 min no first IPOPT iter
    if elapsed > FIRST_ITER_TIMEOUT_S and not all_iters:
        print(f'[monitor] FAIL-FAST: {elapsed:.0f}s elapsed, no IPOPT first iter', flush=True)
        print('[monitor] Diagnosis: CasADi NLP initialization stall (same as v1?)', flush=True)
        print('[monitor] Check: num_parallel setting, model complexity, CasADi codegen', flush=True)
        kill_process(pid, 'No IPOPT first iter within 5 minutes')
        return False, prev_iters, check_time

    # Trigger B: NaN/Inf in objective
    if last_iter:
        _, _, _, obj = last_iter
        import math
        if math.isnan(obj) or math.isinf(obj):
            print(f'[monitor] FAIL-FAST: NaN/Inf objective at iter {last_iter[0]}', flush=True)
            kill_process(pid, 'NaN/Inf objective detected')
            return False, prev_iters, check_time

    # Trigger C: inf_pr divergence (10x increase)
    if len(all_iters) >= 2:
        first_pr  = all_iters[0][1]
        latest_pr = all_iters[-1][1]
        if latest_pr > 10 * first_pr and latest_pr > 1e3:
            print(f'[monitor] FAIL-FAST: inf_pr diverged '
                  f'{first_pr:.3e} -> {latest_pr:.3e} (10x)', flush=True)
            kill_process(pid, f'inf_pr diverged 10x: {first_pr:.3e} -> {latest_pr:.3e}')
            return False, prev_iters, check_time

    # Trigger D: 2 hour wall time
    if elapsed > WALL_TIME_LIMIT_S:
        print(f'[monitor] FAIL-FAST: wall time {elapsed:.0f}s > {WALL_TIME_LIMIT_S}s', flush=True)
        kill_process(pid, f'Wall time limit {WALL_TIME_LIMIT_S}s exceeded')
        return False, prev_iters, check_time

    # Non-kill: 30 min stagnation
    if prev_iters and all_iters:
        time_since_last_check = check_time - prev_check_time
        if time_since_last_check >= STAGNATION_WINDOW_S:
            prev_last_iter = prev_iters[-1][0]
            curr_last_iter = all_iters[-1][0]
            iter_delta = curr_last_iter - prev_last_iter
            if iter_delta < STAGNATION_ITER_MIN:
                print(f'[monitor] STAGNATION WARNING: only {iter_delta} iters '
                      f'in last {time_since_last_check/60:.0f} min '
                      f'(threshold: {STAGNATION_ITER_MIN})', flush=True)
                print('[monitor] Not auto-killing — user decision required', flush=True)

    print(f'[monitor] Status: RUNNING  elapsed={elapsed/60:.1f}min', flush=True)
    return True, all_iters, check_time


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description='B_suit0 Pilot v2 Monitor')
    parser.add_argument('--loop',   action='store_true',
                        help='Run monitor every 5 min indefinitely')
    parser.add_argument('--cycles', type=int, default=0,
                        help='Max cycles in --loop mode (0 = unlimited)')
    args = parser.parse_args()

    # Estimate start time from log first line; fallback to now
    launch_time = get_launch_time()
    if launch_time is None:
        launch_time = time.time()
        print(f'[monitor] Cannot read launch time from log — using now as t=0', flush=True)

    start_wall = launch_time
    cycle = 0
    prev_iters = []
    prev_check_time = start_wall

    if not args.loop:
        # Single cycle
        run_monitor_cycle(cycle, start_wall, prev_iters, prev_check_time)
        return

    # Loop mode
    while True:
        should_continue, prev_iters, prev_check_time = run_monitor_cycle(
            cycle, start_wall, prev_iters, prev_check_time,
        )
        cycle += 1

        if not should_continue:
            print('[monitor] Pilot completed or killed — monitor exiting.', flush=True)
            break

        if args.cycles > 0 and cycle >= args.cycles:
            print(f'[monitor] Max cycles ({args.cycles}) reached — monitor exiting.', flush=True)
            break

        print(f'[monitor] Next check in {MONITOR_INTERVAL_S//60} min '
              f'({time.strftime("%H:%M:%S", time.localtime(time.time() + MONITOR_INTERVAL_S))})',
              flush=True)
        time.sleep(MONITOR_INTERVAL_S)


if __name__ == '__main__':
    main()
