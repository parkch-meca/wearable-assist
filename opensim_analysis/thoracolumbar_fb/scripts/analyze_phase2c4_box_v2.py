"""Phase 2.C.4 v2 — ES activation analysis + suit effect + v1 vs v2 comparison.

Reads MocoInverse solutions from:
  /data/opensim_results/phase2c4_box_v11b_v2/{B_noload,B_suit50,B_suit100,B_suit200}/solution.sto

Also reads v1 results from:
  /data/opensim_results/phase2c4_box_v11b/{B_noload,...}/solution.sto

Outputs to:
  /data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2c4_box_v11b_v2/

Plots:
  1. phase2c4_v2_es_timeseries.png       — ES activation time-series (4 conds)
  2. phase2c4_v2_phase_bars.png          — Phase comparison bar chart
  3. phase2c4_v2_suit_regression.png     — Dose-response regression (R²)
  4. phase2c4_v2_heatmap.png             — 76 ES muscles × 4 conditions heatmap
  5. phase2c4_v2_reserve_check.png       — Reserve timeseries
  6. phase2c4_v2_lower_limb_activation.png — New: lower limb muscles (glut/ham/quad)
  7. phase2c4_v2_vs_v1_reserve.png       — Reserve comparison v1 vs v2

Phase definitions (box v11b, same as v1):
  Eccentric : t=0.5 – 2.0  (bend down)
  Grasp     : t=2.0 – 2.5  (peak bend, box grip)
  Concentric: t=2.5 – 4.0  (stand up with box)
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

# ── Add muscle_set_v2 to path ──────────────────────────────────────────────
SCRIPT_DIR = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts')
sys.path.insert(0, str(SCRIPT_DIR))
from muscle_set_v2 import MUSCLE_SET_V2, PHASE1A_MUSCLES, LOWER_LIMB_MUSCLES

# ── Paths ──────────────────────────────────────────────────────────────────
SOL_ROOT_V2 = Path('/data/opensim_results/phase2c4_box_v11b_v2')
SOL_ROOT_V1 = Path('/data/opensim_results/phase2c4_box_v11b')
OUT_DIR = Path(
    '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2c4_box_v11b_v2'
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
    'B_suit200': '#91bfdb',
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

# Key ES muscles for display
KEY_ES_MUSCLES = [
    'IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'IL_R12_r',
    'LTpL_L5_r', 'LTpL_L5_l', 'LTpL_L4_r', 'LTpT_T12_r',
    'QL_post_I_2-L4_r', 'QL_post_I_3-L1_r',
]
DISPLAY_ES = ['IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'LTpL_L5_r', 'LTpL_L5_l']

# Key lower limb muscles for new plot
KEY_LL_MUSCLES = [
    'glut_max1_r', 'glut_max2_r', 'glut_max3_r',
    'glut_med1_r', 'glut_med2_r',
    'bifemlh_r', 'bifemsh_r',
    'rect_fem_r', 'vas_int_r',
    'iliacus_r', 'Ps_L1_VB_r',
    'tfl_r',
    'med_gas_r', 'soleus_r', 'tib_ant_r',
]
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
    for i, L in enumerate(labels):
        if L.endswith(f'/{muscle_name}/activation'):
            return i
    for i, L in enumerate(labels):
        if L.endswith(f'/{muscle_name}'):
            return i
    return None


def load_solution(sol_path):
    tbl = osim.TimeSeriesTable(str(sol_path))
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    n = tbl.getNumRows()
    data = np.zeros((n, len(labels)))
    for i in range(n):
        row = tbl.getRowAtIndex(i)
        for j in range(len(labels)):
            data[i, j] = row[j]
    return times, labels, data


def get_phase_masks(times):
    masks = {}
    for pname, ts, te in PHASES:
        if pname == PHASES[-1][0]:
            masks[pname] = (times >= ts) & (times <= te)
        else:
            masks[pname] = (times >= ts) & (times < te)
    return masks


def extract_activations(times, labels, data, muscle_names):
    acts = {}
    for nm in muscle_names:
        idx = find_act_col(labels, nm)
        if idx is not None:
            acts[nm] = data[:, idx] * 100.0
    return acts


def extract_reserves(times, labels, data):
    """Extract reserve columns and return as dict {coord_name: array_Nm_or_N}."""
    reserves = {}
    for i, L in enumerate(labels):
        if 'reserve' in L.lower():
            short = re.sub(r'.*/reserve_jointset_[^_]+_', '', L)
            short = re.sub(r'/.*', '', short)
            reserves[short] = data[:, i] * RESERVE_OPTF
    return reserves


def phase_stats(acts, masks):
    result = {}
    for pname, mask in masks.items():
        if mask.sum() == 0: continue
        result[pname] = {}
        for nm, arr in acts.items():
            seg = arr[mask]
            result[pname][nm] = {'mean': float(seg.mean()), 'peak': float(seg.max())}
    return result


def reserve_peak(reserves):
    """Return peak absolute value per reserve coordinate."""
    return {nm: float(np.abs(arr).max()) for nm, arr in reserves.items()}


# ─────────────────────────────────────────────────────────────────────────────
def main():
    print('=== Phase 2.C.4 v2 — ES Activation Analysis (158 muscles) ===')

    phase1a_muscles = load_phase1a_muscles()
    print(f'Phase 1a ES list: {len(phase1a_muscles)} muscles')
    print(f'Lower limb list:  {len(LOWER_LIMB_MUSCLES)} muscles')

    # ── Load all v2 conditions ────────────────────────────────────────────
    cond_data = {}
    for label, suit_nm in CONDITIONS:
        sol_path = SOL_ROOT_V2 / label / 'solution.sto'
        if not sol_path.exists():
            print(f'[MISSING] {sol_path} — skipping {label}')
            continue
        print(f'Loading v2 {label}...')
        times, labels, data = load_solution(sol_path)
        es_acts  = extract_activations(times, labels, data, phase1a_muscles)
        ll_acts  = extract_activations(times, labels, data, LOWER_LIMB_MUSCLES)
        reserves = extract_reserves(times, labels, data)
        masks    = get_phase_masks(times)
        cond_data[label] = {
            'suit_nm': suit_nm,
            'times': times,
            'labels': labels,
            'es_acts': es_acts,
            'll_acts': ll_acts,
            'reserves': reserves,
            'masks': masks,
            'es_phase': phase_stats(es_acts, masks),
            'll_phase': phase_stats(ll_acts, masks),
            'res_peak': reserve_peak(reserves),
        }
        print(f'  t=[{times[0]:.2f},{times[-1]:.2f}]  ES={len(es_acts)}  LL={len(ll_acts)}  reserves={len(reserves)}')

    if not cond_data:
        print('[ERROR] No v2 solution files found. Run run_moco_phase2c4_box_v2_sweep.py first.')
        sys.exit(1)

    ref_label = list(cond_data.keys())[0]
    times     = cond_data[ref_label]['times']
    masks     = cond_data[ref_label]['masks']

    # ── Also load v1 B_noload for comparison ──────────────────────────────
    v1_reserves = {}
    v1_es_acts  = {}
    sol_v1 = SOL_ROOT_V1 / 'B_noload' / 'solution.sto'
    if sol_v1.exists():
        print('Loading v1 B_noload for comparison...')
        t1, l1, d1 = load_solution(sol_v1)
        v1_es_acts  = extract_activations(t1, l1, d1, phase1a_muscles)
        v1_reserves = extract_reserves(t1, l1, d1)
        print(f'  v1 ES={len(v1_es_acts)}  reserves={len(v1_reserves)}')

    # ─────────────────────────────────────────────────────────────────────
    # PLOT 1: ES time-series overlay
    # ─────────────────────────────────────────────────────────────────────
    print('Plot 1: ES time-series overlay...')
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    ts_sets = [
        (['IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'IL_R12_r'],      'IL (Iliocostalis Lumborum)', axes[0]),
        (['LTpL_L5_r', 'LTpL_L5_l', 'LTpL_L4_r', 'LTpT_T12_r'], 'LTpL/LTpT (Longissimus)',   axes[1]),
        (['QL_post_I_2-L4_r', 'QL_post_I_3-L1_r', 'rect_abd_r'], 'QL + RA',                   axes[2]),
    ]
    for muscles, title, ax in ts_sets:
        for label, _ in CONDITIONS:
            if label not in cond_data: continue
            cd = cond_data[label]
            lw = 2.5 if label == 'B_noload' else 1.5
            ls = '-' if label == 'B_noload' else '--'
            for nm in muscles:
                if nm not in cd['es_acts']: continue
                ax.plot(cd['times'], cd['es_acts'][nm], lw=lw, ls=ls, alpha=0.85,
                        label=f'{nm} ({COND_LABELS[label]})')
        for pname, ts, te in PHASES:
            ax.axvspan(ts, te, alpha=0.08, color=PHASE_COLORS[pname])
            if ax == axes[0]:
                ax.text((ts + te) / 2, 95, pname, ha='center', va='top',
                        fontsize=8, color='#555')
        ax.set_xlim(1.0, 4.0); ax.set_ylim(0, 105)
        ax.set_ylabel('Activation (%)', fontsize=10)
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.legend(ncol=2, fontsize=7, loc='upper right')
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel('Time (s)', fontsize=10)
    fig.suptitle('Phase 2.C.4 v2 (158 muscles) — ES Activation (4 Conditions)', fontsize=13, fontweight='bold')
    fig.tight_layout()
    out1 = OUT_DIR / 'phase2c4_v2_es_timeseries.png'
    fig.savefig(str(out1), dpi=120); plt.close(fig)
    print(f'  Saved: {out1}')

    # ─────────────────────────────────────────────────────────────────────
    # PLOT 2: Phase bar chart (ES peak, B_noload baseline)
    # ─────────────────────────────────────────────────────────────────────
    print('Plot 2: Phase bar chart...')
    n_phases = len(PHASES)
    bar_w = 0.15
    fig, ax = plt.subplots(figsize=(14, 7))
    x = np.arange(len(DISPLAY_ES))
    for pi, (pname, ts, te) in enumerate(PHASES):
        x_offset = (pi - n_phases / 2.0 + 0.5) * bar_w
        vals = []
        for nm in DISPLAY_ES:
            if 'B_noload' in cond_data:
                v = cond_data['B_noload']['es_phase'].get(pname, {}).get(nm, {}).get('peak', 0)
            else:
                v = 0
            vals.append(v)
        ax.bar(x + x_offset, vals, bar_w, label=pname,
               color=PHASE_COLORS[pname], alpha=0.85, edgecolor='white', linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(DISPLAY_ES, rotation=20, fontsize=10)
    ax.set_ylabel('Peak activation (%) — B_noload baseline', fontsize=11)
    ax.set_title('5-phase ES peak — B_noload baseline, muscle set v2 (158)', fontsize=12, fontweight='bold')
    ax.legend(title='Phase', fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 115)
    fig.tight_layout()
    out2 = OUT_DIR / 'phase2c4_v2_phase_bars.png'
    fig.savefig(str(out2), dpi=120); plt.close(fig)
    print(f'  Saved: {out2}')

    # ─────────────────────────────────────────────────────────────────────
    # PLOT 3: Dose-response regression
    # ─────────────────────────────────────────────────────────────────────
    print('Plot 3: Dose-response regression...')
    reg_data = {}
    for label, suit_nm in CONDITIONS:
        if label not in cond_data: continue
        cd = cond_data[label]
        ps = cd['es_phase']
        con_peaks = [ps.get('Concentric', {}).get(nm, {}).get('peak', np.nan)
                     for nm in phase1a_muscles if nm in cd['es_acts']]
        il_r10_con  = ps.get('Concentric', {}).get('IL_R10_r', {}).get('peak', np.nan)
        il_r10_gsp  = ps.get('Grasp',      {}).get('IL_R10_r', {}).get('peak', np.nan)
        il_r10_ecc  = ps.get('Eccentric',  {}).get('IL_R10_r', {}).get('peak', np.nan)
        reg_data[label] = {
            'suit_nm': suit_nm,
            'ES_peak_con': float(np.nanmean(con_peaks)),
            'IL_R10_r_con': il_r10_con,
            'IL_R10_r_gsp': il_r10_gsp,
            'IL_R10_r_ecc': il_r10_ecc,
        }

    suit_nms = np.array([reg_data[l]['suit_nm']    for l in reg_data])
    es_peak  = np.array([reg_data[l]['ES_peak_con']for l in reg_data])
    il_r10   = np.array([reg_data[l]['IL_R10_r_con']for l in reg_data])

    fig, axes2 = plt.subplots(1, 2, figsize=(14, 6))
    for ax, ys, title, ylabel in [
        (axes2[0], es_peak, 'ES Peak mean (Concentric, 114 ES muscles)', 'ES peak mean (%)'),
        (axes2[1], il_r10,  'IL_R10_r Peak (Concentric)',                'IL_R10_r peak (%)'),
    ]:
        valid = ~np.isnan(ys)
        if valid.sum() >= 2:
            slope, intercept, r, p, se = stats.linregress(suit_nms[valid], ys[valid])
            r2 = r ** 2
            x_fit = np.array([0, 200])
            y_fit = slope * x_fit + intercept
            ax.plot(x_fit, y_fit, 'r--', lw=1.5, label=f'slope={slope:.4f} %/N·m\nR²={r2:.4f}')
            ax.text(100, ys[valid].max() * 0.97,
                    f'slope={slope:.4f} %/N·m\nR²={r2:.4f}',
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
    fig.suptitle('Phase 2.C.4 v2 — Suit Dose-Response (Concentric phase)',
                 fontsize=13, fontweight='bold')
    fig.tight_layout()
    out3 = OUT_DIR / 'phase2c4_v2_suit_regression.png'
    fig.savefig(str(out3), dpi=120); plt.close(fig)
    print(f'  Saved: {out3}')

    # ─────────────────────────────────────────────────────────────────────
    # PLOT 4: Heatmap
    # ─────────────────────────────────────────────────────────────────────
    print('Plot 4: ES heatmap (Concentric peak)...')
    hm_muscles = [nm for nm in phase1a_muscles
                  if any(nm in cond_data[l]['es_acts'] for l in cond_data)]
    hm_conds   = [l for l, _ in CONDITIONS if l in cond_data]
    mat = np.full((len(hm_muscles), len(hm_conds)), np.nan)
    for ci, label in enumerate(hm_conds):
        cd = cond_data[label]
        for ri, nm in enumerate(hm_muscles):
            v = cd['es_phase'].get('Concentric', {}).get(nm, {}).get('peak', np.nan)
            mat[ri, ci] = v
    noload_col = hm_conds.index('B_noload') if 'B_noload' in hm_conds else 0
    sort_idx   = np.argsort(-mat[:, noload_col])
    mat_sorted = mat[sort_idx]
    muscles_sorted = [hm_muscles[i] for i in sort_idx]
    fig, ax = plt.subplots(figsize=(10, max(12, len(muscles_sorted) * 0.18)))
    im = ax.imshow(mat_sorted, aspect='auto', cmap='YlOrRd', vmin=0, vmax=100)
    ax.set_xticks(range(len(hm_conds)))
    ax.set_xticklabels([COND_LABELS[l] for l in hm_conds], fontsize=9, rotation=20)
    ax.set_yticks(range(len(muscles_sorted)))
    ax.set_yticklabels(muscles_sorted, fontsize=6)
    plt.colorbar(im, ax=ax, label='Peak activation (%)')
    ax.set_title('ES Peak — Concentric phase, muscle set v2 (158)\n(sorted by B_noload)',
                 fontsize=11, fontweight='bold')
    fig.tight_layout()
    out4 = OUT_DIR / 'phase2c4_v2_heatmap.png'
    fig.savefig(str(out4), dpi=120); plt.close(fig)
    print(f'  Saved: {out4}')

    # ─────────────────────────────────────────────────────────────────────
    # PLOT 5: Reserve timeseries (B_noload)
    # ─────────────────────────────────────────────────────────────────────
    print('Plot 5: Reserve check (B_noload)...')
    if 'B_noload' in cond_data:
        cd = cond_data['B_noload']
        t_r  = cd['times']
        res  = cd['reserves']
        # Sort by max abs, show top 10
        max_abs = {nm: np.abs(arr).max() for nm, arr in res.items()}
        top10 = sorted(max_abs, key=lambda x: -max_abs[x])[:10]
        fig, ax = plt.subplots(figsize=(14, 7))
        for nm in top10:
            ax.plot(t_r, res[nm], lw=1.5, label=f'{nm} (max={max_abs[nm]:.1f})')
        for pname, ts, te in PHASES:
            ax.axvspan(ts, te, alpha=0.07, color=PHASE_COLORS[pname])
        ax.axhline(0, color='k', lw=0.5)
        ax.set_xlim(t_r[0], t_r[-1])
        ax.set_xlabel('Time (s)'); ax.set_ylabel('Reserve (N·m or N)')
        ax.set_title('Top 10 Reserves — B_noload v2 (158 muscles)', fontsize=12, fontweight='bold')
        ax.legend(fontsize=8, loc='upper right', ncol=2)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        out5 = OUT_DIR / 'phase2c4_v2_reserve_check.png'
        fig.savefig(str(out5), dpi=120); plt.close(fig)
        print(f'  Saved: {out5}')

    # ─────────────────────────────────────────────────────────────────────
    # PLOT 6: Lower limb activation (B_noload vs B_suit200)
    # ─────────────────────────────────────────────────────────────────────
    print('Plot 6: Lower limb activation (new)...')
    ll_available = [nm for nm in KEY_LL_MUSCLES
                    if any(nm in cond_data[l]['ll_acts'] for l in cond_data)]
    if ll_available and 'B_noload' in cond_data:
        n_ll = len(ll_available)
        fig, axes3 = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
        for ax, label in zip(axes3, ['B_noload', 'B_suit200']):
            if label not in cond_data:
                ax.text(0.5, 0.5, f'{label} not available', transform=ax.transAxes,
                        ha='center', va='center')
                continue
            cd = cond_data[label]
            for nm in ll_available:
                if nm not in cd['ll_acts']: continue
                ax.plot(cd['times'], cd['ll_acts'][nm], lw=1.5, label=nm, alpha=0.85)
            for pname, ts, te in PHASES:
                ax.axvspan(ts, te, alpha=0.07, color=PHASE_COLORS[pname])
            ax.set_xlim(cd['times'][0], cd['times'][-1])
            ax.set_ylim(0, 105)
            ax.set_ylabel('Activation (%)', fontsize=10)
            ax.set_title(f'Lower limb muscles — {COND_LABELS.get(label, label)}',
                         fontsize=11, fontweight='bold')
            ax.legend(ncol=3, fontsize=8, loc='upper right')
            ax.grid(True, alpha=0.3)
        axes3[-1].set_xlabel('Time (s)', fontsize=10)
        fig.suptitle('Phase 2.C.4 v2 — Lower Limb Activation (new in v2)',
                     fontsize=13, fontweight='bold')
        fig.tight_layout()
        out6 = OUT_DIR / 'phase2c4_v2_lower_limb_activation.png'
        fig.savefig(str(out6), dpi=120); plt.close(fig)
        print(f'  Saved: {out6}')
    else:
        print('  Skipped (no lower limb muscles found in solution)')

    # ─────────────────────────────────────────────────────────────────────
    # PLOT 7: Reserve comparison v1 vs v2
    # ─────────────────────────────────────────────────────────────────────
    print('Plot 7: Reserve comparison v1 vs v2...')
    # Identify common reserve coordinates with large v1 values
    TRACK_RESERVES = [
        'pelvis_ty', 'pelvis_tilt', 'hip_flexion_r', 'hip_flexion_l',
        'knee_angle_r', 'knee_angle_l', 'ankle_angle_r', 'ankle_angle_l',
        'pelvis_tx', 'pelvis_tz',
        'lumbar_extension', 'lumbar_bending', 'lumbar_rotation',
    ]
    if v1_reserves and 'B_noload' in cond_data:
        v2_res = cond_data['B_noload']['reserves']
        v1_peak = {nm: np.abs(arr).max() for nm, arr in v1_reserves.items()}
        v2_peak = {nm: np.abs(arr).max() for nm, arr in v2_res.items()}

        # Collect all names seen in either
        all_res_names = sorted(set(v1_peak) | set(v2_peak),
                               key=lambda x: -v1_peak.get(x, 0))[:20]

        v1_vals = np.array([v1_peak.get(nm, 0) for nm in all_res_names])
        v2_vals = np.array([v2_peak.get(nm, 0) for nm in all_res_names])

        fig, ax = plt.subplots(figsize=(14, 8))
        x_pos = np.arange(len(all_res_names))
        bar_w_cmp = 0.35
        bars1 = ax.bar(x_pos - bar_w_cmp/2, v1_vals, bar_w_cmp,
                       label='v1 (114 muscles)', color='#d73027', alpha=0.8)
        bars2 = ax.bar(x_pos + bar_w_cmp/2, v2_vals, bar_w_cmp,
                       label='v2 (158 muscles)', color='#4575b4', alpha=0.8)
        # Annotate delta %
        for i, (v1, v2) in enumerate(zip(v1_vals, v2_vals)):
            if v1 > 1:
                pct = (v2 - v1) / v1 * 100
                color = '#2ca02c' if pct < -20 else ('#ff7f0e' if pct < 0 else '#d73027')
                ax.text(x_pos[i], max(v1, v2) + 3, f'{pct:+.0f}%',
                        ha='center', va='bottom', fontsize=7, color=color)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(all_res_names, rotation=35, ha='right', fontsize=8)
        ax.set_ylabel('Max |Reserve| (N·m or N)', fontsize=11)
        ax.set_title('Reserve Peak Comparison: v1 (114) vs v2 (158 muscles) — B_noload',
                     fontsize=12, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        # Add reference lines
        ax.axhline(20, color='#2ca02c', lw=1, ls='--', alpha=0.6, label='Phase 1a pelvis_tilt: 19.4 N·m')
        fig.tight_layout()
        out7 = OUT_DIR / 'phase2c4_v2_vs_v1_reserve.png'
        fig.savefig(str(out7), dpi=120); plt.close(fig)
        print(f'  Saved: {out7}')

    # ─────────────────────────────────────────────────────────────────────
    # CONSOLE SUMMARY TABLES
    # ─────────────────────────────────────────────────────────────────────
    print()
    print('=' * 70)
    print('PHASE 2.C.4 v2 RESULTS SUMMARY')
    print('=' * 70)

    # Reserve comparison table
    print('\n--- Reserve Peak Comparison (B_noload) ---')
    print(f'{"Coordinate":<30} {"v1 (114)":<12} {"v2 (158)":<12} {"Delta":<12} {"% change"}')
    print('-' * 70)
    track = ['pelvis_ty', 'pelvis_tilt', 'hip_flexion_r', 'hip_flexion_l',
             'knee_angle_r', 'knee_angle_l', 'ankle_angle_r', 'ankle_angle_l',
             'pelvis_tx']
    if 'B_noload' in cond_data:
        v2_res_b = cond_data['B_noload']['reserves']
        for nm in track:
            v1v = np.abs(v1_reserves[nm]).max() if nm in v1_reserves else float('nan')
            v2v = np.abs(v2_res_b[nm]).max() if nm in v2_res_b else float('nan')
            if not np.isnan(v1v) and not np.isnan(v2v):
                delta = v2v - v1v
                pct   = (v2v - v1v) / v1v * 100 if v1v > 0 else float('nan')
                flag  = ' <-- KEY' if abs(delta) > 50 else ''
                print(f'{nm:<30} {v1v:<12.1f} {v2v:<12.1f} {delta:<12.1f} {pct:+.1f}%{flag}')
            else:
                print(f'{nm:<30} {v1v!s:<12} {v2v!s:<12} --')

    # ES activation table
    print('\n--- ES Activation (B_noload, IL_R10_r) ---')
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
            v = cond_data[label]['es_phase'].get(pname, {}).get('IL_R10_r', {}).get('peak', float('nan'))
            print(f'{v:>14.1f}', end='')
        print()

    # Suit effect table (Concentric, v2 vs v1)
    print('\n--- Suit Effect Concentric (IL_R10_r peak) ---')
    print(f'{"Condition":<12} {"v2 (158)":<12} {"v1 (114)":<12} {"Delta v2-v1"}')
    for label, suit_nm in CONDITIONS:
        if label not in reg_data: continue
        v2v = reg_data[label]['IL_R10_r_con']
        # Load v1 data for this condition
        v1_sol = SOL_ROOT_V1 / label / 'solution.sto'
        v1v = float('nan')
        if v1_sol.exists():
            try:
                t1, l1, d1 = load_solution(v1_sol)
                a1 = extract_activations(t1, l1, d1, ['IL_R10_r'])
                if 'IL_R10_r' in a1:
                    msk = get_phase_masks(t1)
                    con_msk = msk.get('Concentric', np.zeros(len(t1), bool))
                    if con_msk.sum() > 0:
                        v1v = float(a1['IL_R10_r'][con_msk].max())
            except Exception:
                pass
        delta = v2v - v1v if not np.isnan(v1v) else float('nan')
        print(f'{label:<12} {v2v:<12.1f} {v1v:<12.1f} {delta:+.1f}')

    # Regression summary
    print('\n--- Dose-Response Regression (Concentric) ---')
    for ys, name in [(es_peak, 'ES_peak_con'), (il_r10, 'IL_R10_r_con')]:
        valid = ~np.isnan(ys)
        if valid.sum() >= 2:
            slope, intercept, r, p, se = stats.linregress(suit_nms[valid], ys[valid])
            print(f'  {name}: slope={slope:.4f} %/N·m  R²={r**2:.4f}  intercept={intercept:.2f}')

    # Lower limb peak activations
    print('\n--- Lower Limb Peak Activation (B_noload, Concentric) ---')
    if 'B_noload' in cond_data:
        ll_phase_b = cond_data['B_noload']['ll_phase']
        for nm in KEY_LL_MUSCLES:
            v = ll_phase_b.get('Concentric', {}).get(nm, {}).get('peak', float('nan'))
            if not np.isnan(v):
                print(f'  {nm:<20}: {v:.1f}%')

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
