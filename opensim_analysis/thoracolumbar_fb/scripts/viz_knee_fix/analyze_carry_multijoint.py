"""[2] 운반 다부위 기여 분해 — 3지표 + 부위별 주동근 활성도 + 가산성 검정.

■ 핵심 질문
  전체 ON 효과가 각 부위 단독 효과의 **합**과 같은가.
    합보다 크면 상호작용(+), 작으면 간섭 또는 재분배.

■ 지표
  ES 계열 (IL/LTpL/LTpT)  — (a) peak · (b) 활성도 합 · (c) 근력 합
  삼각근 (DELT1~3)         — 어깨 부위 확인용 (이번 범위에서 어깨 슈트는 제외)
  팔꿈치 굴근 (BIC/BRA/BRD) — 팔꿈치 부위 지표. ES 지표로는 보이지 않는다.
"""
import os
import json
import numpy as np
import opensim as osim

D = '/data/suit_carry'
CONDS = ['off', 'waist', 'elbow', 'elbow_ext', 'all']
LAB = {'off': 'OFF', 'waist': '허리만 (T8→천골→허벅지)', 'elbow': '팔꿈치만 (기본안)',
       'elbow_ext': '팔꿈치만 (연장안)', 'all': '전체 ON (허리+팔꿈치 연장안)'}
GROUPS = {
    'ES': ('IL_', 'LTpL', 'LTpT'),
    'DELT': ('DELT1', 'DELT2', 'DELT3', 'DELT1_l', 'DELT2_l', 'DELT3_l'),
    'ELBFLX': ('BIClong', 'BICshort', 'BRA_', 'BRD_'),
}


def table(tag, kind):
    p = f'{D}/{tag}/so_StaticOptimization_{kind}.sto'
    t = osim.TimeSeriesTable(p)
    T = np.array(list(t.getIndependentColumn()))
    L = list(t.getColumnLabels())
    return T, L, t


def series(tag, kind, keep):
    T, L, t = table(tag, kind)
    cols = [c for c in L if c.startswith(keep)]
    S = np.vstack([[float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]
                   for c in cols])
    if kind == 'activation':
        S = S * 100
    return T, cols, S


def window():
    """OFF 의 ES peak 가 최대의 90 % 이상인 구간 — 기존 정의와 동일."""
    T, _, A = series('off', 'activation', GROUPS['ES'])
    pk = A.max(axis=0)
    m = pk >= 0.9 * pk.max()
    return float(T[m].min()), float(T[m].max())


def metrics(tag, win):
    out = {}
    for g, keep in GROUPS.items():
        T, cols, A = series(tag, 'activation', keep)
        m = (T >= win[0]) & (T <= win[1])
        dt = np.gradient(T[m])
        _, colf, Fv = series(tag, 'force', keep)
        mf = m
        out[g] = dict(
            peak=float(A.max(axis=0)[m].mean()),
            act_sum=float(np.sum(A[:, m].sum(axis=0) * dt)),
            force_sum=float(np.sum(np.abs(Fv[:, mf]).sum(axis=0) * dt)),
            mean=float(A[:, m].mean()),
            n=len(cols))
    # 관절 액추에이터 잔차 (조임이 유효한지 확인)
    T, L, t = table(tag, 'force')
    m = (T >= win[0]) & (T <= win[1])
    res = {}
    for c in ('elbow_R_actuator', 'reserve_elbow_flexion_r',
              'elv_angle_r_actuator', 'reserve_L5_S1_FE'):
        if c in L:
            v = np.array([float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())])
            res[c] = float(np.abs(v[m]).mean())
    out['residual'] = res
    return out


def rel(o, n):
    o2, n2 = round(o, 3), round(n, 3)
    return round(100.0 * round(n2 - o2, 3) / o2, 1) if abs(o2) > 1e-9 else float('nan')


def main():
    miss = [c for c in CONDS
            if not os.path.exists(f'{D}/{c}/so_StaticOptimization_activation.sto')]
    if miss:
        print('결과 없음:', miss)
        return
    win = window()
    R = {c: metrics(c, win) for c in CONDS}
    base = R['off']
    print('=' * 104)
    print(f'운반 다부위 기여 분해 — 창 {win[0]:.3f}~{win[1]:.3f} s')
    print('=' * 104)

    print(f"\n{'조건':30s} {'(a) ES peak':>18s} {'(b) 활성도 합':>18s} {'(c) 근력 합':>18s}")
    print(f"  {'OFF (절대값)':28s} {base['ES']['peak']:11.2f}       "
          f"{base['ES']['act_sum']:11.1f}       {base['ES']['force_sum']:11.0f}")
    for c in CONDS[1:]:
        d = R[c]['ES']
        print(f"  {LAB[c]:28s} {d['peak']:8.2f} ({rel(base['ES']['peak'], d['peak']):+6.1f}%) "
              f"{d['act_sum']:8.1f} ({rel(base['ES']['act_sum'], d['act_sum']):+6.1f}%) "
              f"{d['force_sum']:8.0f} ({rel(base['ES']['force_sum'], d['force_sum']):+6.1f}%)")

    print('\n' + '=' * 104)
    print('부위별 주동근 활성도 (창내 평균 %) — ES 지표로는 안 보이는 부분')
    print('=' * 104)
    print(f"{'조건':30s} {'ES 평균':>12s} {'삼각근':>16s} {'팔꿈치 굴근':>18s}")
    for c in CONDS:
        d = R[c]
        s = f"  {LAB[c]:28s} {d['ES']['mean']:8.2f}"
        for g in ('DELT', 'ELBFLX'):
            r = rel(base[g]['mean'], d[g]['mean'])
            s += f" {d[g]['mean']:9.3f}" + (f' ({r:+6.1f}%)' if c != 'off' else '        ')
        print(s)

    print('\n' + '=' * 104)
    print('★ 가산성 검정 — 전체 ON = 허리 단독 + 팔꿈치 단독 인가')
    print('=' * 104)
    add = {}
    for g in ('ES', 'ELBFLX'):
        for k in ('peak', 'act_sum', 'force_sum', 'mean'):
            dw = R['waist'][g][k] - base[g][k]
            de = R['elbow_ext'][g][k] - base[g][k]
            da = R['all'][g][k] - base[g][k]
            gap = da - (dw + de)
            add[f'{g}.{k}'] = dict(waist=dw, elbow=de, sum=dw + de, all=da, gap=gap,
                                   gap_pct=(100.0 * gap / abs(dw + de)
                                            if abs(dw + de) > 1e-9 else float('nan')))
    print(f"{'지표':22s} {'허리Δ':>10s} {'팔꿈치Δ':>10s} {'합':>10s} {'전체 ONΔ':>11s} "
          f"{'차이':>10s} {'차이/합':>9s}")
    for k, v in add.items():
        print(f"  {k:20s} {v['waist']:10.2f} {v['elbow']:10.2f} {v['sum']:10.2f} "
              f"{v['all']:11.2f} {v['gap']:10.2f} {v['gap_pct']:8.1f}%")

    g = add['ES.act_sum']
    if abs(g['gap_pct']) < 5:
        verdict = '가산적 — 부위 간 상호작용 없음'
    elif g['gap'] < 0:
        verdict = '합보다 큼 → 상호작용(+). 함께 쓰면 각각의 합보다 더 준다'
    else:
        verdict = '합보다 작음 → 간섭 또는 재분배'
    print(f"\n  판정 (ES 활성도 합 기준): {verdict}")

    print('\n' + '=' * 104)
    print('잔차 점검 — 조임이 유효한가 (액추에이터가 부하를 흡수하면 안 된다)')
    print('=' * 104)
    for c in CONDS:
        r = R[c]['residual']
        print(f"  {LAB[c]:28s} " + '  '.join(f'{k}={v:.3f}' for k, v in r.items()))

    json.dump(dict(win=win, res=R, add=add), open(f'{D}/metrics.json', 'w'),
              ensure_ascii=False, indent=1)
    print(f'\nSAVED {D}/metrics.json')


if __name__ == '__main__':
    main()
