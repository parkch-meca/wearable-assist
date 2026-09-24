"""[2] 용량–반응 곡선 — 스툽 토크커플 0 / 8 / 16.5 / 24 N·m × 3지표.

■ 지표 (L-07 에 따라 3지표 병기)
  (a) ES peak      창내 프레임별 최대 활성도의 평균 [5동작 주 지표]
  (b) 활성도 합     창내 전 ES 근육 활성도 합의 시간적분 (%·s)
  (c) 근력 합       창내 전 ES 근육 힘 합의 시간적분 (N·s)
  창은 24 N·m 조건으로 정의한 (2.091667, 3.408333) s 를 전 조건 공통으로 쓴다
  — analyze_metrics3 와 같은 값이다.

■ 읽는 법
  곡선이 **오목**(저용량 구간이 더 효율적)하면 두 점 비례 배분은 과소평가가 된다.
  참고로 같은 16.5 N·m 를 현 하드웨어 기하(경로힘 L1→허벅지)로 주면 어디에 찍히는지도
  함께 표시한다 — 크기 축(곡선)과 부여 방식 축은 별개라는 것이 요점이다.
"""
import os
import json
import numpy as np
import opensim as osim

WIN = (2.091667, 3.408333)
ES_PREFIX = ('IL_', 'LTpL', 'LTpT')
OFF = '/data/romfix_unified/stoop_off'

# (토크, 경로, 라벨, 종류)
POINTS = [
    (0.0, OFF, '미착용 (0 N·m)', 'couple'),
    (8.0, '/data/suit_dose/couple8', '토크커플 8 N·m', 'couple'),
    (16.5, '/data/suit_16Nm/couple16', '토크커플 16.5 N·m', 'couple'),
    (24.0, '/data/romfix_unified/stoop_on', '토크커플 24 N·m', 'couple'),
]
REF_PATH = (16.5, '/data/suit_16Nm/path16', '경로힘 16.5 N·m (현 하드웨어 기하)', 'path')
OUT = '/data/suit_dose'
METRICS = [('peak', '(a) ES peak', '%'), ('act_sum', '(b) 활성도 합', '%·s'),
           ('force_sum', '(c) 근력 합', 'N·s')]


def series(d, kind):
    t = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_{kind}.sto')
    T = np.array(list(t.getIndependentColumn()))
    L = [c for c in t.getColumnLabels() if c.startswith(ES_PREFIX)]
    S = np.vstack([[float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]
                   for c in L])
    return T, L, S * 100 if kind == 'activation' else S


def metrics(d):
    T, L, A = series(d, 'activation')
    m = (T >= WIN[0]) & (T <= WIN[1])
    dt = np.gradient(T[m])
    _, Lf, Fv = series(d, 'force')
    j = A[:, m].argmax(axis=0)
    names, cnt = np.unique([L[x] for x in j], return_counts=True)
    dom = names[np.argmax(cnt)], float(100.0 * cnt.max() / len(j))
    return dict(peak=float(A.max(axis=0)[m].mean()),
                act_sum=float(np.sum(A[:, m].sum(axis=0) * dt)),
                force_sum=float(np.sum(np.abs(Fv[:, m]).sum(axis=0) * dt)),
                dominant=dom, n_win=int(m.sum()), n_es=len(L))


def rel(o, n):
    o2, n2 = round(o, 3), round(n, 3)
    return round(100.0 * round(n2 - o2, 3) / o2, 1)


def main():
    miss = [lab for _, d, lab, _ in POINTS
            if not os.path.exists(f'{d}/so_StaticOptimization_activation.sto')]
    if miss:
        print('결과 없음:', miss)
        return
    R = {}
    for tq, d, lab, kind in POINTS + [REF_PATH]:
        if not os.path.exists(f'{d}/so_StaticOptimization_activation.sto'):
            continue
        R[lab] = dict(torque=tq, kind=kind, **metrics(d))
    base = R['미착용 (0 N·m)']

    print('=' * 100)
    print(f'용량–반응 (스툽) — 창 {WIN[0]:.3f}~{WIN[1]:.3f} s · ES {base["n_es"]}근육 · '
          f'창내 {base["n_win"]}프레임')
    print('=' * 100)
    print(f"{'조건':30s} {'토크':>6s} {'(a) ES peak':>20s} {'(b) 활성도 합':>20s} "
          f"{'(c) 근력 합':>20s}")
    print(f"  {'미착용 (절대값)':28s} {'0.0':>6s} {base['peak']:11.2f} %      "
          f"{base['act_sum']:11.1f}        {base['force_sum']:11.0f}")
    for lab, v in R.items():
        if lab == '미착용 (0 N·m)':
            continue
        r = {k: rel(base[k], v[k]) for k, _, _ in METRICS}
        v['rel'] = r
        print(f"  {lab:28s} {v['torque']:6.1f} {v['peak']:9.2f} ({r['peak']:+6.1f}%) "
              f"{v['act_sum']:9.1f} ({r['act_sum']:+6.1f}%) "
              f"{v['force_sum']:9.0f} ({r['force_sum']:+6.1f}%)")
    base['rel'] = {k: 0.0 for k, _, _ in METRICS}

    print('\n' + '=' * 100)
    print('[1] 선형성 — (0, 0 %) 와 (24 N·m, 실측) 을 잇는 직선 대비')
    print('=' * 100)
    lin = {}
    for k, name, _ in METRICS:
        e24 = R['토크커플 24 N·m']['rel'][k]
        slope = e24 / 24.0
        print(f'\n  {name}   두 점 기울기 {slope:+.3f} %/N·m')
        for tq, lab in ((8.0, '토크커플 8 N·m'), (16.5, '토크커플 16.5 N·m')):
            act = R[lab]['rel'][k]
            pred = slope * tq
            dev = act - pred
            frac = act / e24 * 100
            lin[f'{k}@{tq}'] = dict(actual=act, linear=pred, dev=dev, frac24=frac)
            print(f'    {tq:5.1f} N·m  실측 {act:+6.1f} %  선형예측 {pred:+6.1f} %  '
                  f'편차 {dev:+5.1f} %p   24 N·m 효과의 {frac:5.1f} % '
                  f'(토크는 {tq/24*100:.0f} %)')

    print('\n' + '=' * 100)
    print('[2] 곡선 형상 판정')
    print('=' * 100)
    for k, name, _ in METRICS:
        f8 = lin[f'{k}@8.0']['frac24']
        f16 = lin[f'{k}@16.5']['frac24']
        shape = ('오목 (저용량이 더 효율적 — 비례 배분은 과소평가)'
                 if (f8 > 8 / 24 * 100 and f16 > 16.5 / 24 * 100) else
                 '볼록 (고용량이 더 효율적)'
                 if (f8 < 8 / 24 * 100 and f16 < 16.5 / 24 * 100) else '혼재')
        print(f'  {name:16s} 8 N·m 이 {f8:5.1f} % · 16.5 N·m 이 {f16:5.1f} % '
              f'(토크 비 33 / 69 %) → {shape}')

    pk = R.get('경로힘 16.5 N·m (현 하드웨어 기하)')
    if pk:
        print('\n' + '=' * 100)
        print('[3] 같은 16.5 N·m 를 현 하드웨어 기하로 주면 — 크기 축과 방식 축은 별개')
        print('=' * 100)
        for k, name, _ in METRICS:
            print(f"  {name:16s} 토크커플 {R['토크커플 16.5 N·m']['rel'][k]:+6.1f} %  vs  "
                  f"경로힘 {pk['rel'][k]:+6.1f} %")
        print('  ⇒ 곡선은 **분산 부여(토크커플) 축**의 용량–반응이다. 현 하드웨어 기하는 '
              '이 곡선 위에 있지 않다.')

    print('\n' + '=' * 100)
    print('[4] peak 결정 근육 — 조건별')
    print('=' * 100)
    for lab, v in R.items():
        print(f"  {lab:30s} {v['dominant'][0]:14s} 점유 {v['dominant'][1]:5.1f} %")

    json.dump(dict(win=WIN, points=R, linearity=lin),
              open(f'{OUT}/dose.json', 'w'), ensure_ascii=False, indent=1)
    print(f'\nSAVED {OUT}/dose.json')


if __name__ == '__main__':
    main()
