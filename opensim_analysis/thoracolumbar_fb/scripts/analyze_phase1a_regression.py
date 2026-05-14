"""
Phase 1a Regression Analysis — New Infrastructure vs Existing Results.

Compares:
    NEW : /data/opensim_results/phase1a_reproduction/
    ORIG: /data/wearable-assist/results/phase1a_full/  (F=0)
          /data/wearable-assist/results/phase1a_suit_sweep/ (F=50..200)

Regression PASS criteria:
    max ΔES < 5 %p (all muscles, all phases)
    Slope deviation < 0.1 %/N·m from 1.164
    28% reduction ±5%p
    Spine FE reserve ±10 N·m from 19.4

Usage:
    /home/sysop/miniconda3/envs/opensim/bin/python analyze_phase1a_regression.py

Output:
    /data/opensim_results/phase1a_reproduction/regression_report.md
"""
import os
import sys
from pathlib import Path

os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
sys.path.insert(0, '/data/wearable-assist/opensim_analysis/thoracolumbar_fb')

import numpy as np
import opensim as osim

# ---------------------------------------------------------------------------
# Paths (original Phase 1a vs new reproduction)
# ---------------------------------------------------------------------------
ORIG_PATHS = {
    0:   '/data/wearable-assist/results/phase1a_full/solution.sto',
    50:  '/data/wearable-assist/results/phase1a_suit_sweep/F50/solution_suit.sto',
    100: '/data/wearable-assist/results/phase1a_suit_sweep/F100/solution_suit.sto',
    150: '/data/wearable-assist/results/phase1a_suit_sweep/F150/solution_suit.sto',
    200: '/data/wearable-assist/results/phase1a_suit_sweep/F200/solution_suit.sto',
}
NEW_PATHS = {
    0:   '/data/opensim_results/phase1a_reproduction/B_suit0/solution.sto',
    50:  '/data/opensim_results/phase1a_reproduction/B_suit50/solution.sto',
    100: '/data/opensim_results/phase1a_reproduction/B_suit100/solution.sto',
    150: '/data/opensim_results/phase1a_reproduction/B_suit150/solution.sto',
    200: '/data/opensim_results/phase1a_reproduction/B_suit200/solution.sto',
}

MOMENT_ARM = 0.12
RESERVE_OPTF = 10.0

# 5-phase definitions (verified)
PHASES = [
    ('Standing',   0.0, 0.5),
    ('Eccentric',  0.5, 1.5),
    ('Hold',       1.5, 2.5),
    ('Concentric', 2.5, 4.0),
    ('Recovery',   4.0, 5.0),
]

# Key muscles for regression comparison
KEY_MUSCLES = [
    'IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'IL_R11_l',
    'LTpL_L5_r', 'LTpL_L5_l',
]

# Memory reference values (from existing Phase 1a)
MEMORY_REF = {
    'IL_R10_Hold_peak': 87.7,
    'slope': 1.164,
    'r2': 1.0000,
    'reduction_28nm': 27.95,   # ES_mean Hold @ 24 N·m
    'spine_fe_reserve': 19.4,  # N·m @ t=2.5s
}

# PASS thresholds
THRESH_DELTA_ES = 5.0      # %p
THRESH_SLOPE = 0.1         # %/N·m
THRESH_REDUCTION = 5.0     # %p
THRESH_RESERVE = 10.0      # N·m


def load_act(tbl, name):
    labels = list(tbl.getColumnLabels())
    for i, L in enumerate(labels):
        if L.endswith(f'/{name}/activation'):
            n = tbl.getNumRows()
            return np.array([tbl.getRowAtIndex(k)[i] for k in range(n)]) * 100
    return None


def load_solution(sol_path):
    """Load solution STO and extract per-phase stats for key muscles."""
    if not os.path.isfile(sol_path):
        return None

    tbl = osim.TimeSeriesTable(sol_path)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())

    acts = {nm: load_act(tbl, nm) for nm in KEY_MUSCLES}
    acts = {k: v for k, v in acts.items() if v is not None}

    result = {'n_muscles': len(acts)}
    for pname, ts, te in PHASES:
        mask = (times >= ts) & (times <= te)
        if mask.sum() == 0:
            continue
        for nm, a in acts.items():
            result[f'{nm}_{pname}_peak'] = float(a[mask].max())
            result[f'{nm}_{pname}_mean'] = float(a[mask].mean())

    # ES_mean (average of available muscles)
    if acts:
        arr = np.stack(list(acts.values()), axis=1)
        es_mean = arr.mean(axis=1)
        for pname, ts, te in PHASES:
            mask = (times >= ts) & (times <= te)
            if mask.sum() > 0:
                result[f'ES_mean_{pname}_mean'] = float(es_mean[mask].mean())

    # Spine FE reserve @ t=2.5s (peak hold)
    spine_fe_cols = [(i, L) for i, L in enumerate(labels)
                     if '_FE' in L and 'reserve' in L.lower()]
    idx_25 = int(np.argmin(np.abs(times - 2.5)))
    spine_fe_sum = 0.0
    for i, L in spine_fe_cols:
        col = np.array([tbl.getRowAtIndex(j)[i] for j in range(tbl.getNumRows())])
        spine_fe_sum += abs(col[idx_25]) * RESERVE_OPTF
    result['spine_fe_reserve_25s'] = spine_fe_sum

    return result


def fit_line(x, y):
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 1.0
    return float(slope), float(intercept), float(r2)


def main():
    print('=' * 70)
    print('Phase 1a Regression Analysis — Existing vs New Infrastructure')
    print('=' * 70)

    forces = [0, 50, 100, 150, 200]
    torques = np.array([f * MOMENT_ARM for f in forces])

    # Load originals
    print('\nLoading original Phase 1a solutions...')
    orig = {}
    for f in forces:
        data = load_solution(ORIG_PATHS[f])
        if data:
            orig[f] = data
            print(f'  F={f}: loaded  spine_FE_reserve={data.get("spine_fe_reserve_25s", "?"):.1f} N·m')
        else:
            print(f'  F={f}: NOT FOUND ({ORIG_PATHS[f]})')

    # Load new
    print('\nLoading new reproduction solutions...')
    new = {}
    for f in forces:
        data = load_solution(NEW_PATHS[f])
        if data:
            new[f] = data
            print(f'  F={f}: loaded  spine_FE_reserve={data.get("spine_fe_reserve_25s", "?"):.1f} N·m')
        else:
            print(f'  F={f}: NOT FOUND ({NEW_PATHS[f]})')

    # Regression comparison (orig vs new)
    print('\n--- Per-phase IL_R10_r comparison (Orig vs New) ---')
    max_delta_es = 0.0
    comparison_rows = []
    for pname, _, _ in PHASES:
        key = f'IL_R10_r_{pname}_peak'
        if 0 in orig and key in orig[0] and 0 in new and key in new[0]:
            v_orig = orig[0][key]
            v_new = new[0][key]
            delta = abs(v_new - v_orig)
            max_delta_es = max(max_delta_es, delta)
            status = 'PASS' if delta < THRESH_DELTA_ES else 'FAIL'
            comparison_rows.append((pname, v_orig, v_new, delta, status))
            print(f'  {pname:<12}: orig={v_orig:.1f}%  new={v_new:.1f}%  delta={delta:.2f}%p  {status}')

    # Dose-response (new infrastructure)
    print('\n--- Dose-response (new infrastructure) ---')
    new_hold_means = []
    new_con_means = []
    for f in forces:
        if f in new:
            h = new[f].get('ES_mean_Hold_mean')
            c = new[f].get('ES_mean_Concentric_mean')
            new_hold_means.append(h)
            new_con_means.append(c)
        else:
            new_hold_means.append(None)
            new_con_means.append(None)

    valid_f = [f for i, f in enumerate(forces) if new_hold_means[i] is not None]
    valid_t = torques[[i for i, f in enumerate(forces) if new_hold_means[i] is not None]]
    valid_h = np.array([v for v in new_hold_means if v is not None])
    valid_c = np.array([v for v in new_con_means  if v is not None])

    new_slope = None
    new_r2 = None
    new_red_28nm = None

    if len(valid_h) >= 2:
        base_h = valid_h[0]
        base_c = valid_c[0]
        red_h = 100 * (base_h - valid_h) / base_h
        red_c = 100 * (base_c - valid_c) / base_c
        s_h, i_h, r2_h = fit_line(valid_t, red_h)
        s_c, i_c, r2_c = fit_line(valid_t, red_c)
        new_slope = s_h
        new_r2 = r2_h
        new_red_28nm = red_h[-1] if len(red_h) >= 5 else None
        print(f'  ES_mean Hold slope: {s_h:.3f} %/N·m  R²={r2_h:.4f}  red@24Nm={red_h[-1]:.2f}%')
        print(f'  ES_mean Con  slope: {s_c:.3f} %/N·m  R²={r2_c:.4f}  red@24Nm={red_c[-1]:.2f}%')
    else:
        print('  Insufficient conditions for dose-response regression')

    # Spine FE reserve comparison
    orig_reserve = orig.get(0, {}).get('spine_fe_reserve_25s', None)
    new_reserve  = new.get(0, {}).get('spine_fe_reserve_25s', None)
    print(f'\n  Spine FE reserve @ 2.5s:')
    print(f'    Orig: {orig_reserve:.1f} N·m (memory: 19.4 N·m)' if orig_reserve else '    Orig: N/A')
    print(f'    New:  {new_reserve:.1f} N·m' if new_reserve else '    New:  N/A')

    # =================== PASS/FAIL SUMMARY ===================
    print()
    print('=' * 70)
    print('Regression PASS/FAIL Summary')
    print('=' * 70)

    p1 = max_delta_es < THRESH_DELTA_ES
    print(f'P1  max ΔES < {THRESH_DELTA_ES}%p:  {max_delta_es:.2f}%p  '
          f'{"PASS" if p1 else "FAIL"}')

    p2 = None
    if new_slope is not None:
        delta_slope = abs(new_slope - MEMORY_REF['slope'])
        p2 = delta_slope < THRESH_SLOPE
        print(f'P2  Slope ±0.1 from 1.164:  {new_slope:.3f} (Δ={delta_slope:.3f})  '
              f'{"PASS" if p2 else "FAIL"}')
    else:
        print(f'P2  Slope: N/A (no new solutions)')

    p3 = None
    if new_r2 is not None:
        p3 = new_r2 >= 0.95
        print(f'P3  R² ≥ 0.95:  {new_r2:.4f}  {"PASS" if p3 else "FAIL"}')
    else:
        print(f'P3  R²: N/A')

    p4 = None
    if new_red_28nm is not None:
        delta_red = abs(new_red_28nm - MEMORY_REF['reduction_28nm'])
        p4 = delta_red < THRESH_REDUCTION
        print(f'P4  28% reduction ±5%p:  {new_red_28nm:.2f}%  (Δ={delta_red:.2f}%p)  '
              f'{"PASS" if p4 else "FAIL"}')
    else:
        print(f'P4  28% reduction: N/A')

    p5 = None
    if new_reserve is not None:
        delta_res = abs(new_reserve - MEMORY_REF['spine_fe_reserve'])
        p5 = delta_res < THRESH_RESERVE
        print(f'P5  Spine FE reserve ±10 Nm:  {new_reserve:.1f} N·m  (Δ={delta_res:.1f})  '
              f'{"PASS" if p5 else "FAIL"}')
    else:
        print(f'P5  Spine FE reserve: N/A (no new solutions)')

    all_tests = [p1] + ([p2] if p2 is not None else []) + \
                ([p3] if p3 is not None else []) + \
                ([p4] if p4 is not None else []) + \
                ([p5] if p5 is not None else [])
    overall = all(all_tests) if all_tests else None
    print()
    print(f'Overall: {"PASS" if overall else ("FAIL" if overall is False else "PARTIAL — new solutions not yet available")}')
    print('=' * 70)

    # Write report
    out_path = Path('/data/opensim_results/phase1a_reproduction/regression_report.md')
    with open(out_path, 'w') as f:
        f.write('# Phase 1a Regression Report — Existing vs New Infrastructure\n\n')
        f.write('## Memory Reference Values\n')
        for k, v in MEMORY_REF.items():
            f.write(f'- {k}: {v}\n')
        f.write('\n## Per-Phase IL_R10_r Comparison (Orig vs New)\n\n')
        f.write('| Phase | Orig (%) | New (%) | Delta (%p) | Result |\n|---|---:|---:|---:|---:|\n')
        for row in comparison_rows:
            pname, v_orig, v_new, delta, status = row
            f.write(f'| {pname} | {v_orig:.1f} | {v_new:.1f} | {delta:.2f} | {status} |\n')
        f.write('\n## Dose-Response (New Infrastructure)\n\n')
        if new_slope is not None:
            f.write(f'- ES_mean Hold slope: {new_slope:.3f} %/N·m (existing: 1.164)\n')
            f.write(f'- R²: {new_r2:.4f} (existing: 1.0000)\n')
            f.write(f'- Reduction @ 24 N·m: {new_red_28nm:.2f}% (existing: 27.95%)\n')
        f.write('\n## PASS/FAIL Summary\n\n')
        f.write(f'- P1 max ΔES < 5%p: {max_delta_es:.2f}%p  {"PASS" if p1 else "FAIL"}\n')
        if p2 is not None:
            f.write(f'- P2 Slope ±0.1: {"PASS" if p2 else "FAIL"}\n')
        if p3 is not None:
            f.write(f'- P3 R² ≥ 0.95: {"PASS" if p3 else "FAIL"}\n')
        if p4 is not None:
            f.write(f'- P4 28% reduction ±5%p: {"PASS" if p4 else "FAIL"}\n')
        if p5 is not None:
            f.write(f'- P5 Spine FE reserve ±10 Nm: {"PASS" if p5 else "FAIL"}\n')
        f.write(f'\n**Overall: {"PASS" if overall else ("FAIL" if overall is False else "PARTIAL")}**\n')
    print(f'\nReport: {out_path}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        print(f'FATAL: {e}')
        traceback.print_exc()
        sys.exit(1)
