"""[3] ROM 수정 + 좌팔 수정 재실행 결과 대조.

새 해석 실행 없음 — .sto 를 읽어 지표를 계산하고 직전 확정본과 대조만 한다.

■ 지표 정의 (직전 확정본과 문자 그대로 동일. 원본 JSON 에서 역산해 재현 검증 완료)
  창(win) = 슈트 토크 |thor_T_z| 가 최대의 90 % 이상인 구간 ∩ 해석 시간범위
  (a) 전주기 정점 (짝지은 시점): OFF 의 전주기 ES peak 최대값과, **그 시점의** ON 값
      (ON 의 자체 최대는 슈트로 억제된 창 밖에서 날 수 있어 짝을 이루지 않는다)
  (b) 창내 ES peak 평균      : ES peak 의 창 내 평균          ← 주 지표
  (c) 창내 ES mean 평균      : 76개 평균의 창 내 평균

세 정의 모두 기존 unified_numbers.json 에서 역산해 오차 0 으로 재현 검증했다.
"""
import os
import re
import json
import numpy as np
import opensim as osim

ES_PREFIX = ('IL_', 'LTpL', 'LTpT')
SPINE_KEYS = ('_FE', '_LB', '_AR', 'Abs_')

NEW = {k: (f'/data/romfix_unified/{k}_off', f'/data/romfix_unified/{k}_on')
       for k in ('squat', 'stoop', 'box', 'gait', 'carry')}
OLD = {'squat': ('/data/tight_unified/squat_off', '/data/tight_unified/squat_on'),
       'stoop': ('/data/tight_unified/stoop_off', '/data/tight_unified/stoop_on'),
       'box':   ('/data/tight_unified/box_off', '/data/tight_unified/box_on'),
       'gait':  ('/data/gait_results/gait_off_tight', '/data/gait_results/gait_on_tight'),
       'carry': ('/data/carry_results/carry_off', '/data/carry_results/carry_on')}
NAME = {'squat': '맨몸 스쿼트', 'stoop': '맨몸 스툽', 'box': '박스 들기',
        'gait': '맨몸 보행', 'carry': '박스 운반'}
ORDER = ['squat', 'stoop', 'box', 'gait', 'carry']
# 운동학이 바뀐 동작 (나머지는 ROM 수정만 -> 회귀 검증 대상)
MOT_CHANGED = {'stoop', 'box', 'carry'}


def es_series(d):
    t = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_activation.sto')
    T = np.array(list(t.getIndependentColumn()))
    L = list(t.getColumnLabels())
    E = [l for l in L if l.startswith(ES_PREFIX)]
    S = np.vstack([[float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]
                   for c in E]) * 100
    return T, S, len(E)


# 결과 디렉터리에 외력 XML 이 복사돼 있지 않은 경우(보행 tight 재실행 등)의 대체 경로
EXT_FALLBACK = {'/data/gait_results/gait_on_tight': '/data/gait_results/gait_on'}


def suit_window(d_on, T):
    """슈트 토크 |thor_T_z| >= 0.9*max 인 구간 ∩ 해석 시간범위."""
    src = d_on
    xmls = [f for f in os.listdir(src)
            if f.endswith('.xml') and 'setup' not in f and 'controls' not in f]
    if not xmls:
        src = EXT_FALLBACK[d_on]
        xmls = [f for f in os.listdir(src)
                if f.endswith('.xml') and 'setup' not in f and 'controls' not in f]
    d_on = src
    txt = open(os.path.join(d_on, xmls[0])).read()
    df = re.findall(r'<datafile>([^<]+)<', txt)[0].strip()
    p = df if df.startswith('/') else os.path.join(d_on, os.path.basename(df))
    t = osim.TimeSeriesTable(p)
    Te = np.array(list(t.getIndependentColumn()))
    col = t.getDependentColumn('thor_T_z')
    v = np.abs(np.array([float(col[i]) for i in range(t.getNumRows())]))
    m = v >= 0.9 * v.max()
    idx = np.where(m)[0]
    lo, hi = Te[idx[0]], Te[idx[-1]]
    return max(lo, T[0]), min(hi, T[-1])


def spine_reserve(d):
    p = f'{d}/so_StaticOptimization_force.sto'
    if not os.path.exists(p):
        return float('nan')
    t = osim.TimeSeriesTable(p)
    L = [l for l in t.getColumnLabels()
         if l.startswith('reserve_') and any(k in l for k in SPINE_KEYS)]
    best = 0.0
    for c in L:
        col = t.getDependentColumn(c)
        best = max(best, max(abs(float(col[i])) for i in range(t.getNumRows())))
    return best


def metrics(d_off, d_on):
    T, So, n = es_series(d_off)
    _, Sn, _ = es_series(d_on)
    w0, w1 = suit_window(d_on, T)
    m = (T >= w0) & (T <= w1)
    pk_o, pk_n = So.max(axis=0), Sn.max(axis=0)
    mn_o, mn_n = So.mean(axis=0), Sn.mean(axis=0)
    i_pk = int(np.argmax(pk_o))          # (a) 는 OFF 정점 시점에서 짝지어 읽는다
    return dict(a_off=float(pk_o[i_pk]), a_on=float(pk_n[i_pk]), a_t=float(T[i_pk]),
                b_off=float(pk_o[m].mean()), b_on=float(pk_n[m].mean()),
                c_off=float(mn_o[m].mean()), c_on=float(mn_n[m].mean()),
                res=float(spine_reserve(d_off)),      # 기존 정의와 동일: OFF 기준
                res_on=float(spine_reserve(d_on)),
                win=[float(w0), float(w1)], nES=n)


def rel(o, n):
    o2, n2 = round(o, 2), round(n, 2)
    return round(100.0 * round(n2 - o2, 2) / o2, 1)


def main():
    missing = [k for k in ORDER
               if not os.path.exists(f'{NEW[k][0]}/so_StaticOptimization_activation.sto')]
    if missing:
        print('아직 결과 없음:', missing)
        return

    new = {k: metrics(*NEW[k]) for k in ORDER}
    old = json.load(open('/data/tight_unified/unified_numbers.json'))

    # 지표 정의 재현 검증 — 기존 경로에 대해 같은 함수를 돌려 기존 JSON 과 일치하는지
    print('=' * 104)
    print('[0] 지표 정의 재현 검증 (기존 결과에 새 코드를 적용 -> 기존 JSON 과 일치해야 함)')
    print('=' * 104)
    worst = 0.0
    for k in ORDER:
        chk = metrics(*OLD[k])
        for f in ('a_off', 'a_on', 'b_off', 'b_on', 'c_off', 'c_on'):
            worst = max(worst, abs(chk[f] - old[k][f]))
    print(f'  전 동작·전 지표 최대 차이 {worst:.3e}   -> '
          f'{"재현 OK" if worst < 1e-6 else "불일치 (조사 필요)"}')

    print('\n' + '=' * 104)
    print('[1] 신규 vs 기존 — 주 지표 (b) 창내 ES peak 평균')
    print('=' * 104)
    print(f"{'동작':12s} {'운동학':8s} "
          f"{'기존 OFF':>9s} {'신규 OFF':>9s} {'ΔOFF':>8s}  "
          f"{'기존 ON':>9s} {'신규 ON':>9s} {'ΔON':>8s}  "
          f"{'기존 효과':>9s} {'신규 효과':>9s} {'Δ효과':>8s}")
    table = {}
    for k in ORDER:
        o, n = old[k], new[k]
        eo, en = rel(o['b_off'], o['b_on']), rel(n['b_off'], n['b_on'])
        tag = '수정' if k in MOT_CHANGED else '동일'
        print(f"{NAME[k]:12s} {tag:8s} "
              f"{o['b_off']:9.2f} {n['b_off']:9.2f} {n['b_off']-o['b_off']:+8.2f}  "
              f"{o['b_on']:9.2f} {n['b_on']:9.2f} {n['b_on']-o['b_on']:+8.2f}  "
              f"{eo:+8.1f}% {en:+8.1f}% {en-eo:+7.1f}%p")
        table[k] = dict(old=o, new=n, eff_old=eo, eff_new=en)

    print('\n' + '=' * 104)
    print('[2] 세 지표 전체 — 슈트 효과 (%)')
    print('=' * 104)
    print(f"{'동작':12s} " + ''.join(f"{'(' + m + ') 기존':>11s}{'신규':>9s}{'차':>8s}"
                                     for m in 'abc'))
    for k in ORDER:
        o, n = old[k], new[k]
        row = f'{NAME[k]:12s} '
        for mm in 'abc':
            eo, en = rel(o[f'{mm}_off'], o[f'{mm}_on']), rel(n[f'{mm}_off'], n[f'{mm}_on'])
            row += f'{eo:+10.1f}%{en:+8.1f}%{en-eo:+7.1f}p'
        print(row)

    print('\n' + '=' * 104)
    print('[3] 회귀 검증 — 운동학이 안 바뀐 동작은 ROM 수정만의 효과')
    print('=' * 104)
    for k in ORDER:
        if k in MOT_CHANGED:
            continue
        o, n = old[k], new[k]
        d = max(abs(n[f] - o[f]) for f in ('a_off', 'a_on', 'b_off', 'b_on', 'c_off', 'c_on'))
        verd = '동일 (ROM 수정은 SO 결과에 영향 없음)' if d < 0.005 else f'차이 {d:.4f} %p'
        print(f'  {NAME[k]:12s} 전 지표 최대 차이 {d:.3e} %p   -> {verd}')

    print('\n' + '=' * 104)
    print('[4] spine reserve 최대 (N·m) — tight 유지 확인')
    print('=' * 104)
    for k in ORDER:
        print(f"  {NAME[k]:12s} 기존 {old[k]['res']:6.2f}  신규 {new[k]['res']:6.2f}")

    json.dump(new, open('/data/romfix_unified/unified_numbers.json', 'w'), indent=1)
    json.dump(table, open('/data/romfix_unified/comparison.json', 'w'),
              ensure_ascii=False, indent=1)
    print('\nSAVED /data/romfix_unified/unified_numbers.json, comparison.json')


if __name__ == '__main__':
    main()
