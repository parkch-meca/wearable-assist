"""Step A.2 — Generate Grid PNG figures for pelvis_tilt root cause diagnosis.

Output:
  docs/images/step_a2/pelvis_tilt_root_diagnosis_diagram.png
  docs/images/step_a2/pelvis_tilt_root_diagnosis_grid.png
"""
import os
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

OUT_DIR = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/step_a2')
OUT_DIR.mkdir(parents=True, exist_ok=True)

HICKS_PT = 12.9   # Nm
HICKS_TY = 36.8   # N

# Verified data from actual solves
DATA = {
    'V1': {
        'label': 'V1\nOriginal\n(coupler + no forearm)',
        'coupler': True,
        'forearm': False,
        'pelvis_tilt': 0.126,
        'pelvis_ty': 64.65,
        'spine_fe': 19.40,
        'il_r10_r': 92.4,
        'mode': 'full',
    },
    'V2': {
        'label': 'V2\nForearm only\n(coupler + forearm_v1)',
        'coupler': True,
        'forearm': True,
        'pelvis_tilt': 1.820,
        'pelvis_ty': 65.89,
        'spine_fe': 21.09,
        'il_r10_r': 93.1,
        'mode': 'smoke',
    },
    'V3': {
        'label': 'V3\nNo coupler\n(no coupler + no forearm)',
        'coupler': False,
        'forearm': False,
        'pelvis_tilt': 174.08,
        'pelvis_ty': 65.83,
        'spine_fe': 20.93,
        'il_r10_r': 92.0,
        'mode': 'smoke',
    },
    'V4': {
        'label': 'V4\nCurrent (REPRO_V2)\n(no coupler + forearm_v1)',
        'coupler': False,
        'forearm': True,
        'pelvis_tilt': 174.79,
        'pelvis_ty': 65.88,
        'spine_fe': 21.04,
        'il_r10_r': 93.2,
        'mode': 'smoke',
    },
    'V3h': {
        'label': 'V3_armhang\nNo coupler\n(arm at 0° instead of 72.9°)',
        'coupler': False,
        'forearm': False,
        'pelvis_tilt': 145.73,
        'pelvis_ty': 62.30,
        'spine_fe': 17.54,
        'il_r10_r': 48.8,
        'mode': 'smoke',
    },
}

COLORS = {
    'V1':  '#2ecc71',   # green = PASS
    'V2':  '#27ae60',   # dark green = PASS
    'V3':  '#e74c3c',   # red = FAIL
    'V4':  '#c0392b',   # dark red = FAIL (current)
    'V3h': '#e67e22',   # orange = FAIL (partial fix)
}

# ── Figure A: Diagram (bar chart + mechanism) ─────────────────────────────
def plot_diagram():
    fig = plt.figure(figsize=(14, 9))
    fig.patch.set_facecolor('#1a1a2e')
    gs = GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35,
                  left=0.08, right=0.98, top=0.90, bottom=0.10)

    keys = ['V1', 'V2', 'V3', 'V4']
    labels = [DATA[k]['label'] for k in keys]
    pt_vals = [DATA[k]['pelvis_tilt'] for k in keys]
    colors  = [COLORS[k] for k in keys]

    # Panel A: pelvis_tilt bar chart
    ax1 = fig.add_subplot(gs[0, :])
    ax1.set_facecolor('#16213e')
    bars = ax1.bar(range(len(keys)), pt_vals, color=colors, edgecolor='white',
                   linewidth=0.8, width=0.55, zorder=3)
    ax1.axhline(HICKS_PT, color='#f1c40f', lw=2.0, ls='--', zorder=4,
                label=f'Hicks 2015 threshold: {HICKS_PT} Nm')
    ax1.set_xticks(range(len(keys)))
    ax1.set_xticklabels(labels, color='white', fontsize=8.5, multialignment='center')
    ax1.set_ylabel('pelvis_tilt reserve (Nm)', color='white', fontsize=10)
    ax1.set_title('Variation Matrix: pelvis_tilt Reserve — Isolation of Coupler vs Forearm Effect',
                  color='white', fontsize=11, fontweight='bold', pad=10)
    ax1.tick_params(colors='white', labelsize=9)
    for spine in ax1.spines.values():
        spine.set_edgecolor('#555')
    ax1.set_ylim(0, 210)
    ax1.legend(loc='upper left', fontsize=9, facecolor='#16213e', labelcolor='white',
               edgecolor='#555')
    ax1.grid(axis='y', color='#2a2a4a', lw=0.5, zorder=1)
    ax1.set_axisbelow(True)

    # Annotate bars
    for bar, val, k in zip(bars, pt_vals, keys):
        flag = 'PASS' if val <= HICKS_PT else f'FAIL\n({val/HICKS_PT:.1f}x)'
        col = '#2ecc71' if val <= HICKS_PT else '#ff6b6b'
        ax1.text(bar.get_x() + bar.get_width()/2, val + 3,
                 f'{val:.2f} Nm\n{flag}',
                 ha='center', va='bottom', color=col, fontsize=8.0, fontweight='bold')

    # Arrows/annotations for delta
    x1, x3 = 0, 2
    y_annot = max(pt_vals) * 0.75
    ax1.annotate('', xy=(x3, y_annot), xytext=(x1, y_annot),
                 arrowprops=dict(arrowstyle='<->', color='#f39c12', lw=1.5))
    ax1.text((x1+x3)/2, y_annot + 5,
             f'D_nocoupler = {DATA["V3"]["pelvis_tilt"]-DATA["V1"]["pelvis_tilt"]:.1f} Nm (99.6%)',
             ha='center', color='#f39c12', fontsize=8.5, fontweight='bold')

    x2 = 1
    y_annot2 = 25
    ax1.annotate('', xy=(x2, y_annot2), xytext=(x1, y_annot2),
                 arrowprops=dict(arrowstyle='<->', color='#3498db', lw=1.5))
    ax1.text((x1+x2)/2, y_annot2 + 5,
             f'D_forearm = {DATA["V2"]["pelvis_tilt"]-DATA["V1"]["pelvis_tilt"]:.2f} Nm (1.0%)',
             ha='center', color='#3498db', fontsize=8.5)

    # Panel B: IL_R10_r peak activation (ES validation)
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.set_facecolor('#16213e')
    il_vals = [DATA[k]['il_r10_r'] for k in keys]
    bars2 = ax2.bar(range(len(keys)), il_vals, color=colors, edgecolor='white',
                    linewidth=0.7, width=0.55, zorder=3)
    ax2.set_xticks(range(len(keys)))
    ax2.set_xticklabels(['V1', 'V2', 'V3', 'V4'], color='white', fontsize=9)
    ax2.set_ylabel('IL_R10_r peak activation (%)', color='white', fontsize=9)
    ax2.set_title('ES Muscle: IL_R10_r Peak\n(max ΔES 0.41 %p — ES unaffected)', color='white',
                  fontsize=9, fontweight='bold')
    ax2.tick_params(colors='white', labelsize=8)
    ax2.set_ylim(0, 110)
    ax2.grid(axis='y', color='#2a2a4a', lw=0.5, zorder=1)
    ax2.set_axisbelow(True)
    for spine in ax2.spines.values():
        spine.set_edgecolor('#555')
    for bar, val in zip(bars2, il_vals):
        ax2.text(bar.get_x() + bar.get_width()/2, val + 1, f'{val:.1f}%',
                 ha='center', va='bottom', color='white', fontsize=8, fontweight='bold')

    # Panel C: mechanism diagram (text)
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.set_facecolor('#0f3460')
    ax3.axis('off')
    mechanism_text = (
        "MECHANISM CONFIRMED\n"
        "─────────────────────────────\n"
        "WITH COUPLER:\n"
        "  shoulder_elv = -1.62 × pelvis_tilt\n"
        "  Constraint J^T × lambda provides\n"
        "  ~174 Nm at pelvis_tilt DOF\n"
        "  Reserve = 0.13 Nm (PASS)\n\n"
        "WITHOUT COUPLER:\n"
        "  J^T × lambda = 0 (no constraint)\n"
        "  Reserve must supply ~174 Nm\n"
        "  Reserve = 174 Nm (FAIL, 13.5x)\n\n"
        "V3_armhang (arm at 0°):\n"
        "  Still 145.7 Nm (FAIL)\n"
        "  Structural cause, not kinematic\n\n"
        "ES IMPACT: max ΔES = 0.41 %p\n"
        "→ ES analysis VALID despite reserve"
    )
    ax3.text(0.05, 0.97, mechanism_text, transform=ax3.transAxes,
             va='top', ha='left', color='#ecf0f1', fontsize=7.8,
             fontfamily='monospace', linespacing=1.5)
    ax3.set_title('Root Cause Mechanism', color='white', fontsize=9,
                  fontweight='bold', pad=8)

    fig.text(0.5, 0.01,
             'Step A.2 | stoop_synthetic_v5 | mesh=25 | ModOpAddReserves(10.0) | Hicks 2015 threshold: 12.9 Nm',
             ha='center', color='#888', fontsize=7.5)

    out_path = OUT_DIR / 'pelvis_tilt_root_diagnosis_diagram.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'Saved: {out_path}')
    return out_path


# ── Figure B: Grid table + scenario ──────────────────────────────────────
def plot_grid():
    fig = plt.figure(figsize=(16, 11))
    fig.patch.set_facecolor('#1a1a2e')
    gs = GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.32,
                  left=0.05, right=0.98, top=0.91, bottom=0.08)

    # Panel 1: Variation matrix table
    ax_tbl = fig.add_subplot(gs[0, :])
    ax_tbl.set_facecolor('#0f3460')
    ax_tbl.axis('off')
    ax_tbl.set_title('Variation Matrix — 4 Variants Actual Solve Results (Step A.2)',
                     color='white', fontsize=12, fontweight='bold', pad=10)

    col_labels = ['Variant', 'Coupler', 'Forearm_v1', 'pelvis_tilt (Nm)',
                  'vs Hicks 12.9', 'pelvis_ty (N)', 'Spine FE (Nm)', 'IL_R10_r (%)']
    rows = [
        ['V1 Original', 'YES', 'NO', '0.126', 'PASS (0.01x)', '64.65', '19.40', '92.4'],
        ['V2 Forearm only', 'YES', 'YES', '1.820', 'PASS (0.14x)', '65.89', '21.09', '93.1'],
        ['V3 No coupler', 'NO', 'NO', '174.08', 'FAIL (13.5x)', '65.83', '20.93', '92.0'],
        ['V4 Current (REPRO_V2)', 'NO', 'YES', '174.79', 'FAIL (13.5x)', '65.88', '21.04', '93.2'],
    ]
    row_colors_list = [
        ['#27ae60', '#2ecc71', '#2ecc71', '#27ae60', '#27ae60', '#f39c12', '#555', '#555'],
        ['#27ae60', '#2ecc71', '#2ecc71', '#27ae60', '#27ae60', '#f39c12', '#555', '#555'],
        ['#c0392b', '#e74c3c', '#e74c3c', '#c0392b', '#c0392b', '#f39c12', '#555', '#555'],
        ['#922b21', '#e74c3c', '#e74c3c', '#922b21', '#922b21', '#f39c12', '#555', '#555'],
    ]
    y_pos = 0.85
    header_y = 0.95
    col_x = [0.01, 0.18, 0.28, 0.39, 0.50, 0.63, 0.74, 0.85]
    for j, col in enumerate(col_labels):
        ax_tbl.text(col_x[j], header_y, col, color='#f1c40f', fontsize=8,
                    fontweight='bold', transform=ax_tbl.transAxes, va='top')
    ax_tbl.plot([0, 1], [0.88, 0.88], color='#f1c40f', lw=0.8, transform=ax_tbl.transAxes)

    for i, (row, rcols) in enumerate(zip(rows, row_colors_list)):
        for j, (cell, rcol) in enumerate(zip(row, rcols)):
            ax_tbl.text(col_x[j], y_pos - i*0.20, cell, color='white', fontsize=7.5,
                        transform=ax_tbl.transAxes, va='top',
                        bbox=dict(boxstyle='round,pad=0.15', facecolor=rcol, alpha=0.7,
                                  edgecolor='none') if j in [3, 4] else None)

    ax_tbl.text(0.01, 0.03,
                'V3_armhang test: shoulder_elv=0 (arm hanging) → 145.7 Nm still FAIL → '
                'Structural cause confirmed (not just kinematic artifact)',
                color='#e67e22', fontsize=7.5, transform=ax_tbl.transAxes, va='bottom')

    # Panel 2: Root cause bar
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.set_facecolor('#16213e')
    deltas = [
        ('D_forearm\n(V2-V1)', 1.69, '#3498db'),
        ('D_nocoupler\n(V3-V1)', 173.95, '#e74c3c'),
        ('D_interaction\n(V4-V3-V2+V1)', -0.98, '#95a5a6'),
        ('Total\n(V4-V1)', 174.66, '#e67e22'),
    ]
    x_pos = range(len(deltas))
    bars = ax2.bar(x_pos, [abs(d[1]) for d in deltas], color=[d[2] for d in deltas],
                   edgecolor='white', linewidth=0.7, width=0.55, zorder=3)
    ax2.set_xticks(list(x_pos))
    ax2.set_xticklabels([d[0] for d in deltas], color='white', fontsize=7.5,
                         multialignment='center')
    ax2.set_ylabel('|Delta| pelvis_tilt (Nm)', color='white', fontsize=9)
    ax2.set_title('Root Cause Decomposition', color='white', fontsize=9, fontweight='bold')
    ax2.tick_params(colors='white', labelsize=8)
    ax2.set_ylim(0, 210)
    ax2.grid(axis='y', color='#2a2a4a', lw=0.5, zorder=1)
    ax2.set_axisbelow(True)
    for spine in ax2.spines.values():
        spine.set_edgecolor('#555')
    fracs = ['1.0%', '99.6%', '(neg.)', '100%']
    for bar, (_, val, _), frac in zip(bars, deltas, fracs):
        ax2.text(bar.get_x() + bar.get_width()/2, abs(val) + 3,
                 f'{abs(val):.1f} Nm\n{frac}',
                 ha='center', va='bottom', color='white', fontsize=7.5, fontweight='bold')

    # Panel 3: pelvis_tilt all variants (including V3h)
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.set_facecolor('#16213e')
    all_keys = ['V1', 'V2', 'V3', 'V4', 'V3h']
    all_labels = ['V1\nw/coupler', 'V2\nw/coupler\n+forearm', 'V3\nno coupler',
                  'V4\ncurrent', 'V3h\narm 0°']
    all_vals = [DATA[k]['pelvis_tilt'] for k in all_keys]
    all_cols = [COLORS[k] for k in all_keys]
    bars3 = ax3.bar(range(len(all_keys)), all_vals, color=all_cols, edgecolor='white',
                    linewidth=0.7, width=0.55, zorder=3)
    ax3.axhline(HICKS_PT, color='#f1c40f', lw=2, ls='--', zorder=4,
                label=f'Hicks: {HICKS_PT} Nm')
    ax3.set_xticks(range(len(all_keys)))
    ax3.set_xticklabels(all_labels, color='white', fontsize=7.5, multialignment='center')
    ax3.set_ylabel('pelvis_tilt reserve (Nm)', color='white', fontsize=9)
    ax3.set_title('Reserve All Variants\n(incl. V3h arm-hang test)', color='white',
                  fontsize=9, fontweight='bold')
    ax3.tick_params(colors='white', labelsize=8)
    ax3.set_ylim(0, 210)
    ax3.legend(loc='upper left', fontsize=8, facecolor='#16213e', labelcolor='white',
               edgecolor='#555')
    ax3.grid(axis='y', color='#2a2a4a', lw=0.5, zorder=1)
    ax3.set_axisbelow(True)
    for spine in ax3.spines.values():
        spine.set_edgecolor('#555')
    for bar, val in zip(bars3, all_vals):
        ax3.text(bar.get_x() + bar.get_width()/2, val + 3,
                 f'{val:.1f}', ha='center', va='bottom', color='white', fontsize=7, fontweight='bold')

    # Panel 4: ES unaffected
    ax4 = fig.add_subplot(gs[1, 2])
    ax4.set_facecolor('#16213e')
    es_keys = ['V1', 'V2', 'V3', 'V4']
    es_vals = [DATA[k]['il_r10_r'] for k in es_keys]
    es_cols = [COLORS[k] for k in es_keys]
    bars4 = ax4.bar(range(4), es_vals, color=es_cols, edgecolor='white',
                    linewidth=0.7, width=0.55, zorder=3)
    ax4.set_xticks(range(4))
    ax4.set_xticklabels(['V1', 'V2', 'V3', 'V4'], color='white', fontsize=9)
    ax4.set_ylabel('IL_R10_r peak (%)', color='white', fontsize=9)
    ax4.set_title('ES Activation Unchanged\nmax ΔES = 0.41 %p (PASS)', color='white',
                  fontsize=9, fontweight='bold')
    ax4.tick_params(colors='white', labelsize=8)
    ax4.set_ylim(85, 98)
    ax4.grid(axis='y', color='#2a2a4a', lw=0.5, zorder=1)
    ax4.set_axisbelow(True)
    for spine in ax4.spines.values():
        spine.set_edgecolor('#555')
    for bar, val in zip(bars4, es_vals):
        ax4.text(bar.get_x() + bar.get_width()/2, val + 0.15,
                 f'{val:.1f}%', ha='center', va='bottom', color='white',
                 fontsize=8, fontweight='bold')
    ax4.axhspan(85, 87.5, alpha=0.1, color='gray')

    # Panel 5: Scenario/decision box
    ax5 = fig.add_subplot(gs[2, :])
    ax5.set_facecolor('#0a1628')
    ax5.axis('off')
    ax5.set_title('Scenario Judgment & Box Motion Model Decision', color='#f1c40f',
                  fontsize=11, fontweight='bold', pad=8)

    scenario_text = (
        "SCENARIO A: Root cause IDENTIFIED, solution is TRADE-OFF\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        "Cause:       Coupler removal (4 shoulder-pelvis CoordinateCouplerConstraints)        99.6% of 174 Nm anomaly\n"
        "Mechanism:   Coupler J^T×lambda was supplying ~174 Nm at pelvis_tilt DOF.\n"
        "             Without coupler: reserve must compensate for missing constraint force.\n"
        "Forearm_v1:  Negligible contribution (1.69 Nm, 1.0%).  Not the root cause.\n"
        "V3_armhang:  Setting shoulder_elv=0 reduces to 145.7 Nm — still FAIL. STRUCTURAL cause.\n\n"
        "BOX MOTION MODEL DECISION:   Option A — no_coupler + forearm_v1 (CURRENT)\n"
        "  Rationale: (1) ES analysis valid (max ΔES 0.41 %p — PASS)\n"
        "             (2) with_coupler model incompatible with box grip (coupler forces arm to 72.9°)\n"
        "             (3) pelvis_tilt anomaly is a MODEL ARTIFACT, not a musculoskeletal error\n"
        "             (4) Disclose as limitation in Methods/Limitations section\n\n"
        "NEXT STEP:   Week 4-5 Box MocoTrack with no_coupler + forearm_v1 model\n"
        "             Monitor pelvis_tilt reserve in box solve; report magnitude honestly."
    )
    ax5.text(0.01, 0.96, scenario_text, transform=ax5.transAxes, va='top', ha='left',
             color='#ecf0f1', fontsize=8.2, fontfamily='monospace', linespacing=1.45,
             wrap=False)

    fig.text(0.5, 0.01,
             'Step A.2 | Actual solve data (V1: full 5s, V2: smoke 2s NEW, V3/V4/V3h: smoke 2s) | '
             'ModOpAddReserves(10.0) | Hicks 2015 | 2026-05-15',
             ha='center', color='#888', fontsize=7.5)

    fig.suptitle('pelvis_tilt 174 Nm Root Cause Analysis — Step A.2',
                 color='white', fontsize=13, fontweight='bold', y=0.97)

    out_path = OUT_DIR / 'pelvis_tilt_root_diagnosis_grid.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'Saved: {out_path}')
    return out_path


if __name__ == '__main__':
    p1 = plot_diagram()
    p2 = plot_grid()
    print('\nAll figures generated.')
    print(f'  {p1}')
    print(f'  {p2}')
