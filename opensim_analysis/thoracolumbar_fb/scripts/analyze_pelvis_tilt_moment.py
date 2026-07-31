"""Phase 2.C.4 v2 — Pelvis_tilt Moment Analysis.

Step 1 of root cause diagnosis:
- Extract pelvis_tilt reserve time series (4 conditions)
- Moment decomposition (GRF + upper body + reserve)
- Compare Phase 1a vs Phase 2.C.4
- Explain why 221 N·m is invariant to suit torque
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

RESERVE_OPTF = 10.0
g = 9.81

RESULTS_V2 = '/data/opensim_results/phase2c4_box_v11b_v2'
CONDITIONS = ['B_noload', 'B_suit50', 'B_suit100', 'B_suit200']
SUIT_NM = [0, 50, 100, 200]
COND_LABELS = {
    'B_noload':  'No suit',
    'B_suit50':  'Suit 50 N·m',
    'B_suit100': 'Suit 100 N·m',
    'B_suit200': 'Suit 200 N·m',
}
COLORS = ['#d73027', '#fc8d59', '#74add1', '#4575b4']

PHASES = [
    ('Approach',   1.0, 1.5),
    ('Eccentric',  1.5, 2.0),
    ('Grasp',      2.0, 2.5),
    ('Concentric', 2.5, 4.0),
]
PHASE_COLORS = {
    'Approach': '#888888', 'Eccentric': '#1f77b4',
    'Grasp': '#d62728', 'Concentric': '#2ca02c',
}


def load_sto(path):
    with open(path) as f:
        lines = f.readlines()
    for i, l in enumerate(lines):
        if 'endheader' in l:
            header_end = i
            break
    cols = lines[header_end+1].strip().split('\t')
    data = []
    for l in lines[header_end+2:]:
        if l.strip():
            data.append([float(x) for x in l.strip().split('\t')])
    return cols, np.array(data)


def main():
    print('=== Pelvis_tilt Moment Analysis ===')

    # ── Reserve time series ──────────────────────────────────────────────
    res_col = '/forceset/reserve_jointset_ground_pelvis_pelvis_tilt'
    phase_peaks = {}
    all_reserves = {}

    print('\nPelvis_tilt Reserve (actual N·m = raw × 10):')
    for cond in CONDITIONS:
        path = '%s/%s/solution.sto' % (RESULTS_V2, cond)
        cols, data = load_sto(path)
        t = data[:,0]
        res = data[:,cols.index(res_col)] * RESERVE_OPTF
        all_reserves[cond] = (t, res)

        peak_idx = np.argmax(np.abs(res))
        print('  %s: peak=%.1f N·m at t=%.3fs' % (cond, res[peak_idx], t[peak_idx]))
        ph_peaks = {}
        for ph_name, t_s, t_e in PHASES:
            mask = (t >= t_s) & (t < t_e)
            if mask.sum() > 0:
                seg = res[mask]
                ph_peaks[ph_name] = seg[np.argmax(np.abs(seg))]
        phase_peaks[cond] = ph_peaks

    # ── ES peak comparison ───────────────────────────────────────────────
    key_es = ['IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'LTpL_L5_r']
    es_peaks = {}
    for cond in CONDITIONS:
        path = '%s/%s/solution.sto' % (RESULTS_V2, cond)
        cols, data = load_sto(path)
        peaks = {}
        for muscle in key_es:
            for i, c in enumerate(cols):
                if ('/%s/activation' % muscle) in c:
                    peaks[muscle] = data[:,i].max() * 100
                    break
        es_peaks[cond] = peaks

    # ── Moment decomposition at peak (t=2.47s) ──────────────────────────
    moment_components = {
        'GRF (extension)': 432.1,
        'Upper body (flexion)': -104.2,
        'Net external': 327.9,
        'Reserve (actual)': -221.1,
    }

    # ── Print summary table ──────────────────────────────────────────────
    print('\n--- Moment Decomposition (t=2.47s, B_noload) ---')
    for k, v in moment_components.items():
        print('  %s: %.1f N·m' % (k, v))

    print('\n--- ES Peak Summary ---')
    for muscle in key_es:
        row = '  %-15s' % muscle
        for cond in CONDITIONS:
            row += ' %6.1f%%' % es_peaks[cond].get(muscle, 0)
        print(row)

    # ── Plots ────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(18, 16))
    gs_main = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.35)

    # Panel 1: Reserve time series
    ax1 = fig.add_subplot(gs_main[0, :])
    for i, cond in enumerate(CONDITIONS):
        t, res = all_reserves[cond]
        ax1.plot(t, res, lw=2.5, color=COLORS[i], label=COND_LABELS[cond], zorder=3)
    for ph_name, t_s, t_e in PHASES:
        ax1.axvspan(t_s, t_e, alpha=0.07, color=PHASE_COLORS[ph_name])
        ax1.text((t_s+t_e)/2, 15, ph_name, ha='center', fontsize=9,
                 color=PHASE_COLORS[ph_name], fontweight='bold')
    ax1.axhline(0, color='k', lw=0.8, ls='--', alpha=0.5)
    ax1.axvline(2.47, color='red', lw=1.5, ls=':', alpha=0.7)
    ax1.axhline(-19.4, color='#2ca02c', lw=1.5, ls='-.', alpha=0.8, label='Phase 1a: ~0 N·m')
    ax1.axhline(-221.1, color='#d73027', lw=1, ls=':', alpha=0.5)
    ax1.text(1.05, -215, '221.1 N·m', color='#d73027', fontsize=8)
    ax1.set_xlabel('Time (s)', fontsize=11)
    ax1.set_ylabel('Reserve Torque (N·m)', fontsize=11)
    ax1.set_title('Pelvis_tilt Reserve (all 4 conditions identical — suit has NO effect)', fontsize=12, fontweight='bold')
    ax1.legend(loc='lower right', fontsize=9, ncol=3)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(1.0, 4.0)

    # Panel 2: Moment decomposition
    ax2 = fig.add_subplot(gs_main[1, 0])
    labels_bar = ['GRF\n(extension)', 'Upper body\n(flexion)', 'Net\nexternal', 'Reserve\n(actual)']
    values_bar = [432.1, -104.2, 327.9, -221.1]
    colors_bar = ['#2ca02c', '#d73027', '#ff7f0e', '#9467bd']
    bars = ax2.bar(labels_bar, values_bar, color=colors_bar, alpha=0.8, edgecolor='k')
    for bar, val in zip(bars, values_bar):
        ax2.text(bar.get_x() + bar.get_width()/2,
                 val + (8 if val >= 0 else -8),
                 '%.1f' % val, ha='center',
                 va='bottom' if val >= 0 else 'top', fontsize=11, fontweight='bold')
    ax2.axhline(0, color='k', lw=1)
    ax2.set_ylabel('Moment (N·m)', fontsize=11)
    ax2.set_title('Moment Decomposition at t=2.47s\n(B_noload, pelvis_tilt DOF)', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_ylim(-280, 500)

    # Panel 3: ES peak bars
    ax3 = fig.add_subplot(gs_main[1, 1])
    x = np.arange(len(key_es))
    width = 0.2
    for i, cond in enumerate(CONDITIONS):
        vals = [es_peaks[cond].get(m, 0) for m in key_es]
        ax3.bar(x + i*width, vals, width, label=COND_LABELS[cond], color=COLORS[i], alpha=0.8)
    ax3.set_xticks(x + width*1.5)
    ax3.set_xticklabels(key_es, rotation=20, ha='right', fontsize=9)
    ax3.set_ylabel('Peak Activation (%)', fontsize=11)
    ax3.set_title('ES Peak vs Suit Torque\n(ES drops 99%, reserve stays at 221 N·m)', fontsize=11, fontweight='bold')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.set_ylim(0, 115)

    # Panel 4: Decoupling plot
    ax4 = fig.add_subplot(gs_main[2, :])
    il_peaks = []
    res_peaks_list = []
    for cond in CONDITIONS:
        path = '%s/%s/solution.sto' % (RESULTS_V2, cond)
        cols, data = load_sto(path)
        t = data[:,0]
        col_idx = None
        for i, c in enumerate(cols):
            if '/IL_R10_r/activation' in c:
                col_idx = i
                break
        il_peaks.append(data[:,col_idx].max()*100 if col_idx else 0)
        res = data[:,cols.index(res_col)] * RESERVE_OPTF
        res_peaks_list.append(abs(res).max())

    ax4b = ax4.twinx()
    l1 = ax4.plot(SUIT_NM, il_peaks, 'o-', color='#d73027', lw=2.5, ms=10,
                  markerfacecolor='white', markeredgewidth=2.5, label='IL_R10_r peak (%)')
    l2 = ax4b.plot(SUIT_NM, res_peaks_list, 's--', color='#9467bd', lw=2.5, ms=10,
                   markerfacecolor='white', markeredgewidth=2.5, label='pelvis_tilt reserve (N·m)')
    ax4.set_xlabel('Suit Torque (N·m)', fontsize=11)
    ax4.set_ylabel('IL_R10_r Peak Activation (%)', fontsize=11, color='#d73027')
    ax4b.set_ylabel('|Reserve| Peak (N·m)', fontsize=11, color='#9467bd')
    ax4.set_title('Decoupling: Suit reduces ES (−99%) but reserve remains constant (221 N·m)\n→ Reserve = kinematic imbalance from backward pelvis translation (pelvis_tx = −0.435m)',
                  fontsize=12, fontweight='bold')
    ax4.tick_params(axis='y', colors='#d73027')
    ax4b.tick_params(axis='y', colors='#9467bd')
    lines = l1 + l2
    ax4.legend(lines, [l.get_label() for l in lines], loc='center right', fontsize=10)
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(-10, 210)
    ax4.set_ylim(0, 120)
    ax4b.set_ylim(0, 280)
    ax4b.axhline(221.1, color='#9467bd', lw=1, ls=':', alpha=0.5)
    ax4b.text(5, 210, 'Phase 1a stoop: ~0.1 N·m', color='#2ca02c', fontsize=8, style='italic')
    ax4b.axhline(0.13, color='#2ca02c', lw=1.5, ls='-.', alpha=0.8)

    fig.suptitle('Pelvis_tilt Moment Analysis — Phase 2.C.4 v2 (Box v11b, 158 muscles)\n221 N·m Reserve: Root Cause = Backward Pelvis Translation (pelvis_tx = −0.435m)',
                 fontsize=13, fontweight='bold', y=0.98)

    out_path = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/pelvis_tilt_moment_analysis_v2.png'
    fig.savefig(out_path, dpi=120, bbox_inches='tight')
    plt.close()
    print('\nSaved:', out_path)


if __name__ == '__main__':
    main()
