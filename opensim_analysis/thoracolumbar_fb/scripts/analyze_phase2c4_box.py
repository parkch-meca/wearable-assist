"""Phase 2.C.4 — Box motion v11b: ES activation analysis + suit effect.

Reads MocoInverse solutions from:
  /data/opensim_results/phase2c4_box_v11b/{B_noload,B_suit50,B_suit100,B_suit200}/solution.sto

Outputs (all to /data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2c4_box_v11b/):
  1. phase2c4_es_timeseries.png   — ES activation time-series (4 conditions overlay)
  2. phase2c4_phase_bars.png      — Phase comparison bar chart (5 phases × key muscles)
  3. phase2c4_suit_regression.png — Dose-response linear regression (R²)
  4. phase2c4_heatmap.png         — 76 ES muscles × 4 conditions heatmap (Concentric peak)
  5. phase2c4_reserve_check.png   — Reserve timeseries (data quality check)

Phase definitions (box v11b):
  Standing  : t=0.0 – 0.5  (quiet stand)
  Eccentric : t=0.5 – 2.0  (bend down)
  Grasp     : t=2.0 – 2.5  (hold at peak bend / box grip)
  Concentric: t=2.5 – 4.0  (stand up with box)   ← ES peak phase
  Carry     : t=4.0 – 5.0  (carry box standing)  ← NEW vs Phase 1a
"""
import os, sys, re, json
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

# ── Paths ──────────────────────────────────────────────────────────────────
SOL_ROOT = Path('/data/opensim_results/phase2c4_box_v11b')
OUT_DIR  = Path(
    '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2c4_box_v11b'
)
OUT_DIR.mkdir(parents=True, exist_ok=True)
PHASE1A_LIST = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/phase1a_muscle_list.txt'

# ── Conditions ─────────────────────────────────────────────────────────────
CONDITIONS = [
    ('B_noload',  0.0),
    ('B_suit50',  50.0),
    ('B_suit100', 100.0),
    ('B_suit200', 200.0),
]
COND_COLORS = {
    'B_noload':  '#333333',
    'B_suit50':  '#4575b4',
    'B_suit100': '#74add1',
    'B_suit200': '#e0f3f8',
}
COND_LABELS = {
    'B_noload':  'No suit (baseline)',
    'B_suit50':  'Suit 50 N·m',
    'B_suit100': 'Suit 100 N·m',
    'B_suit200': 'Suit 200 N·m',
}

# ── Phase definitions ──────────────────────────────────────────────────────
PHASES = [
    ('Standing',   0.0,  0.5),
    ('Eccentric',  0.5,  2.0),
    ('Grasp',      2.0,  2.5),
    ('Concentric', 2.5,  4.0),
    ('Carry',      4.0,  5.0),
]
PHASE_COLORS = {
    'Standing':   '#888888',
    'Eccentric':  '#1f77b4',
    'Grasp':      '#d62728',
    'Concentric': '#2ca02c',
    'Carry':      '#ff7f0e',
}

# ── ES muscle groups ───────────────────────────────────────────────────────
KEY_MUSCLES = [
    'IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'IL_R12_r',
    'LTpL_L5_r', 'LTpL_L5_l', 'LTpL_L4_r', 'LTpT_T12_r', 'LTpT_T11_r',
    'QL_post_I_2-L4_r', 'QL_post_I_3-L1_r', 'rect_abd_r', 'rect_abd_l',
]
DISPLAY_MUSCLES = ['IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'LTpL_L5_r', 'LTpL_L5_l']
RESERVE_OPTF = 10.0


def log(msg):
    print(f'  {msg}', flush=True)


def load_phase1a_muscles():
    names = []
    with open(PHASE1A_LIST) as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith('#'):
                names.append(s)
    return names


def find_act_col(labels, muscle_name):
    """Find column index for muscle activation."""
    for i, L in enumerate(labels):
        if L.endswith(f'/{muscle_name}/activation'):
            return i
    for i, L in enumerate(labels):
        if L.endswith(f'/{muscle_name}'):
            return i
    return None


def load_solution(sol_path):
    """Load solution .sto and return (times, labels, data dict)."""
    tbl = osim.TimeSeriesTable(str(sol_path))
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    n = tbl.getNumRows()
    # Load all columns into numpy array (efficient)
    data = np.zeros((n, len(labels)))
    for i in range(n):
        row = tbl.getRowAtIndex(i)
        for j in range(len(labels)):
            data[i, j] = row[j]
    return times, labels, data


def get_phase_masks(times):
    masks = {}
    for pname, ts, te in PHASES:
        if pname == PHASES[-1][0]:  # last phase: inclusive end
            masks[pname] = (times >= ts) & (times <= te)
        else:
            masks[pname] = (times >= ts) & (times < te)
    return masks


def extract_activations(times, labels, data, muscle_names):
    """Extract activation arrays (%) for given muscle names."""
    acts = {}
    for nm in muscle_names:
        idx = find_act_col(labels, nm)
        if idx is not None:
            acts[nm] = data[:, idx] * 100.0  # → %
    return acts


def phase_stats(acts, masks):
    """Compute peak and mean per muscle per phase."""
    result = {}
    for pname, mask in masks.items():
        if mask.sum() == 0: continue
        result[pname] = {}
        for nm, arr in acts.items():
            seg = arr[mask]
            result[pname][nm] = {'mean': float(seg.mean()), 'peak': float(seg.max())}
    return result


# ─────────────────────────────────────────────────────────────────────────────
def main():
    print('=== Phase 2.C.4 Box v11b — ES Activation Analysis ===')

    all_muscles = load_phase1a_muscles()
    print(f'Phase 1a muscle list: {len(all_muscles)} muscles')

    # ── Load all conditions ──────────────────────────────────────────────
    cond_data = {}
    for label, suit_nm in CONDITIONS:
        sol_path = SOL_ROOT / label / 'solution.sto'
        if not sol_path.exists():
            print(f'[MISSING] {sol_path} — skipping {label}')
            continue
        print(f'Loading {label}...')
        times, labels, data = load_solution(sol_path)
        acts = extract_activations(times, labels, data, all_muscles)
        # Also extract key muscles separately for convenience
        key_acts = {nm: acts[nm] for nm in KEY_MUSCLES if nm in acts}
        cond_data[label] = {
            'suit_nm': suit_nm,
            'times': times,
            'labels': labels,
            'acts': acts,
            'key_acts': key_acts,
            'masks': get_phase_masks(times),
            'phase_stats': phase_stats(acts, get_phase_masks(times)),
        }
        print(f'  t=[{times[0]:.2f},{times[-1]:.2f}]  muscles loaded: {len(acts)}')

    if not cond_data:
        print('[ERROR] No solution files found. Run run_moco_phase2c4_box_sweep.py first.')
        sys.exit(1)

    # Reference times from first available condition
    ref_label = list(cond_data.keys())[0]
    times = cond_data[ref_label]['times']
    masks = cond_data[ref_label]['masks']

    # ── 1. Time-series overlay plot ─────────────────────────────────────
    print('Plot 1: ES time-series overlay...')
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

    ts_sets = [
        (['IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'IL_R12_r'], 'IL (Iliocostalis Lumborum)', axes[0]),
        (['LTpL_L5_r', 'LTpL_L5_l', 'LTpL_L4_r', 'LTpT_T12_r'], 'LTpL/LTpT (Longissimus)', axes[1]),
        (['QL_post_I_2-L4_r', 'QL_post_I_3-L1_r', 'rect_abd_r', 'rect_abd_l'], 'QL + RA', axes[2]),
    ]

    for muscles, title, ax in ts_sets:
        for label, _ in CONDITIONS:
            if label not in cond_data: continue
            cd = cond_data[label]
            lw = 2.5 if label == 'B_noload' else 1.5
            ls = '-' if label == 'B_noload' else '--'
            for nm in muscles:
                if nm not in cd['key_acts']: continue
                arr = cd['key_acts'][nm]
                muscle_short = nm.split('_')[-2] + '_' + nm.split('_')[-1] if '_' in nm else nm
                ax.plot(times, arr, lw=lw, ls=ls, alpha=0.8,
                        label=f'{nm} ({COND_LABELS[label]})')

        # Phase shading
        for pname, ts, te in PHASES:
            ax.axvspan(ts, te, alpha=0.08, color=PHASE_COLORS[pname])
            if ax == axes[0]:
                ax.text((ts + te) / 2, 95, pname, ha='center', va='top',
                        fontsize=8, color='#555')

        ax.set_xlim(0, 5); ax.set_ylim(0, 100)
        ax.set_ylabel('Activation (%)', fontsize=10)
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.legend(ncol=2, fontsize=7, loc='upper right')
        ax.grid(True, alpha=0.3)
        ax.axvline(2.0, color='#d62728', lw=1.0, ls=':', alpha=0.7)   # grasp
        ax.axvline(4.0, color='#ff7f0e', lw=1.0, ls=':', alpha=0.7)   # carry

    axes[-1].set_xlabel('Time (s)', fontsize=10)
    fig.suptitle('Phase 2.C.4 Box v11b — ES Activation (4 Conditions)', fontsize=13, fontweight='bold')
    fig.tight_layout()
    out1 = OUT_DIR / 'phase2c4_es_timeseries.png'
    fig.savefig(str(out1), dpi=120)
    plt.close(fig)
    print(f'  Saved: {out1}')

    # ── 2. Phase bar chart ───────────────────────────────────────────────
    print('Plot 2: Phase bar chart...')
    n_phases = len(PHASES)
    n_muscles = len(DISPLAY_MUSCLES)
    bar_w = 0.18
    fig, ax = plt.subplots(figsize=(14, 7))
    x = np.arange(n_muscles)

    cond_list = [c for c in [lbl for lbl, _ in CONDITIONS] if c in cond_data]
    n_conds = len(cond_list)

    for pi, (pname, ts, te) in enumerate(PHASES):
        x_offset = (pi - n_phases / 2.0 + 0.5) * bar_w
        peak_vals = []
        for nm in DISPLAY_MUSCLES:
            # average across conditions (baseline only for phase bar)
            if 'B_noload' in cond_data:
                cd = cond_data['B_noload']
                v = cd['phase_stats'].get(pname, {}).get(nm, {}).get('peak', 0)
            else:
                v = 0
            peak_vals.append(v)
        bars = ax.bar(x + x_offset, peak_vals, bar_w,
                      label=pname, color=PHASE_COLORS[pname], alpha=0.85,
                      edgecolor='white', linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(DISPLAY_MUSCLES, rotation=20, fontsize=10)
    ax.set_ylabel('Peak activation (%) — B_noload baseline', fontsize=11)
    ax.set_title('5-phase peak activation — B_noload baseline (box v11b)', fontsize=12, fontweight='bold')
    ax.legend(title='Phase', fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 110)
    fig.tight_layout()
    out2 = OUT_DIR / 'phase2c4_phase_bars.png'
    fig.savefig(str(out2), dpi=120)
    plt.close(fig)
    print(f'  Saved: {out2}')

    # ── 2b. Suit comparison bar (IL_R10_r across 4 conditions × phases) ─
    print('Plot 2b: Suit × phase comparison...')
    fig, ax = plt.subplots(figsize=(14, 7))
    target_muscle = 'IL_R10_r'
    phase_names = [p[0] for p in PHASES]
    n_phases2 = len(phase_names)
    bar_w2 = 0.18
    x2 = np.arange(n_phases2)

    for ci, label in enumerate(cond_list):
        cd = cond_data[label]
        vals = []
        for pname in phase_names:
            v = cd['phase_stats'].get(pname, {}).get(target_muscle, {}).get('peak', 0)
            vals.append(v)
        offset = (ci - n_conds / 2.0 + 0.5) * bar_w2
        ax.bar(x2 + offset, vals, bar_w2, label=COND_LABELS[label],
               color=COND_COLORS[label], alpha=0.85, edgecolor='white', linewidth=0.5)

    ax.set_xticks(x2)
    ax.set_xticklabels(phase_names, fontsize=11)
    ax.set_ylabel('Peak activation (%)', fontsize=11)
    ax.set_title(f'{target_muscle} — Phase × Suit comparison', fontsize=12, fontweight='bold')
    ax.legend(title='Condition', fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 110)
    fig.tight_layout()
    out2b = OUT_DIR / 'phase2c4_suit_phase_IL_R10.png'
    fig.savefig(str(out2b), dpi=120)
    plt.close(fig)
    print(f'  Saved: {out2b}')

    # ── 3. Dose-response linear regression ──────────────────────────────
    print('Plot 3: Suit dose-response regression...')

    # Compute ES peak/mean per condition (Concentric phase, IL_R10_r as representative)
    reg_data = {}
    for label, suit_nm in CONDITIONS:
        if label not in cond_data: continue
        cd = cond_data[label]
        ps = cd['phase_stats']
        # ES mean: average across all ES muscles in Concentric
        con_peaks = [ps.get('Concentric', {}).get(nm, {}).get('peak', np.nan)
                     for nm in all_muscles if nm in cd['acts']]
        con_means = [ps.get('Concentric', {}).get(nm, {}).get('mean', np.nan)
                     for nm in all_muscles if nm in cd['acts']]
        il_r10_peak = ps.get('Concentric', {}).get('IL_R10_r', {}).get('peak', np.nan)
        il_r10_grasp = ps.get('Grasp', {}).get('IL_R10_r', {}).get('peak', np.nan)
        reg_data[label] = {
            'suit_nm': suit_nm,
            'ES_peak_con': float(np.nanmean(con_peaks)),
            'ES_mean_con': float(np.nanmean(con_means)),
            'IL_R10_r_peak_con': il_r10_peak,
            'IL_R10_r_peak_grasp': il_r10_grasp,
        }

    # Regression: suit_nm vs ES_peak_con
    suit_nms  = np.array([reg_data[l]['suit_nm'] for l in reg_data])
    es_peak   = np.array([reg_data[l]['ES_peak_con'] for l in reg_data])
    es_mean   = np.array([reg_data[l]['ES_mean_con'] for l in reg_data])
    il_r10    = np.array([reg_data[l]['IL_R10_r_peak_con'] for l in reg_data])

    fig, axes = plt.subplots(1, 3, figsize=(16, 6))

    for ax, ys, title, ylabel in [
        (axes[0], es_peak,  'ES Peak (mean of 114, Concentric)', 'ES peak mean (%)'),
        (axes[1], es_mean,  'ES Mean (mean of 114, Concentric)', 'ES mean (%)'),
        (axes[2], il_r10,   'IL_R10_r peak (Concentric)',        'IL_R10_r peak (%)'),
    ]:
        valid = ~np.isnan(ys)
        if valid.sum() >= 2:
            slope, intercept, r, p, se = stats.linregress(suit_nms[valid], ys[valid])
            r2 = r ** 2
            x_fit = np.array([0, 200])
            y_fit = slope * x_fit + intercept
            ax.plot(x_fit, y_fit, 'r--', lw=1.5, label=f'Fit: slope={slope:.3f} %/N·m\nR²={r2:.4f}')
            ax.text(100, ys[valid].max() * 0.97, f'slope={slope:.3f} %/N·m\nR²={r2:.4f}',
                    ha='center', va='top', fontsize=10,
                    bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
        for i, (label, _) in enumerate(CONDITIONS):
            if label in reg_data and not np.isnan(ys[i]):
                ax.scatter(suit_nms[i], ys[i], s=80, zorder=5,
                           color=COND_COLORS[label], edgecolors='black', linewidths=0.8)
                ax.annotate(label, (suit_nms[i], ys[i]),
                            textcoords='offset points', xytext=(5, 5), fontsize=8)
        ax.set_xlabel('Suit torque (N·m)', fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.set_xlim(-10, 210)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=9)

    fig.suptitle('Phase 2.C.4 Box v11b — Dose-Response (Concentric phase)',
                 fontsize=13, fontweight='bold')
    fig.tight_layout()
    out3 = OUT_DIR / 'phase2c4_suit_regression.png'
    fig.savefig(str(out3), dpi=120)
    plt.close(fig)
    print(f'  Saved: {out3}')

    # ── 4. Heatmap (ES muscles × conditions, Concentric peak) ───────────
    print('Plot 4: ES heatmap (Concentric peak)...')

    # Build matrix: rows = muscles, cols = conditions
    hm_muscles = [nm for nm in all_muscles if any(
        nm in cond_data[l]['acts'] for l in cond_data)]
    hm_conds   = [l for l, _ in CONDITIONS if l in cond_data]

    mat = np.full((len(hm_muscles), len(hm_conds)), np.nan)
    for ci, label in enumerate(hm_conds):
        cd = cond_data[label]
        for ri, nm in enumerate(hm_muscles):
            v = cd['phase_stats'].get('Concentric', {}).get(nm, {}).get('peak', np.nan)
            mat[ri, ci] = v

    # Sort by B_noload peak (descending)
    noload_col = hm_conds.index('B_noload') if 'B_noload' in hm_conds else 0
    sort_idx = np.argsort(-mat[:, noload_col])
    mat_sorted = mat[sort_idx]
    muscles_sorted = [hm_muscles[i] for i in sort_idx]

    fig, ax = plt.subplots(figsize=(10, max(12, len(muscles_sorted) * 0.18)))
    im = ax.imshow(mat_sorted, aspect='auto', cmap='YlOrRd', vmin=0, vmax=100)
    ax.set_xticks(range(len(hm_conds)))
    ax.set_xticklabels([COND_LABELS[l] for l in hm_conds], fontsize=9, rotation=20)
    ax.set_yticks(range(len(muscles_sorted)))
    ax.set_yticklabels(muscles_sorted, fontsize=6)
    plt.colorbar(im, ax=ax, label='Peak activation (%)')
    ax.set_title('ES Muscle Peak Activation — Concentric phase\n(sorted by B_noload, 4 conditions)',
                 fontsize=11, fontweight='bold')
    fig.tight_layout()
    out4 = OUT_DIR / 'phase2c4_heatmap.png'
    fig.savefig(str(out4), dpi=120)
    plt.close(fig)
    print(f'  Saved: {out4}')

    # ── 5. Reserve timeseries (B_noload) ────────────────────────────────
    print('Plot 5: Reserve check (B_noload)...')
    if 'B_noload' in cond_data:
        cd = cond_data['B_noload']
        times_nl = cd['times']
        labels_nl = cd['labels']
        data_nl   = cd['acts']  # this is acts dict

        # Load raw data for reserves
        sol_path = SOL_ROOT / 'B_noload' / 'solution.sto'
        tbl = osim.TimeSeriesTable(str(sol_path))
        times_r = np.array(list(tbl.getIndependentColumn()))
        labels_r = list(tbl.getColumnLabels())
        res_cols = [(i, L) for i, L in enumerate(labels_r)
                    if '/reserve_' in L or 'reserve' in L.lower()]

        if res_cols:
            # Load top reserves
            res_data = np.zeros((tbl.getNumRows(), len(res_cols)))
            for i in range(tbl.getNumRows()):
                row = tbl.getRowAtIndex(i)
                for j, (idx, _) in enumerate(res_cols):
                    res_data[i, j] = row[idx] * RESERVE_OPTF  # → Nm or N

            # Sort by max abs
            max_abs = np.abs(res_data).max(axis=0)
            top_idx = np.argsort(-max_abs)[:8]

            fig, ax = plt.subplots(figsize=(14, 6))
            for j in top_idx:
                _, L = res_cols[j]
                short = re.sub(r'.*/reserve_jointset_', '', L)[:35]
                ax.plot(times_r, res_data[:, j], lw=1.5, label=short)
            for pname, ts, te in PHASES:
                ax.axvspan(ts, te, alpha=0.07, color=PHASE_COLORS[pname])
            ax.axhline(0, color='k', lw=0.5)
            ax.axvline(2.0, color='#d62728', lw=1.0, ls=':', alpha=0.7)
            ax.axvline(4.0, color='#ff7f0e', lw=1.0, ls=':', alpha=0.7)
            ax.set_xlim(0, 5)
            ax.set_xlabel('Time (s)'); ax.set_ylabel('Reserve generated (Nm or N)')
            ax.set_title('Top 8 Reserves — B_noload (data quality check)')
            ax.legend(fontsize=8, loc='upper right', ncol=2)
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            out5 = OUT_DIR / 'phase2c4_reserve_check.png'
            fig.savefig(str(out5), dpi=120)
            plt.close(fig)
            print(f'  Saved: {out5}')

            # Print reserve values at key times
            t_samples = [1.5, 2.5, 3.5, 4.5]
            for t_smp in t_samples:
                idx_t = int(np.argmin(np.abs(times_r - t_smp)))
                row_abs = np.abs(res_data[idx_t])
                top3 = np.argsort(-row_abs)[:3]
                vals = ', '.join([f'{res_cols[j][1].split("/")[-1]}={res_data[idx_t,j]:.1f}'
                                  for j in top3])
                print(f'    Reserves @ t={times_r[idx_t]:.2f}s: {vals}')

    # ── 6. Suit effect summary table ────────────────────────────────────
    print()
    print('=== SUIT EFFECT SUMMARY (Concentric phase, IL_R10_r peak) ===')
    baseline_val = None
    if 'B_noload' in reg_data:
        baseline_val = reg_data['B_noload']['IL_R10_r_peak_con']

    print(f'{"Condition":<12} {"Suit(Nm)":<10} {"IL_R10_r Conc peak":>20} {"Delta vs baseline":>20}')
    for label, suit_nm in CONDITIONS:
        if label not in reg_data: continue
        v = reg_data[label]['IL_R10_r_peak_con']
        delta = (v - baseline_val) if baseline_val and not np.isnan(v) else np.nan
        print(f'{label:<12} {suit_nm:<10.0f} {v:>20.1f}% {delta:>+20.1f} %p')

    print()
    print('=== PHASE × CONDITION TABLE (IL_R10_r, peak %) ===')
    ph_names = [p[0] for p in PHASES]
    print(f'{"Phase":<12}', end='')
    for label, _ in CONDITIONS:
        if label in cond_data:
            print(f'{label:>14}', end='')
    print()
    for pname in ph_names:
        print(f'{pname:<12}', end='')
        for label, _ in CONDITIONS:
            if label not in cond_data: continue
            cd = cond_data[label]
            v = cd['phase_stats'].get(pname, {}).get('IL_R10_r', {}).get('peak', np.nan)
            print(f'{v:>14.1f}', end='')
        print()

    # ── 7. Carry phase analysis (new vs Phase 1a) ───────────────────────
    print()
    print('=== CARRY PHASE ANALYSIS (new — no equivalent in Phase 1a) ===')
    for label, suit_nm in CONDITIONS:
        if label not in cond_data: continue
        cd = cond_data[label]
        # ES mean during carry
        carry_vals = []
        for nm in all_muscles:
            if nm not in cd['acts']: continue
            mask = cd['masks']['Carry']
            if mask.sum() > 0:
                carry_vals.append(cd['acts'][nm][mask].mean())
        carry_mean = np.nanmean(carry_vals) if carry_vals else np.nan
        # IL_R10_r during carry
        il_carry = np.nan
        if 'IL_R10_r' in cd['acts']:
            mask = cd['masks']['Carry']
            if mask.sum() > 0:
                il_carry = cd['acts']['IL_R10_r'][mask].max()
        print(f'  {label:<12}: ES_mean_carry={carry_mean:.1f}%  IL_R10_r_carry_peak={il_carry:.1f}%')

    # ── 8. Regression summary ────────────────────────────────────────────
    print()
    print('=== DOSE-RESPONSE REGRESSION (Concentric peak) ===')
    for ys, name in [(es_peak, 'ES_peak_con'), (es_mean, 'ES_mean_con'), (il_r10, 'IL_R10_r_peak_con')]:
        valid = ~np.isnan(ys)
        if valid.sum() >= 2:
            slope, intercept, r, p, se = stats.linregress(suit_nms[valid], ys[valid])
            print(f'  {name}: slope={slope:.4f} %/N·m  R²={r**2:.4f}  '
                  f'(Phase 1a ref: ES_mean Hold=1.164 %/N·m)')

    print()
    print(f'All plots saved to: {OUT_DIR}')
    print('=== Analysis complete ===')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'FATAL: {e}')
        import traceback; traceback.print_exc()
        sys.exit(1)
