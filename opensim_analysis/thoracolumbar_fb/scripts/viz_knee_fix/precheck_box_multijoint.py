"""[3-pre] 들기 20 kg 다부위 해석 전 사전검증 — 창내 팔 각도와 피팅 자세 결정.

■ 왜 먼저 하는가
  팔 전면 경로는 굴곡 시 **짧아진다**. 착용(기준장 L0) 자세가 작업 자세보다
  펴져 있으면 작업 중 경로가 L0 보다 짧아져 SMA 가 스트로크를 다 쓰고 장력이 0 이 된다
  (이완각 팔꿈치 70° · 어깨 80°). 운반에서 이 문제를 만나 작업 자세 피팅으로 처리했다.
  들기는 **직립에서 시작해 굽히는 동작**이라 프레임 0 이 작업 자세가 아니다 —
  운반에서 쓴 "프레임 0 = 작업 자세" 전제가 성립하는지 먼저 확인해야 한다.

■ 하는 일
  (1) 들기 창(슈트 작동창) 을 기존 5동작 OFF 에서 산출 (운동학이 같으므로 창도 같다)
  (2) 창내 팔꿈치·어깨 각도 실측 → 이완각 대비 판정
  (3) 팔꿈치 경로장을 두 피팅 규칙으로 계산해 장력 결과를 비교
        규칙 ①  L0 = 해석 첫 프레임          (운반에서 쓴 규칙)
        규칙 ②  L0 = 창 중앙 프레임 (작업 자세)  ← 일반화 규칙
  (4) 운반에 규칙 ②를 적용해도 기존 값이 재현되는지 확인 (규칙 교체의 안전성)

⚠️ InverseDynamicsTool 은 쓰지 않는다 (L-10). 요구 모멘트는 SO 출력에서 읽는다.
"""
import os
import sys
import json
import numpy as np
import opensim as osim

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suit_model as sm
import suit_arm_geom as AG
import suit_multijoint_conditions as MC
import suit_span_conditions as SC

OUT = '/data/suit_box'
os.makedirs(OUT, exist_ok=True)
ES_PREFIX = ('IL_', 'LTpL', 'LTpT')
K_SER = 5.0
D2R = np.pi / 180

CASES = {
    'box': dict(off='/data/romfix_unified/box_off',
                mot='/data/stoop_motion/box_stoop_lift_m1_armfix.mot',
                trange=(0.0, 7.5), label='박스 들기 20 kg'),
    'carry': dict(off='/data/suit_carry/off',
                  mot='/data/gait_motion/carry_walk_so_armfix.mot',
                  trange=(0.4, 1.6), label='박스 운반 20 kg (기존 다부위)'),
}
WATCH = ['elbow_flexion_r', 'elbow_flexion_l', 'elv_angle_r', 'elv_angle_l',
         'shoulder_elv_r', 'shoulder_elv_l']
RELAX = {'elbow': 70.0, 'shoulder': 80.0}


def es_window(d):
    """OFF 의 ES peak 가 최대의 90 % 이상인 구간 — analyze_carry_multijoint 와 동일 정의."""
    t = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_activation.sto')
    T = np.array(list(t.getIndependentColumn()))
    cols = [c for c in t.getColumnLabels() if c.startswith(ES_PREFIX)]
    A = np.vstack([[float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]
                   for c in cols]) * 100
    pk = A.max(axis=0)
    m = pk >= 0.9 * pk.max()
    return float(T[m].min()), float(T[m].max()), float(pk[m].mean())


def angles(mot, trange, win):
    T, K = SC.load_mot(mot)
    sel = (T >= trange[0] - 1e-9) & (T <= trange[1] + 1e-9)
    T, K = T[sel], {c: v[sel] for c, v in K.items()}
    m = (T >= win[0]) & (T <= win[1])
    out = {}
    for c in WATCH:
        if c not in K:
            continue
        v = K[c]                     # .mot 이 inDegrees=yes 라 도 단위
        out[c] = dict(f0=float(v[0]), win_mean=float(v[m].mean()),
                      win_min=float(v[m].min()), win_max=float(v[m].max()))
    return T, K, m, out


def elbow_path_lengths(mot, trange, win, extended=True):
    """팔꿈치 슈트(우측) 경로장 시계열 — 프레임별 실제 기하."""
    P = MC.elbow_points('R', extended=extended)
    m = osim.Model(MC.MODEL)
    m.initSystem()
    cs, bs = m.getCoordinateSet(), m.getBodySet()
    T, K = SC.load_mot(mot)
    sel = (T >= trange[0] - 1e-9) & (T <= trange[1] + 1e-9)
    T, K = T[sel], {c: v[sel] for c, v in K.items()}
    L = []
    for fi in range(len(T)):
        m.initSystem()
        s = m.initializeState()
        for c in K:
            try:
                co = cs.get(c)
            except Exception:
                continue
            if co.getLocked(s):
                continue
            co.setValue(s, K[c][fi] * D2R if co.getMotionType() == 1 else K[c][fi], False)
        m.assemble(s)
        m.realizePosition(s)
        G = [np.array([(q := bs.get(b).findStationLocationInGround(s, osim.Vec3(*loc))).get(0),
                       q.get(1), q.get(2)]) for b, loc in P]
        L.append(sum(np.linalg.norm(G[i + 1] - G[i]) for i in range(len(G) - 1)) * 1000)
    return T, np.array(L)


def tension(L, L0):
    T0c = sm.calibrate_T0(K_SER)
    return np.array([sm.solve(x - L0, K_SER, T0c)[0] for x in L])


def main():
    R = {}
    for key, cfg in CASES.items():
        w0, w1, pk = es_window(cfg['off'])
        T, K, m, ang = angles(cfg['mot'], cfg['trange'], (w0, w1))
        print('=' * 100)
        print(f"{cfg['label']} — 창 {w0:.3f}~{w1:.3f} s (창내 ES peak 평균 {pk:.2f} %) "
              f"· 창내 프레임 {int(m.sum())}개")
        print('=' * 100)
        print(f"  {'좌표':18s} {'프레임0':>9s} {'창내 평균':>10s} {'창내 최소':>10s} "
              f"{'창내 최대':>10s}   판정")
        for c, v in ang.items():
            grp = 'elbow' if c.startswith('elbow') else 'shoulder'
            rl = RELAX[grp]
            j = ('이완각 초과 — 0° 피팅이면 장력 0'
                 if v['win_mean'] > rl else '이완각 이내')
            print(f"  {c:18s} {v['f0']:9.1f} {v['win_mean']:10.1f} {v['win_min']:10.1f} "
                  f"{v['win_max']:10.1f}   {j} (이완 {rl:.0f}°)")

        # 창 중앙 프레임 (작업 자세)
        idx = np.where(m)[0]
        mid = int(idx[len(idx) // 2])
        Tl, L = elbow_path_lengths(cfg['mot'], cfg['trange'], (w0, w1))
        L0_f0, L0_mid = float(L[0]), float(L[mid])
        t_f0, t_mid = tension(L, L0_f0), tension(L, L0_mid)
        print(f"\n  팔꿈치 경로장 (연장안·우측)  창내 {L[m].min():.1f}~{L[m].max():.1f} mm")
        print(f"    규칙 ① L0 = 프레임0     {L0_f0:7.1f} mm → 창내 장력 "
              f"{t_f0[m].min():6.1f}~{t_f0[m].max():6.1f} N (평균 {t_f0[m].mean():.1f})")
        print(f"    규칙 ② L0 = 창중앙(t={Tl[mid]:.2f}s) {L0_mid:7.1f} mm → 창내 장력 "
              f"{t_mid[m].min():6.1f}~{t_mid[m].max():6.1f} N (평균 {t_mid[m].mean():.1f})")
        print(f"    두 규칙 L0 차이 {L0_mid - L0_f0:+.1f} mm · 창내 장력 평균 차이 "
              f"{t_mid[m].mean() - t_f0[m].mean():+.1f} N")
        R[key] = dict(win=(w0, w1), es_peak_off=pk, n_win=int(m.sum()),
                      angles=ang, L0_f0=L0_f0, L0_mid=L0_mid, t_mid=float(Tl[mid]),
                      tens_f0=[float(t_f0[m].min()), float(t_f0[m].mean()), float(t_f0[m].max())],
                      tens_mid=[float(t_mid[m].min()), float(t_mid[m].mean()), float(t_mid[m].max())],
                      L_win=[float(L[m].min()), float(L[m].max())])
        print()

    print('=' * 100)
    print('판정')
    print('=' * 100)
    b, c = R['box'], R['carry']
    dc = abs(c['L0_mid'] - c['L0_f0'])
    print(f"  운반: 두 규칙 L0 차이 {dc:.1f} mm → "
          f"{'규칙 ② 가 기존 운반 결과를 재현 (규칙 교체 안전)' if dc < 1.0 else '⚠️ 규칙 교체 시 운반 값이 달라진다'}")
    eb = b['angles']['elbow_flexion_r']['win_mean']
    print(f"  들기: 창내 팔꿈치 {eb:.1f}° "
          f"{'> 이완각 70° → 작업 자세 피팅 필요' if eb > 70 else '≤ 이완각 70° → 중립 피팅으로도 장력 발생'}")
    print(f"        프레임0 팔꿈치 {b['angles']['elbow_flexion_r']['f0']:.1f}° — "
          f"{'프레임0 은 작업 자세가 아니다 (규칙 ② 필수)' if abs(b['angles']['elbow_flexion_r']['f0'] - eb) > 10 else '프레임0 ≈ 작업 자세'}")
    json.dump(R, open(f'{OUT}/precheck.json', 'w'), ensure_ascii=False, indent=1)
    print(f'\nSAVED {OUT}/precheck.json')


if __name__ == '__main__':
    main()
