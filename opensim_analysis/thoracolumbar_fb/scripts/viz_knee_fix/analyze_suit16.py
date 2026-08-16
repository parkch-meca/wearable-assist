"""[1]/[4] 16 N·m 실검증 + 설계 레버 결과 분석.

지표 정의는 5동작 논문과 동일하다 (analyze_romfix 와 문자 그대로 같은 함수).
  창(win) = 슈트 토크가 최대의 90 % 이상인 구간 ∩ 해석 시간범위
  (b) 창내 ES peak 평균  ← 주 지표
OFF 는 /data/romfix_unified/stoop_off 를 재사용한다.
"""
import os
import json
import numpy as np
import opensim as osim

OFF = '/data/romfix_unified/stoop_off'
REF24 = '/data/romfix_unified/stoop_on'          # 기존 24 N·m 조건
NEW = '/data/suit_16Nm'
ES_PREFIX = ('IL_', 'LTpL', 'LTpT')
LUMB = ['L5_S1_FE', 'L4_L5_FE', 'L3_L4_FE', 'L2_L3_FE', 'L1_L2_FE']

CASES = {
    'path16':   ('경로힘 (재산출 r, 100 N)', 16.5),
    'couple16': ('토크 커플 16.5 N·m', 16.5),
    'leverA':   ('(A) 보조력 200 N', 30.6),
    'leverB':   ('(B) 강성 k=20 N/mm', 16.6),
    'leverC':   ('(C) 모멘트 암 +20 mm', 19.0),
}


def es(d):
    t = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_activation.sto')
    T = np.array(list(t.getIndependentColumn()))
    L = list(t.getColumnLabels())
    E = [c for c in L if c.startswith(ES_PREFIX)]
    S = np.vstack([[float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]
                   for c in E]) * 100
    return T, S


def suit_torque_series(d):
    """해당 조건이 요추에 준 보조 토크(양측 합) 시계열 — 창 정의와 실효 토크 산출용."""
    import re
    xmls = [f for f in os.listdir(d)
            if f.endswith('.xml') and 'setup' not in f and 'controls' not in f]
    if xmls:
        txt = open(os.path.join(d, xmls[0])).read()
    else:
        return None, None
    df = re.findall(r'<datafile>([^<]+)<', txt)[0].strip()
    p = df if df.startswith('/') else os.path.join(d, os.path.basename(df))
    if not os.path.exists(p):
        return None, None
    t = osim.TimeSeriesTable(p)
    Te = np.array(list(t.getIndependentColumn()))
    L = list(t.getColumnLabels())
    if 'thor_T_z' in L:                       # 토크 커플 조건
        col = t.getDependentColumn('thor_T_z')
        return Te, np.abs([float(col[i]) for i in range(t.getNumRows())])
    return None, None


def window(d_on, T):
    Te, v = suit_torque_series(d_on)
    if v is None:
        return None
    m = v >= 0.9 * v.max()
    idx = np.where(m)[0]
    return max(Te[idx[0]], T[0]), min(Te[idx[-1]], T[-1])


def metric_b(d_off, d_on, win):
    T, So = es(d_off)
    _, Sn = es(d_on)
    m = (T >= win[0]) & (T <= win[1])
    return float(So.max(axis=0)[m].mean()), float(Sn.max(axis=0)[m].mean())


def rel(o, n):
    o2, n2 = round(o, 2), round(n, 2)
    return round(100.0 * round(n2 - o2, 2) / o2, 1)


def main():
    missing = [k for k in CASES
               if not os.path.exists(f'{NEW}/{k}/so_StaticOptimization_activation.sto')]
    if missing:
        print('아직 결과 없음:', missing)
        return
    T, _ = es(OFF)
    win24 = window(REF24, T)          # 24 N·m 조건의 창 — 전 조건 공통으로 쓴다
    print('=' * 96)
    print(f'[기준] 창 = {win24[0]:.3f} ~ {win24[1]:.3f} s  (24 N·m 조건 토크 프로파일로 정의)')
    print('       OFF = /data/romfix_unified/stoop_off (재사용)')
    print('=' * 96)

    off24, on24 = metric_b(OFF, REF24, win24)
    e24 = rel(off24, on24)
    print(f'\n■ 기존 24 N·m 조건   OFF {off24:.2f} → ON {on24:.2f}   효과 {e24:+.1f} %')

    out = {'ref24': dict(off=off24, on=on24, eff=e24, torque=24.0)}
    print(f"\n{'조건':26s} {'토크 (N·m)':>10s} {'OFF':>8s} {'ON':>8s} {'효과':>8s} "
          f"{'24 대비':>8s}")
    for k, (lab, tq) in CASES.items():
        o, n = metric_b(OFF, f'{NEW}/{k}', win24)
        e = rel(o, n)
        out[k] = dict(label=lab, torque=tq, off=o, on=n, eff=e)
        print(f'  {lab:26s} {tq:10.1f} {o:8.2f} {n:8.2f} {e:+7.1f} % {e/e24*100:7.0f} %')

    # ── 선형성 검사 — 0 과 24 를 잇는 직선 위에 16.5 가 있는가 ──
    print('\n' + '=' * 96)
    print('[1] 선형성 검사 — (0 N·m, 0 %) 와 (24 N·m, 기존값) 을 잇는 직선 대비')
    print('=' * 96)
    slope = e24 / 24.0
    print(f'  두 점 기울기 {slope:.4f} %/N·m')
    ok = True
    for k in ('couple16', 'path16'):
        d = out[k]
        pred = slope * d['torque']
        dev = d['eff'] - pred
        rel_dev = abs(dev) / abs(pred) * 100
        flag = rel_dev <= 10.0
        ok &= flag
        print(f"  {d['label']:26s} 예측 {pred:+6.1f} %  실측 {d['eff']:+6.1f} %  "
              f"편차 {dev:+5.1f} %p ({rel_dev:4.1f} %)  "
              f"{'선형 유지' if flag else '⚠ 이탈'}")
    print(f'\n  판정: {"선형성 유지 — 병기 가능" if ok else "⚠ 선형성 이탈 — 중단 보고 대상"}')
    out['linearity'] = dict(slope=slope, pass_=bool(ok))

    # ── 근육군 분해 — path16 이 왜 효과가 없는지 ──
    print('\n' + '=' * 96)
    print('[진단] 근육군별 창내 peak 평균 (%) — 보조가 어디로 갔는가')
    print('=' * 96)
    GRP = {'IL (장늑근)': 'IL_', 'LTpL (최장근 요추부)': 'LTpL',
           'LTpT (최장근 흉추부)': 'LTpT'}
    T2, So = es(OFF)
    mw = (T2 >= win24[0]) & (T2 <= win24[1])
    tt = osim.TimeSeriesTable(f'{OFF}/so_StaticOptimization_activation.sto')
    # es() 가 돌려주는 행렬은 ES 부분집합이므로, 인덱스도 그 부분집합 기준이어야 한다
    labs = [c for c in tt.getColumnLabels() if c.startswith(ES_PREFIX)]
    print(f"{'근육군':22s} {'n':>4s} {'OFF':>8s} " +
          ''.join(f'{CASES[k][0][:10]:>11s}' for k in ('path16', 'couple16')) +
          f"{'24 N·m':>9s}")
    grp = {}
    for lab, pre in GRP.items():
        idx = [i for i, c in enumerate(labs) if c.startswith(pre)]
        row = {}
        for tag, d in (('OFF', OFF), ('path16', f'{NEW}/path16'),
                       ('couple16', f'{NEW}/couple16'), ('24', REF24)):
            _, S = es(d)
            row[tag] = float(S[idx].max(axis=0)[mw].mean())
        grp[lab] = row
        print(f'  {lab:22s} {len(idx):4d} {row["OFF"]:8.2f} {row["path16"]:11.2f} '
              f'{row["couple16"]:11.2f} {row["24"]:9.2f}')
    out['groups'] = grp

    json.dump(out, open(f'{NEW}/results.json', 'w'), ensure_ascii=False, indent=1)
    print(f'\nSAVED {NEW}/results.json')


if __name__ == '__main__':
    main()
