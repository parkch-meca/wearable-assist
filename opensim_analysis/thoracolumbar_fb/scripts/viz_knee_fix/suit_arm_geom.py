"""[1] 어깨·팔꿈치 슈트 PathActuator 구성 — 허리에서 확립한 원칙 그대로.

■ 적용 원칙 (허리와 동일)
  (a) 경유점을 체표면에 배치 — 뼈 표면이 아니라 **그 높이 근육 외피 + 피하 10 + 의복 5 mm**
      ⚠️ 앵커 위치를 눈대중으로 넣지 않는다. 허리에서 ES 후방 외피를 실측했듯
         흉곽·쇄골·상완·전완도 같은 쪽 근육 경로점에서 전방 외피를 실측한다.
  (b) 게이트: 슈트 모멘트 암 > 해당 관절 주동근 최대 근속
  (c) 부여 스팬이 부하 스팬을 포함하는가
  (d) 직렬 탄성 k = 5 N/mm, 메쉬 리미터 200 mm, 스트로크 60~80 mm
  (e) 경로가 짧아져 SMA 가 스트로크를 다 쓰면 장력 0 (이완각)

■ 밀착 / 들뜸 — 허리와 동일한 상하한 2조건
  밀착(conform)   : 관절에 랩 실린더(반경 = 실측 체표 반경). 끈이 피부를 따라 감김.
  들뜸(bowstring) : 근위·원위 앵커만. 굴곡 시 끈이 팔오금을 가로질러 뜬다.
  ⚠️ 팔꿈치는 **근육 쪽이 활시위**다. 이두근 건은 굴곡 시 관절에서 떠 44.7 mm 까지
     커지므로, 밀착 의복이 근육보다 안쪽일 수 있다. 허리(슈트가 항상 ES 바깥)와
     기하 관계가 반대이므로 게이트 해석이 다르다 — 결과에 그대로 기록한다.

■ 부하 스팬 (본 모델 실측)
  어깨 시상굴곡 elv_angle 주동근 = DELT1  clavicle_R → humerus_R
  팔꿈치 굴곡  BRA  humerus_R → ulna_R (단관절) / BIClong·BICshort scapula_R → radius_R (이관절)
  ⇒ 팔꿈치 슈트를 상완–전완만 걸치면 이두근의 견갑–상완 구간이 부여 스팬 밖이다.
     허리에서 L1 고정이 L5_S1 을 건너뛴 것과 같은 구조 → 연장안(견갑 앵커)을 함께 산출.
"""
import os
import sys
import json
import numpy as np
import opensim as osim

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suit_model as sm

MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom_elbow.osim')
OUT = '/data/suit_multijoint'
D2R = np.pi / 180
SUBCUT, GARMENT = 0.010, 0.005
OFFSET = SUBCUT + GARMENT
F_SIDE, K_SER = 100.0, 5.0

SH_PRIME = ['DELT1', 'DELT2', 'DELT3']
EL_FLEX = ['BIClong_R', 'BICshort_R', 'BRA_R', 'BRD_R']


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
        c.setValue(s, v * D2R if c.getMotionType() == 1 else v, False)
    m.assemble(s)
    m.realizePosition(s)
    return s


def to_local(m, s, body, g):
    t = m.getBodySet().get(body).getTransformInGround(s)
    R, p = t.R(), t.p()
    Rm = np.array([[R.get(i, j) for j in range(3)] for i in range(3)])
    return tuple(Rm.T @ (np.asarray(g) - np.array([p.get(0), p.get(1), p.get(2)])))


def jc(m, s, coord):
    p = m.getCoordinateSet().get(coord).getJoint().getChildFrame().getPositionInGround(s)
    return np.array([p.get(0), p.get(1), p.get(2)])


def _pts(m, s, keep):
    """같은 쪽(우측) 근육 경로점을 ground 좌표로 모은다."""
    ms = m.getMuscles()
    out = []
    for i in range(ms.getSize()):
        n = ms.get(i).getName()
        if not any(n.startswith(k) for k in keep):
            continue
        if n.endswith('_l') or n.endswith('_L'):
            continue
        ps = ms.get(i).getGeometryPath().getPathPointSet()
        for j in range(ps.getSize()):
            q = ps.get(j).getLocationInGround(s)
            out.append((n, np.array([q.get(0), q.get(1), q.get(2)])))
    return out


def anterior_envelope(m, s, keep, y, band, zmin=None):
    """높이 y 부근에서 전방(+x) 최외곽 점. 반환 (x, who)."""
    best, who = -1e9, None
    for n, v in _pts(m, s, keep):
        if abs(v[1] - y) > band:
            continue
        if zmin is not None and v[2] < zmin:
            continue
        if v[0] > best:
            best, who = v[0], n
    return float(best), who


def measure(m, s):
    """설계에 쓰는 체표면 실측값 일체."""
    Cs, Ce = jc(m, s, 'elv_angle_r'), jc(m, s, 'elbow_flexion_r')
    T4 = m.getBodySet().get('thoracic4').getPositionInGround(s)
    y_t4 = T4.get(1)
    x_chest, w_chest = anterior_envelope(m, s, ('PECM', 'SERA', 'RA_', 'EO_'), y_t4, 0.05, 0.005)
    x_gh, w_gh = anterior_envelope(m, s, ('DELT', 'PECM', 'CORB'), Cs[1], 0.045, Cs[2] - 0.03)
    x_el, w_el = anterior_envelope(m, s, ('BIC', 'BRA', 'BRD'), Ce[1], 0.035, Ce[2] - 0.03)
    y_cl = Cs[1] + 0.05
    x_cl, w_cl = anterior_envelope(m, s, ('DELT', 'PECM'), y_cl, 0.035, Cs[2] - 0.05)
    x_hu, w_hu = anterior_envelope(m, s, ('BIC', 'BRA'), Cs[1] - 0.20, 0.04, Cs[2] - 0.03)
    x_ra, w_ra = anterior_envelope(m, s, ('BIC', 'BRD'), Ce[1] - 0.055, 0.035, Ce[2] - 0.03)
    return dict(
        Cs=Cs, Ce=Ce, y_t4=float(y_t4), y_cl=float(y_cl),
        chest=(x_chest, w_chest), gh=(x_gh, w_gh), elbow=(x_el, w_el),
        clav=(x_cl, w_cl), hum=(x_hu, w_hu), rad=(x_ra, w_ra),
        R_gh=float(x_gh - Cs[0] + OFFSET), R_el=float(x_el - Ce[0] + OFFSET))


def build(m0, s0, design):
    """설계안 → (경유점 리스트, 랩 정의).  랩 = (body, 국소원점, 반경) 또는 None"""
    M = measure(m0, s0)
    Cs, Ce = M['Cs'], M['Ce']
    g = lambda b, v: (b, tuple(to_local(m0, s0, b, np.asarray(v))))

    p_chest = g('thoracic4', [M['chest'][0] + OFFSET, M['y_t4'], Cs[2] * 0.35])
    p_clav = g('clavicle_R', [M['clav'][0] + OFFSET, M['y_cl'], Cs[2] * 0.6])
    p_humd = g('humerus_R', [M['hum'][0] + OFFSET, Cs[1] - 0.20, Cs[2]])
    p_humpx = g('humerus_R', [M['hum'][0] + OFFSET, Cs[1] - 0.09, Cs[2]])
    p_rad = g('radius_R', [M['rad'][0] + OFFSET, Ce[1] - 0.055, Ce[2]])
    p_scap = g('scapula_R', [Cs[0] + 0.010, Cs[1] + 0.030, Cs[2]])
    # 숄더 캡 — 끈을 삼각근 표면(반경 R_gh)에 띄워 잡아 주는 강성 컵.
    # 캡이 없으면 끈이 흉곽에서 상완으로 질러가 관절 가까이를 지난다(게이트 미달).
    cap_up = g('scapula_R', [Cs[0] + M['R_gh'], Cs[1] + 0.020, Cs[2]])
    cap_dn = g('humerus_R', [Cs[0] + M['R_gh'], Cs[1] - 0.045, Cs[2]])

    W_SH = ('humerus_R', to_local(m0, s0, 'humerus_R', Cs), M['R_gh'])
    W_EL = ('humerus_R', to_local(m0, s0, 'humerus_R', Ce), M['R_el'])
    D = {
        'shoulder_strap':    ([p_chest, p_clav, p_humd], None),
        'shoulder_cap':      ([p_chest, p_clav, cap_up, cap_dn, p_humd], W_SH),
        'shoulder_conform':  ([p_chest, p_clav, p_humd], W_SH),
        'shoulder_bow':      ([p_chest, p_clav, p_humd], None),
        'elbow_conform':     ([p_humpx, p_rad], W_EL),
        'elbow_bow':         ([p_humpx, p_rad], None),
        'elbow_ext_conform': ([p_scap, p_humpx, p_rad], W_EL),
        'elbow_ext_bow':     ([p_scap, p_humpx, p_rad], None),
    }
    return D[design], M


def make_model(design):
    m0 = osim.Model(MODEL)
    m0.initSystem()
    s0 = pose(m0)
    (pts, wrap), M = build(m0, s0, design)
    m = osim.Model(MODEL)
    m.initSystem()
    bs = m.getBodySet()
    nm = f'suit_{design}_R'
    if wrap:
        wb, wo, wr = wrap
        w = osim.WrapCylinder()
        w.setName(f'{nm}_wrap')
        w.set_radius(float(wr))
        w.set_length(0.18)
        w.set_translation(osim.Vec3(*wo))
        w.set_xyz_body_rotation(osim.Vec3(0, 0, 0))
        w.set_quadrant('+x')
        bs.get(wb).addWrapObject(w)
        m.finalizeConnections()
        m.initSystem()
    pa = osim.PathActuator()
    pa.setName(nm)
    pa.setOptimalForce(F_SIDE)
    for i, (b, v) in enumerate(pts):
        pa.addNewPathPoint(f'{nm}_p{i}', bs.get(b), osim.Vec3(*v))
    m.addForce(pa)
    m.finalizeConnections()
    m.initSystem()
    if wrap:
        gp = osim.PathActuator.safeDownCast(m.getForceSet().get(nm)).getGeometryPath()
        gp.addPathWrap(bs.get(wrap[0]).getWrapObject(f'{nm}_wrap'))
        m.finalizeConnections()
        m.initSystem()
    return m, nm, pts, M


def sweep(design):
    m, nm, pts, M = make_model(design)
    is_sh = design.startswith('shoulder')
    coord = 'elv_angle_r' if is_sh else 'elbow_flexion_r'
    prime = SH_PRIME if is_sh else EL_FLEX
    ms, cs = m.getMuscles(), m.getCoordinateSet()
    rows = []
    for a in range(0, 141, 10):
        s = pose(m, **{coord: float(a)})
        gp = osim.PathActuator.safeDownCast(m.getForceSet().get(nm)).getGeometryPath()
        r = gp.computeMomentArm(s, cs.get(coord)) * 1000
        rs = gp.computeMomentArm(s, cs.get('elv_angle_r')) * 1000
        pm = {}
        for n in prime:
            try:
                pm[n] = float(ms.get(n).computeMomentArm(s, cs.get(coord)) * 1000)
            except Exception:
                pm[n] = float('nan')
        rows.append(dict(angle=a, r=float(r), r_shoulder=float(rs),
                         L=float(gp.getLength(s) * 1000),
                         prime_max=float(max(v for v in pm.values() if v == v))))
    L0 = rows[0]['L']
    T0c = sm.calibrate_T0(K_SER)
    for row in rows:
        F, x, _ = sm.solve(row['L'] - L0, K_SER, T0c)
        row['tension'] = float(F)
        row['torque'] = float(2 * F * row['r'] / 1000)
    return dict(design=design, name=nm, coord=coord, L0=float(L0), rows=rows,
                points=[(b, [float(x) for x in v]) for b, v in pts])


def main():
    m = osim.Model(MODEL)
    m.initSystem()
    s = pose(m)
    M = measure(m, s)

    print('=' * 100)
    print('[1-a] 체표면 실측 — 각 부위 전방 외피 + 피하 10 + 의복 5 mm')
    print('=' * 100)
    for k, lab in (('chest', '흉곽 T4 높이'), ('clav', '쇄골 높이'), ('gh', '어깨 관절 높이'),
                   ('hum', '상완 원위'), ('elbow', '팔꿈치 높이'), ('rad', '전완 근위')):
        print(f'  {lab:14s} 전방 외피 x = {M[k][0]*1000:7.1f} mm  (근육 {M[k][1]})')
    print(f'\n  → 어깨 랩 반경 {M["R_gh"]*1000:5.1f} mm   팔꿈치 랩 반경 {M["R_el"]*1000:5.1f} mm')

    ms = m.getMuscles()
    print('\n' + '=' * 100)
    print('[1-c] ★ 부하 스팬 — 주동근이 어느 body 사이에 걸쳐 있는가')
    print('=' * 100)
    span = {}
    for n in SH_PRIME + EL_FLEX:
        ps = ms.get(n).getGeometryPath().getPathPointSet()
        bl = [ps.get(i).getBody().getName() for i in range(ps.getSize())]
        span[n] = dict(origin=bl[0], insertion=bl[-1])
        bi = '★ 이관절 (견갑 기점)' if bl[0].startswith('scapula') and n.startswith('BIC') else ''
        print(f'  {n:12s} {bl[0]:12s} → {bl[-1]:12s}  {bi}')

    res = {d: sweep(d) for d in
           ('shoulder_strap', 'shoulder_cap', 'elbow_bow', 'elbow_ext_bow')}

    print('\n' + '=' * 100)
    print('[1-b] 게이트 — 유효 구간(장력>5 N 이고 r>0)에서 슈트 r vs 주동근 최대 근속')
    print('=' * 100)
    gates = {}
    for d, v in res.items():
        act = [r for r in v['rows'] if r['tension'] > 5 and r['r'] > 0]
        if not act:
            gates[d] = dict(ok=False, note='유효 구간 없음')
            print(f'  {d:20s} 유효 구간 없음')
            continue
        npass = sum(1 for r in act if r['r'] > r['prime_max'])
        gates[d] = dict(ok=bool(npass == len(act)), n_pass=npass, n=len(act),
                        rng=[act[0]['angle'], act[-1]['angle']],
                        r_mean=float(np.mean([r['r'] for r in act])),
                        prime_mean=float(np.mean([r['prime_max'] for r in act])),
                        tau_max=float(max(r['torque'] for r in act)))
        g = gates[d]
        print(f"  {d:20s} 구간 {g['rng'][0]:3d}~{g['rng'][1]:3d}°  r 평균 {g['r_mean']:5.1f} "
              f"vs 주동근 {g['prime_mean']:5.1f} mm  통과 {npass}/{len(act)}  "
              f"최대토크 {g['tau_max']:5.2f} N·m → {'통과' if g['ok'] else '미달'}")

    print('\n' + '=' * 100)
    print('[1-e] 각도별 장력 · 보조 토크 (양측 합)   ※ 어깨 연장안은 elv_angle 모멘트 암 병기')
    print('=' * 100)
    for d, v in res.items():
        z = [r['angle'] for r in v['rows'] if r['tension'] < 1.0]
        print(f"\n■ {d}   기준장 {v['L0']:.1f} mm   이완 시작각 "
              f"{str(z[0])+'°' if z else '없음'}")
        hdr = f"   {'각도':>5s} {'ΔL':>7s} {'장력':>7s} {'슈트 r':>8s} {'주동근':>7s} {'토크':>7s}"
        if d.startswith('elbow_ext'):
            hdr += f" {'어깨 r':>8s}"
        print(hdr)
        for r in v['rows'][:13]:
            line = (f"   {r['angle']:5d} {r['L']-v['L0']:+7.1f} {r['tension']:7.1f} "
                    f"{r['r']:8.1f} {r['prime_max']:7.1f} {r['torque']:7.2f}")
            if d.startswith('elbow_ext'):
                line += f" {r['r_shoulder']:8.1f}"
            print(line)

    json.dump(dict(span=span, gates=gates, sweeps=res,
                   measure={k: (list(v) if isinstance(v, (tuple, list)) and
                                not isinstance(v, np.ndarray) else
                                (v.tolist() if isinstance(v, np.ndarray) else v))
                            for k, v in M.items()}),
              open(f'{OUT}/arm_suit_geom.json', 'w'), ensure_ascii=False, indent=1)
    print(f'\nSAVED {OUT}/arm_suit_geom.json')


if __name__ == '__main__':
    main()
