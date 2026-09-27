"""[벤치 ■2] 전달 법칙 — 장력 T 가 L5–S1 근육 모멘트를 얼마나 덜어 주는가.

SO 결과에서 **근육이 실제로 낸 L5–S1 모멘트**를 직접 합산해
  ΔM(T) = M_musc(OFF) − M_musc(T)
를 구하고, 하중 환산(kg)으로 바꾼다. reserve 가 둔감한 이유도 여기서 드러난다.

하중–모멘트 기울기는 같은 방식으로 23 kg ↔ 36 kg 실행에서 실측한다.
"""
import os
import sys
import json
import numpy as np
import opensim as osim

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suit_span_conditions as SC

OUT = '/data/suit_bench'
SO = f'{OUT}/so'
D2R = np.pi / 180
TENS = [50.0, 100.0, 200.0, 300.0, 400.0, 600.0]
VARIANTS = ['A_neutral', 'B_half']
COORD = 'L5_S1_FE'


def state_at(model, variant, fi):
    m = osim.Model(model)
    m.initSystem()
    cs = m.getCoordinateSet()
    T, K = SC.load_mot(f'{OUT}/bench_{variant}.mot')
    s = m.initializeState()
    for c in K:
        try:
            co = cs.get(c)
        except Exception:
            continue
        if co.getLocked(s):
            continue
        co.setValue(s, K[c][fi] * D2R if co.getMotionType() == 1 else K[c][fi], False)
    m.realizePosition(s)
    return m, s


def muscle_moment(m, s, d, fi):
    coord = m.getCoordinateSet().get(COORD)
    ms = m.getMuscles()
    t = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_force.sto')
    lab = set(t.getColumnLabels())
    M = 0.0
    for i in range(ms.getSize()):
        mu = ms.get(i)
        nm = mu.getName()
        if nm not in lab:
            continue
        r = mu.getGeometryPath().computeMomentArm(s, coord)
        if abs(r) < 1e-5:
            continue
        M += float(t.getDependentColumn(nm)[fi]) * r
    res = float(t.getDependentColumn(f'reserve_{COORD}')[fi])
    return M, res


def main(fi=0):
    rep = {}
    print('=' * 100)
    print(f'[전달 법칙] 프레임 {fi} (최저점) · {COORD} 근육 모멘트')
    print('=' * 100)
    for variant in VARIANTS:
        m, s = state_at(f'{OUT}/model_tight.osim', variant, fi)
        base = f'{SO}/model_tight_{variant}_23kg_off'
        M0, r0 = muscle_moment(m, s, base, fi)
        rows = []
        print(f'\n  [{variant}] 23 kg · OFF 근육 모멘트 {M0:.1f} N·m (reserve {r0:+.2f})')
        print(f"      {'T (한쪽/양측)':>16s} {'근육 M':>9s} {'ΔM':>8s} {'reserve':>9s}")
        for T in TENS:
            d = f'{SO}/model_tight_{variant}_23kg_T{T:g}'
            if not os.path.exists(f'{d}/so_StaticOptimization_force.sto'):
                continue
            M, r = muscle_moment(m, s, d, fi)
            rows.append(dict(T=T, M=M, dM=M0 - M, res=r))
            print(f'      {T:7.0f}/{2*T:<8.0f} {M:9.1f} {M0-M:8.1f} {r:9.2f}')
        # 선형 적합 ΔM = k·T
        if rows:
            Ts = np.array([r['T'] for r in rows])
            dM = np.array([r['dM'] for r in rows])
            k = float((Ts * dM).sum() / (Ts * Ts).sum())
            print(f'      → ΔM = {k:.4f} N·m per N (한쪽)  '
                  f'= 2 × T × {k/2*1000:.1f} mm (모멘트 암)')
        # 36 kg 근력축소 모델 OFF 로 하중 기울기
        m2, s2 = state_at(f'{OUT}/model_s0p95.osim', variant, fi)
        d36 = f'{SO}/model_s0p95_{variant}_36kg_off'
        slope = None
        if os.path.exists(f'{d36}/so_StaticOptimization_force.sto'):
            M36, r36 = muscle_moment(m2, s2, d36, fi)
            slope = (M36 - M0) / (36 - 23)
            print(f'      36 kg(축소 모델) OFF {M36:.1f} N·m → 하중 기울기 '
                  f'{slope:.2f} N·m/kg')
            print(f'      → 하중 환산: T 100 N(한쪽) = {k*100/slope:.1f} kg · '
                  f'T 400 N = {k*400/slope:.1f} kg')
            print(f'      → G2(34→36 kg, 2 kg) 필요 T = '
                  f'{2*slope/k:.0f} N (한쪽) / {4*slope/k:.0f} N (양측 합)')
        rep[variant] = dict(M0=M0, rows=rows, k=k, slope=slope,
                            kg_per_100N=(k * 100 / slope) if slope else None,
                            T_need_G2=(2 * slope / k) if slope else None)
    json.dump(rep, open(f'{OUT}/transfer.json', 'w'), ensure_ascii=False, indent=1,
              default=float)
    print(f'\nSAVED {OUT}/transfer.json')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
