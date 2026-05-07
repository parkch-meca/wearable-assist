"""Phase 1a regression comparison: forearm_v1 (114) vs v2_lower_limb (158).

Compares:
  - 76 ES muscles activation (max delta, mean delta)
  - Reserve pelvis_tilt, hip_flexion, knee_angle, ankle_angle
  - IL_R10_r time series overlay
  - Summary PASS/FAIL

Usage:
  python compare_phase1a_v2_regression.py [smoke|full]

Output:
  /data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/
    phase1a_regression_v2_lower_limb.png
"""
import os, sys
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

mode = sys.argv[1] if len(sys.argv) > 1 else 'smoke'

# Paths
if mode == 'smoke':
    BASELINE_STO = '/data/wearable-assist/results/phase1a_smoke_forearm_v1/solution.sto'
    NEW_STO      = '/data/opensim_results/phase1a_v2_lower_limb/smoke/solution.sto'
else:
    BASELINE_STO = '/data/wearable-assist/results/phase1a_full_forearm_v1/solution.sto'
    NEW_STO      = '/data/opensim_results/phase1a_v2_lower_limb/full/solution.sto'

OUT_IMG = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase1a_regression_v2_lower_limb.png')
OUT_IMG.parent.mkdir(parents=True, exist_ok=True)


def parse_sto(path):
    """Parse .sto / MocoSolution file -> (times, {colname: np.array})."""
    with open(path) as f:
        lines = f.readlines()

    # find data start
    header_idx = None
    for i, l in enumerate(lines):
        if l.startswith('time\t'):
            header_idx = i
            break
    if header_idx is None:
        for i, l in enumerate(lines):
            if 'endheader' in l:
                header_idx = i + 1
                break

    cols = lines[header_idx].strip().split('\t')
    data = []
    for l in lines[header_idx + 1:]:
        if l.strip():
            try:
                data.append([float(x) for x in l.strip().split('\t')])
            except ValueError:
                continue
    data = np.array(data)
    times = data[:, 0]
    result = {}
    for ci, cn in enumerate(cols[1:], start=1):
        result[cn] = data[:, ci]
    return times, result


def extract_es76(data):
    """Extract 76 ES muscles (IL+LTpT+LTpL) activation values as dict.

    Column format: /forceset/IL_R10_r/activation
    -> short name = parts[-2] (muscle name between /forceset/ and /activation)
    """
    es_groups = ['IL_', 'LTpT_', 'LTpL_']
    es = {}
    for col, arr in data.items():
        if '/activation' not in col:
            continue
        parts = col.split('/')
        # ['', 'forceset', 'IL_R10_r', 'activation']
        name = parts[-2] if len(parts) >= 3 else col
        if any(name.startswith(g) for g in es_groups):
            es[name] = arr
    return es


def extract_reserves(data):
    """Extract key reserve forces."""
    reserves_of_interest = [
        'reserve_jointset_ground_pelvis_pelvis_tilt',
        'reserve_jointset_hip_r_hip_flexion_r',
        'reserve_jointset_hip_l_hip_flexion_l',
        'reserve_jointset_knee_r_knee_angle_r',
        'reserve_jointset_knee_l_knee_angle_l',
        'reserve_jointset_ankle_r_ankle_angle_r',
        'reserve_jointset_ankle_l_ankle_angle_l',
    ]
    result = {}
    for interest in reserves_of_interest:
        for col, arr in data.items():
            if interest in col:
                short = interest.replace('reserve_jointset_', '').replace('_', ' ')
                result[short] = arr
                break
    return result


def main():
    print(f'Loading baseline: {BASELINE_STO}')
    t_base, d_base = parse_sto(BASELINE_STO)
    print(f'Loading new:      {NEW_STO}')
    t_new, d_new = parse_sto(NEW_STO)

    # ── 1. ES activation comparison ──────────────────────────────────────
    es_base = extract_es76(d_base)
    es_new  = extract_es76(d_new)

    common_es = sorted(set(es_base.keys()) & set(es_new.keys()))
    print(f'\nES muscles found: baseline={len(es_base)}, new={len(es_new)}, common={len(common_es)}')

    delta_peaks = {}
    for m in common_es:
        base_peak = np.max(es_base[m])
        new_peak  = np.max(es_new[m])
        delta_peaks[m] = (new_peak - base_peak) * 100  # %p

    max_delta_es = max(abs(v) for v in delta_peaks.values()) if delta_peaks else 0
    mean_delta_es = np.mean([abs(v) for v in delta_peaks.values()]) if delta_peaks else 0

    # ── 2. Reserve comparison ─────────────────────────────────────────────
    res_base = extract_reserves(d_base)
    res_new  = extract_reserves(d_new)

    # ── 3. IL_R10_r time series ───────────────────────────────────────────
    il_col_base = '/forceset/IL_R10_r/activation'
    il_col_new  = '/forceset/IL_R10_r/activation'

    # ── Plotting ──────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(20, 14))
    fig.patch.set_facecolor('#1a1a2e')
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.35)

    TEXT_COLOR = '#e0e0e0'
    GRID_COLOR = '#3a3a5a'
    COLOR_BASE = '#4fc3f7'   # light blue = baseline
    COLOR_NEW  = '#ff8a65'   # orange = new v2
    COLOR_PASS = '#66bb6a'
    COLOR_FAIL = '#ef5350'
    COLOR_WARN = '#ffa726'

    # Panel 1: ES delta bar chart (top common_es sorted by |delta|)
    ax1 = fig.add_subplot(gs[0, :])
    ax1.set_facecolor('#16213e')
    sorted_by_delta = sorted(delta_peaks.items(), key=lambda x: abs(x[1]), reverse=True)
    top_n = min(30, len(sorted_by_delta))
    names_top = [x[0] for x in sorted_by_delta[:top_n]]
    deltas_top = [x[1] for x in sorted_by_delta[:top_n]]
    colors_bar = [COLOR_FAIL if abs(d) >= 5 else (COLOR_WARN if abs(d) >= 2 else COLOR_PASS)
                  for d in deltas_top]
    ax1.bar(range(top_n), deltas_top, color=colors_bar, alpha=0.85, edgecolor='none')
    ax1.axhline(0, color=TEXT_COLOR, lw=0.8, alpha=0.4)
    ax1.axhline(5,  color=COLOR_FAIL, lw=1.2, ls='--', alpha=0.7, label='+5 %p threshold')
    ax1.axhline(-5, color=COLOR_FAIL, lw=1.2, ls='--', alpha=0.7)
    ax1.set_xticks(range(top_n))
    ax1.set_xticklabels(names_top, rotation=45, ha='right', fontsize=7, color=TEXT_COLOR)
    ax1.set_ylabel('ΔActivation (v2 - v1) [%p]', color=TEXT_COLOR)
    ax1.tick_params(colors=TEXT_COLOR)
    for sp in ax1.spines.values():
        sp.set_color(GRID_COLOR)
    ax1.set_title(f'ES Activation Delta: 114-muscle vs 158-muscle  |  max |Δ|={max_delta_es:.2f} %p  mean |Δ|={mean_delta_es:.2f} %p',
                  color=TEXT_COLOR, fontsize=12, fontweight='bold')
    ax1.legend(facecolor='#2a2a4e', labelcolor=TEXT_COLOR, edgecolor=GRID_COLOR)
    ax1.grid(axis='y', color=GRID_COLOR, alpha=0.5)

    # Panel 2: IL_R10_r time series overlay
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.set_facecolor('#16213e')
    if il_col_base in d_base:
        ax2.plot(t_base, d_base[il_col_base] * 100, color=COLOR_BASE, lw=2, label='114-muscle (baseline)')
    if il_col_new in d_new:
        ax2.plot(t_new, d_new[il_col_new] * 100, color=COLOR_NEW, lw=2, ls='--', label='158-muscle (v2)')
    ax2.set_xlabel('Time [s]', color=TEXT_COLOR)
    ax2.set_ylabel('Activation [%]', color=TEXT_COLOR)
    ax2.set_title('IL_R10_r activation time series', color=TEXT_COLOR, fontsize=11)
    ax2.tick_params(colors=TEXT_COLOR)
    ax2.legend(facecolor='#2a2a4e', labelcolor=TEXT_COLOR, edgecolor=GRID_COLOR)
    ax2.grid(color=GRID_COLOR, alpha=0.4)
    for sp in ax2.spines.values():
        sp.set_color(GRID_COLOR)

    # Panel 3: Reserve comparison bar chart
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.set_facecolor('#16213e')
    res_names = list(res_base.keys())
    x = np.arange(len(res_names))
    width = 0.35
    base_maxabs = [np.max(np.abs(res_base.get(n, np.zeros(1)))) for n in res_names]
    new_maxabs  = [np.max(np.abs(res_new.get(n, np.zeros(1)))) for n in res_names]
    ax3.bar(x - width/2, base_maxabs, width, color=COLOR_BASE, alpha=0.85, label='114-muscle')
    ax3.bar(x + width/2, new_maxabs,  width, color=COLOR_NEW,  alpha=0.85, label='158-muscle')
    short_names = [n.replace('ground pelvis ', '').replace(' r', '').replace(' l', '')
                   for n in res_names]
    ax3.set_xticks(x)
    ax3.set_xticklabels(short_names, rotation=30, ha='right', fontsize=8, color=TEXT_COLOR)
    ax3.set_ylabel('Reserve max |F| [N·m]', color=TEXT_COLOR)
    ax3.set_title('Reserve forces: 114 vs 158 muscles', color=TEXT_COLOR, fontsize=11)
    ax3.tick_params(colors=TEXT_COLOR)
    ax3.legend(facecolor='#2a2a4e', labelcolor=TEXT_COLOR, edgecolor=GRID_COLOR)
    ax3.grid(axis='y', color=GRID_COLOR, alpha=0.4)
    for sp in ax3.spines.values():
        sp.set_color(GRID_COLOR)

    # Panel 4: Summary table
    ax4 = fig.add_subplot(gs[2, :])
    ax4.set_facecolor('#16213e')
    ax4.axis('off')

    # Build table data
    table_data = []
    table_data.append(['Metric', '114-muscle (v1)', '158-muscle (v2)', 'Change', 'Criterion', 'Status'])

    # ES delta rows
    table_data.append([
        'ES max |ΔActivation|',
        '--', '--',
        f'{max_delta_es:.2f} %p',
        '< 5 %p',
        'PASS' if max_delta_es < 5 else ('WARN' if max_delta_es < 10 else 'FAIL')
    ])
    table_data.append([
        'ES mean |ΔActivation|',
        '--', '--',
        f'{mean_delta_es:.2f} %p',
        '< 3 %p',
        'PASS' if mean_delta_es < 3 else 'WARN'
    ])

    # Reserve rows
    for rn in res_names:
        bv = np.max(np.abs(res_base.get(rn, np.zeros(1))))
        nv = np.max(np.abs(res_new.get(rn, np.zeros(1))))
        chg = nv - bv
        chg_pct = (nv - bv) / bv * 100 if bv > 1e-9 else 0
        short = rn.replace('ground pelvis ', 'pelvis_')
        if chg < 0:
            status = 'PASS'
        elif abs(chg) < 1.0:
            status = 'OK'
        else:
            status = 'WARN'
        table_data.append([
            f'reserve {short}',
            f'{bv:.1f} N·m',
            f'{nv:.1f} N·m',
            f'{chg:+.1f} ({chg_pct:+.0f}%)',
            'Decrease',
            status
        ])

    col_labels = table_data[0]
    row_data   = table_data[1:]

    tbl = ax4.table(
        cellText=row_data,
        colLabels=col_labels,
        loc='center',
        cellLoc='center'
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.6)

    for (r, c), cell in tbl.get_celld().items():
        cell.set_facecolor('#0d0d23')
        cell.set_edgecolor(GRID_COLOR)
        cell.set_text_props(color=TEXT_COLOR)
        if r == 0:
            cell.set_facecolor('#1e3a5f')
            cell.set_text_props(fontweight='bold', color='#bbdefb')
        elif c == 5 and r > 0:
            status_val = row_data[r-1][5]
            if status_val == 'PASS':
                cell.set_facecolor('#1b5e20')
                cell.set_text_props(color='#a5d6a7')
            elif status_val == 'FAIL':
                cell.set_facecolor('#b71c1c')
                cell.set_text_props(color='#ef9a9a')
            elif status_val == 'WARN':
                cell.set_facecolor('#e65100')
                cell.set_text_props(color='#ffe0b2')

    # Overall verdict
    es_pass = max_delta_es < 5
    reserve_improved = any(
        np.max(np.abs(res_new.get(rn, np.zeros(1)))) < np.max(np.abs(res_base.get(rn, np.zeros(1))))
        for rn in res_names
    )
    verdict_color = COLOR_PASS if (es_pass and reserve_improved) else (COLOR_WARN if es_pass else COLOR_FAIL)
    verdict_text  = 'OVERALL: PASS — Model Adopted' if (es_pass and reserve_improved) else \
                    ('OVERALL: WARN — User Review' if es_pass else 'OVERALL: FAIL')

    fig.text(0.5, 0.01, verdict_text, ha='center', va='bottom',
             fontsize=14, fontweight='bold', color=verdict_color,
             bbox=dict(facecolor='#0d0d23', edgecolor=verdict_color, boxstyle='round,pad=0.4'))

    title = (f'Phase 1a Regression: Muscle Set v1 (114) vs v2 (158)  |  mode={mode}  |  '
             f'max ΔES={max_delta_es:.2f} %p')
    fig.suptitle(title, fontsize=13, color=TEXT_COLOR, fontweight='bold', y=0.98)

    plt.savefig(str(OUT_IMG), dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f'\n=== RESULTS ===')
    print(f'  ES max |Δ|:   {max_delta_es:.2f} %p  -> {"PASS" if es_pass else "FAIL"}')
    print(f'  ES mean |Δ|:  {mean_delta_es:.2f} %p')
    print(f'  Reserve improved: {reserve_improved}')
    print(f'  Verdict: {verdict_text}')
    print(f'  Figure: {OUT_IMG}')

    # Print reserve table to console
    print('\n  Reserve comparison:')
    for rn in res_names:
        bv = np.max(np.abs(res_base.get(rn, np.zeros(1))))
        nv = np.max(np.abs(res_new.get(rn, np.zeros(1))))
        print(f'    {rn:40s}: {bv:7.2f} -> {nv:7.2f} N·m  (Δ{nv-bv:+.2f})')


if __name__ == '__main__':
    main()
