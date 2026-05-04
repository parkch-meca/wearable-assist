"""
compare_phase1a_forearm_v1.py
============================
Phase 1a regression test: forearm_v1 vs no_coupler 비교.

두 솔루션의 근육 활성화 peak값 비교 + 그림 생성.

Usage:
  python compare_phase1a_forearm_v1.py
  (requires both smoke solutions to be present)
"""
import numpy as np
import os

NC_SOL = '/data/wearable-assist/results/phase1a_smoke_no_coupler/solution.sto'
FV_SOL = '/data/wearable-assist/results/phase1a_smoke_forearm_v1/solution.sto'
OUT_IMG = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase1a_forearm_v1_regression.png'
THRESHOLD_CAUTION = 5.0  # %p
THRESHOLD_FAIL = 10.0  # %p


def load_solution_raw(sol_path):
    with open(sol_path) as f:
        lines = f.readlines()
    header_end = 0
    for i, line in enumerate(lines):
        if 'endheader' in line:
            header_end = i + 1
            break
    col_labels = lines[header_end].strip().split('\t')
    data = []
    for line in lines[header_end+1:]:
        if line.strip():
            data.append([float(x) for x in line.strip().split('\t')])
    return col_labels, np.array(data)


def get_acts(labels, data):
    d = {}
    for i, l in enumerate(labels):
        if 'activation' in l and 'reserve' not in l:
            name = l.split('/')[2]
            d[name] = data[:, i]
    return d


def main():
    print("=== Phase 1a Regression: forearm_v1 vs no_coupler ===")

    labels_nc, data_nc = load_solution_raw(NC_SOL)
    labels_fv, data_fv = load_solution_raw(FV_SOL)
    time = data_nc[:, 0]

    nc_acts = get_acts(labels_nc, data_nc)
    fv_acts = get_acts(labels_fv, data_fv)

    common = sorted(set(nc_acts.keys()) & set(fv_acts.keys()))
    print(f"Common muscles: {len(common)}")

    deltas = {n: abs(np.max(fv_acts[n]) - np.max(nc_acts[n]))*100 for n in common}
    max_delta = max(deltas.values())

    # Print results
    print(f"\nTop 10 by |Δ|:")
    for n, d in sorted(deltas.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {n:30s}: Δ={d:.3f}%p (nc={np.max(nc_acts[n]):.4f}, fv1={np.max(fv_acts[n]):.4f})")

    print(f"\nMax Δ activation: {max_delta:.3f} %p")
    if max_delta < THRESHOLD_CAUTION:
        print(f"STATUS: PASS (< {THRESHOLD_CAUTION} %p threshold)")
    elif max_delta < THRESHOLD_FAIL:
        print(f"STATUS: CAUTION ({THRESHOLD_CAUTION}-{THRESHOLD_FAIL} %p range, 사용자 협의)")
    else:
        print(f"STATUS: FAIL (> {THRESHOLD_FAIL} %p threshold)")

    # Plot
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec

    fig = plt.figure(figsize=(16, 12))
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.4)

    # Bar chart
    ax1 = fig.add_subplot(gs[0, :2])
    top20 = sorted(deltas.items(), key=lambda x: x[1], reverse=True)[:20]
    names20 = [x[0] for x in top20]
    vals20 = [x[1] for x in top20]
    colors = ['#d62728' if v > 5 else '#ff7f0e' if v > 2 else '#1f77b4' for v in vals20]
    ax1.barh(range(len(names20)), vals20, color=colors)
    ax1.set_yticks(range(len(names20)))
    ax1.set_yticklabels(names20, fontsize=9)
    ax1.axvline(x=5, color='red', linestyle='--', linewidth=1.5, label='5%p PASS threshold')
    ax1.set_xlabel('|Delta Peak Activation| (%p)', fontsize=11)
    ax1.set_title('Top 20 Muscles: |Delta Activation| (forearm_v1 vs no_coupler)', fontsize=11, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.set_xlim(0, max(max_delta*1.2, 6))

    # Summary text
    ax2 = fig.add_subplot(gs[0, 2])
    ax2.axis('off')
    status = 'PASS' if max_delta < THRESHOLD_CAUTION else ('CAUTION' if max_delta < THRESHOLD_FAIL else 'FAIL')
    color = 'lightgreen' if status == 'PASS' else 'lightyellow' if status == 'CAUTION' else '#ffcccc'
    summary_text = (
        "REGRESSION SUMMARY\n"
        "──────────────────────\n"
        f"Model: forearm_v1\n"
        f"Modification: +19.2 cm hand\n"
        f"(De Leva 1996)\n\n"
        f"GH to hand_R:\n"
        f"  Before: 54.5 cm\n"
        f"  After:  73.7 cm\n\n"
        f"Muscles tested: {len(common)}\n"
        f"Time: t=[1.0, 3.0] s\n\n"
        f"Max DeltaActivation:\n"
        f"  {max_delta:.3f} %p\n\n"
        f"Threshold: 5 %p\n\n"
        f"STATUS: {status}\n"
        f"(max DeltaES = {max_delta:.2f} %p)"
    )
    ax2.text(0.05, 0.95, summary_text, transform=ax2.transAxes,
             fontsize=10, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor=color, alpha=0.8))

    # IL_R10 time series
    ax3 = fig.add_subplot(gs[1, 0])
    for m in ['IL_R10_r', 'IL_R10_l']:
        if m in nc_acts:
            ax3.plot(time, nc_acts[m], 'b-', label=f'{m} no_coupler', linewidth=2)
            ax3.plot(time, fv_acts[m], 'r--', label=f'{m} forearm_v1', linewidth=2)
    ax3.set_xlabel('Time (s)'); ax3.set_ylabel('Activation')
    ax3.set_title('IL_R10 (max DeltaES muscle)', fontsize=10)
    ax3.legend(fontsize=7); ax3.grid(True, alpha=0.3)

    # LTpL time series
    ax4 = fig.add_subplot(gs[1, 1])
    for m in ['LTpL_L5_l', 'LTpL_L5_r']:
        if m in nc_acts:
            ax4.plot(time, nc_acts[m], 'b-', label=f'{m} no_coupler', linewidth=2)
            ax4.plot(time, fv_acts[m], 'r--', label=f'{m} forearm_v1', linewidth=2)
    ax4.set_xlabel('Time (s)'); ax4.set_ylabel('Activation')
    ax4.set_title('LTpL_L5 time series', fontsize=10)
    ax4.legend(fontsize=7); ax4.grid(True, alpha=0.3)

    # Scatter
    ax5 = fig.add_subplot(gs[1, 2])
    nc_peaks = [np.max(nc_acts[n]) for n in common]
    fv_peaks = [np.max(fv_acts[n]) for n in common]
    ax5.scatter(nc_peaks, fv_peaks, alpha=0.6, s=20, c='#1f77b4')
    ax5.plot([0, 1], [0, 1], 'k--', linewidth=1, label='y=x')
    ax5.set_xlabel('no_coupler peak act.')
    ax5.set_ylabel('forearm_v1 peak act.')
    ax5.set_title('Peak Activation Correlation', fontsize=10)
    ax5.legend(fontsize=8); ax5.grid(True, alpha=0.3)
    r = np.corrcoef(nc_peaks, fv_peaks)[0, 1]
    ax5.text(0.05, 0.95, f'R={r:.6f}', transform=ax5.transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))

    os.makedirs(os.path.dirname(OUT_IMG), exist_ok=True)
    plt.savefig(OUT_IMG, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"\nPlot saved: {OUT_IMG}")
    plt.close()

    return max_delta


if __name__ == '__main__':
    main()
