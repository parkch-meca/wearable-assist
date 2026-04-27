"""Polished publication-quality figures for Phase 1a Full results.

Inputs:
  /data/wearable-assist/results/phase1a_full/solution.sto

Outputs:
  /data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase1a_full/
    figure_5phase_activation.png   — 5-phase × 5 muscles bar chart (paper figure)
    figure_summary_polished.png    — 4-panel composite (suppl. figure)
"""
import os
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm

SOL = '/data/wearable-assist/results/phase1a_full/solution.sto'
OUT = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase1a_full')
OUT.mkdir(parents=True, exist_ok=True)

PHASES = [
    ('Quiet',      0.0, 1.0, '#888888'),
    ('Eccentric',  1.0, 2.0, '#1f77b4'),
    ('Hold',       2.0, 2.5, '#d62728'),
    ('Concentric', 2.5, 4.0, '#2ca02c'),
    ('Recovery',   4.0, 5.0, '#ff7f0e'),
]

KEY = ['IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'LTpL_L5_r', 'LTpL_L5_l']
LABELS_DISPLAY = {  # nicer labels for x-axis
    'IL_R10_r': 'IL\nR10 (R)',
    'IL_R10_l': 'IL\nR10 (L)',
    'IL_R11_r': 'IL\nR11 (R)',
    'LTpL_L5_r': 'LTpL\nL5 (R)',
    'LTpL_L5_l': 'LTpL\nL5 (L)',
}


def load_col(tbl, idx):
    n = tbl.getNumRows()
    out = np.zeros(n)
    for i in range(n):
        out[i] = tbl.getRowAtIndex(i)[idx]
    return out


def find_act(labels, name):
    for i, L in enumerate(labels):
        if L.endswith(f'/{name}/activation'):
            return i
    return None


def main():
    tbl = osim.TimeSeriesTable(SOL)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())

    acts = {}
    for nm in KEY:
        i = find_act(labels, nm)
        if i is not None:
            acts[nm] = load_col(tbl, i) * 100

    # --- Figure A: 5-phase × 5 muscles bar chart with std error bars ---
    fig, ax = plt.subplots(figsize=(11, 6.5))
    bar_w = 0.16
    x = np.arange(len(KEY))

    # For each phase, plot bars with std error
    for pi, (pname, ts, te, color) in enumerate(PHASES):
        mask = (times >= ts) & (times < te)
        if pi == len(PHASES) - 1:
            mask = (times >= ts) & (times <= te)
        means = []
        stds = []
        for nm in KEY:
            c = acts.get(nm, np.zeros_like(times))
            means.append(float(c[mask].mean()))
            stds.append(float(c[mask].std()))
        offset = (pi - 2) * bar_w
        bars = ax.bar(x + offset, means, bar_w, yerr=stds,
                      label=f'{pname} ({ts:.1f}–{te:.1f}s)',
                      color=color, ecolor='#444', capsize=3,
                      edgecolor='black', linewidth=0.5)
        # peak label on top of bar
        for j, (m_, s_) in enumerate(zip(means, stds)):
            if m_ > 5:
                ax.text(x[j] + offset, m_ + s_ + 1.2,
                        f'{m_:.0f}', ha='center', fontsize=8, color=color, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels([LABELS_DISPLAY[k] for k in KEY], fontsize=11)
    ax.set_ylabel('Mean activation (% MVC)', fontsize=12)
    ax.set_ylim(0, 100)
    ax.set_title('Phase-wise erector spinae activation during stoop lifting (Phase 1a Full)',
                 fontsize=13, fontweight='bold', pad=12)
    ax.legend(loc='upper right', fontsize=10, framealpha=0.95, ncol=1)
    ax.grid(True, alpha=0.3, axis='y')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # subtitle
    ax.text(0.01, -0.13,
            'Mean ± SD over each phase. Error bars show within-phase activation variability.\n'
            'Hold (2.0–2.5 s) and Concentric (2.5–4.0 s) phases impose ~30 %p more demand than Eccentric (1.0–2.0 s).',
            transform=ax.transAxes, fontsize=9, color='#444')

    fig.tight_layout()
    out_a = OUT / 'figure_5phase_activation.png'
    fig.savefig(out_a, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved {out_a}')

    # --- Figure B: 4-panel polished composite ---
    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.25)

    # Panel 1: ES time-series with phase shading
    ax1 = fig.add_subplot(gs[0, 0])
    plot_set = ['IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'LTpL_L5_r', 'LTpL_L5_l']
    palette = cm.tab10(np.linspace(0, 1, len(plot_set)))
    for c_, nm in zip(palette, plot_set):
        if nm in acts:
            ax1.plot(times, acts[nm], lw=1.8, color=c_, label=nm.replace('_', ' '))
    for pname, ts, te, color in PHASES:
        ax1.axvspan(ts, te, alpha=0.12, color=color)
        ax1.text((ts + te) / 2, 96, pname, ha='center', va='top',
                 fontsize=8.5, fontweight='bold', color='#333')
    ax1.set_xlim(0, 5)
    ax1.set_ylim(0, 100)
    ax1.set_xlabel('Time (s)', fontsize=11)
    ax1.set_ylabel('Activation (%)', fontsize=11)
    ax1.set_title('A. ES activation time-series (5 phases shaded)',
                  fontsize=11, fontweight='bold', loc='left')
    ax1.legend(fontsize=8, loc='upper left', framealpha=0.92, ncol=1)
    ax1.grid(True, alpha=0.3)
    ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)

    # Panel 2: 5-phase bar (compact)
    ax2 = fig.add_subplot(gs[0, 1])
    bar_w = 0.16
    x = np.arange(len(KEY))
    for pi, (pname, ts, te, color) in enumerate(PHASES):
        mask = (times >= ts) & (times < te)
        if pi == len(PHASES) - 1:
            mask = (times >= ts) & (times <= te)
        means = [acts.get(nm, np.zeros_like(times))[mask].mean() for nm in KEY]
        offset = (pi - 2) * bar_w
        ax2.bar(x + offset, means, bar_w, label=pname,
                color=color, edgecolor='black', linewidth=0.4)
    ax2.set_xticks(x)
    ax2.set_xticklabels([k.replace('_','\n') for k in KEY], fontsize=8.5)
    ax2.set_ylabel('Mean activation (%)', fontsize=11)
    ax2.set_ylim(0, 100)
    ax2.set_title('B. 5-phase mean activation', fontsize=11, fontweight='bold', loc='left')
    ax2.legend(fontsize=8, ncol=2, loc='upper right', framealpha=0.92)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)

    # Panel 3: Eccentric vs Concentric scatter with delta annotations
    ax3 = fig.add_subplot(gs[1, 0])
    plot_muscles = ['IL_R10_r','IL_R10_l','IL_R11_r','IL_R12_r','LTpL_L5_r','LTpL_L5_l']
    ecc_means = []; con_means = []
    for nm in plot_muscles:
        if nm not in acts:
            ecc_means.append(0); con_means.append(0); continue
        c = acts[nm]
        ecc_means.append(c[(times>=1.0)&(times<2.0)].mean())
        con_means.append(c[(times>=2.5)&(times<=4.0)].mean())
    pos = np.arange(len(plot_muscles))
    ax3.bar(pos - 0.2, ecc_means, 0.4, label='Eccentric (1.0–2.0 s)',
            color='#1f77b4', edgecolor='black', linewidth=0.4)
    ax3.bar(pos + 0.2, con_means, 0.4, label='Concentric (2.5–4.0 s)',
            color='#2ca02c', edgecolor='black', linewidth=0.4)
    for i in range(len(plot_muscles)):
        delta = con_means[i] - ecc_means[i]
        ax3.annotate(f'Δ{delta:+.0f} %p', xy=(i, max(ecc_means[i], con_means[i]) + 4),
                     ha='center', fontsize=9, fontweight='bold', color='#222')
    ax3.set_xticks(pos)
    ax3.set_xticklabels([m.replace('_','\n') for m in plot_muscles], fontsize=8.5)
    ax3.set_ylabel('Mean activation (%)', fontsize=11)
    ax3.set_ylim(0, 100)
    ax3.set_title('C. Eccentric vs Concentric asymmetry', fontsize=11, fontweight='bold', loc='left')
    ax3.legend(fontsize=9, loc='upper right')
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.spines['top'].set_visible(False); ax3.spines['right'].set_visible(False)

    # Panel 4: Reserve category breakdown at peak
    ax4 = fig.add_subplot(gs[1, 1])
    cats = ['spine_FE','spine_LB','spine_AR','pelvis','hip','knee','ankle']
    cat_vals = [19.4, 2.6, 5.8, 52.3, 31.1, 157.6, 36.6]  # from full_report
    cat_colors = ['#d62728','#1f77b4','#9467bd','#8c564b','#e377c2','#7f7f7f','#17becf']
    bars = ax4.bar(cats, cat_vals, color=cat_colors,
                    edgecolor='black', linewidth=0.4)
    for b, v in zip(bars, cat_vals):
        ax4.text(b.get_x() + b.get_width()/2, v + 3, f'{v:.0f}',
                  ha='center', fontsize=9, fontweight='bold')
    ax4.set_ylabel('Reserve generated (Nm or N)', fontsize=11)
    ax4.set_xticklabels(cats, rotation=20, fontsize=9)
    ax4.set_title('D. Reserve usage @ peak (t=2.5 s)', fontsize=11, fontweight='bold', loc='left')
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.spines['top'].set_visible(False); ax4.spines['right'].set_visible(False)
    # Annotation
    ax4.text(0.97, 0.92,
             'Spine FE 19.4 Nm matches SO R10 (22 Nm).\n'
             'Knee 158 Nm: leg muscles excluded in Phase 1a.',
             transform=ax4.transAxes, ha='right', va='top', fontsize=8.5,
             color='#555', bbox=dict(boxstyle='round,pad=0.4', fc='#f8f8f8', ec='#bbb'))

    fig.suptitle(
        'Phase 1a Full — MocoInverse with GRF (114 muscles, 5 s motion, mesh 50, IPOPT Optimal in 140 s)',
        fontsize=13, fontweight='bold')

    out_b = OUT / 'figure_summary_polished.png'
    fig.savefig(out_b, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved {out_b}')


if __name__ == '__main__':
    main()
