"""[4] 어깨 CoordinateActuator tight 전/후 대조 — 삼각근 측정 가능성 판정.

판정 기준 (작업 지시): 어깨 총 effort 에서 액추에이터·reserve 가 차지하는 비율이
10 % 미만이어야 근육(삼각근) 측정이 유의하다.

어깨 굴곡(shoulder_elv) 축의 관절 토크를 세 갈래로 분해한다.
  근육      Σ F_muscle × r_muscle
  액추에이터  Σ F_actuator × 1   (CoordinateActuator 는 힘 = 토크)
  reserve   Σ F_reserve × 1
"""
import os
import json
import numpy as np
import opensim as osim

BEFORE = '/data/romfix_unified/box_off'
AFTER = '/data/shoulder_tight/box_off'
OUT = '/data/suit_multijoint/shoulder_tight.json'
MODEL_B = f'{BEFORE}/model_res_tight.osim'
MODEL_A = f'{AFTER}/model_res_tight.osim'
MOT = '/data/stoop_motion/box_stoop_lift_m1_armfix.mot'
SIDES = ('r', 'l')
D2R = np.pi / 180


def load_force(d):
    t = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_force.sto')
    T = np.array(list(t.getIndependentColumn()))
    L = list(t.getColumnLabels())
    D = {c: np.array([float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())])
         for c in L}
    return T, D


def decompose(model_path, res_dir):
    """shoulder_elv_r/l 축 토크를 근육 / 내장 액추에이터 / reserve 로 분해."""
    m = osim.Model(model_path)
    m.initSystem()
    cs = m.getCoordinateSet()
    ms = m.getMuscles()
    mus = [ms.get(i).getName() for i in range(ms.getSize())]
    T, F = load_force(res_dir)

    # 운동학 (모멘트암 계산용)
    st = osim.Storage(MOT)
    labs = [st.getColumnLabels().get(i) for i in range(st.getColumnLabels().getSize())]
    K = {}
    for c in labs[1:]:
        a = osim.ArrayDouble()
        st.getDataColumn(labs.index(c) - 1, a)
        K[c] = np.array([a.get(i) for i in range(a.getSize())])
    Tk = osim.ArrayDouble(); st.getTimeColumn(Tk)
    Tk = np.array([Tk.get(i) for i in range(Tk.getSize())])

    out = {}
    for side in SIDES:
        coord = f'shoulder_elv_{side}'
        # 근육 토크가 최대인 프레임을 찾기 위해 몇 개 프레임만 평가 (비용 절감)
        idx = np.linspace(0, len(T) - 1, 25).astype(int)
        best = None
        for i in idx:
            ki = int(np.argmin(np.abs(Tk - T[i])))
            m.initSystem(); s = m.initializeState()
            for c in K:
                try:
                    co = cs.get(c)
                except Exception:
                    continue
                if co.getLocked(s):
                    continue
                co.setValue(s, K[c][ki] * D2R if co.getMotionType() == 1 else K[c][ki], False)
            m.assemble(s); m.realizePosition(s)
            tau_mus = 0.0
            for n in mus:
                if n not in F:
                    continue
                try:
                    r = ms.get(n).computeMomentArm(s, cs.get(coord))
                except Exception:
                    continue
                if abs(r) > 1e-4:
                    tau_mus += F[n][i] * r
            act = F.get(f'{coord}_actuator', np.zeros(len(T)))[i]
            res = F.get(f'reserve_{coord}', np.zeros(len(T)))[i]
            tot = abs(tau_mus) + abs(act) + abs(res)
            if best is None or tot > best['total']:
                best = dict(t=float(T[i]), muscle=float(tau_mus), actuator=float(act),
                            reserve=float(res), total=float(tot))
        best['muscle_share'] = 100.0 * abs(best['muscle']) / max(best['total'], 1e-9)
        best['nonmuscle_share'] = 100.0 - best['muscle_share']
        out[coord] = best
    return out


def main():
    if not os.path.exists(f'{AFTER}/so_StaticOptimization_force.sto'):
        print('tight 결과 없음 — 아직 실행 중')
        return
    print('=' * 92)
    print('[4] 어깨 shoulder_elv 축 토크 분해 — tight 전/후 (박스 들기 OFF)')
    print('=' * 92)
    bef = decompose(MODEL_B, BEFORE)
    aft = decompose(MODEL_A, AFTER)
    print(f"{'좌표':16s} {'조건':8s} {'근육':>9s} {'액추에이터':>11s} {'reserve':>9s} "
          f"{'근육 비중':>10s}")
    bars, worst = [], 100.0
    for coord in bef:
        for tag, d in (('tight 전', bef[coord]), ('tight 후', aft[coord])):
            print(f'{coord:16s} {tag:8s} {d["muscle"]:8.3f} {d["actuator"]:10.3f} '
                  f'{d["reserve"]:8.3f} {d["muscle_share"]:9.1f} %')
        worst = min(worst, aft[coord]['muscle_share'])
        bars.append(dict(label=coord.replace('shoulder_elv_', '어깨거상 '),
                         before=abs(bef[coord]['actuator']),
                         after=abs(aft[coord]['actuator'])))
    ok = worst >= 90.0
    verdict = (f'tight 후 근육 비중 {worst:.1f} % → 삼각근 측정 가능'
               if ok else
               f'tight 후에도 근육 비중 {worst:.1f} % → 삼각근 측정 불가')
    print(f'\n판정: {verdict}')
    json.dump(dict(before=bef, after=aft, bars=bars, muscle_share_min=worst,
                   pass_=bool(ok), verdict=verdict,
                   color=('#1a7f37' if ok else '#c44e52')),
              open(OUT, 'w'), ensure_ascii=False, indent=1)
    print(f'SAVED {OUT}')


if __name__ == '__main__':
    main()
