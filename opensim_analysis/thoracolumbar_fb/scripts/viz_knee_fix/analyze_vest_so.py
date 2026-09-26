"""[정정 3] 조끼 사슬 SO 결과 분석 — 표면 EMG 대응 ES + 전체 ES + 보조 근육.

■ ES 지표 두 가지를 병기한다
  ES(표면)  요추부 장늑근·최장근 중 **피부 쪽(후방 외피)** 근속만 — 표면 전극 대응
            선택은 눈대중이 아니라 L1~L3 높이대에서 후방 x 좌표로 실측해 고른다
  ES(전체)  기존 76개 (IL_ · LTpL · LTpT) — 기존 지표와의 연속성

■ 보조 지표
  둔근 (glut_max/med) · 햄스트링 (bifemlh/sh) — 슈트가 부하를 어디로 옮기는지 확인용
  ※ 이 모델에는 반막양근·반건양근이 없다 (하지 근육군 축소 모델) — 한계로 기록

■ O3 판정
  실측 "반복 들기에서 척추기립근 EMG 40 % 이상 감소" 에 대응하는 값은
  **표면 ES 활성도의 창내 평균**(EMG 진폭 대응)으로 본다. peak·합도 함께 보고한다.
"""
import os
import sys
import json
import numpy as np
import opensim as osim

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SO = '/data/suit_vest/so'
OFF20 = '/data/romfix_unified/box_off'
MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom.osim')
ES_PREFIX = ('IL_', 'LTpL', 'LTpT')
GLUT = ('glut_max', 'glut_med')
HAM = ('bifemlh', 'bifemsh')
OUT = '/data/suit_vest'

COND20 = [('off', OFF20, '미착용'), ('cold', f'{SO}/cold', '착용·미가열'),
          ('hot100', f'{SO}/hot100', '가열 F_hot 100 N'),
          ('hot150', f'{SO}/hot150', '가열 F_hot 150 N'),
          ('hot200', f'{SO}/hot200', '가열 F_hot 200 N ⚠️O1 이탈'),
          ('hot250', f'{SO}/hot250', '가열 F_hot 250 N ⚠️O1 이탈'),
          ('k2x2', f'{SO}/k2x2', '■4 사슬 경질 2배'),
          ('k2x4', f'{SO}/k2x4', '■4 사슬 경질 4배'),
          ('hot225', f'{SO}/hot225', '■4 구동기 1.5배 ⚠️O1 이탈')]
COND36 = [('off_36', f'{SO}/off_36', '미착용 36 kg'),
          ('cold_36', f'{SO}/cold_36', '착용·미가열 36 kg'),
          ('hot150_36', f'{SO}/hot150_36', '가열 150 N 36 kg')]


def surface_es(pct=50.0):
    """L1~L3 높이대에서 후방 외피에 가까운 ES 근속을 실측으로 고른다."""
    m = osim.Model(MODEL)
    s = m.initSystem()
    m.realizePosition(s)
    bs = m.getBodySet()
    ys = []
    for b in ('lumbar1', 'lumbar2', 'lumbar3'):
        p = bs.get(b).getPositionInGround(s)
        ys.append(p.get(1))
    y_lo, y_hi = min(ys) - 0.03, max(ys) + 0.03
    ms = m.getMuscles()
    rows = []
    for i in range(ms.getSize()):
        mu = ms.get(i)
        nm = mu.getName()
        if not nm.startswith(ES_PREFIX):
            continue
        ps = mu.getGeometryPath().getPathPointSet()
        xs = []
        for j in range(ps.getSize()):
            g = ps.get(j).getLocationInGround(s)
            if y_lo <= g.get(1) <= y_hi:
                xs.append(g.get(0))
        if xs:
            rows.append((nm, float(np.min(xs))))       # 가장 후방(작은 x)
    if not rows:
        return []
    xs = np.array([r[1] for r in rows])
    thr = np.percentile(xs, pct)                       # 후방 pct % = 피부 쪽
    sel = sorted([r[0] for r in rows if r[1] <= thr])
    return sel


def series(d, cols, kind='activation'):
    t = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_{kind}.sto')
    T = np.array(list(t.getIndependentColumn()))
    have = [c for c in cols if c in list(t.getColumnLabels())]
    S = np.vstack([[float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]
                   for c in have])
    return T, have, S * 100 if kind == 'activation' else S


def names(d, prefixes):
    t = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_activation.sto')
    return [c for c in t.getColumnLabels() if c.startswith(prefixes)]


def window(d, es_all):
    T, _, A = series(d, es_all)
    pk = A.max(axis=0)
    m = pk >= 0.9 * pk.max()
    return float(T[m].min()), float(T[m].max())


def metrics(d, cols, win):
    T, have, A = series(d, cols)
    m = (T >= win[0]) & (T <= win[1])
    dt = np.gradient(T[m])
    _, _, F = series(d, cols, 'force')
    return dict(peak=float(A.max(axis=0)[m].mean()),
                mean=float(A[:, m].mean()),
                act_sum=float(np.sum(A[:, m].sum(axis=0) * dt)),
                force_sum=float(np.sum(np.abs(F[:, m]).sum(axis=0) * dt)),
                n=len(have))


def rel(o, n):
    o2, n2 = round(o, 4), round(n, 4)
    return 100.0 * (n2 - o2) / o2 if abs(o2) > 1e-9 else float('nan')


def block(conds, tag):
    ok = [(k, d, lab) for k, d, lab in conds
          if os.path.exists(f'{d}/so_StaticOptimization_activation.sto')]
    if not ok:
        print(f'[{tag}] 결과 없음')
        return {}
    es_all = names(ok[0][1], ES_PREFIX)
    surf = [c for c in surface_es() if c in es_all]
    surf_var = {p: [c for c in surface_es(p) if c in es_all] for p in (35.0, 60.0)}
    glut = names(ok[0][1], GLUT)
    ham = names(ok[0][1], HAM)
    win = window(ok[0][1], es_all)
    print('=' * 108)
    print(f'[{tag}] 창 {win[0]:.3f}~{win[1]:.3f} s · ES 전체 {len(es_all)} · '
          f'ES 표면 {len(surf)} · 둔근 {len(glut)} · 햄스트링 {len(ham)}')
    print('=' * 108)
    R = {}
    for k, d, lab in ok:
        R[k] = dict(label=lab,
                    surf=metrics(d, surf, win), all=metrics(d, es_all, win),
                    glut=metrics(d, glut, win), ham=metrics(d, ham, win))
    base = R[ok[0][0]]
    print(f"{'조건':26s} {'ES표면 평균':>14s} {'ES표면 peak':>14s} "
          f"{'ES전체 평균':>14s} {'ES전체 peak':>14s} {'둔근':>10s} {'햄스':>10s}")
    print(f"  {'미착용 (절대값 %)':24s} {base['surf']['mean']:9.2f}      "
          f"{base['surf']['peak']:9.2f}      {base['all']['mean']:9.2f}      "
          f"{base['all']['peak']:9.2f}  {base['glut']['mean']:8.2f}  "
          f"{base['ham']['mean']:8.2f}")
    for k, d, lab in ok[1:]:
        r = R[k]
        f = lambda g, m: rel(base[g][m], r[g][m])
        print(f"  {lab:24s} {r['surf']['mean']:6.2f}({f('surf','mean'):+6.1f}%) "
              f"{r['surf']['peak']:6.2f}({f('surf','peak'):+6.1f}%) "
              f"{r['all']['mean']:6.2f}({f('all','mean'):+6.1f}%) "
              f"{r['all']['peak']:6.2f}({f('all','peak'):+6.1f}%) "
              f"{f('glut','mean'):+8.1f}% {f('ham','mean'):+8.1f}%")
    for k in R:
        for g in ('surf', 'all', 'glut', 'ham'):
            R[k][g]['rel'] = {m: rel(base[g][m], R[k][g][m])
                              for m in ('peak', 'mean', 'act_sum', 'force_sum')}
    # 표면 문턱 민감도 — 35 / 50 / 60 %
    print(f"\n  [민감도] 표면 집합 문턱  50 % = {len(surf)}개 (기본) · "
          f"35 % = {len(surf_var[35.0])} · 60 % = {len(surf_var[60.0])}")
    if len(ok) > 1:
        print(f"    {'조건':26s} " + ' '.join(f'{p:>10.0f}%' for p in (35, 50, 60)))
        for k, d, lab in ok[1:]:
            vals = []
            for p, cols in ((35.0, surf_var[35.0]), (50.0, surf), (60.0, surf_var[60.0])):
                v = metrics(d, cols, win)['mean']
                b = metrics(ok[0][1], cols, win)['mean']
                vals.append(rel(b, v))
            print(f"    {lab:26s} " + ' '.join(f'{v:+10.1f}%' for v in vals))
            R[k]['surf_sens'] = {35: vals[0], 50: vals[1], 60: vals[2]}
    R['_meta'] = dict(win=win, surf=surf, n_all=len(es_all), glut=glut, ham=ham,
                      surf35=surf_var[35.0], surf60=surf_var[60.0])
    return R


def high_tension(tagref='hot150', frac=0.7):
    """슈트 장력이 최대의 frac 이상인 구간 — 보조가 실제로 실리는 프레임만."""
    import suit_span_conditions as SC
    T, K = SC.load_mot(f'/data/suit_vest/ext/ext_{tagref}.mot')
    F = np.sqrt(sum(K[f'vR0_F_v{a}'] ** 2 for a in 'xyz'))
    return T, F, frac


def block_hi(conds, win, surf, tag):
    """고장력 창에서의 표면 ES — 슈트가 실제로 힘을 내는 구간의 효과."""
    T, F, frac = high_tension()
    m = (T >= win[0]) & (T <= win[1])
    thr = frac * F[m].max()
    sel = m & (F >= thr)
    print('\n' + '=' * 108)
    print(f'[{tag}] 고장력 창 — 슈트 장력 ≥ {thr:.0f} N ({frac:.0%} of max) · '
          f'{int(sel.sum())} 프레임 ({T[sel].min():.2f}~{T[sel].max():.2f} s)')
    print('=' * 108)
    out = {}
    base = None
    for k, d, lab in conds:
        if not os.path.exists(f'{d}/so_StaticOptimization_activation.sto'):
            continue
        t = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_activation.sto')
        Tt = np.array(list(t.getIndependentColumn()))
        cc = [c for c in surf if c in list(t.getColumnLabels())]
        S = np.vstack([[float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]
                       for c in cc]) * 100
        mm = np.interp(Tt, T, sel.astype(float)) > 0.5
        v = dict(mean=float(S[:, mm].mean()), peak=float(S.max(axis=0)[mm].mean()))
        if base is None:
            base = v
            print(f"  {lab:26s} 평균 {v['mean']:6.2f} %   peak {v['peak']:6.2f} %  (기준)")
        else:
            v['rel_mean'] = rel(base['mean'], v['mean'])
            v['rel_peak'] = rel(base['peak'], v['peak'])
            print(f"  {lab:26s} 평균 {v['mean']:6.2f} ({v['rel_mean']:+6.1f}%)   "
                  f"peak {v['peak']:6.2f} ({v['rel_peak']:+6.1f}%)")
        out[k] = v
    return dict(thr=float(thr), n=int(sel.sum()),
                t=(float(T[sel].min()), float(T[sel].max())), res=out)


def main():
    R20 = block(COND20, '들기 20 kg')
    print()
    R36 = block(COND36, '들기 36 kg')

    print('\n' + '=' * 108)
    print('[O3] 실측 대조 — 표면 ES 활성도 창내 평균 (EMG 진폭 대응), 목표 −40 %')
    print('=' * 108)
    o3 = {}
    for tag, R in (('20 kg', R20), ('36 kg', R36)):
        if not R:
            continue
        for k, v in R.items():
            if k == '_meta' or k.startswith('off'):
                continue
            d = v['surf']['rel']['mean']
            o3[f'{tag}/{k}'] = d
            mark = '✅ 도달' if d <= -40 else ('근접' if d <= -30 else '미달')
            print(f"  {tag:6s} {v['label']:26s} {d:+7.1f} %   {mark}")

    if 'cold' in R20 and 'hot150' in R20:
        c = R20['cold']['surf']['rel']['mean']
        h = R20['hot150']['surf']['rel']['mean']
        print(f"\n  수동/능동 비 (표면 ES 평균 감소): 미가열 {c:+.1f} % / "
              f"가열150 {h:+.1f} % → 수동이 능동의 {abs(c/h)*100:.0f} %"
              if abs(h) > 1e-9 else '')

    print('\n' + '=' * 108)
    print('[■4] 설계 레버 — 사슬 경질 강성 vs 구동기 힘 (기준 = 가열 150 N)')
    print('=' * 108)
    if 'hot150' in R20:
        b = R20['hot150']['surf']['rel']['mean']
        print(f"  {'조건':28s} {'표면 ES 평균':>12s} {'기준 대비':>10s}")
        print(f"  {'기준 (가열 150 N)':26s} {b:+11.1f} %")
        for k in ('k2x2', 'k2x4', 'hot225'):
            if k in R20:
                v = R20[k]['surf']['rel']['mean']
                print(f"  {R20[k]['label']:26s} {v:+11.1f} % {v - b:+9.1f} %p")

    HI = block_hi(COND20, R20['_meta']['win'], R20['_meta']['surf'], '들기 20 kg') \
        if R20 else {}

    json.dump(dict(R20=R20, R36=R36, o3=o3, hi=HI),
              open(f'{OUT}/vest_so_metrics.json', 'w'),
              ensure_ascii=False, indent=1, default=str)
    print(f'\nSAVED {OUT}/vest_so_metrics.json')


if __name__ == '__main__':
    main()
