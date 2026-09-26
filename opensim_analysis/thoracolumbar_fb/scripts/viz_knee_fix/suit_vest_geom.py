"""[정정 1] 조끼 구조 기반 슈트 기하 재구성 — 사진에서 힘 사슬을 끝점까지 추적.

■ 무엇이 틀렸었나
  기존 모델은 구동부(근육옷감)가 놓인 **위치**를 힘의 **작용점**으로 썼다.
  실제 제품은 조끼다. 근육옷감 윗끝은 조끼 등판에 봉제되고, 등판은 어깨끈으로 어깨에 걸린다.
  직렬 사슬이므로 장력은 사슬 전체에서 같고, 몸에 힘이 전달되는 곳은 **양 끝(어깨·허벅지)** 과
  경로가 몸에 닿는 접촉면이다. 윗끝을 L1 뼈에 고정하면 부여 스팬이 인위적으로 좁아진다.

■ 사진 판독 (docs/refs/pdf_pages/page-1·2·3.png, sartexo 제품 사진 3장)
  허리    어깨끈(견봉 위) → 조끼 등판(흉추 체표) → 근육옷감(하부 흉추~요추) → BOA → 천골·둔부 → 허벅지 밴드
          · 근육옷감 자체는 하부 등에 있으나(제어기 가방 아래), 그 윗끝은 등판을 통해 어깨끈으로 간다
          · 허리 지지 밴드(복대)는 등판을 몸에 눌러 붙이는 역할 — 경로를 끊지 않는다
  팔꿈치  조끼 어깨 요크(견봉) → 상완 전면 → BOA(원위 상완) → 전완 커프
          · page-2 좌(전면)에서 상완 전면, 우(후면)에서 같은 조각이 견갑 위로 넘어가는 것이 보인다
          · = 기존 "연장안"이 실제 제품 구성이다
  어깨    상부 등(흉추 3 부근, 견갑 내측) → 견봉 위 경유 → 상완 외측(삼각근 조면 높이) BOA
          · page-1 후면 뷰의 대각선 조각 + crop_C_side 의 BOA 위치(상완 외측)로 확정
          · 기존 모델의 "전면 단일 경로"가 아니라 **후면 대각 → 견봉 넘김** 이다

■ 이 모듈이 하는 일
  체표면(근육 외피 + 피하 10 + 의복 5 mm)에서 경유점을 실측해 세 경로를 만들고,
  길이·모멘트암·각도 스윕을 산출한다. 눈대중 좌표를 쓰지 않는다.
"""
import os
import sys
import json
import numpy as np
import opensim as osim

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suit_moment_arm_fix as F
import suit_span_conditions as SC

MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom_elbow.osim')
OUT = '/data/suit_vest'
os.makedirs(OUT, exist_ok=True)
D2R = np.pi / 180
SUBCUT, GARMENT = 0.010, 0.005
OFFSET = SUBCUT + GARMENT
Z_LAT = F.Z_LAT                      # 척추 좌우로 벌린 거리 (기존 허리 경로와 동일)

# 조끼 등판이 덮는 척추 레벨 — 어깨끈(견봉)부터 요추까지 전부
BACK_CHAIN = ['thoracic2', 'thoracic4', 'thoracic6', 'thoracic8', 'thoracic10',
              'thoracic12', 'lumbar1', 'lumbar2', 'lumbar3', 'lumbar4', 'lumbar5']
# 하단 — 천골 경유 후 허벅지 밴드 (기존 조건 B 와 동일한 끝점)
BOTTOM = [('sacrum', (-0.150 - SUBCUT, -0.020, 0.0)),
          ('femur', (-0.060 - SUBCUT, -0.150, 0.0))]


def neutral(m):
    return F.neutral(m)


def path_points_of(m, prefixes, side='R'):
    """근육 경로점을 (부착 body, 국소좌표, ground 좌표) 로 모은다."""
    out = []
    ms = m.getMuscles()
    sfx_bad = '_l' if side == 'R' else '_r'
    for i in range(ms.getSize()):
        mu = ms.get(i)
        nm = mu.getName()
        if not any(nm.startswith(p) for p in prefixes):
            continue
        if nm.endswith(sfx_bad) or nm.endswith(sfx_bad.upper()):
            continue
        ps = mu.getGeometryPath().getPathPointSet()
        for j in range(ps.getSize()):
            p = ps.get(j)
            fr = p.getParentFrame().getName()
            loc = p.getLocation(m.getWorkingState()) if False else None
            out.append((nm, fr, p))
    return out


def station_ground(m, s, body, loc):
    q = m.getBodySet().get(body).findStationLocationInGround(s, osim.Vec3(*loc))
    return np.array([q.get(0), q.get(1), q.get(2)])


def muscle_points_ground(m, s, prefixes, side='R', frames=None):
    """(근육명, 부착 frame, ground 좌표) — 지정 frame 에 붙은 점만."""
    res = []
    ms = m.getMuscles()
    bad = '_l' if side == 'R' else '_r'
    for i in range(ms.getSize()):
        mu = ms.get(i)
        nm = mu.getName()
        if not any(nm.startswith(p) for p in prefixes):
            continue
        if nm.endswith(bad) or nm.endswith(bad.upper()):
            continue
        ps = mu.getGeometryPath().getPathPointSet()
        for j in range(ps.getSize()):
            p = ps.get(j)
            fr = p.getParentFrame().getName()
            if frames and fr not in frames:
                continue
            g = p.getLocationInGround(s)
            res.append((nm, fr, np.array([g.get(0), g.get(1), g.get(2)])))
    return res


def acromion(m, s, side='R'):
    """견봉 위 — 삼각근 기시점 중 가장 높은 점 (견갑/쇄골 부착) + 의복 오프셋."""
    pts = muscle_points_ground(m, s, ('DELT1', 'DELT2', 'DELT3', 'TRP'), side,
                               frames={f'scapula_{side}', f'clavicle_{side}'})
    if not pts:
        raise RuntimeError('견봉 추정 실패 — 삼각근 기시점을 찾지 못함')
    nm, fr, g = max(pts, key=lambda t: t[2][1])
    g = g + np.array([0.0, OFFSET, 0.0])          # 끈이 어깨 위를 지난다
    return f'scapula_{side}', F.ground_to_local(m, s, f'scapula_{side}', g), nm, g


def delt_insertion(m, s, side='R'):
    """삼각근 조면 — 삼각근 정지점(상완) 평균 + 외측 의복 오프셋."""
    pts = muscle_points_ground(m, s, ('DELT1', 'DELT2', 'DELT3'), side,
                               frames={f'humerus_{side}'})
    g = np.mean([p[2] for p in pts], axis=0)
    sg = 1.0 if side == 'R' else -1.0
    g = g + np.array([0.0, 0.0, sg * OFFSET])     # 팔 외측 표면
    return f'humerus_{side}', F.ground_to_local(m, s, f'humerus_{side}', g), len(pts), g


def anterior_arm(m, s, side='R'):
    """상완 전면(이두근 외피) 경유점과 전완 커프 — 기존 팔꿈치 기하와 같은 규칙."""
    import suit_arm_geom as AG
    (pts, _), _ = AG.build(m, s, 'elbow_ext_bow')
    # AG 기본안: [scapula, humerus, radius] — 윗점만 조끼 요크(견봉)로 바꾼다
    return pts


def vest_waist_points(m, s, side='R'):
    """조끼 허리 사슬 — 견봉(어깨끈) → 등판 체표 → 천골 → 허벅지."""
    sg = 1.0 if side == 'R' else -1.0
    P = []
    b_ac, loc_ac, _, _ = acromion(m, s, side)
    P.append((b_ac, loc_ac))
    env = SC.posterior_envelope(m, s, BACK_CHAIN)
    for b in BACK_CHAIN:
        x, y = env[b]
        g = np.array([x - OFFSET, y, sg * Z_LAT])
        P.append((b, F.ground_to_local(m, s, b, g)))
    for b, loc in BOTTOM:
        bb = (f'femur_r' if side == 'R' else 'femur_l') if b == 'femur' else b
        v = list(loc)
        if b == 'sacrum':
            v[2] = sg * Z_LAT
        P.append((bb, tuple(v)))
    return P


def vest_shoulder_points(m, s, side='R'):
    """조끼 어깨 사슬 — 상부 등(흉추3 체표) → 견봉 위 → 상완 외측(삼각근 조면)."""
    sg = 1.0 if side == 'R' else -1.0
    env = SC.posterior_envelope(m, s, ['thoracic3'])
    x, y = env['thoracic3']
    g0 = np.array([x - OFFSET, y, sg * 0.030])        # 견갑 내측(척추 옆)
    p0 = ('thoracic3', F.ground_to_local(m, s, 'thoracic3', g0))
    b_ac, loc_ac, _, _ = acromion(m, s, side)
    p1 = (b_ac, loc_ac)
    b_hu, loc_hu, n, _ = delt_insertion(m, s, side)
    p2 = (b_hu, loc_hu)
    return [p0, p1, p2]


def vest_elbow_points(m, s, side='R'):
    """조끼 팔꿈치 사슬 — 견봉(조끼 요크) → 상완 전면 → 전완 커프."""
    pts = anterior_arm(m, s, side)
    b_ac, loc_ac, _, _ = acromion(m, s, side)
    out = [(b_ac, loc_ac)]
    for b, v in pts[1:]:
        if side == 'R':
            out.append((b, tuple(float(x) for x in v)))
        else:
            out.append((b.replace('_R', '_L'), (float(v[0]), float(v[1]), -float(v[2]))))
    return out


BUILD = {'waist': vest_waist_points, 'shoulder': vest_shoulder_points,
         'elbow': vest_elbow_points}


def build_paths(side='R'):
    m = osim.Model(MODEL)
    m.initSystem()
    s = neutral(m)
    return {k: f(m, s, side) for k, f in BUILD.items()}


# ── 모델에 PathActuator 로 얹어 길이·모멘트암을 재는 유틸 ─────────────
def model_with_paths(sides=('R', 'L')):
    m0 = osim.Model(MODEL)
    m0.initSystem()
    s0 = neutral(m0)
    P = {sd: {k: f(m0, s0, sd) for k, f in BUILD.items()} for sd in sides}
    m = osim.Model(MODEL)
    m.initSystem()
    bs = m.getBodySet()
    for sd in sides:
        for reg, pts in P[sd].items():
            pa = osim.PathActuator()
            nm = f'vest_{reg}_{sd}'
            pa.setName(nm)
            pa.setOptimalForce(100.0)
            for i, (b, v) in enumerate(pts):
                pa.addNewPathPoint(f'{nm}_p{i}', bs.get(b), osim.Vec3(*v))
            m.addForce(pa)
    m.finalizeConnections()
    m.initSystem()
    return m, P


def pose(m, **q):
    m.initSystem()
    s = m.initializeState()
    cs = m.getCoordinateSet()
    for i in range(cs.getSize()):
        c = cs.get(i)
        if not c.getLocked(s):
            c.setValue(s, 0.0, False)
    for k, v in q.items():
        c = cs.get(k)
        if not c.getLocked(s):
            c.setValue(s, v * D2R if c.getMotionType() == 1 else v, False)
    m.assemble(s)
    m.realizePosition(s)
    return s


def length_mm(m, s, nm):
    pa = osim.PathActuator.safeDownCast(m.getForceSet().get(nm))
    return pa.getGeometryPath().getLength(s) * 1000.0


def marm_mm(m, s, nm, coord):
    pa = osim.PathActuator.safeDownCast(m.getForceSet().get(nm))
    return pa.getGeometryPath().computeMomentArm(s, m.getCoordinateSet().get(coord)) * 1000.0


LUMB = ['L5_S1_FE', 'L4_L5_FE', 'L3_L4_FE', 'L2_L3_FE', 'L1_L2_FE']
THOR = ['T12_L1_FE', 'T10_T11_FE', 'T8_T9_FE', 'T6_T7_FE', 'T4_T5_FE']


def main():
    m, P = model_with_paths()
    s = pose(m)
    rep = {'points': {sd: {k: [(b, list(map(float, v))) for b, v in pts]
                           for k, pts in P[sd].items()} for sd in P}}

    print('=' * 100)
    print('[1] 조끼 구조 경로 — 중립 기립에서 실측한 경유점')
    print('=' * 100)
    for reg in ('waist', 'shoulder', 'elbow'):
        pts = P['R'][reg]
        L = length_mm(m, s, f'vest_{reg}_R')
        print(f'\n  {reg}  경로점 {len(pts)}개 · 중립 길이 {L:.1f} mm')
        for b, v in pts:
            print(f'      {b:12s} ({v[0]:+.4f}, {v[1]:+.4f}, {v[2]:+.4f})')
        rep.setdefault('L0', {})[reg] = float(L)

    print('\n' + '=' * 100)
    print('[2] 허리 경로 모멘트 암 (중립) — 어느 레벨에 보조가 가는가')
    print('=' * 100)
    print(f"  {'좌표':12s} {'슈트 r (mm)':>12s}")
    rep['marm_waist'] = {}
    for c in THOR[::-1] + LUMB:
        try:
            r = marm_mm(m, s, 'vest_waist_R', c)
        except Exception:
            continue
        rep['marm_waist'][c] = float(r)
        print(f'  {c:12s} {r:12.1f}')

    print('\n' + '=' * 100)
    print('[3] 어깨 경로 모멘트 암 스윕 — 후면 대각 + 견봉 경유 (부호가 유지되는가)')
    print('=' * 100)
    print(f"  {'elv_angle (°)':>14s} {'슈트 r (mm)':>12s} {'경로장 (mm)':>12s} "
          f"{'삼각근 최대 r':>14s}")
    rep['shoulder_sweep'] = []
    ms = m.getMuscles()
    delt = [ms.get(i).getName() for i in range(ms.getSize())
            if ms.get(i).getName().startswith(('DELT1', 'DELT2', 'DELT3'))
            and not ms.get(i).getName().endswith('_l')]
    for a in range(0, 100, 10):
        ss = pose(m, elv_angle_r=float(a))
        r = marm_mm(m, ss, 'vest_shoulder_R', 'elv_angle_r')
        L = length_mm(m, ss, 'vest_shoulder_R')
        dmax = 0.0
        for n in delt:
            mu = ms.get(n)
            dmax = max(dmax, abs(mu.getGeometryPath().computeMomentArm(
                ss, m.getCoordinateSet().get('elv_angle_r')) * 1000))
        rep['shoulder_sweep'].append(dict(angle=a, r=float(r), L=float(L),
                                          delt_max=float(dmax)))
        print(f'  {a:14d} {r:12.1f} {L:12.1f} {dmax:14.1f}')

    print('\n' + '=' * 100)
    print('[4] 팔꿈치 경로 모멘트 암 스윕')
    print('=' * 100)
    print(f"  {'elbow_flexion (°)':>18s} {'슈트 r (mm)':>12s} {'경로장 (mm)':>12s}")
    rep['elbow_sweep'] = []
    for a in range(0, 130, 15):
        ss = pose(m, elbow_flexion_r=float(a))
        r = marm_mm(m, ss, 'vest_elbow_R', 'elbow_flexion_r')
        L = length_mm(m, ss, 'vest_elbow_R')
        rep['elbow_sweep'].append(dict(angle=a, r=float(r), L=float(L)))
        print(f'  {a:18d} {r:12.1f} {L:12.1f}')

    json.dump(rep, open(f'{OUT}/vest_geom.json', 'w'), ensure_ascii=False, indent=1)
    print(f'\nSAVED {OUT}/vest_geom.json')


if __name__ == '__main__':
    main()
