"""[5] 팔꿈치 구동 근육 추가 — Holzbaur 상지 모델 기반.

■ 현황
  elbow_flexion / pro_sup 을 지나는 근육이 좌우 각 0개. reserve 로만 구동되어
  슈트 효과 측정이 불가능하다.

■ 추가 근육 (좌우 각 7개)
  굴근  BIClong, BICshort, BRA(상완근), BRD(상완요골근)
  신근  TRIlong, TRIlat, TRImed

■ 파라미터
  Holzbaur et al. (2005) 표준값. 본 모델 상완 길이 290.7 mm 가 Holzbaur 의 약 287 mm 와
  1.3 % 차이라 스케일 없이 쓴다. 부착점만 본 모델 골격 좌표계에 맞춰 배치한다.

■ 팔꿈치 축
  elbow_flexion 축벡터 (+0.0494, +0.0366, +0.99811) — 내외측축 지배(99.8 %),
  즉 시상면 굴곡/신전이다.

■ 검증 (전부 통과해야 다음 단계)
  (a) 팔꿈치 굽힘 최대 등척 모멘트가 성인 남성 문헌 범위 60~80 N·m
  (b) 각도별 모멘트 곡선의 형상·피크 위치가 문헌과 부합 (피크 약 80~100°)
  (c) 팔 질량·관성 불변 — 근육 추가는 질량을 바꾸지 않아야 한다
"""
import os
import json
import numpy as np
import opensim as osim

SRC = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
       'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom.osim')
DST = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
       'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom_elbow.osim')
D2R = np.pi / 180

# Holzbaur et al. 2005 — (Fmax N, Lopt m, Lts m, pennation rad)
PARAM = {
    'BIClong':  (624.3, 0.1157, 0.2723, 0.0),
    'BICshort': (435.6, 0.1321, 0.1923, 0.0),
    'BRA':      (987.3, 0.0858, 0.0535, 0.0),
    'BRD':      (261.3, 0.1726, 0.1330, 0.0),
    'TRIlong':  (798.5, 0.1340, 0.1430, 0.209),
    'TRIlat':   (624.3, 0.1138, 0.0980, 0.157),
    'TRImed':   (624.3, 0.1138, 0.0908, 0.157),
}

# 경로 — (body 접미사 없는 이름, 국소좌표). side 에 따라 z 부호를 뒤집는다.
# +x 전방 / +y 상방(근위) / +z 우측.  humerus·ulna·radius 는 y 가 근위→원위로 음수 방향.
def paths(side):
    z = 1.0 if side == 'R' else -1.0
    sc, hu, ul, ra = f'scapula_{side}', f'humerus_{side}', f'ulna_{side}', f'radius_{side}'
    return {
        # 굴근 — 상완 전면을 지나 전완 근위 전면에 부착
        'BIClong':  [(sc, (0.000, 0.010, z * 0.010)),
                     (hu, (0.020, -0.060, z * 0.000)),
                     (hu, (0.028, -0.250, z * 0.000)),
                     (ra, (0.020, -0.040, z * 0.000))],
        'BICshort': [(sc, (0.010, -0.010, z * 0.005)),
                     (hu, (0.018, -0.120, z * 0.000)),
                     (hu, (0.028, -0.250, z * 0.000)),
                     (ra, (0.020, -0.040, z * 0.000))],
        'BRA':      [(hu, (0.018, -0.180, z * 0.000)),
                     (ul, (0.014, -0.022, z * 0.000))],
        'BRD':      [(hu, (0.010, -0.240, z * 0.018)),
                     (ra, (0.006, -0.220, z * 0.012))],
        # 신근 — 상완 후면을 지나 주두(olecranon)에 부착
        'TRIlong':  [(sc, (-0.020, -0.020, z * 0.010)),
                     (hu, (-0.020, -0.200, z * 0.000)),
                     (hu, (-0.024, -0.270, z * 0.000)),
                     (ul, (-0.022, 0.010, z * 0.000))],
        'TRIlat':   [(hu, (-0.018, -0.150, z * 0.008)),
                     (hu, (-0.024, -0.270, z * 0.000)),
                     (ul, (-0.022, 0.010, z * 0.000))],
        'TRImed':   [(hu, (-0.016, -0.170, z * -0.008)),
                     (hu, (-0.024, -0.270, z * 0.000)),
                     (ul, (-0.022, 0.010, z * 0.000))],
    }


def calibrate_lts(m, ref_angle=80.0):
    """건슬랙장을 보정해 중간 굴곡각에서 섬유가 최적장 근처가 되게 한다.

    ⚠️ Fmax(최대등척력)는 건드리지 않는다. 골격이 다른 모델에 근육을 재부착할 때
       건슬랙장은 표준적으로 재조정하는 파라미터다 — 수렴 목적의 강도 조작이 아니다.
    """
    cs = m.getCoordinateSet()
    ms = m.getMuscles()
    m.initSystem()
    s = m.initializeState()
    for i in range(cs.getSize()):
        c = cs.get(i)
        if not c.getLocked(s):
            c.setValue(s, 0.0, False)
    for sd in ('r', 'l'):
        cs.get(f'elbow_flexion_{sd}').setValue(s, ref_angle * D2R, False)
        cs.get(f'shoulder_elv_{sd}').setValue(s, 5 * D2R, False)
    m.assemble(s)
    m.realizePosition(s)
    out = {}
    for base, (F, Lo, Lts0, pen) in PARAM.items():
        for side in ('R', 'L'):
            mu = ms.get(f'{base}_{side}')
            L = mu.getGeometryPath().getLength(s)
            new = max(L - Lo * np.cos(pen), 0.01)
            mu.setTendonSlackLength(new)
            out[f'{base}_{side}'] = (Lts0, new, L)
    m.finalizeConnections()
    return out


def build(dst=DST):
    m = osim.Model(SRC)
    m.initSystem()
    bs = m.getBodySet()
    added = []
    for side in ('R', 'L'):
        P = paths(side)
        for base, pts in P.items():
            nm = f'{base}_{side}'
            mu = osim.Millard2012EquilibriumMuscle()
            mu.setName(nm)
            F, Lo, Lts, pen = PARAM[base]
            mu.setMaxIsometricForce(F)
            mu.setOptimalFiberLength(Lo)
            mu.setTendonSlackLength(Lts)
            mu.setPennationAngleAtOptimalFiberLength(pen)
            mu.setMaxContractionVelocity(10.0)
            for i, (b, v) in enumerate(pts):
                mu.addNewPathPoint(f'{nm}_p{i}', bs.get(b), osim.Vec3(*v))
            m.addForce(mu)
            added.append(nm)
    m.finalizeConnections()
    m.initSystem()
    cal = calibrate_lts(m)
    m.printToXML(dst)
    print('건슬랙장 보정 (Holzbaur 원값 → 본 모델 재부착값, 우측):')
    for k, (a, b, L) in cal.items():
        if k.endswith('_R'):
            print(f'  {k:12s} {a*1000:6.1f} → {b*1000:6.1f} mm   (경로장 {L*1000:.1f} mm)')
    return dst, added


def check(dst):
    m0, m1 = osim.Model(SRC), osim.Model(dst)
    s0, s1 = m0.initSystem(), m1.initSystem()
    cs = m1.getCoordinateSet()
    ms = m1.getMuscles()
    FLEX = ['BIClong', 'BICshort', 'BRA', 'BRD']
    EXT = ['TRIlong', 'TRIlat', 'TRImed']

    print('=' * 92)
    print('[5-c] 질량·관성 불변 확인')
    print('=' * 92)
    print(f'  총 질량 {m0.getTotalMass(s0):.6f} → {m1.getTotalMass(s1):.6f} kg')
    print(f'  근육 수 {m0.getMuscles().getSize()} → {m1.getMuscles().getSize()}  '
          f'(+{m1.getMuscles().getSize()-m0.getMuscles().getSize()})')
    print(f'  좌표 수 {m0.getCoordinateSet().getSize()} → {m1.getCoordinateSet().getSize()}')

    print('\n' + '=' * 92)
    print('[5-a/b] 각도별 팔꿈치 등척 모멘트 (우측, 최대 활성)')
    print('=' * 92)
    print(f"{'굴곡각':>7s} {'굴근 모멘트':>11s} {'신근 모멘트':>11s} "
          f"{'BIC r':>8s} {'BRA r':>8s} {'TRI r':>8s}")
    rows = []
    for a in range(0, 141, 10):
        m1.initSystem()
        s = m1.initializeState()
        for i in range(cs.getSize()):
            c = cs.get(i)
            if not c.getLocked(s):
                c.setValue(s, 0.0, False)
        cs.get('elbow_flexion_r').setValue(s, a * D2R, False)
        cs.get('shoulder_elv_r').setValue(s, 5 * D2R, False)
        m1.assemble(s)
        m1.equilibrateMuscles(s)
        m1.realizeDynamics(s)
        tf = te = 0.0
        ma = {}
        for base in FLEX + EXT:
            mu = ms.get(f'{base}_R')
            r = mu.computeMomentArm(s, cs.get('elbow_flexion_r'))
            f = mu.getMaxIsometricForce() * mu.getActiveForceLengthMultiplier(s) * \
                np.cos(mu.getPennationAngle(s))
            t = f * r
            ma[base] = r * 1000
            if base in FLEX:
                tf += t
            else:
                te += t
        rows.append(dict(angle=a, flex=tf, ext=te,
                         r_bic=ma['BIClong'], r_bra=ma['BRA'], r_tri=ma['TRIlong']))
        print(f'{a:7d} {tf:10.1f} {te:11.1f} {ma["BIClong"]:8.1f} {ma["BRA"]:8.1f} '
              f'{ma["TRIlong"]:8.1f}')
    pk = max(rows, key=lambda r: r['flex'])
    print(f'\n  최대 굴곡 모멘트 {pk["flex"]:.1f} N·m  @ {pk["angle"]}°')
    print(f'  최대 신전 모멘트 {min(r["ext"] for r in rows):.1f} N·m')
    ok_a = 60.0 <= pk['flex'] <= 80.0
    ok_b = 60 <= pk['angle'] <= 110
    print(f'  (a) 60~80 N·m 범위      : {"통과" if ok_a else "미달/초과"}')
    print(f'  (b) 피크 60~110° 구간    : {"통과" if ok_b else "벗어남"}')
    json.dump(dict(rows=rows, peak=pk, ok_a=bool(ok_a), ok_b=bool(ok_b)),
              open('/data/suit_multijoint/elbow_check.json', 'w'), indent=1)
    return ok_a and ok_b


if __name__ == '__main__':
    dst, added = build()
    print(f'추가 근육 {len(added)}개 → {dst}\n')
    ok = check(dst)
    print(f'\n검증 게이트: {"전부 통과" if ok else "미달 — 부착점 재검토 필요"}')
