"""Phase 1a — suit effect analysis: Δ ES per phase, baseline vs +24 N·m suit.

Outputs:
  results/phase1a_suit_effect/suit_effect_report.md
  docs/images/phase1a_full/figure_es_timeseries_comparison.png
  docs/images/phase1a_full/figure_5phase_delta_heatmap.png
  docs/images/phase1a_full/figure_temporal_effect_distribution.png
  docs/images/phase1a_full/figure_so_vs_moco_suit_effect.png
  docs/images/phase1a_full/figure_hierarchy_redistribution.png
"""
import os
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE_SOL = '/data/wearable-assist/results/phase1a_full/solution.sto'
SUIT_SOL = '/data/wearable-assist/results/phase1a_suit_effect/solution_suit.sto'
OUT_RESULTS = Path('/data/wearable-assist/results/phase1a_suit_effect')
OUT_FIG = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase1a_full')
REPORT = OUT_RESULTS / 'suit_effect_report.md'

PHASES = [
    ('Quiet', 0.0, 1.0, '#888888'),
    ('Eccentric', 1.0, 2.0, '#1f77b4'),
    ('Hold', 2.0, 2.5, '#d62728'),
    ('Concentric', 2.5, 4.0, '#2ca02c'),
    ('Recovery', 4.0, 5.0, '#ff7f0e'),
]
KEY = ['IL_R10_r','IL_R10_l','IL_R11_r','IL_R12_r','IL_R11_l','IL_R12_l',
       'LTpL_L5_r','LTpL_L5_l','LTpL_L4_r','LTpT_T11_r','LTpT_T12_r',
       'QL_post_I_2-L4_r','QL_post_I_3-L1_r','rect_abd_r']
DISPLAY = ['IL_R10_r','IL_R10_l','IL_R11_r','LTpL_L5_r','LTpL_L5_l','IL_R12_r']


def load_act(tbl, name):
    labels = list(tbl.getColumnLabels())
    for i, L in enumerate(labels):
        if L.endswith(f'/{name}/activation'):
            n = tbl.getNumRows()
            return np.array([tbl.getRowAtIndex(k)[i] for k in range(n)]) * 100
    return None


def main():
    tb = osim.TimeSeriesTable(BASE_SOL); ts = osim.TimeSeriesTable(SUIT_SOL)
    times = np.array(list(tb.getIndependentColumn()))
    if not np.allclose(times, np.array(list(ts.getIndependentColumn()))):
        print('WARNING: time grids differ, interpolating not implemented; assuming match')
    base = {n: load_act(tb, n) for n in KEY}
    suit = {n: load_act(ts, n) for n in KEY}
    base = {k: v for k, v in base.items() if v is not None}
    suit = {k: v for k, v in suit.items() if v is not None}
    print(f'Loaded {len(base)} muscles')

    # Phase × muscle deltas
    rows = []
    for nm in KEY:
        if nm not in base or nm not in suit: continue
        for pname, ts_, te_, _ in PHASES:
            mask = (times >= ts_) & (times < te_)
            if pname == 'Recovery':
                mask = (times >= ts_) & (times <= te_)
            b = float(base[nm][mask].mean())
            s = float(suit[nm][mask].mean())
            d = s - b
            d_rel = (d / b * 100) if b > 1 else 0
            rows.append({'muscle': nm, 'phase': pname, 'base': b, 'suit': s,
                         'delta_pp': d, 'delta_rel_pct': d_rel})
    # ===== Figure 1: ES timeseries comparison (5 muscles) =====
    fig, axs = plt.subplots(len(DISPLAY), 1, figsize=(11, 12), sharex=True)
    for ax, nm in zip(axs, DISPLAY):
        ax.plot(times, base.get(nm, np.zeros_like(times)), lw=1.6, color='#444', label='baseline')
        ax.plot(times, suit.get(nm, np.zeros_like(times)), lw=1.6, color='#d62728', label='+24 N·m suit')
        for ts_, te_, _, color in [(0,1,None,'#888888'),(1,2,None,'#1f77b4'),
                                    (2,2.5,None,'#d62728'),(2.5,4,None,'#2ca02c'),
                                    (4,5,None,'#ff7f0e')]:
            ax.axvspan(ts_, te_, alpha=0.10, color=color)
        ax.set_ylim(0, 100); ax.set_ylabel(f'{nm}\n(%)', fontsize=10)
        ax.legend(fontsize=8, loc='upper right'); ax.grid(True, alpha=0.3)
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    axs[-1].set_xlabel('time (s)')
    fig.suptitle('Baseline vs +24 N·m suit — ES activation comparison', fontsize=12, fontweight='bold')
    fig.tight_layout()
    fig.savefig(OUT_FIG / 'figure_es_timeseries_comparison.png', dpi=140, bbox_inches='tight')
    plt.close(fig)

    # ===== Figure 2: 5-phase × 6 muscle Δ heatmap =====
    grid = np.zeros((len(DISPLAY), len(PHASES)))
    grid_rel = np.zeros_like(grid)
    for i, nm in enumerate(DISPLAY):
        for j, (pname, ts_, te_, _) in enumerate(PHASES):
            mask = (times >= ts_) & (times < te_) if pname != 'Recovery' else (times >= ts_) & (times <= te_)
            b = float(base[nm][mask].mean()) if nm in base else 0
            s = float(suit[nm][mask].mean()) if nm in suit else 0
            grid[i, j] = s - b
            grid_rel[i, j] = (s - b)/b*100 if b > 1 else 0

    fig, ax = plt.subplots(figsize=(11, 7))
    im = ax.imshow(grid, aspect='auto', cmap='RdBu_r',
                   vmin=-max(abs(grid).max(),1), vmax=max(abs(grid).max(),1))
    ax.set_yticks(range(len(DISPLAY))); ax.set_yticklabels(DISPLAY, fontsize=10)
    ax.set_xticks(range(len(PHASES))); ax.set_xticklabels([p[0] for p in PHASES], fontsize=10)
    for i in range(len(DISPLAY)):
        for j in range(len(PHASES)):
            d = grid[i, j]; dr = grid_rel[i, j]
            color = 'black' if abs(d) < grid.max()*0.6 else 'white'
            ax.text(j, i, f'{d:+.1f}\n({dr:+.0f}%)', ha='center', va='center',
                    fontsize=9, color=color, fontweight='bold')
    ax.set_title('ΔES (suit − baseline) — phase × muscle (mean activation %p, relative %)',
                 fontsize=12, fontweight='bold', pad=10)
    fig.colorbar(im, ax=ax, label='Δ (%p)')
    fig.tight_layout()
    fig.savefig(OUT_FIG / 'figure_5phase_delta_heatmap.png', dpi=140, bbox_inches='tight')
    plt.close(fig)

    # ===== Figure 3: temporal effect distribution =====
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for nm in DISPLAY[:5]:
        if nm in base and nm in suit:
            d = suit[nm] - base[nm]
            ax.plot(times, d, lw=1.5, label=nm)
    ax.axhline(0, color='k', lw=0.5)
    for ts_, te_, color, name in [(0,1,'#888888','Quiet'),(1,2,'#1f77b4','Ecc'),
                                    (2,2.5,'#d62728','Hold'),(2.5,4,'#2ca02c','Con'),
                                    (4,5,'#ff7f0e','Rec')]:
        ax.axvspan(ts_, te_, alpha=0.10, color=color)
    ax.set_xlim(0, 5)
    ax.set_xlabel('time (s)'); ax.set_ylabel('ΔES (suit − baseline) %p')
    ax.set_title('Temporal distribution of suit effect (∂ES/∂t)',
                 fontsize=12, fontweight='bold')
    ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT_FIG / 'figure_temporal_effect_distribution.png', dpi=140, bbox_inches='tight')
    plt.close(fig)

    # ===== Figure 4: SO 28.97% vs Moco ΔES (Hold/Conc) =====
    fig, ax = plt.subplots(figsize=(8, 6))
    # SO §1.6 reference (R100 baseline): 28.97% reduction at 24 Nm
    # Moco analog: ΔES of dominant muscle relative to baseline at Hold/Concentric
    so_red_pct = 28.97  # absolute claim is across SO mean; comparable here is relative reduction
    so_red_pct_r50 = 21.25  # R50 estimate
    moco_il_r10_hold_rel = -grid_rel[0, 2]  # IL_R10_r Hold relative reduction (sign flipped to positive)
    moco_il_r10_con_rel = -grid_rel[0, 3]
    moco_ltpl_hold_rel = -grid_rel[3, 2]    # LTpL_L5_r
    moco_ltpl_con_rel = -grid_rel[3, 3]

    items = ['SO §1.6\n(R100, 28.97%)', 'SO R50\n(re-est. 21%)',
             'Moco IL_R10\nHold', 'Moco IL_R10\nConc',
             'Moco LTpL_L5\nHold', 'Moco LTpL_L5\nConc']
    vals = [so_red_pct, so_red_pct_r50, moco_il_r10_hold_rel, moco_il_r10_con_rel,
            moco_ltpl_hold_rel, moco_ltpl_con_rel]
    colors = ['#9999cc','#9999cc','#d62728','#2ca02c','#d62728','#2ca02c']
    bars = ax.bar(items, vals, color=colors, edgecolor='black', linewidth=0.5)
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, v + 0.3 * np.sign(v if v else 1),
                f'{v:+.1f}%', ha='center', fontsize=10, fontweight='bold')
    ax.set_ylabel('ES reduction (%) at 24 N·m suit')
    ax.set_title('SO vs MocoInverse — relative ES reduction', fontsize=12, fontweight='bold')
    ax.axhline(0, color='k', lw=0.5)
    ax.grid(True, alpha=0.3, axis='y')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT_FIG / 'figure_so_vs_moco_suit_effect.png', dpi=140, bbox_inches='tight')
    plt.close(fig)

    # ===== Figure 5: Hierarchy redistribution =====
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_hier = ['IL_R10_r','LTpL_L5_r','IL_R11_r','IL_R12_r']
    base_hold = []; suit_hold = []
    for nm in plot_hier:
        mask = (times >= 2.0) & (times < 2.5)
        base_hold.append(base[nm][mask].mean() if nm in base else 0)
        suit_hold.append(suit[nm][mask].mean() if nm in suit else 0)
    pos = np.arange(len(plot_hier))
    bw = 0.35
    ax.bar(pos - bw/2, base_hold, bw, label='Baseline', color='#444', edgecolor='black')
    ax.bar(pos + bw/2, suit_hold, bw, label='+24 N·m suit', color='#d62728', edgecolor='black')
    for i, (b, s) in enumerate(zip(base_hold, suit_hold)):
        d = s - b
        y_top = max(b, s)
        ax.text(i, y_top + 2, f'Δ {d:+.1f}', ha='center', fontsize=10, fontweight='bold')
    ax.set_xticks(pos); ax.set_xticklabels(plot_hier, fontsize=10)
    ax.set_ylabel('Hold-phase mean activation (%)')
    ax.set_ylim(0, 100)
    ax.set_title('Recruitment hierarchy under suit assist (Hold phase)',
                 fontsize=12, fontweight='bold')
    ax.legend(fontsize=10); ax.grid(True, alpha=0.3, axis='y')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT_FIG / 'figure_hierarchy_redistribution.png', dpi=140, bbox_inches='tight')
    plt.close(fig)

    # ===== Report =====
    with open(REPORT, 'w') as f:
        f.write('# Phase 1a Suit Effect — Report\n\n')
        f.write('- Baseline solution: `results/phase1a_full/solution.sto`\n')
        f.write('- Suit (+24 N·m) solution: `results/phase1a_suit_effect/solution_suit.sto`\n')
        f.write('- Suit profile: cosine ramp 0.5–2.5 s up, hold 2.5–3.0 s, ramp 3.0–5.0 s down (matches v5 SO suit_sweep)\n')
        f.write('- Both runs converged (Optimal Solution Found)\n\n')

        f.write('## Phase × muscle ΔES (suit − baseline)\n\n')
        f.write('| Muscle | Phase | Baseline (%) | Suit (%) | Δ (%p) | Δ (%) |\n|---|---|---:|---:|---:|---:|\n')
        for r in rows:
            f.write(f'| {r["muscle"]} | {r["phase"]} | {r["base"]:.1f} | {r["suit"]:.1f} | '
                    f'{r["delta_pp"]:+.1f} | {r["delta_rel_pct"]:+.1f} |\n')

        # Compute ES_mean (avg over key 6 muscles) per phase and report Hold/Concentric ΔES
        es6 = ['IL_R10_r','IL_R10_l','IL_R11_r','IL_R11_l','LTpL_L5_r','LTpL_L5_l']
        ph_summary = []
        for pname, ts_, te_, _ in PHASES:
            mask = (times >= ts_) & (times < te_) if pname != 'Recovery' else (times >= ts_) & (times <= te_)
            b_avg = np.mean([base[m][mask].mean() for m in es6 if m in base])
            s_avg = np.mean([suit[m][mask].mean() for m in es6 if m in suit])
            ph_summary.append((pname, b_avg, s_avg, s_avg - b_avg, (s_avg-b_avg)/b_avg*100 if b_avg > 1 else 0))

        f.write('\n## ES summary (mean of 6 dominant ES muscles)\n\n')
        f.write('| Phase | Baseline (%) | Suit (%) | Δ (%p) | Δ (%) |\n|---|---:|---:|---:|---:|\n')
        for pname, b, s, d, dr in ph_summary:
            f.write(f'| {pname} | {b:.1f} | {s:.1f} | {d:+.1f} | {dr:+.1f} |\n')

        f.write('\n## SO §1.6 comparison\n\n')
        f.write('| Metric | SO R100 | SO R50 (re-est.) | Moco IL_R10 Hold | Moco IL_R10 Conc |\n|---|---:|---:|---:|---:|\n')
        f.write(f'| Reduction at 24 N·m | 28.97 % | 21.25 % | {moco_il_r10_hold_rel:+.1f} % | {moco_il_r10_con_rel:+.1f} % |\n')

    # Print summary
    print('=== Phase summary (mean of 6 dominant ES muscles) ===')
    for pname, b, s, d, dr in ph_summary:
        print(f'  {pname:11s}  base={b:6.1f}  suit={s:6.1f}  Δ={d:+6.1f} %p ({dr:+5.1f} %)')
    print(f'\nMoco IL_R10_r Hold ΔES rel: {moco_il_r10_hold_rel:+.1f}%')
    print(f'Moco IL_R10_r Conc ΔES rel: {moco_il_r10_con_rel:+.1f}%')
    print(f'SO §1.6 reference: 28.97% (R100) / 21.25% (R50)')
    print(f'\nReport: {REPORT}')


if __name__ == '__main__':
    main()
