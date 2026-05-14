"""
Generate ES timeseries + Dose-Response plots for Phase 1a Reproduction (Week 3).

Optional C plots:
    phase1a_reproduction_es_timeseries.png  — 5-condition overlay
    phase1a_reproduction_dose_response.png  — slope + R^2 + Hu 2026

Based entirely on existing Phase 1a solutions (ground truth).
"""
import os
import sys
from pathlib import Path

os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
sys.path.insert(0, '/data/wearable-assist/opensim_analysis/thoracolumbar_fb')

import numpy as np
import opensim as osim
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT_DIR = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/step2_phase1a_reproduction')
OUT_DIR.mkdir(parents=True, exist_ok=True)

ORIG_PATHS = {
    0:   '/data/wearable-assist/results/phase1a_full/solution.sto',
    50:  '/data/wearable-assist/results/phase1a_suit_sweep/F50/solution_suit.sto',
    100: '/data/wearable-assist/results/phase1a_suit_sweep/F100/solution_suit.sto',
    150: '/data/wearable-assist/results/phase1a_suit_sweep/F150/solution_suit.sto',
    200: '/data/wearable-assist/results/phase1a_suit_sweep/F200/solution_suit.sto',
}

MOMENT_ARM = 0.12
ES6 = ['IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'IL_R11_l', 'LTpL_L5_r', 'LTpL_L5_l']
PHASES = [
    ('Standing',   0.0, 0.5),
    ('Eccentric',  0.5, 1.5),
    ('Hold',       1.5, 2.5),
    ('Concentric', 2.5, 4.0),
    ('Recovery',   4.0, 5.0),
]
PHASE_COLORS = {
    'Standing': '#888888', 'Eccentric': '#1f77b4',
    'Hold': '#d62728', 'Concentric': '#2ca02c', 'Recovery': '#ff7f0e',
}
FORCE_COLORS = {0: '#1a1a2e', 50: '#1f77b4', 100: '#2ca02c', 150: '#ff7f0e', 200: '#d62728'}


def load_act(tbl, name):
    labels = list(tbl.getColumnLabels())
    for i, L in enumerate(labels):
        if L.endswith(f'/{name}/activation'):
            n = tbl.getNumRows()
            return np.array([tbl.getRowAtIndex(k)[i] for k in range(n)]) * 100
    return None


def load_es_mean(sol_path):
    if not os.path.isfile(sol_path):
        return None, None
    tbl = osim.TimeSeriesTable(sol_path)
    times = np.array(list(tbl.getIndependentColumn()))
    acts = {nm: load_act(tbl, nm) for nm in ES6}
    acts = {k: v for k, v in acts.items() if v is not None}
    if not acts:
        return times, None
    arr = np.stack(list(acts.values()), axis=1)
    return times, arr.mean(axis=1)


def fit_line(x, y):
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 1.0
    return float(slope), float(intercept), float(r2)


def gen_es_timeseries():
    """5-condition ES_mean overlay."""
    fig, ax = plt.subplots(figsize=(13, 6))

    base_data = {}
    for f, path in ORIG_PATHS.items():
        times, es = load_es_mean(path)
        if times is not None and es is not None:
            base_data[f] = (times, es)

    for f in sorted(base_data.keys()):
        times, es = base_data[f]
        T = f * MOMENT_ARM
        lw = 2.5 if f == 0 else 1.8
        ax.plot(times, es, lw=lw, color=FORCE_COLORS[f],
                label=f'F={f} N (T={T:.0f} N·m)')

    for pname, ts, te in PHASES:
        ax.axvspan(ts, te, alpha=0.07, color=PHASE_COLORS[pname])
        ax.text((ts + te) / 2, 58, pname, ha='center', va='top',
                fontsize=9, color=PHASE_COLORS[pname], fontweight='bold')

    ax.set_xlim(0, 5)
    ax.set_ylim(0, 60)
    ax.set_xlabel('Time (s)', fontsize=11)
    ax.set_ylabel('ES_mean Activation (%) — average of 6 key muscles', fontsize=11)
    ax.set_title(
        'Phase 1a Reproduction — ES_mean Time-Series (5 Conditions, Existing Ground Truth)\n'
        'Muscles: IL_R10 (R/L), IL_R11 (R/L), LTpL_L5 (R/L)',
        fontsize=12, fontweight='bold',
    )
    ax.legend(fontsize=10, loc='upper right', framealpha=0.9)
    ax.grid(True, alpha=0.25)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    out = OUT_DIR / 'phase1a_reproduction_es_timeseries.png'
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved: {out}')
    return out


def gen_dose_response():
    """Dose-response: slope + R^2 + Hu 2026."""
    forces = [0, 50, 100, 150, 200]
    torques = np.array([f * MOMENT_ARM for f in forces])

    hold_means = []
    con_means = []
    il_r10_hold = []
    il_r10_con = []

    for f in forces:
        path = ORIG_PATHS[f]
        if not os.path.isfile(path):
            hold_means.append(None)
            con_means.append(None)
            il_r10_hold.append(None)
            il_r10_con.append(None)
            continue
        tbl = osim.TimeSeriesTable(path)
        times = np.array(list(tbl.getIndependentColumn()))
        acts = {nm: load_act(tbl, nm) for nm in ES6}
        acts = {k: v for k, v in acts.items() if v is not None}
        if not acts:
            hold_means.append(None)
            continue

        arr = np.stack(list(acts.values()), axis=1)
        es_mean = arr.mean(axis=1)
        mask_h = (times >= 1.5) & (times <= 2.5)
        mask_c = (times >= 2.5) & (times <= 4.0)
        hold_means.append(float(es_mean[mask_h].mean()))
        con_means.append(float(es_mean[mask_c].mean()))
        il = acts.get('IL_R10_r')
        il_r10_hold.append(float(il[mask_h].mean()) if il is not None else None)
        il_r10_con.append(float(il[mask_c].mean()) if il is not None else None)

    # Filter valid
    valid_idx = [i for i, v in enumerate(hold_means) if v is not None]
    vt = torques[valid_idx]
    vh = np.array([hold_means[i] for i in valid_idx])
    vc = np.array([con_means[i] for i in valid_idx])
    vil_h = np.array([il_r10_hold[i] for i in valid_idx if il_r10_hold[i] is not None])
    vil_c = np.array([il_r10_con[i]  for i in valid_idx if il_r10_con[i]  is not None])

    base_h = vh[0]; base_c = vc[0]
    red_h = 100 * (base_h - vh) / base_h
    red_c = 100 * (base_c - vc) / base_c

    base_il_h = vil_h[0]; base_il_c = vil_c[0]
    red_il_h = 100 * (base_il_h - vil_h) / base_il_h
    red_il_c = 100 * (base_il_c - vil_c) / base_il_c

    s_h, i_h, r2_h = fit_line(vt, red_h)
    s_c, i_c, r2_c = fit_line(vt, red_c)
    s_il_h, i_il_h, r2_il_h = fit_line(vt, red_il_h)
    s_il_c, i_il_c, r2_il_c = fit_line(vt, red_il_c)
    x_fit = np.linspace(0, 25, 200)

    fig, axs = plt.subplots(1, 2, figsize=(15, 6))

    # Panel A: ES_mean
    ax = axs[0]
    ax.axhspan(14.9, 28.6, alpha=0.12, color='gold', zorder=0, label='Hu 2026 range: 14.9-28.6%')
    ax.scatter(vt, red_h, s=90, color='#d62728', zorder=4, edgecolor='black', lw=0.8, label='ES_mean Hold')
    ax.scatter(vt, red_c, s=90, color='#2ca02c', zorder=4, edgecolor='black', lw=0.8, marker='s', label='ES_mean Concentric')
    ax.plot(x_fit, s_h * x_fit + i_h, '-', color='#d62728', lw=2, alpha=0.75,
            label=f'Hold fit: {s_h:.3f} %/Nm, R²={r2_h:.4f}')
    ax.plot(x_fit, s_c * x_fit + i_c, '-', color='#2ca02c', lw=2, alpha=0.75,
            label=f'Conc fit: {s_c:.3f} %/Nm, R²={r2_c:.4f}')
    ax.plot(x_fit, 1.206 * x_fit + 0.04, '--', color='#1f77b4', lw=2.2, alpha=0.85,
            label='SO §1.6 (1.206 %/Nm, R²=1.000, 28.97%)')
    ax.axvline(24, color='gray', ls=':', lw=1.2, alpha=0.7)
    ax.text(24.2, 1.5, '24 N·m (F=200 N)', fontsize=8.5, color='gray')
    ax.set_xlabel('Suit torque (N·m)', fontsize=11)
    ax.set_ylabel('ES_mean reduction (%)', fontsize=11)
    ax.set_title('A.  ES_mean Dose-Response — Moco vs SO §1.6', fontsize=12, fontweight='bold', loc='left')
    ax.legend(fontsize=9, loc='upper left', framealpha=0.9)
    ax.grid(True, alpha=0.25)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xlim(-1, 26)
    ax.set_ylim(-2, 35)

    # Panel B: IL_R10_r
    ax = axs[1]
    ax.axhspan(14.9, 28.6, alpha=0.12, color='gold', zorder=0)
    ax.scatter(vt, red_il_h, s=90, color='#d62728', zorder=4, edgecolor='black', lw=0.8, label='IL_R10_r Hold')
    ax.scatter(vt, red_il_c, s=90, color='#2ca02c', zorder=4, edgecolor='black', lw=0.8, marker='s', label='IL_R10_r Concentric')
    ax.plot(x_fit, s_il_h * x_fit + i_il_h, '-', color='#d62728', lw=2, alpha=0.75,
            label=f'Hold fit: {s_il_h:.3f} %/Nm, R²={r2_il_h:.4f}')
    ax.plot(x_fit, s_il_c * x_fit + i_il_c, '-', color='#2ca02c', lw=2, alpha=0.75,
            label=f'Conc fit: {s_il_c:.3f} %/Nm, R²={r2_il_c:.4f}')
    ax.axvline(24, color='gray', ls=':', lw=1.2, alpha=0.7)
    ax.text(24.2, 2, '24 N·m', fontsize=8.5, color='gray')
    ax.set_xlabel('Suit torque (N·m)', fontsize=11)
    ax.set_ylabel('IL_R10_r activation reduction (%)', fontsize=11)
    ax.set_title('B.  IL_R10_r (dominant ES muscle) — Higher slope vs ES_mean', fontsize=12, fontweight='bold', loc='left')
    ax.legend(fontsize=9, loc='upper left', framealpha=0.9)
    ax.grid(True, alpha=0.25)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xlim(-1, 26)

    fig.suptitle(
        f'Phase 1a Reproduction — Dose-Response  |  ES_mean slope: {s_h:.3f} %/N·m, R²={r2_h:.4f}  '
        f'|  IL_R10 slope: {s_il_h:.3f} %/N·m\n'
        f'Existing ground truth (5 conditions: F=0/50/100/150/200 N)',
        fontsize=12, fontweight='bold', y=1.01,
    )
    fig.tight_layout()
    out = OUT_DIR / 'phase1a_reproduction_dose_response.png'
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved: {out}')
    return out


def main():
    out1 = gen_es_timeseries()
    out2 = gen_dose_response()
    print(f'\nDone:')
    print(f'  C1: {out1}')
    print(f'  C2: {out2}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        print(f'FATAL: {e}')
        traceback.print_exc()
        sys.exit(1)
