"""[1]/[2] 부여 스팬 조건 분석 — 재분배 원인 분리 + 상부 고정 높이 스윕.

지표·창 정의는 5동작 논문과 동일. OFF 는 /data/romfix_unified/stoop_off 재사용.
"""
import os
import json
import numpy as np
import opensim as osim

OFF = '/data/romfix_unified/stoop_off'
REF24 = '/data/romfix_unified/stoop_on'
WIN = (2.091667, 3.408333)          # 24 N·m 조건 토크 프로파일로 정의된 창
ES_PREFIX = ('IL_', 'LTpL', 'LTpT')
# 추가 근육군 — 요방형근(QL) / 복직근(RA) 이 모델에 있으면 함께 본다
GRP = {'IL': ('IL_',), 'LTpL': ('LTpL',), 'LTpT': ('LTpT',),
       'QL': ('QL_', 'Quad'), 'RA': ('RA_', 'rect_abd', 'Rect')}

COND = [
    ('(i) 토크커플 · 흉추1↔골반', REF24, 'couple_T1', 24.0),
    ('(i-16) 토크커플 · 흉추1↔골반 16.5', '/data/suit_16Nm/couple16', 'couple_T1_16', 16.5),
    ('(ii) 토크커플 · L1↔골반', '/data/suit_span/couple_L1', 'couple_L1', 16.5),
    ('(iii) 경로힘 · L1→허벅지', '/data/suit_16Nm/path16', 'path_L1', 16.5),
    ('(iv) 경로힘 · T8→허벅지', '/data/suit_span/path_T8', 'path_T8', 16.5),
    ('경로힘 · T12→허벅지', '/data/suit_span/path_T12', 'path_T12', 16.5),
    ('경로힘 · T4→허벅지', '/data/suit_span/path_T4', 'path_T4', 16.5),
]


def table(d):
    return osim.TimeSeriesTable(f'{d}/so_StaticOptimization_activation.sto')


def peaks(d):
    t = table(d)
    T = np.array(list(t.getIndependentColumn()))
    L = list(t.getColumnLabels())
    m = (T >= WIN[0]) & (T <= WIN[1])
    out = {}
    for g, pres in GRP.items():
        C = [c for c in L if c.startswith(pres)]
        if not C:
            out[g] = None
            continue
        S = np.vstack([[float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]
                       for c in C]) * 100
        out[g] = (float(S.max(axis=0)[m].mean()), len(C))
    ES = [c for c in L if c.startswith(ES_PREFIX)]
    S = np.vstack([[float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]
                   for c in ES]) * 100
    out['ES'] = (float(S.max(axis=0)[m].mean()), len(ES))
    return out


def rel(o, n):
    o2, n2 = round(o, 2), round(n, 2)
    return round(100.0 * round(n2 - o2, 2) / o2, 1)


def compress(d, levels):
    """지정 레벨의 관절 반력 크기 대리 지표 — 근육 힘 합 (압축 경향)."""
    p = f'{d}/so_StaticOptimization_force.sto'
    if not os.path.exists(p):
        return float('nan')
    t = osim.TimeSeriesTable(p)
    T = np.array(list(t.getIndependentColumn()))
    m = (T >= WIN[0]) & (T <= WIN[1])
    L = [c for c in t.getColumnLabels() if c.startswith(('LTpT', 'IL_R'))]
    S = np.vstack([[float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]
                   for c in L])
    return float(S.sum(axis=0)[m].mean())


def main():
    miss = [tag for _, d, tag, _ in COND
            if not os.path.exists(f'{d}/so_StaticOptimization_activation.sto')]
    if miss:
        print('아직 결과 없음:', miss)
        return
    base = peaks(OFF)
    print('=' * 108)
    print('[1] 재분배 원인 분리 — 창내 peak 평균 (%) 과 변화율')
    print('=' * 108)
    hdr = f"{'조건':30s} {'토크':>6s} "
    for g in ('IL', 'LTpL', 'LTpT'):
        hdr += f'{g:>16s}'
    hdr += f"{'ES 전체':>16s}"
    print(hdr)
    print(f"  {'OFF (기준)':28s} {'—':>6s} " +
          ''.join(f"{base[g][0]:10.2f}      " for g in ('IL', 'LTpL', 'LTpT')) +
          f"{base['ES'][0]:10.2f}")
    res = {}
    for lab, d, tag, tq in COND:
        p = peaks(d)
        row = {g: dict(off=base[g][0], on=p[g][0], rel=rel(base[g][0], p[g][0]))
               for g in ('IL', 'LTpL', 'LTpT', 'ES') if p[g]}
        row['torque'] = tq
        row['label'] = lab
        row['compress'] = compress(d, None)
        res[tag] = row
        line = f'  {lab:28s} {tq:6.1f} '
        for g in ('IL', 'LTpL', 'LTpT', 'ES'):
            line += f"{p[g][0]:7.2f}({row[g]['rel']:+6.1f}%)"
        print(line)

    print('\n' + '=' * 108)
    print('[1] 판정 — (i)↔(ii) 는 스팬만, (ii)↔(iii) 은 방식만 다르다')
    print('=' * 108)
    e = {k: res[k]['ES']['rel'] for k in res}
    print(f"  (i-16) 토크커플 흉추1↔골반  ES {e['couple_T1_16']:+6.1f} %   스팬 넓음 · 커플")
    print(f"  (ii)   토크커플 L1↔골반     ES {e['couple_L1']:+6.1f} %   스팬 좁음 · 커플")
    print(f"  (iii)  경로힘   L1→허벅지   ES {e['path_L1']:+6.1f} %   스팬 좁음 · 경로힘")
    print(f"  (iv)   경로힘   T8→허벅지   ES {e['path_T8']:+6.1f} %   스팬 넓음 · 경로힘")
    d_span = e['couple_L1'] - e['couple_T1_16']
    d_mode = e['path_L1'] - e['couple_L1']
    print(f"\n  스팬 효과 (i-16 → ii)  {d_span:+6.1f} %p")
    print(f"  방식 효과 (ii → iii)   {d_mode:+6.1f} %p")
    dom = '스팬' if abs(d_span) > abs(d_mode) else '부여 방식(지점 집중)'
    print(f"  → 지배 원인: **{dom}**")

    print('\n' + '=' * 108)
    print('[2] 상부 고정 높이 스윕 (경로힘)  ⚠️ 현 하드웨어는 L1. 그 위는 설계 제안')
    print('=' * 108)
    print(f"{'상부 앵커':10s} {'ES 전체':>10s} {'IL':>10s} {'LTpL':>10s} {'LTpT':>10s} "
          f"{'흉추 근육힘 합 (N)':>18s}")
    for tag, nm in (('path_L1', 'L1 (현재)'), ('path_T12', 'T12'),
                    ('path_T8', 'T8'), ('path_T4', 'T4')):
        r = res[tag]
        print(f"  {nm:10s} {r['ES']['rel']:+9.1f}% {r['IL']['rel']:+9.1f}% "
              f"{r['LTpL']['rel']:+9.1f}% {r['LTpT']['rel']:+9.1f}% {r['compress']:17.1f}")
    off_c = compress(OFF, None)
    print(f"  {'OFF':10s} {'—':>10s} {'—':>10s} {'—':>10s} {'—':>10s} {off_c:17.1f}")

    json.dump(dict(off={g: base[g][0] for g in ('IL', 'LTpL', 'LTpT', 'ES')},
                   off_compress=off_c, cond=res),
              open('/data/suit_span/results.json', 'w'), ensure_ascii=False, indent=1)
    print('\nSAVED /data/suit_span/results.json')


if __name__ == '__main__':
    main()
