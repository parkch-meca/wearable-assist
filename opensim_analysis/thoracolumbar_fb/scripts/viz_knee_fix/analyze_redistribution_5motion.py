"""[3] 5동작 재분배 재집계 — 보행 예외인가, 일반 현상인가.

⚠️ 5동작 결과 수치는 변경하지 않는다. 기존 .sto 를 다시 읽어 **재집계·재해석만** 한다.

■ 가설
  기존 해석: 보행의 IL 침묵 / LTpL 증가 재분배는 "저부하 × 면외 운동" 조합에서만
             나타나는 예외다.
  새 가설  : 부여 스팬이 부하 스팬보다 좁으면 나타나는 일반 현상이다.
             (복합관절 연구에서 L1→허벅지 경로힘이 같은 패턴을 만들었다)

■ 검사
  5동작 전부에서 IL / LTpL / LTpT 의 변화 방향을 재집계하고,
  부하 수준(외부 하중, 절대 ES 요구)과의 관계를 정리한다.
  5동작은 전부 흉추1↔골반 토크커플(넓은 스팬)이므로, 새 가설이 맞다면
  5동작에서는 재분배가 **드물어야** 한다.
"""
import json
import numpy as np
import opensim as osim

RES = '/data/romfix_unified'
ORDER = ['squat', 'stoop', 'box', 'gait', 'carry']
NAME = {'squat': '맨몸 스쿼트', 'stoop': '맨몸 스툽', 'box': '박스 들기',
        'gait': '맨몸 보행', 'carry': '박스 운반'}
LOAD = {'squat': 0, 'stoop': 0, 'box': 20, 'gait': 0, 'carry': 20}
GRP = {'IL': 'IL_', 'LTpL': 'LTpL', 'LTpT': 'LTpT'}
U = json.load(open(f'{RES}/unified_numbers.json'))


def act(d):
    t = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_activation.sto')
    T = np.array(list(t.getIndependentColumn()))
    L = list(t.getColumnLabels())
    return T, L, t


def group_peak(d, win):
    T, L, t = act(d)
    m = (T >= win[0]) & (T <= win[1])
    out = {}
    for g, pre in GRP.items():
        C = [c for c in L if c.startswith(pre)]
        S = np.vstack([[float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]
                       for c in C]) * 100
        out[g] = (float(S.max(axis=0)[m].mean()), len(C))
    return out


DIRS = {'squat': (f'{RES}/squat_off', f'{RES}/squat_on'),
        'stoop': (f'{RES}/stoop_off', f'{RES}/stoop_on'),
        'box': (f'{RES}/box_off', f'{RES}/box_on'),
        'gait': (f'{RES}/gait_off', f'{RES}/gait_on'),
        'carry': (f'{RES}/carry_off', f'{RES}/carry_on')}


def main():
    print('=' * 100)
    print('[3] 5동작 근육군 재집계 — 창내 peak 평균 (%)  ※ 기존 .sto 재집계, 수치 변경 없음')
    print('=' * 100)
    print(f"{'동작':12s} {'하중':>5s} " +
          ''.join(f'{g:>22s}' for g in GRP) + f"{'ES 전체':>10s}")
    res = {}
    for k in ORDER:
        win = U[k]['win']
        o = group_peak(DIRS[k][0], win)
        n = group_peak(DIRS[k][1], win)
        row = {}
        line = f'  {NAME[k]:12s} {LOAD[k]:4d}kg '
        for g in GRP:
            do, cnt = o[g]
            dn, _ = n[g]
            rel = 100 * (dn - do) / do if do > 1e-9 else float('nan')
            row[g] = dict(off=do, on=dn, rel=rel, n=cnt)
            line += f'{do:7.2f}→{dn:6.2f} ({rel:+6.1f}%)'
        eff = round(100.0 * round(round(U[k]['b_on'], 2) - round(U[k]['b_off'], 2), 2)
                    / round(U[k]['b_off'], 2), 1)
        row['ES'] = eff
        res[k] = row
        print(line + f'{eff:+9.1f}%')

    print('\n' + '=' * 100)
    print('[3] 재분배 판정 — 한 근육군이라도 증가하면 재분배로 본다')
    print('=' * 100)
    print(f"{'동작':12s} {'하중':>6s} {'증가한 근육군':>26s} {'ES 전체':>9s}  판정")
    for k in ORDER:
        inc = [g for g in GRP if res[k][g]['rel'] > 0]
        v = '없음' if not inc else ', '.join(
            f"{g} {res[k][g]['rel']:+.1f}%" for g in inc)
        verdict = '재분배' if inc else '전 근육군 감소'
        print(f'  {NAME[k]:12s} {LOAD[k]:5d}kg {v:>26s} {res[k]["ES"]:+8.1f}%  {verdict}')

    print('\n' + '=' * 100)
    print('[3] 부하 수준과의 관계 (OFF 절대 ES 요구 = 부하 대리 지표)')
    print('=' * 100)
    print(f"{'동작':12s} {'OFF ES peak':>12s} {'IL 변화':>9s} {'LTpL 변화':>10s} "
          f"{'LTpT 변화':>10s}")
    for k in sorted(ORDER, key=lambda x: U[x]['b_off']):
        r = res[k]
        print(f"  {NAME[k]:12s} {U[k]['b_off']:11.2f} {r['IL']['rel']:+8.1f}% "
              f"{r['LTpL']['rel']:+9.1f}% {r['LTpT']['rel']:+9.1f}%")

    json.dump(res, open('/data/suit_span/redistribution_5motion.json', 'w'),
              ensure_ascii=False, indent=1)
    print('\nSAVED /data/suit_span/redistribution_5motion.json')


if __name__ == '__main__':
    main()
