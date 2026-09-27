"""[벤치 ■1·■2] 영상 운동학 → 모델 자세 재구성 + 슈트 ΔL·장력 + 요구 모멘트 수계산.

■ 영상에서 확정된 것 (bench_pose_extract, MediaPipe PoseLandmarker heavy)
  · 무릎 0~5°  (벤치가 다리를 구속 — 무릎 사용 불가)
  · 대퇴 경사 57.5° (수평 기준) = 허벅지 패드 각도
  · 최저점 몸통 경사 −4.4°(NO SUIT) / 0.0°(ACTIVE) — 수평 또는 약간 아래
  · 최저점 고관절(어깨–고관절–무릎) 60.8°(NO SUIT) / 55.9°(ACTIVE)

■ 표면 랜드마크로 나눌 수 없는 것 — 요추 굴곡 vs 골반 회전
  어깨–고관절 선은 둘의 **합**이다. 두 변형안을 만들어 영상과 대조한다.
    (A) 중립 요추  요추 굴곡 합 10°  (힙힌지, 등을 편 자세)
    (B) 절반 분담  요추 굴곡 합 30°
  ⚠️ 이 모델에서 `*_FE` 는 **양수가 신전**이다 (실측 확인). 굴곡은 음수로 준다.

■ 슈트 (사양 정정 반영)
  가열력 **한쪽 100 N** (양측 합 200 N). 사슬 이중선형 k1 0.2 / x_k 180 / k2 20,
  구동부 직립장 160 mm · F_plat 10 N (한쪽). 100 N 조건에서 O1·O2 재확인 통과.
"""
import os
import sys
import json
import numpy as np
import opensim as osim

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suit_vest_geom as VG
import suit_force_v2 as FV

OUT = '/data/suit_bench'
D2R = np.pi / 180
MODEL = VG.MODEL
G = 9.80665

TARGET = dict(femur=122.5, trunk=184.4, knee=3.0)      # 모델 각 규약 (180 = 전방 수평)
VARIANTS = {'A_neutral': 10.0, 'B_half': 30.0}
LUMB = [('L5_S1_FE', 0.28), ('L4_L5_FE', 0.24), ('L3_L4_FE', 0.20),
        ('L2_L3_FE', 0.16), ('L1_L2_FE', 0.12)]
SUIT = dict(L_stand=160.0, F_plat=10.0, F_hot=100.0,
            chain=FV.Chain('bi', k1=0.2, xk=180.0, k2=20.0))
TRUNK_KW = ('lumbar', 'thoracic', 'clavicle', 'scapula', 'humerus', 'ulna',
            'radius', 'hand', 'head', 'skull', 'cerv', 'sternum', 'jaw', 'hyoid',
            'rib', 'costal')


def joint_center(m, s, coord):
    p = m.getCoordinateSet().get(coord).getJoint().getChildFrame().getPositionInGround(s)
    return np.array([p.get(0), p.get(1), p.get(2)])


def station(m, s, body, loc):
    q = m.getBodySet().get(body).findStationLocationInGround(s, osim.Vec3(*loc))
    return np.array([q.get(0), q.get(1), q.get(2)])


def ang_h(p, q):
    """p→q 가 수평과 이루는 각. 0 = 후방 수평 · 90 = 연직 상방 · 180 = 전방 수평."""
    d = q - p
    return float(np.degrees(np.arctan2(d[1], -d[0])))


def fixed_acromion():
    """중립에서 견봉의 **국소 좌표**를 고정한다 (자세가 바뀌어도 같은 점)."""
    m = osim.Model(MODEL)
    m.initSystem()
    s = VG.neutral(m)
    b, loc, who, _ = VG.acromion(m, s, 'R')
    return b, tuple(float(x) for x in loc), who


AC_BODY, AC_LOC, AC_SRC = fixed_acromion()


def set_pose(m, phi_lum, pelvis_tilt, hip_flex, knee=3.0, ankle=0.0, arm=None):
    s = m.initializeState()
    cs = m.getCoordinateSet()
    for i in range(cs.getSize()):
        c = cs.get(i)
        if not c.getLocked(s):
            c.setValue(s, 0.0, False)
    vals = {'pelvis_tilt': pelvis_tilt}
    for nm, f in LUMB:
        vals[nm] = -phi_lum * f                      # 음수 = 굴곡
    for sd in ('r', 'l'):
        vals[f'hip_flexion_{sd}'] = hip_flex
        vals[f'knee_angle_{sd}'] = -abs(knee)
        vals[f'ankle_angle_{sd}'] = ankle
    if arm is not None:                              # 팔은 중력으로 수직으로 늘어진다
        for sd in ('r', 'l'):
            vals[f'elv_angle_{sd}'] = arm
    for k, v in vals.items():
        try:
            c = cs.get(k)
        except Exception:
            continue
        if not c.getLocked(s):
            c.setValue(s, v * D2R, False)
    m.realizePosition(s)
    return s


def angles(m, s):
    hip = joint_center(m, s, 'hip_flexion_r')
    kn = joint_center(m, s, 'knee_angle_r')
    ac = station(m, s, AC_BODY, AC_LOC)
    return ang_h(hip, ac), ang_h(kn, hip), hip, kn, ac


def solve_arm(m, phi_lum, pt, hf):
    """손이 견봉 바로 아래 오도록 어깨 굴곡각을 맞춘다 (팔이 수직으로 늘어진 상태)."""
    lo, hi = -120.0, 120.0

    def dx(a):
        s = set_pose(m, phi_lum, pt, hf, arm=a)
        ac = station(m, s, AC_BODY, AC_LOC)
        hd = 0.5 * (station(m, s, 'hand_R', (0, 0, 0)) +
                    station(m, s, 'hand_L', (0, 0, 0)))
        return hd[0] - ac[0]
    # dx(a) 는 단조가 아니다 (코사인 형태) → 격자 탐색 후 국소 이분법
    grid = np.linspace(lo, hi, 49)
    vals = np.array([dx(a) for a in grid])
    i = int(np.argmin(np.abs(vals)))
    a0, a1 = grid[max(0, i - 1)], grid[min(len(grid) - 1, i + 1)]
    if dx(a0) * dx(a1) <= 0:
        for _ in range(50):
            mid = 0.5 * (a0 + a1)
            if dx(a0) * dx(mid) <= 0:
                a1 = mid
            else:
                a0 = mid
        return 0.5 * (a0 + a1)
    return float(grid[i])


def solve_posture(m, phi_lum):
    """(pelvis_tilt, hip_flex) 뉴턴 2×2 — 수치 야코비안."""
    x = np.array([-70.0, 40.0])

    def resid(v):
        s = set_pose(m, phi_lum, v[0], v[1])
        t, f, *_ = angles(m, s)
        t = t + 360 if t < 0 else t
        return np.array([t - TARGET['trunk'], f - TARGET['femur']])
    for _ in range(30):
        r = resid(x)
        if np.max(np.abs(r)) < 0.02:
            break
        J = np.zeros((2, 2))
        for j in range(2):
            dx = np.zeros(2)
            dx[j] = 0.5
            J[:, j] = (resid(x + dx) - r) / 0.5
        x = x - np.linalg.solve(J, r)
    r_end = resid(x)                       # ⚠️ initializeState 는 같은 상태를 재사용한다
    arm = solve_arm(m, phi_lum, x[0], x[1])   #    → 잔차·팔 해를 먼저 구하고
    s = set_pose(m, phi_lum, x[0], x[1], arm=arm)   # 마지막에 최종 자세를 만든다
    return s, float(x[0]), float(x[1]), r_end, float(arm)


def suit_lengths(m, s, P, L0):
    out = {}
    for sd, pts in P.items():
        Gs = [station(m, s, b, v) for b, v in pts]
        L = sum(np.linalg.norm(Gs[i + 1] - Gs[i]) for i in range(len(Gs) - 1)) * 1000
        dL = L - L0[sd]
        c = FV.solve(max(0.0, dL), SUIT, False)
        h = FV.solve(max(0.0, dL), SUIT, True)
        out[sd] = dict(L0=L0[sd], L=L, dL=dL, F_cold=c['F'], F_hot=h['F'],
                       state_hot=h['state'])
    return out


def suit_moment(m, s, P, F_side):
    """슈트가 L5_S1 과 고관절에 주는 모멘트 (양측 합) — 경로점 힘의 합으로 직접 계산."""
    l5 = joint_center(m, s, 'L5_S1_FE')
    hip = joint_center(m, s, 'hip_flexion_r')
    Ml5 = Mhip = 0.0
    for sd, pts in P.items():
        Gs = [station(m, s, b, v) for b, v in pts]
        n = len(Gs)
        # 경로점 i 위(상단)쪽 구간에 걸리는 장력이 L5_S1 위 body 에 주는 모멘트
        for i, g in enumerate(Gs):
            v = np.zeros(3)
            if i > 0:
                u = Gs[i - 1] - g
                v += u / max(np.linalg.norm(u), 1e-9)
            if i < n - 1:
                u = Gs[i + 1] - g
                v += u / max(np.linalg.norm(u), 1e-9)
            f = F_side * v
            b = pts[i][0]
            lb = b.lower()
            if any(k in lb for k in TRUNK_KW) or lb.startswith('scapula'):
                r = g - l5
                Ml5 += r[0] * f[1] - r[1] * f[0]
            if not lb.startswith('femur'):               # 골반 위쪽 = 고관절 교차
                r = g - hip
                Mhip += r[0] * f[1] - r[1] * f[0]
    return dict(M_L5S1=float(Ml5), M_hip=float(Mhip))


def demand_moment(m, s, kb_mass):
    bs = m.getBodySet()
    names = [bs.get(i).getName() for i in range(bs.getSize())]
    above = [n for n in names if any(k in n.lower() for k in TRUNK_KW)]
    l5 = joint_center(m, s, 'L5_S1_FE')
    hip = joint_center(m, s, 'hip_flexion_r')
    Ml5 = Mhip = 0.0
    mtot = 0.0
    for n in above:
        b = bs.get(n)
        mass = b.getMass()
        if mass <= 0:
            continue
        c = station(m, s, n, [b.getMassCenter().get(i) for i in range(3)])
        Ml5 += mass * G * (c[0] - l5[0])
        Mhip += mass * G * (c[0] - hip[0])
        mtot += mass
    hand = 0.5 * (station(m, s, 'hand_R', (0, 0, 0)) +
                  station(m, s, 'hand_L', (0, 0, 0)))
    Ml5 += kb_mass * G * (hand[0] - l5[0])
    Mhip += kb_mass * G * (hand[0] - hip[0])
    return dict(M_L5S1=abs(Ml5), M_hip=abs(Mhip), trunk_mass=mtot,
                hand_x_rel_l5=float(hand[0] - l5[0]), hand=hand.tolist())


def main():
    m0 = osim.Model(MODEL)
    m0.initSystem()
    s0 = VG.neutral(m0)
    P = {sd: VG.vest_waist_points(m0, s0, sd) for sd in ('R', 'L')}
    L0 = {}
    for sd, pts in P.items():
        Gs = [station(m0, s0, b, v) for b, v in pts]
        L0[sd] = sum(np.linalg.norm(Gs[i + 1] - Gs[i]) for i in range(len(Gs) - 1)) * 1000

    m = osim.Model(MODEL)
    m.initSystem()
    rep = {'acromion': dict(body=AC_BODY, loc=AC_LOC, src=AC_SRC), 'L0': L0}
    print('=' * 104)
    print(f'[■1] 영상 운동학 → 모델 자세 (최저점) · 견봉 기준점 {AC_SRC} @ {AC_BODY}')
    print(f'     중립 슈트 경로 {L0["R"]:.1f} mm (한쪽)')
    print('=' * 104)
    for key, phi in VARIANTS.items():
        s, pt, hf, res, arm = solve_posture(m, phi)
        t, f, hip, kn, ac = angles(m, s)
        t = t + 360 if t < 0 else t
        sl = suit_lengths(m, s, P, L0)
        r = sl['R']
        sm = suit_moment(m, s, P, r['F_hot'])
        smc = suit_moment(m, s, P, r['F_cold'])
        print(f'\n  ■ 변형 {key} — 요추 굴곡 합 {phi:.0f}° '
              f'({" / ".join(f"{phi*fr:.1f}" for _, fr in LUMB)}°)')
        print(f'    골반 기울기 {pt:+.1f}° · 고관절 굴곡 {hf:+.1f}° · 무릎 3° · '
              f'어깨 {arm:+.1f}° (팔 수직) (잔차 몸통 {res[0]:+.2f}° · 대퇴 {res[1]:+.2f}°)')
        print(f'    달성: 몸통 {t:.1f}° (목표 {TARGET["trunk"]}) · 대퇴 {f:.1f}° '
              f'(목표 {TARGET["femur"]})')
        print(f'    슈트 경로 {r["L0"]:.1f} → {r["L"]:.1f} mm  **ΔL {r["dL"]:+.1f} mm**'
              f'   [스툽 135 · 들기 166 mm 대비]')
        print(f'    장력 한쪽  미가열 {r["F_cold"]:.1f} N · 가열 {r["F_hot"]:.1f} N'
              f'   |  양측 합  {2*r["F_cold"]:.0f} / {2*r["F_hot"]:.0f} N')
        print(f'    슈트 모멘트(양측 합)  L5_S1 미가열 {abs(smc["M_L5S1"]):.1f} · '
              f'가열 {abs(sm["M_L5S1"]):.1f} N·m  |  고관절 가열 {abs(sm["M_hip"]):.1f} N·m')
        dm = {}
        print(f"      {'케틀벨':>8s} {'L5_S1 요구':>12s} {'고관절 요구':>12s} "
              f"{'슈트/요구(L5S1)':>16s}")
        for kb in (0.0, 20.0, 36.0, 40.0):
            d = demand_moment(m, s, kb)
            dm[kb] = d
            ratio = 100 * abs(sm['M_L5S1']) / d['M_L5S1'] if d['M_L5S1'] > 1e-6 else 0
            print(f"      {kb:8.0f} {d['M_L5S1']:12.1f} {d['M_hip']:12.1f} "
                  f"{ratio:15.1f} %")
        rep[key] = dict(phi=phi, pelvis_tilt=pt, hip_flex=hf, arm=arm, trunk=t, femur=f,
                        suit=sl, suit_moment_hot=sm, suit_moment_cold=smc,
                        demand={str(k): v for k, v in dm.items()},
                        trunk_mass=dm[0.0]['trunk_mass'])
    json.dump(rep, open(f'{OUT}/posture.json', 'w'), ensure_ascii=False, indent=1,
              default=float)
    print(f'\nSAVED {OUT}/posture.json')


if __name__ == '__main__':
    main()
