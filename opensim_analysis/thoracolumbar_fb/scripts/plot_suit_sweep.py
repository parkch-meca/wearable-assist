"""Plot suit assist vs ES activation reduction across conditions."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import opensim as osim

# Baseline (0 N) was computed earlier in so_result; also covered by F0 in sweep.
SWEEP = Path('/data/stoop_results/suit_sweep_v2')
OUT_PNG = Path('/data/opensim_results/suit_effect_plot.png')

FORCES = [0, 50, 100, 150, 200]
MOMENT_ARM = 0.12
ES_PREFIXES = ('IL_', 'LTpT_', 'LTpL_')


def load_activation(path):
    tbl = osim.TimeSeriesTable(str(path))
    labels = list(tbl.getColumnLabels())
    t = np.array(list(tbl.getIndependentColumn()))
    data = np.zeros((tbl.getNumRows(), tbl.getNumColumns()))
    for i in range(tbl.getNumRows()):
        row = tbl.getRowAtIndex(i)
        for j in range(tbl.getNumColumns()):
            data[i, j] = row[j]
    es_idx = [i for i, l in enumerate(labels) if l.startswith(ES_PREFIXES)]
    es = data[:, es_idx]
    return t, es


def main():
    rows = []
    for F in FORCES:
        T = F * MOMENT_ARM
        tag = f'F{int(F)}'
        act_path = SWEEP / tag / f'suit_{tag}_StaticOptimization_activation.sto'
        if not act_path.exists():
            print(f'[miss] {act_path}')
            continue
        t, es = load_activation(act_path)
        es_mean = es.mean(axis=1)
        es_max = es.max(axis=1)
        rows.append({
            'F': F, 'T': T,
            'peak_mean': float(es_mean.max()),
            'peak_max':  float(es_max.max()),
            't': t, 'es_mean': es_mean, 'es_max': es_max,
        })

    # Reductions relative to F=0 baseline
    base_mean = rows[0]['peak_mean']
    base_max  = rows[0]['peak_max']
    for r in rows:
        r['red_mean_pct'] = 100.0 * (base_mean - r['peak_mean']) / base_mean if base_mean > 1e-9 else 0.0
        r['red_max_pct']  = 100.0 * (base_max  - r['peak_max'])  / base_max  if base_max  > 1e-9 else 0.0

    # Linear regression: T vs reduction (%)
    T_arr = np.array([r['T'] for r in rows])
    red_arr = np.array([r['red_mean_pct'] for r in rows])
    if len(rows) >= 2 and T_arr.max() > 0:
        slope, intercept = np.polyfit(T_arr, red_arr, 1)
        y_pred = slope * T_arr + intercept
        ss_res = np.sum((red_arr - y_pred)**2)
        ss_tot = np.sum((red_arr - red_arr.mean())**2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 1e-12 else 1.0
    else:
        slope, intercept, r2 = 0.0, 0.0, 0.0

    # --- figure ---
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    cmap = plt.cm.viridis(np.linspace(0, 0.9, len(rows)))
    for r, c in zip(rows, cmap):
        ax.plot(r['t'], r['es_mean'], color=c, lw=1.8,
                label=f'{r["F"]} N ({r["T"]:.1f} N·m)')
    ax.axvspan(1.0, 2.0, alpha=0.08, color='orange')
    ax.axvspan(2.0, 3.0, alpha=0.08, color='green')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('ES mean activation')
    ax.set_title('ES activation timeseries vs suit assist')
    ax.legend(fontsize=9); ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.scatter(T_arr, red_arr, s=60, color='tab:red', zorder=3, label='ES mean peak')
    red_max_arr = np.array([r['red_max_pct'] for r in rows])
    ax.scatter(T_arr, red_max_arr, s=40, color='tab:blue', alpha=0.6, marker='s', zorder=3,
               label='ES max peak')
    x_fit = np.linspace(0, T_arr.max(), 50)
    ax.plot(x_fit, slope * x_fit + intercept, 'r--', lw=1.5,
            label=f'fit (mean): y={slope:.2f}x+{intercept:.2f},  R²={r2:.3f}')
    ax.set_xlabel('Suit assist torque (N·m)')
    ax.set_ylabel('ES peak activation reduction (%)')
    ax.set_title('Dose-response: assist torque → ES reduction')
    ax.axhline(0, color='k', lw=0.5)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=9)

    fig.suptitle('SMA suit effect on erector spinae activation (stoop lift)')
    plt.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=120, bbox_inches='tight')
    print(f'Wrote {OUT_PNG}')

    # --- numeric report ---
    print('\n=== Suit sweep results ===')
    print(f'{"F (N)":>6} {"T (Nm)":>8} {"ES mean peak":>14} {"ES max peak":>12} {"Δmean %":>8} {"Δmax %":>8}')
    for r in rows:
        print(f'{r["F"]:>6} {r["T"]:>8.2f} {r["peak_mean"]:>14.4f} {r["peak_max"]:>12.4f} '
              f'{r["red_mean_pct"]:>8.2f} {r["red_max_pct"]:>8.2f}')
    print(f'\nLinear fit (ES mean reduction): slope={slope:.3f} %/Nm  intercept={intercept:.3f}  R²={r2:.4f}')


if __name__ == '__main__':
    main()
