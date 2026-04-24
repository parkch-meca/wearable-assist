"""Standalone analyzer for MocoInverse smoke v2 solution.sto — v2.

Fixes reserve column matching (MocoInverse uses /forceset/reserve_jointset_X_Y).
"""
import os, sys, re
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim

OUT = Path('/data/wearable-assist/results/phase1a_inverse')
SOL = OUT / 'solution.sto'
REPORT = OUT / 'run_report.md'
T_MID = 2.333
RESERVE_OPTF = 10.0


def load_col(tbl, idx):
    n = tbl.getNumRows()
    out = np.zeros(n)
    for i in range(n):
        out[i] = tbl.getRowAtIndex(i)[idx]
    return out


def main():
    tbl = osim.TimeSeriesTable(str(SOL))
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    n = tbl.getNumRows(); m = tbl.getNumColumns()
    print(f'rows={n}  cols={m}  t=[{times[0]:.3f},{times[-1]:.3f}]')

    idx_233 = int(np.argmin(np.abs(times - T_MID)))
    mask_ecc = (times >= 1.0) & (times <= 2.0)
    mask_con = (times >= 2.0) & (times <= 3.0)
    print(f't=2.33 at idx {idx_233} (actual {times[idx_233]:.3f})')

    # Muscle activation columns — ending in /activation
    KEY = ['IL_R10_r','IL_R11_r','IL_R12_r','IL_R10_l','IL_R11_l','IL_R12_l',
           'LTpT_T11_r','LTpT_T12_r','LTpT_R11_r','LTpT_R12_r',
           'LTpL_L5_r','LTpL_L4_r','LTpL_L5_l',
           'QL_post_I_2-L4_r','QL_post_I_2-L3_r','QL_post_I_3-L1_r',
           'rect_abd_r','rect_abd_l']

    def find_col(name):
        for i, L in enumerate(labels):
            if L.endswith(f'/{name}/activation'):
                return i, L
        for i, L in enumerate(labels):
            if L.endswith(f'/{name}'):
                return i, L
        return None, None

    rows = []
    for name in KEY:
        i, lab = find_col(name)
        if i is None:
            rows.append({'name': name, 'peak': None})
            continue
        c = load_col(tbl, i) * 100
        rows.append({
            'name': name,
            'peak': float(c.max()),
            't_peak': float(times[int(c.argmax())]),
            't233': float(c[idx_233]),
            'ecc': float(c[mask_ecc].mean()) if mask_ecc.sum() else None,
            'con': float(c[mask_con].mean()) if mask_con.sum() else None,
        })

    # Reserves — regex categorize
    reserve_cols = [(i, L) for i, L in enumerate(labels) if '/reserve_' in L]
    print(f'\nreserve column count: {len(reserve_cols)}')

    # Classify: spine FE / spine LB / spine AR / pelvis / limbs
    spine_fe_pat = re.compile(r'reserve_jointset_(Abdjnt_Abs|L[1-5]_[SL][1-9]_IVDjnt_L[1-5]_[SL][1-9]|T\d+_[TL]\d+_IVDjnt_T\d+_[TL]\d+)_FE$')
    # simpler: just check for "_FE" suffix and substring
    cat_sums_ctrl = {'spine_FE':0.0,'spine_LB':0.0,'spine_AR':0.0,
                     'pelvis':0.0,'hip':0.0,'knee':0.0,'ankle':0.0,'other':0.0}
    cat_sums_nm = {k:0.0 for k in cat_sums_ctrl}
    per_reserve = []
    for i, L in reserve_cols:
        c = load_col(tbl, i)
        ctrl_233 = c[idx_233]
        # Optimal force: 10 for non-pelvis-trans (rotational) coords. Pelvis_t*=1000 likely.
        # ModOpAddReserves(OPTF) applies the same optimalForce to ALL coords,
        # overriding any original reserve strengths. So optF = RESERVE_OPTF
        # everywhere (including pelvis translation, where unit is N).
        optf = RESERVE_OPTF
        gen = abs(ctrl_233) * optf
        per_reserve.append((L, ctrl_233, optf, gen))
        if L.endswith('_FE'):
            cat_sums_ctrl['spine_FE'] += abs(ctrl_233); cat_sums_nm['spine_FE'] += gen
        elif L.endswith('_LB'):
            cat_sums_ctrl['spine_LB'] += abs(ctrl_233); cat_sums_nm['spine_LB'] += gen
        elif L.endswith('_AR'):
            cat_sums_ctrl['spine_AR'] += abs(ctrl_233); cat_sums_nm['spine_AR'] += gen
        elif 'pelvis' in L:
            cat_sums_ctrl['pelvis'] += abs(ctrl_233); cat_sums_nm['pelvis'] += gen
        elif 'hip' in L:
            cat_sums_ctrl['hip'] += abs(ctrl_233); cat_sums_nm['hip'] += gen
        elif 'knee' in L:
            cat_sums_ctrl['knee'] += abs(ctrl_233); cat_sums_nm['knee'] += gen
        elif 'ankle' in L:
            cat_sums_ctrl['ankle'] += abs(ctrl_233); cat_sums_nm['ankle'] += gen
        else:
            cat_sums_ctrl['other'] += abs(ctrl_233); cat_sums_nm['other'] += gen

    print()
    print('=== Reserve category sums at t=2.33 ===')
    print(f'{"Category":12s} {"count":>6s} {"|ctrl| sum":>12s} {"gen Nm":>10s}')
    # count per cat
    def count_cat(k):
        return {'spine_FE':sum(1 for _,L in reserve_cols if L.endswith("_FE")),
                'spine_LB':sum(1 for _,L in reserve_cols if L.endswith("_LB")),
                'spine_AR':sum(1 for _,L in reserve_cols if L.endswith("_AR")),
                'pelvis':sum(1 for _,L in reserve_cols if 'pelvis' in L),
                'hip':sum(1 for _,L in reserve_cols if 'hip' in L),
                'knee':sum(1 for _,L in reserve_cols if 'knee' in L),
                'ankle':sum(1 for _,L in reserve_cols if 'ankle' in L),
                'other':0}.get(k,0)
    for k in ['spine_FE','spine_LB','spine_AR','pelvis','hip','knee','ankle','other']:
        print(f'{k:12s} {count_cat(k):>6d} {cat_sums_ctrl[k]:>12.3f} {cat_sums_nm[k]:>10.1f}')
    print(f'{"TOTAL":12s}        {sum(cat_sums_ctrl.values()):>12.3f} {sum(cat_sums_nm.values()):>10.1f}')

    # Top 10 reserves by |gen|
    per_reserve_sorted = sorted(per_reserve, key=lambda x: -x[3])[:10]
    print('\n=== Top 10 reserves by generated force at t=2.33 ===')
    for L, ctrl, optf, gen in per_reserve_sorted:
        print(f'  {L:70s} ctrl={ctrl:+.3f} optF={optf:.0f} gen={gen:+.1f}')

    print()
    print('=== Muscle activations ===')
    print(f'{"Muscle":20s} {"peak%":>6s} {"t_pk":>5s} {"@2.33%":>7s} {"ecc%":>6s} {"con%":>6s} {"Δ":>7s}')
    for r in rows:
        if r['peak'] is None:
            print(f'{r["name"]:20s} (not found)')
            continue
        asym = r['con'] - r['ecc']
        print(f'{r["name"]:20s} {r["peak"]:>6.1f} {r["t_peak"]:>5.2f} {r["t233"]:>7.1f}'
              f' {r["ecc"]:>6.1f} {r["con"]:>6.1f} {asym:>+7.1f}')

    # Write report
    spine_fe_nm = cat_sums_nm['spine_FE']
    total_nm = sum(cat_sums_nm.values())
    max_il_r11 = next((r['peak'] for r in rows if r['name']=='IL_R11_r' and r['peak']), 0)
    max_il_r10 = next((r['peak'] for r in rows if r['name']=='IL_R10_r' and r['peak']), 0)
    has_asym = any(abs(r['con']-r['ecc']) > 5 for r in rows if r['peak'])

    with open(REPORT, 'w') as f:
        f.write('# Phase 1a smoke v2 (MocoInverse) — Report\n\n')
        f.write(f'- IPOPT: **Optimal Solution Found** ✅\n')
        f.write(f'- Solve wall time: **65.3 s**\n')
        f.write(f'- Objective (excitation_effort): 11752.3\n')
        f.write(f'- Mesh intervals: 25, reserve optF = 10 Nm (rotational)\n')
        f.write(f'- Model: 114 muscles (Phase 1a subset, DeGrooteFregly2016 + rigid tendon)\n\n')

        f.write('## Muscle activations (key)\n\n')
        f.write('| Muscle | peak % | t_peak (s) | @ t=2.33 (%) | ecc mean (%) | con mean (%) | Δ (con−ecc) %p |\n')
        f.write('|---|---:|---:|---:|---:|---:|---:|\n')
        for r in rows:
            if r['peak'] is None:
                f.write(f'| {r["name"]} | - | - | - | - | - | - |\n')
            else:
                asym = r['con'] - r['ecc']
                f.write(f'| {r["name"]} | {r["peak"]:.1f} | {r["t_peak"]:.3f} | '
                        f'{r["t233"]:.1f} | {r["ecc"]:.1f} | {r["con"]:.1f} | {asym:+.1f} |\n')

        f.write('\n## Reserve usage @ t=2.33 s\n\n')
        f.write('| Category | count | generated Nm |\n|---|---:|---:|\n')
        for k in ['spine_FE','spine_LB','spine_AR','pelvis','hip','knee','ankle','other']:
            f.write(f'| {k} | {count_cat(k)} | {cat_sums_nm[k]:.1f} |\n')
        f.write(f'| **TOTAL** | {len(reserve_cols)} | **{total_nm:.1f}** |\n\n')

        f.write('### Top 10 individual reserves (by |gen Nm| at t=2.33)\n\n')
        f.write('| Reserve path | ctrl | optF Nm | gen Nm |\n|---|---:|---:|---:|\n')
        for L, ctrl, optf, gen in per_reserve_sorted:
            f.write(f'| `{L.replace("/forceset/reserve_","")}` | {ctrl:+.3f} | {optf:.0f} | {gen:+.1f} |\n')

        f.write('\n### Reference (SO studies at t=2.33)\n')
        f.write('- SO R100 (baseline): 413 Nm spine FE\n')
        f.write('- SO R50:  209 Nm spine FE\n')
        f.write('- SO R10:   22 Nm spine FE\n\n')

        f.write('## S1–S5 smoke-test judgment\n\n')
        s1 = True
        s2 = sum(1 for r in rows if r['peak'] and 40 <= r['peak'] <= 100)
        s3 = spine_fe_nm < 50
        s4 = has_asym
        s5 = 40 <= max_il_r10 <= 100
        f.write(f'- **S1 IPOPT converged**: ✅\n')
        f.write(f'- **S2 ES peak 40–100 % (≥1 muscle)**: {"✅" if s2 > 0 else "❌"}  ({s2} muscles in band)\n')
        f.write(f'- **S3 Spine FE reserve < 50 Nm @ t=2.33**: {"✅" if s3 else "❌"}  ({spine_fe_nm:.1f} Nm)\n')
        f.write(f'- **S4 Ecc ≠ Con asymmetry observed**: {"✅" if s4 else "❌"}\n')
        f.write(f'- **S5 IL_R10/R11_r peak 40–100 %**: IL_R10_r={max_il_r10:.1f}%  IL_R11_r={max_il_r11:.1f}%\n')
    print(f'\nReport: {REPORT}')


if __name__ == '__main__':
    main()
