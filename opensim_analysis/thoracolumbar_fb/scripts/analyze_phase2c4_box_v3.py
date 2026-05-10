"""Phase 2.C.4 v3 — Reserve + ES analysis, v1/v2/v3 comparison.

Reads:
  v1: /data/opensim_results/phase2c4_box_v11b/B_noload/solution.sto
  v2: /data/opensim_results/phase2c4_box_v11b_v2/B_noload/solution.sto
  v3: /data/opensim_results/phase2c4_box_v11b_v3_external_force/B_noload/solution.sto

Outputs:
  /data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2c4_box_v11b_v3/

Plots:
  1. phase2c4_v3_pelvis_reserve_timeseries.png — pelvis_tilt + pelvis_ty time series
  2. phase2c4_v3_reserve_bar_comparison.png    — v1/v2/v3 reserve comparison bar chart
  3. phase2c4_v3_es_timeseries.png             — ES activation time series
  4. phase2c4_v3_external_force_check.png      — hand force profile + Newton check
"""
import os, sys
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SCRIPT_DIR = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts')
sys.path.insert(0, str(SCRIPT_DIR))

SOL_V1 = Path('/data/opensim_results/phase2c4_box_v11b/B_noload/solution.sto')
SOL_V2 = Path('/data/opensim_results/phase2c4_box_v11b_v2/B_noload/solution.sto')
SOL_V3 = Path('/data/opensim_results/phase2c4_box_v11b_v3_external_force/B_noload/solution.sto')
EXT_V3 = Path('/data/opensim_results/phase2c4_box_v11b_v3_external_force/B_noload/ext_loads.mot')

OUT_DIR = Path(
    '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2c4_box_v11b_v3'
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

RESERVE_OPTF = 10.0
PHASE1A_LIST = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/phase1a_muscle_list.txt'


def load_solution(path):
    tbl = osim.TimeSeriesTable(str(path))
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    n = tbl.getNumRows()
    data = np.zeros((n, len(labels)))
    for i in range(n):
        row = tbl.getRowAtIndex(i)
        for j in range(len(labels)):
            data[i, j] = row[j]
    return times, labels, data


def get_reserve(labels, data, coord_name):
    for i, L in enumerate(labels):
        if coord_name in L and 'reserve' in L.lower():
            return data[:, i] * RESERVE_OPTF
    return None


def get_reserve_peak(labels, data, coord_name):
    arr = get_reserve(labels, data, coord_name)
    if arr is not None:
        return float(np.abs(arr).max())
    return float('nan')


def load_phase1a_muscles():
    names = []
    with open(PHASE1A_LIST) as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith('#'):
                names.append(s)
    return names


def get_activation(labels, data, muscle_name):
    for i, L in enumerate(labels):
        if muscle_name in L and 'activation' in L:
            return data[:, i] * 100.0
    return None


def main():
    print('=== Phase 2.C.4 v3 Analysis ===')

    # ── Load all versions ──────────────────────────────────────────────────
    print('Loading solutions...')
    t1, l1, d1 = load_solution(SOL_V1)
    t2, l2, d2 = load_solution(SOL_V2)
    t3, l3, d3 = load_solution(SOL_V3)

    print(f'v1: t=[{t1[0]:.2f},{t1[-1]:.2f}], n={len(t1)}')
    print(f'v2: t=[{t2[0]:.2f},{t2[-1]:.2f}], n={len(t2)}')
    print(f'v3: t=[{t3[0]:.2f},{t3[-1]:.2f}], n={len(t3)}')

    phase1a_muscles = load_phase1a_muscles()

    # ── Reserve summary table ──────────────────────────────────────────────
    print()
    print('RESERVE COMPARISON (B_noload)')
    KEY_COORDS = [
        'pelvis_tilt', 'pelvis_ty', 'pelvis_tx',
        'pelvis_rotation', 'pelvis_list',
        'Abs_FE', 'L5_S1_FE',
        'hip_flexion_r', 'hip_flexion_l',
        'hip_adduction_r', 'hip_adduction_l',
        'hip_rotation_r', 'knee_angle_r', 'ankle_angle_r',
    ]
    print(f'{"Coordinate":<30} {"v1 (114)":>10} {"v2 (158)":>10} {"v3 (158+ext)":>14} {"v3-v2":>8}')
    print('-' * 80)
    reserve_data = {}
    for nm in KEY_COORDS:
        v1 = get_reserve_peak(l1, d1, nm)
        v2 = get_reserve_peak(l2, d2, nm)
        v3 = get_reserve_peak(l3, d3, nm)
        delta = v3 - v2 if not (v3 != v3 or v2 != v2) else float('nan')
        flag = ' WORSE' if delta > 10 else (' BETTER' if delta < -10 else '')
        v1s = f'{v1:.1f}' if not (v1 != v1) else 'N/A'
        v2s = f'{v2:.1f}' if not (v2 != v2) else 'N/A'
        v3s = f'{v3:.1f}' if not (v3 != v3) else 'N/A'
        ds  = f'{delta:+.1f}' if not (delta != delta) else 'N/A'
        print(f'  {nm:<30} {v1s:>10} {v2s:>10} {v3s:>14} {ds:>8}{flag}')
        reserve_data[nm] = {'v1': v1, 'v2': v2, 'v3': v3, 'delta': delta}

    # ── PLOT 1: pelvis reserves time series ────────────────────────────────
    print('\nPlot 1: pelvis reserve time series...')
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    for ax, coord, title in [
        (axes[0], 'pelvis_tilt', 'pelvis_tilt reserve (N·m)'),
        (axes[1], 'pelvis_ty',   'pelvis_ty reserve (N)'),
    ]:
        for label, t, L, d, color, lw in [
            ('v1 (114 muscles, no hand force)', t1, l1, d1, '#d73027', 1.2),
            ('v2 (158 muscles, no hand force)', t2, l2, d2, '#4575b4', 1.8),
            ('v3 (158 muscles, + hand force)',  t3, l3, d3, '#1a9850', 2.5),
        ]:
            arr = get_reserve(L, d, coord)
            if arr is not None:
                ax.plot(t, arr, lw=lw, label=label, color=color)
        ax.axhline(0, color='k', lw=0.5)
        # Phase shading
        for pname, ts, te, pc in [
            ('Eccentric', 1.0, 2.0, '#aec7e8'),
            ('Grasp',     2.0, 2.5, '#ffbb78'),
            ('Concentric',2.5, 4.0, '#98df8a'),
        ]:
            ax.axvspan(ts, te, alpha=0.1, color=pc)
            ax.text((ts + te) / 2, ax.get_ylim()[0] if ax.get_ylim()[0] > -100 else -200,
                    pname, ha='center', va='bottom', fontsize=8, color='#555')
        ax.set_ylabel(title, fontsize=10)
        ax.legend(fontsize=9, loc='lower right')
        ax.grid(True, alpha=0.3)
        peak1 = get_reserve_peak(l1, d1, coord)
        peak2 = get_reserve_peak(l2, d2, coord)
        peak3 = get_reserve_peak(l3, d3, coord)
        ax.set_title(f'{title}\n|peak|: v1={peak1:.0f}  v2={peak2:.0f}  v3={peak3:.0f}',
                     fontsize=10, fontweight='bold')

    axes[-1].set_xlabel('Time (s)', fontsize=10)
    axes[0].set_xlim(1.0, 4.0)
    fig.suptitle('Phase 2.C.4: Pelvis Reserves — v1 / v2 / v3 Comparison (B_noload)',
                 fontsize=13, fontweight='bold')
    fig.tight_layout()
    out1 = OUT_DIR / 'phase2c4_v3_pelvis_reserve_timeseries.png'
    fig.savefig(str(out1), dpi=120); plt.close(fig)
    print(f'  Saved: {out1}')

    # ── PLOT 2: Reserve bar comparison ─────────────────────────────────────
    print('Plot 2: reserve bar comparison...')
    plot_coords = [nm for nm in KEY_COORDS
                   if any(not (reserve_data[nm][v] != reserve_data[nm][v])
                          and reserve_data[nm][v] > 1.0
                          for v in ['v1', 'v2', 'v3'])]
    x = np.arange(len(plot_coords))
    bw = 0.25
    fig, ax = plt.subplots(figsize=(16, 8))
    for xi, (v, color, label) in enumerate([
        ('v1', '#d73027', 'v1 (114 muscles)'),
        ('v2', '#4575b4', 'v2 (158 muscles)'),
        ('v3', '#1a9850', 'v3 (158 + hand force)'),
    ]):
        vals = np.array([reserve_data[nm].get(v, float('nan')) for nm in plot_coords])
        ax.bar(x + (xi - 1) * bw, np.nan_to_num(vals), bw,
               label=label, color=color, alpha=0.8, edgecolor='white')

    ax.set_xticks(x)
    ax.set_xticklabels(plot_coords, rotation=30, ha='right', fontsize=9)
    ax.set_ylabel('Max |Reserve| (N·m or N)', fontsize=11)
    ax.set_title('Reserve Peak Comparison: v1 / v2 / v3 (B_noload)\n'
                 'v3: hand ExternalForce added, foot GRF body-only',
                 fontsize=12, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    # Note about pelvis_ty
    ax.axhline(221, color='gray', lw=0.8, ls=':', alpha=0.5)
    ax.text(len(plot_coords) - 0.5, 225, 'pelvis_tilt v1/v2 = 221 N·m',
            ha='right', va='bottom', fontsize=8, color='gray')
    fig.tight_layout()
    out2 = OUT_DIR / 'phase2c4_v3_reserve_bar_comparison.png'
    fig.savefig(str(out2), dpi=120); plt.close(fig)
    print(f'  Saved: {out2}')

    # ── PLOT 3: ES activation time series ─────────────────────────────────
    print('Plot 3: ES activation time series...')
    KEY_ES = ['IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'LTpL_L5_r', 'LTpL_L5_l']
    fig, axes2 = plt.subplots(len(KEY_ES), 1, figsize=(14, 3 * len(KEY_ES)), sharex=True)
    for ax, muscle in zip(axes2, KEY_ES):
        for label, t, L, d, color, lw in [
            ('v2 (baseline)', t2, l2, d2, '#4575b4', 2.0),
            ('v3 (+hand)',    t3, l3, d3, '#1a9850', 2.5),
        ]:
            arr = get_activation(L, d, muscle)
            if arr is not None:
                ax.plot(t, arr, lw=lw, label=label, color=color)
        for pname, ts, te, pc in [
            ('Eccentric', 1.0, 2.0, '#aec7e8'),
            ('Grasp',     2.0, 2.5, '#ffbb78'),
            ('Concentric',2.5, 4.0, '#98df8a'),
        ]:
            ax.axvspan(ts, te, alpha=0.1, color=pc)
        ax.set_ylim(0, 105)
        ax.set_ylabel('Activation (%)', fontsize=9)
        ax.set_title(muscle, fontsize=10, fontweight='bold')
        ax.legend(fontsize=8, loc='upper right')
        ax.grid(True, alpha=0.3)
    axes2[-1].set_xlabel('Time (s)', fontsize=10)
    axes2[0].set_xlim(1.0, 4.0)
    fig.suptitle('Phase 2.C.4 v3: ES Activation (v2 vs v3 comparison)',
                 fontsize=13, fontweight='bold')
    fig.tight_layout()
    out3 = OUT_DIR / 'phase2c4_v3_es_timeseries.png'
    fig.savefig(str(out3), dpi=120); plt.close(fig)
    print(f'  Saved: {out3}')

    # ── PLOT 4: External force check ───────────────────────────────────────
    print('Plot 4: external force check...')
    ext_tbl    = osim.TimeSeriesTable(str(EXT_V3))
    ext_times  = np.array(list(ext_tbl.getIndependentColumn()))
    ext_labels = list(ext_tbl.getColumnLabels())
    ext_n      = ext_tbl.getNumRows()
    ext_data   = np.zeros((ext_n, len(ext_labels)))
    for i in range(ext_n):
        row = ext_tbl.getRowAtIndex(i)
        for j in range(len(ext_labels)):
            ext_data[i, j] = row[j]

    fig, axes3 = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

    # Hand force profiles
    ax = axes3[0]
    for col, color, label in [
        ('hand_R_force_vy', '#1a9850', 'hand_R upward force (N)'),
        ('hand_L_force_vy', '#d73027', 'hand_L upward force (N)'),
    ]:
        if col in ext_labels:
            idx = ext_labels.index(col)
            ax.plot(ext_times, ext_data[:, idx], lw=2, label=label, color=color)
    ax.axhline(98.1, color='gray', lw=0.8, ls='--', label='98.1 N = box/2')
    ax.set_ylabel('Force (N)', fontsize=10)
    ax.set_title('Hand Force Profile (v3): Upward reaction to box weight', fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-5, 110)

    # GRF vertical (foot only vs foot+box)
    ax = axes3[1]
    grf_cols = ['ground_force_R_vy', 'ground_force_L_vy']
    grf_total = np.zeros(ext_n)
    for col in grf_cols:
        if col in ext_labels:
            idx = ext_labels.index(col)
            grf_total += ext_data[:, idx]
    hand_total = np.zeros(ext_n)
    for col in ['hand_R_force_vy', 'hand_L_force_vy']:
        if col in ext_labels:
            idx = ext_labels.index(col)
            hand_total += ext_data[:, idx]
    total = grf_total + hand_total

    ax.plot(ext_times, grf_total, lw=1.5, label='Foot GRF (body only)', color='#4575b4')
    ax.plot(ext_times, hand_total, lw=1.5, label='Hand forces total', color='#1a9850')
    ax.plot(ext_times, total, lw=2.0, label='Total external Fy', color='#d73027')
    ax.axhline(75 * 9.81, color='gray', lw=0.8, ls=':', label='Body weight (735.8 N)')
    ax.axhline((75 + 20) * 9.81, color='gray', lw=0.8, ls='--', label='Body+box (931.9 N)')
    ax.set_ylabel('Force (N)', fontsize=10)
    ax.set_title('Vertical Force Balance Check (Newton)', fontsize=11)
    ax.legend(fontsize=9, ncol=2)
    ax.grid(True, alpha=0.3)

    # Pelvis_tilt reserve (v2 vs v3)
    ax = axes3[2]
    for label, t, L, d, color, lw in [
        ('v2 (no hand force)', t2, l2, d2, '#4575b4', 2.0),
        ('v3 (+hand force)',   t3, l3, d3, '#1a9850', 2.5),
    ]:
        arr = get_reserve(L, d, 'pelvis_tilt')
        if arr is not None:
            ax.plot(t, arr, lw=lw, label=label, color=color)
    ax.axhline(0, color='k', lw=0.5)
    ax.set_ylabel('pelvis_tilt reserve (N·m)', fontsize=10)
    ax.set_title('pelvis_tilt Reserve: v2 vs v3 (Expected: decrease, Actual: INCREASE)',
                 fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    # Annotation
    ax.text(2.5, -260, 'v3 WORSE than v2\nGRF mismatch dominates',
            ha='center', va='top', fontsize=10, color='#d73027',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    axes3[-1].set_xlabel('Time (s)', fontsize=10)
    axes3[0].set_xlim(ext_times[0], ext_times[-1])
    fig.suptitle('Phase 2.C.4 v3: External Force Verification + Reserve Effect',
                 fontsize=13, fontweight='bold')
    fig.tight_layout()
    out4 = OUT_DIR / 'phase2c4_v3_external_force_check.png'
    fig.savefig(str(out4), dpi=120); plt.close(fig)
    print(f'  Saved: {out4}')

    print()
    print(f'All plots saved to: {OUT_DIR}')
    print('=== Analysis complete ===')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'FATAL: {e}')
        import traceback; traceback.print_exc()
        import sys; sys.exit(1)
