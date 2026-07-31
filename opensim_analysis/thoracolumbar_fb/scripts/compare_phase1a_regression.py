"""Compare Phase 1a results: with-coupler baseline vs no-coupler regression.

Usage:
  python compare_phase1a_regression.py smoke
  python compare_phase1a_regression.py full
"""
import os, sys
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DOC_DIR = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs')
ES_IDS = ['IL_R10_r','IL_R10_l','IL_R11_r','IL_R12_r','LTpL_L5_r','LTpL_L5_l']

PHASES = {
    'Pre-bend (0.5-1.0)':   (0.5, 1.0),
    'Concentric (1.0-2.0)':  (1.0, 1.99),
    'Hold (2.0-2.4)':        (2.0, 2.4),
    'Eccentric (2.5-4.0)':   (2.5, 4.0),
    'Recovery (4.0-5.0)':    (4.0, 5.0),
}


def load_solution(path):
    sol = osim.MocoTrajectory(path)
    nT = sol.getNumTimes()
    times = np.array([sol.getTime()[i] for i in range(nT)])
    sn = list(sol.getStateNames())
    M = sol.getStatesTrajectory()
    arr = np.array([[M.get(i, j) for j in range(M.ncol())] for i in range(M.nrow())])
    name_to_idx = {n: i for i, n in enumerate(sn)}
    return times, arr, name_to_idx


def get_act(arr, name_to_idx, muscle):
    sname = f'/forceset/{muscle}/activation'
    if sname not in name_to_idx: return None
    return arr[:, name_to_idx[sname]]


def peak_in_range(times, vals, t_lo, t_hi):
    mask = (times >= t_lo) & (times <= t_hi)
    if not mask.any(): return float('nan')
    return float(vals[mask].max())


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'smoke'
    if mode == 'smoke':
        baseline = '/data/wearable-assist/results/phase1a_smoke_grf/solution.sto'
        modified = '/data/wearable-assist/results/phase1a_smoke_no_coupler/solution.sto'
        out_md   = DOC_DIR / 'phase1a_regression_test_smoke.md'
        out_png  = DOC_DIR / 'images' / 'phase1a_regression_smoke.png'
    else:
        baseline = '/data/wearable-assist/results/phase1a_full/solution.sto'
        modified = '/data/wearable-assist/results/phase1a_full_no_coupler/solution.sto'
        out_md   = DOC_DIR / 'phase1a_regression_test_full.md'
        out_png  = DOC_DIR / 'images' / 'phase1a_regression_full.png'
    out_png.parent.mkdir(parents=True, exist_ok=True)

    print(f'Comparing:')
    print(f'  baseline (with coupler): {baseline}')
    print(f'  modified (no coupler):   {modified}')

    if not os.path.exists(modified):
        print(f'ERROR: modified solution not found at {modified}')
        sys.exit(1)

    tB, aB, idxB = load_solution(baseline)
    tM, aM, idxM = load_solution(modified)

    # --- Per-muscle peak comparison ---
    rows = []
    for nm in ES_IDS:
        bv = get_act(aB, idxB, nm)
        mv = get_act(aM, idxM, nm)
        if bv is None or mv is None: continue
        for ph_name, (t_lo, t_hi) in PHASES.items():
            pb = peak_in_range(tB, bv, t_lo, t_hi)
            pm = peak_in_range(tM, mv, t_lo, t_hi)
            if np.isnan(pb) or np.isnan(pm): continue
            d_pp = (pm - pb) * 100
            rel = d_pp / (pb * 100) * 100 if pb > 0.01 else 0
            rows.append((nm, ph_name, pb*100, pm*100, d_pp, rel))

    # --- Reserve usage comparison ---
    reserves_pelvis_ty_B = get_act(aB, idxB, 'reserve_pelvis_ty')
    if reserves_pelvis_ty_B is None:
        # Try alternate naming
        alt = [n for n in idxB if 'reserve' in n and 'pelvis_ty' in n]
        print(f'reserve states (baseline) matching pelvis_ty: {alt[:5]}')

    # --- Time-series plot ---
    fig, axes = plt.subplots(3, 2, figsize=(14, 11), sharex=True)
    for ax, nm in zip(axes.flatten(), ES_IDS):
        bv = get_act(aB, idxB, nm)
        mv = get_act(aM, idxM, nm)
        if bv is None or mv is None: continue
        ax.plot(tB, bv*100, color='tab:blue', lw=1.8, label='baseline (with coupler)')
        ax.plot(tM, mv*100, color='tab:red', lw=1.4, ls='--', label='modified (no coupler)')
        ax.set_title(nm, fontweight='bold', loc='left')
        ax.set_ylabel('activation (%)')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc='upper right')
        for ts, te, col in [(0, 0.5, '#888'), (0.5, 1.0, '#aaa'),
                             (1.0, 2.0, '#1f77b4'), (2.0, 2.4, '#d62728'),
                             (2.4, 4.0, '#2ca02c'), (4.0, 5.0, '#ff7f0e')]:
            ax.axvspan(ts, te, alpha=0.06, color=col)
    for ax in axes[-1]: ax.set_xlabel('time (s)')
    fig.suptitle(f'Phase 1a regression — coupler removal effect on ES activation ({mode})',
                 fontsize=12, fontweight='bold')
    fig.tight_layout()
    fig.savefig(out_png, dpi=140, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved {out_png}')

    # --- Pass/fail judgment ---
    big_changes = [(nm, ph, b, m, d_pp, rel) for nm, ph, b, m, d_pp, rel in rows if abs(d_pp) > 5]
    medium_changes = [(nm, ph, b, m, d_pp, rel) for nm, ph, b, m, d_pp, rel in rows if 2 < abs(d_pp) <= 5]
    max_abs_d = max([abs(r[4]) for r in rows]) if rows else 0
    if not big_changes:
        verdict = 'PASS'
    elif len(big_changes) <= 2 and max_abs_d < 8:
        verdict = 'BORDERLINE'
    else:
        verdict = 'FAIL'

    # --- Markdown report ---
    with open(out_md, 'w') as f:
        f.write(f'# Phase 1a regression test — {mode} ({verdict})\n\n')
        f.write(f'Date: 2026-04-28\n\n')
        f.write(f'Baseline:  `{baseline}` (with coupler, original Phase 1a result)\n')
        f.write(f'Modified:  `{modified}` (4 couplers removed)\n\n')
        f.write(f'**Verdict: {verdict}** (max |Δ| = {max_abs_d:.2f} %p; ')
        f.write(f'big changes >5 %p: {len(big_changes)}; medium 2-5 %p: {len(medium_changes)})\n\n')
        f.write(f'PASS criteria: all ES peaks within ±5 %p of baseline.\n\n')
        f.write(f'## ES activation peaks per phase\n\n')
        f.write(f'| muscle | phase | baseline (%) | modified (%) | Δ (%p) | rel (%) |\n')
        f.write(f'|---|---|---:|---:|---:|---:|\n')
        for nm, ph, pb, pm, d, rel in rows:
            tag = ' ❌' if abs(d) > 5 else (' ⚠️' if abs(d) > 2 else '')
            f.write(f'| `{nm}` | {ph} | {pb:.2f} | {pm:.2f} | {d:+.2f}{tag} | {rel:+.1f} |\n')
        f.write('\n')
        if verdict == 'PASS':
            f.write('## Verdict: PASS\n\n')
            f.write('Coupler removal does not alter ES activation patterns. ')
            f.write('The modified model is suitable for box motion v6 design and Phase 2 analyses.\n\n')
        elif verdict == 'BORDERLINE':
            f.write('## Verdict: BORDERLINE\n\n')
            f.write('Some ES peaks moved by 5-8 %p. ')
            f.write('Inspect the affected phases — likely small differences in reserve ')
            f.write('budget redistribution (no shoulder constraint reactions).\n\n')
        else:
            f.write('## Verdict: FAIL\n\n')
            f.write('ES activations changed substantially. Investigate before adopting.\n\n')
        f.write(f'Time-series plot: `images/{out_png.name}`\n')
    print(f'Saved {out_md}')
    print(f'\nVerdict: {verdict}  (max |Δ| = {max_abs_d:.2f} %p)')


if __name__ == '__main__':
    main()
