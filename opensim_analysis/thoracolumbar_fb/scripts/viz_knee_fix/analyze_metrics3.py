"""[0]/[1] ES peak 결정 근육 규명 + 3지표 병기.

■ 왜 필요한가
  (iv) T8 조건은 IL −25.5 %, LTpT −26.6 % 인데 ES peak 전체는 −2.8 % 다.
  ES peak 는 "그 프레임에서 가장 활성이 높은 근육 하나"만 보므로,
  다른 근육이 그 자리를 차지하면 나머지 근육의 개선이 지표에 잡히지 않는다.

■ 지표 (다관절 연구 병기용 — 5동작 논문의 주 지표는 변경하지 않는다)
  (a) ES peak       : 창내 프레임별 최대 활성도의 평균 [기존 주 지표]
  (b) ES 활성도 합   : 창내 전 ES 근육 활성도 합의 시간적분 (%·s)
  (c) ES 근력 합     : 창내 전 ES 근육 힘 합의 시간적분 (N·s)
  (b)(c) 는 "근육 절반이 좋아졌는데 지표는 그대로"인 상황을 잡아낸다.
"""
import os
import json
import numpy as np
import opensim as osim

OFF = '/data/romfix_unified/stoop_off'
WIN = (2.091667, 3.408333)
ES_PREFIX = ('IL_', 'LTpL', 'LTpT')
GRP = {'IL': 'IL_', 'LTpL': 'LTpL', 'LTpT': 'LTpT'}

COND = [
    ('OFF', OFF),
    ('(i) 커플 T1↔골반 16.5', '/data/suit_16Nm/couple16'),
    ('(ii) 커플 L1↔골반', '/data/suit_span/couple_L1'),
    ('(iii) 경로힘 L1→허벅지', '/data/suit_16Nm/path16'),
    ('(iv) 경로힘 T8→허벅지', '/data/suit_span/path_T8'),
    ('경로힘 T12→허벅지', '/data/suit_span/path_T12'),
    ('경로힘 T4→허벅지', '/data/suit_span/path_T4'),
    # 하단 고정 스윕 (■2-3) — 현 하드웨어는 허벅지. 나머지는 설계 제안
    ('T8→천골', '/data/suit_span/path_T8_sacrum'),
    ('T8→장골능', '/data/suit_span/path_T8_pelvis'),
    ('T8→천골경유→허벅지', '/data/suit_span/path_T8_sacfem'),
    ('L1→천골경유→허벅지', '/data/suit_span/path_L1_sacfem'),
    ('참고: 커플 T1↔골반 24', '/data/romfix_unified/stoop_on'),
]


def series(d, kind='activation'):
    t = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_{kind}.sto')
    T = np.array(list(t.getIndependentColumn()))
    L = [c for c in t.getColumnLabels() if c.startswith(ES_PREFIX)]
    S = np.vstack([[float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]
                   for c in L])
    if kind == 'activation':
        S = S * 100
    return T, L, S


def metrics(d):
    T, L, A = series(d, 'activation')
    m = (T >= WIN[0]) & (T <= WIN[1])
    Tw = T[m]
    dt = np.gradient(Tw) if len(Tw) > 1 else np.array([1.0])
    pk = A.max(axis=0)[m]
    # (a) 창내 peak 평균
    a = float(pk.mean())
    # (b) 활성도 합의 시간적분
    b = float(np.sum(A[:, m].sum(axis=0) * dt))
    # (c) 근력 합의 시간적분
    _, Lf, Fv = series(d, 'force')
    c = float(np.sum(np.abs(Fv[:, m]).sum(axis=0) * dt))
    # peak 결정 근육
    j = A[:, m].argmax(axis=0)
    names, cnt = np.unique([L[x] for x in j], return_counts=True)
    order = np.argsort(-cnt)
    dom = [(names[i], int(cnt[i]), 100.0 * cnt[i] / len(j)) for i in order[:3]]
    # 근육군별 peak
    gp = {}
    for g, pre in GRP.items():
        idx = [i for i, cc in enumerate(L) if cc.startswith(pre)]
        gp[g] = float(A[idx][:, m].max(axis=0).mean())
    return dict(peak=a, act_sum=b, force_sum=c, dominant=dom, group=gp, n=len(L))


def rel(o, n):
    o2, n2 = round(o, 2), round(n, 2)
    return round(100.0 * round(n2 - o2, 2) / o2, 1) if abs(o2) > 1e-9 else float('nan')


def main():
    miss = [lab for lab, d in COND
            if not os.path.exists(f'{d}/so_StaticOptimization_activation.sto')]
    if miss:
        print('결과 없음:', miss)
        return
    R = {lab: metrics(d) for lab, d in COND}
    base = R['OFF']

    print('=' * 104)
    print('[0] ES peak 를 결정한 근육 — 창내 프레임에서 최대 활성이었던 근육')
    print('=' * 104)
    print(f"{'조건':26s} {'1위 근육':16s} {'점유':>6s} {'그 근육 peak':>12s}  2위")
    for lab, _ in COND:
        d = R[lab]
        n1 = d['dominant'][0]
        n2 = d['dominant'][1] if len(d['dominant']) > 1 else ('—', 0, 0)
        print(f"  {lab:24s} {n1[0]:16s} {n1[2]:5.0f}% {d['peak']:11.2f}   "
              f"{n2[0]} ({n2[2]:.0f}%)")

    print('\n' + '=' * 104)
    print('[1] 3지표 병기 — OFF 대비 변화율')
    print('=' * 104)
    print(f"{'조건':26s} {'(a) ES peak':>22s} {'(b) 활성도 합':>22s} {'(c) 근력 합':>22s}")
    print(f"  {'OFF (절대값)':24s} {base['peak']:12.2f}          "
          f"{base['act_sum']:12.1f}          {base['force_sum']:12.0f}")
    out = {}
    for lab, _ in COND[1:]:
        d = R[lab]
        ra = rel(base['peak'], d['peak'])
        rb = rel(base['act_sum'], d['act_sum'])
        rc = rel(base['force_sum'], d['force_sum'])
        out[lab] = dict(peak=d['peak'], act=d['act_sum'], force=d['force_sum'],
                        rel_peak=ra, rel_act=rb, rel_force=rc,
                        dominant=d['dominant'], group=d['group'])
        print(f"  {lab:24s} {d['peak']:9.2f} ({ra:+6.1f}%) "
              f"{d['act_sum']:9.1f} ({rb:+6.1f}%) {d['force_sum']:9.0f} ({rc:+6.1f}%)")

    print('\n' + '=' * 104)
    print('[1] 판정 — (iv) T8 조건이 실제로 효과가 없는가, 지표 문제인가')
    print('=' * 104)
    k = '(iv) 경로힘 T8→허벅지'
    d = out[k]
    print(f"  (a) ES peak     {d['rel_peak']:+6.1f} %")
    print(f"  (b) 활성도 합    {d['rel_act']:+6.1f} %")
    print(f"  (c) 근력 합      {d['rel_force']:+6.1f} %")
    if min(abs(d['rel_act']), abs(d['rel_force'])) > 3 * abs(d['rel_peak']):
        print('  → 총 부하 지표에서 뚜렷한 개선. **지표 선택의 문제**다.')
    elif max(abs(d['rel_act']), abs(d['rel_force'])) < 5:
        print('  → 총 부하 지표에서도 미미. **실제로 효과가 없다**.')
    else:
        print('  → 중간. 두 지표를 병기해 판단해야 한다.')

    json.dump(dict(off=dict(peak=base['peak'], act=base['act_sum'],
                            force=base['force_sum'], dominant=base['dominant'],
                            group=base['group']), cond=out),
              open('/data/suit_span/metrics3.json', 'w'), ensure_ascii=False, indent=1)
    print('\nSAVED /data/suit_span/metrics3.json')


if __name__ == '__main__':
    main()
