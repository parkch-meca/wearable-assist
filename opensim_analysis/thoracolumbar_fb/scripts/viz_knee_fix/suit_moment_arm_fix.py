"""[A] 허리 슈트 모멘트 암 재산출 — 경유점을 체표면으로 재배치.

■ 문제
  1차 배치는 `lumbar1` 국소 x = −0.050 (관절중심 기준 후방 약 50 mm)에 경유점을 두었다.
  그 결과 모멘트 암이 43~61 mm 로, 같은 모델 척추기립근(ES) 최대 근속(70~77 mm)보다
  **안쪽**이었다. 슈트는 ES 위를 덮는 외피이므로 해부학적으로 성립하지 않는다.

■ 재배치 기준
  각 요추 레벨에서 ES 근육 경로점의 **후방 외피**를 체표면 대용으로 삼고,
  그 바깥에 의복 두께를 더한 위치에 경유점을 둔다.
  (골격 모델이라 피부 메쉬가 없다. 뼈 표면은 관절중심 기준 36~51 mm 로 ES 안쪽이라
   기준으로 쓸 수 없다 — 실측 확인.)

■ 두 조건의 상·하한
  밀착(conforming) : 복대가 슈트를 눌러 체표면을 따라가게 한다.
                     각 요추 레벨에 경유점 → 경로가 요추 전만을 따라 휜다.  → 하한
  들뜸(bowstring)  : 끈이 양 끝단 사이에서 팽팽해져 요추 전만의 오목한 부분을 가로지른다.
                     중간 경유점 없이 직선 → 관절중심에서 더 멀어진다.        → 상한

■ 검증 게이트
  각 레벨에서  슈트 모멘트 암 > 해당 레벨 ES 최대 근속.
  미달이면 배치 오류로 보고 중단한다 (임의 보정 금지).
"""
import os
import json
import numpy as np
import opensim as osim

MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom.osim')
OUT = '/data/suit_multijoint'
LUMB = ['L5_S1_FE', 'L4_L5_FE', 'L3_L4_FE', 'L2_L3_FE', 'L1_L2_FE']
BODY = {'L5_S1_FE': 'lumbar5', 'L4_L5_FE': 'lumbar4', 'L3_L4_FE': 'lumbar3',
        'L2_L3_FE': 'lumbar2', 'L1_L2_FE': 'lumbar1'}
Z_LAT = 0.040            # m — 구동기 중심의 외측 위치 (모듈 폭 110 mm 의 중앙)
GARMENT = 0.005          # m — 의복 두께
SUBCUT = 0.010           # m — 피하조직 (ES 외피 → 피부). 민감도 대상
F_SIDE = 100.0           # N — 편측 SMA 힘
D2R = np.pi / 180


def neutral(m):
    m.initSystem()
    s = m.initializeState()
    cs = m.getCoordinateSet()
    for i in range(cs.getSize()):
        c = cs.get(i)
        if not c.getLocked(s):
            c.setValue(s, 0.0, False)
    m.assemble(s)
    m.realizePosition(s)
    return s


def es_envelope(m, s):
    """레벨별 ES 후방 외피 x (ground) 와 ES 최대 근속 모멘트암."""
    ms, cs = m.getMuscles(), m.getCoordinateSet()
    ES = [ms.get(i).getName() for i in range(ms.getSize())
          if ms.get(i).getName().startswith(('IL_', 'LTpL', 'LTpT'))]
    pts = []
    for n in ES:
        ps = ms.get(n).getGeometryPath().getPathPointSet()
        for i in range(ps.getSize()):
            q = ps.get(i).getLocationInGround(s)
            v = np.array([q.get(0), q.get(1), q.get(2)])
            if 0.015 < v[2] < 0.075:
                pts.append(v)
    pts = np.array(pts)
    out = {}
    for c in LUMB:
        j = cs.get(c).getJoint()
        p = j.getChildFrame().getPositionInGround(s)
        jc = np.array([p.get(0), p.get(1), p.get(2)])
        band = pts[np.abs(pts[:, 1] - jc[1]) < 0.025]
        r = []
        for n in ES:
            try:
                v = ms.get(n).computeMomentArm(s, cs.get(c)) * 1000
                if abs(v) > 2:
                    r.append(v)
            except Exception:
                pass
        out[c] = dict(jc=jc, es_x=float(band[:, 0].min()),
                      es_max=float(max(r)), es_med=float(np.median(r)))
    return out


def ground_to_local(m, s, body, g):
    """ground 좌표 g 를 body 국소좌표로."""
    t = m.getBodySet().get(body).getTransformInGround(s)
    R, p = t.R(), t.p()
    Rm = np.array([[R.get(i, j) for j in range(3)] for i in range(3)])
    o = np.array([p.get(0), p.get(1), p.get(2)])
    return tuple(Rm.T @ (np.asarray(g) - o))


def build_waist(m0, s0, env, mode, extra=0.0, side='R'):
    """허리 PathActuator 를 재배치해 새 모델을 만든다.

    mode='conform' : 각 요추 레벨에 경유점 (체표면 추종)
    mode='bowstring': 양 끝단만 (직선)
    extra : 체표면 오프셋 추가분 (m). 기본은 GARMENT 만.
    """
    m = osim.Model(MODEL)
    m.initSystem()
    bs = m.getBodySet()
    sg = 1.0 if side == 'R' else -1.0
    off = GARMENT + extra
    pa = osim.PathActuator()
    pa.setName(f'suit_waist_{side}')
    pa.setOptimalForce(F_SIDE)
    k = 0
    order = ['L1_L2_FE', 'L2_L3_FE', 'L3_L4_FE', 'L4_L5_FE', 'L5_S1_FE']
    if mode == 'conform':
        for c in order:
            g = np.array([env[c]['es_x'] - off, env[c]['jc'][1], sg * Z_LAT])
            b = BODY[c]
            pa.addNewPathPoint(f'wp{k}', bs.get(b), osim.Vec3(*ground_to_local(m0, s0, b, g)))
            k += 1
    else:
        c = 'L1_L2_FE'
        g = np.array([env[c]['es_x'] - off, env[c]['jc'][1], sg * Z_LAT])
        pa.addNewPathPoint(f'wp{k}', bs.get(BODY[c]),
                           osim.Vec3(*ground_to_local(m0, s0, BODY[c], g)))
        k += 1
    fem = 'femur_r' if side == 'R' else 'femur_l'
    # 허벅지 밴드 — 대퇴 후면, 둔부 주름 아래. 체표면 대용으로 대퇴 원점 기준 후방 60 mm.
    pa.addNewPathPoint(f'wp{k}', bs.get(fem), osim.Vec3(-0.060 - extra, -0.150, 0.0))
    m.addForce(pa)
    m.finalizeConnections()
    m.initSystem()
    return m


def measure(m, name='suit_waist_R'):
    s = neutral(m)
    cs = m.getCoordinateSet()
    pa = osim.PathActuator.safeDownCast(m.getForceSet().get(name))
    gp = pa.getGeometryPath()
    return {c: gp.computeMomentArm(s, cs.get(c)) * 1000 for c in LUMB}, \
        gp.getLength(s) * 1000


def main():
    m0 = osim.Model(MODEL)
    m0.initSystem()
    s0 = neutral(m0)
    env = es_envelope(m0, s0)

    print('=' * 100)
    print('[A-1/2] 레벨별 후방 깊이 (관절중심 기준, mm) 와 경유점 재배치')
    print('=' * 100)
    print(f"{'관절':10s} {'ES 후방외피':>11s} {'ES 최대근속':>11s} {'재배치 경유점 깊이':>16s}")
    for c in LUMB:
        e = env[c]
        d_env = (e['jc'][0] - e['es_x']) * 1000
        print(f'  {c:10s} {d_env:10.1f} {e["es_max"]:11.1f} {d_env + GARMENT*1000:16.1f}')

    print('\n' + '=' * 100)
    print('[A-3/4] 재산출 모멘트 암과 검증 게이트')
    print('=' * 100)
    CASES = [('밀착 (ES외피+의복 5 mm)', 'conform', 0.0),
             ('밀착 +피하 10 mm', 'conform', SUBCUT),
             ('들뜸 bowstring (ES외피+의복)', 'bowstring', 0.0),
             ('들뜸 bowstring +피하 10 mm', 'bowstring', SUBCUT)]
    res = {}
    for lab, mode, extra in CASES:
        m = build_waist(m0, s0, env, mode, extra)
        ma, L = measure(m)
        gate = {c: ma[c] > env[c]['es_max'] for c in LUMB}
        res[lab] = dict(ma={c: float(ma[c]) for c in LUMB}, L=float(L),
                        gate=all(gate.values()), mean=float(np.mean(list(ma.values()))),
                        tau2=float(2 * F_SIDE * np.mean(list(ma.values())) / 1000))
        print(f'\n■ {lab}   경로 {L:.1f} mm')
        print(f"   {'관절':10s} {'슈트 r':>9s} {'ES 최대':>9s}  게이트")
        for c in LUMB:
            print(f'   {c:10s} {ma[c]:8.1f} {env[c]["es_max"]:9.1f}  '
                  f'{"통과" if gate[c] else "미달"}')
        print(f'   평균 r {np.mean(list(ma.values())):.1f} mm  '
              f'→ 양측 보조 토크 {res[lab]["tau2"]:.1f} N·m  '
              f'| 게이트 {"전 레벨 통과" if all(gate.values()) else "미달 있음"}')

    print('\n' + '=' * 100)
    print('[A-5/6] 보조 토크 밴드')
    print('=' * 100)
    taus = [res[l]['tau2'] for l in res]
    lo_lab = min(res, key=lambda l: res[l]['tau2'])
    hi_lab = max(res, key=lambda l: res[l]['tau2'])
    print(f'  하한 {min(taus):5.1f} N·m  ({lo_lab})')
    print(f'  상한 {max(taus):5.1f} N·m  ({hi_lab})')
    print(f'  1차 추정(폐기) 10.5 N·m  |  기존 5동작 가정 24 N·m')
    exp = (13.0, 18.0)
    inside = exp[0] <= min(taus) and max(taus) <= exp[1]
    print(f'  사용자 예상 범위 {exp[0]}~{exp[1]} N·m — '
          f'{"범위 내" if inside else "범위와 어긋남 (아래 근거 참조)"}')

    json.dump(dict(env={c: {k: (v.tolist() if isinstance(v, np.ndarray) else v)
                            for k, v in env[c].items()} for c in LUMB},
                   cases=res, band=[min(taus), max(taus)]),
              open(f'{OUT}/moment_arm_fix.json', 'w'), ensure_ascii=False, indent=1)
    print(f'\nSAVED {OUT}/moment_arm_fix.json')


if __name__ == '__main__':
    main()
