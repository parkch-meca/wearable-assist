"""[1]/[2] 재분배 원인 분리 — 부여 스팬 vs 부여 지점 수.

■ 문제
  현재 대조된 두 조건은 두 가지가 동시에 다르다.
    토크커플 : 흉추1 ↔ 골반, 두 body 에 반대 토크 → 사이의 **모든 관절**에 같은 모멘트
    경로힘   : L1 → 허벅지, 6개 경로점에 장력 → **요추 5관절 + 고관절**에만 모멘트
  (a) 부여 스팬(어디부터 어디까지)과 (b) 부여 방식(커플 vs 경로힘)이 섞여 있다.

■ 분리 설계
    (i)   토크커플 · 흉추1↔골반   [기존 couple16]   스팬 넓음 · 커플
    (ii)  토크커플 · L1↔골반                        스팬 좁음 · 커플
    (iii) 경로힘   · L1→허벅지    [기존 path16]     스팬 좁음 · 경로힘
    (iv)  경로힘   · T8→허벅지                      스팬 넓음 · 경로힘
  (i)↔(ii) 는 방식을 고정하고 스팬만, (ii)↔(iii) 은 스팬을 고정하고 방식만 바꾼다.

■ 상부 고정 높이 스윕 (■2)
  경로힘의 상부 앵커를 T4 / T8 / T12 / L1 로 바꿔 최적 높이를 찾는다.
  ⚠️ 현 하드웨어는 L1 고정이다. 그 위는 **설계 제안**으로만 다룬다.
"""
import os
import sys
import json
import numpy as np
import opensim as osim

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suit_model as sm
import suit_moment_arm_fix as F

D2R = np.pi / 180
OUT = '/data/suit_span'
os.makedirs(OUT, exist_ok=True)
K_SER = 5.0
Z_LAT = F.Z_LAT
OFFSET = F.GARMENT + F.SUBCUT          # 체표면 오프셋 (의복 5 + 피하 10 mm)

# 상부 앵커 후보 → (body, 그 레벨의 굴곡 좌표)
TOPS = {
    'T4': ('thoracic4', 'T4_T5_FE'),
    'T8': ('thoracic8', 'T8_T9_FE'),
    'T12': ('thoracic12', 'T12_L1_FE'),
    'L1': ('lumbar1', 'L1_L2_FE'),
}
# 앵커 아래로 지나는 경유 body 순서 (위 → 아래)
CHAIN = ['thoracic4', 'thoracic6', 'thoracic8', 'thoracic10', 'thoracic12',
         'lumbar1', 'lumbar2', 'lumbar3', 'lumbar4', 'lumbar5']


def neutral(m):
    return F.neutral(m)


def posterior_envelope(m, s, bodies):
    """각 body 높이에서 ES 근육 경로점의 후방 외피 x (ground)."""
    ms = m.getMuscles()
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
    bs = m.getBodySet()
    out = {}
    for b in bodies:
        p = bs.get(b).getPositionInGround(s)
        y = p.get(1)
        band = pts[np.abs(pts[:, 1] - y) < 0.030]
        if len(band) < 3:
            band = pts[np.argsort(np.abs(pts[:, 1] - y))[:12]]
        out[b] = (float(band[:, 0].min()), float(y))
    return out


def path_points(m, s, top, side='R'):
    """상부 앵커 top 부터 허벅지까지의 (body, 국소좌표) 목록."""
    b_top = TOPS[top][0]
    idx = CHAIN.index(b_top)
    chain = CHAIN[idx:]
    env = posterior_envelope(m, s, chain)
    sg = 1.0 if side == 'R' else -1.0
    pts = []
    for b in chain:
        x, y = env[b]
        g = np.array([x - OFFSET, y, sg * Z_LAT])
        pts.append((b, F.ground_to_local(m, s, b, g)))
    fem = 'femur_r' if side == 'R' else 'femur_l'
    pts.append((fem, (-0.060 - F.SUBCUT, -0.150, 0.0)))
    return pts


def load_mot(path):
    st = osim.Storage(path)
    labs = [st.getColumnLabels().get(i) for i in range(st.getColumnLabels().getSize())]
    d = {}
    for c in labs[1:]:
        a = osim.ArrayDouble()
        st.getDataColumn(labs.index(c) - 1, a)
        d[c] = np.array([a.get(i) for i in range(a.getSize())])
    t = osim.ArrayDouble()
    st.getTimeColumn(t)
    return np.array([t.get(i) for i in range(t.getSize())]), d


def grf_columns(grf_src, T):
    Tg, Kg = load_mot(grf_src)
    return {c: np.interp(T, Tg, Kg[c]) for c in Kg
            if not c.startswith(('suit', 'thor_', 'pel_'))}


def grf_objects(grf_src):
    import re
    src_xml = os.path.join(os.path.dirname(grf_src), 'ext_loads_F200.xml')
    if not os.path.exists(src_xml):
        return []
    txt = open(src_xml).read()
    return [mm.group(0) for mm in
            re.finditer(r'<ExternalForce name="(?!suit|thor|pel)[^"]*">.*?</ExternalForce>',
                        txt, re.S)]


def build_pathforce(top, mot, out_tag, grf_src, k_ser=K_SER, scale=1.0):
    """경로힘 조건 생성. 상부 앵커 top."""
    m0 = osim.Model(F.MODEL)
    m0.initSystem()
    s0 = neutral(m0)
    P = {sd: path_points(m0, s0, top, sd) for sd in ('R', 'L')}
    m = osim.Model(F.MODEL)
    m.initSystem()
    cs, bs = m.getCoordinateSet(), m.getBodySet()
    T, K = load_mot(mot)

    cols = [f'suit{sd}{i}_{q}{ax}' for sd in ('R', 'L')
            for i in range(len(P['R'])) for q in ('F_v', 'P_p') for ax in 'xyz']
    data = {c: np.zeros(len(T)) for c in cols}
    L0, tens = {}, np.zeros(len(T))
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
        for sd in ('R', 'L'):
            G = [np.array([(q := bs.get(b).findStationLocationInGround(s, osim.Vec3(*loc))).get(0),
                           q.get(1), q.get(2)]) for b, loc in P[sd]]
            L = sum(np.linalg.norm(G[i + 1] - G[i]) for i in range(len(G) - 1)) * 1000
            L0.setdefault(sd, L)
            Ft, _, _ = sm.solve(L - L0[sd], k_ser, sm.calibrate_T0(k_ser))
            Ft *= scale
            if sd == 'R':
                tens[fi] = Ft
            for i, g in enumerate(G):
                v = np.zeros(3)
                if i > 0:
                    u = G[i - 1] - g
                    v += u / max(np.linalg.norm(u), 1e-9)
                if i < len(G) - 1:
                    u = G[i + 1] - g
                    v += u / max(np.linalg.norm(u), 1e-9)
                v *= Ft
                for j, ax in enumerate('xyz'):
                    data[f'suit{sd}{i}_F_v{ax}'][fi] = v[j]
                    data[f'suit{sd}{i}_P_p{ax}'][fi] = P[sd][i][1][j]

    data.update(grf_columns(grf_src, T))
    allc = [c for c in data]
    mot_out = f'{OUT}/ext_{out_tag}.mot'
    with open(mot_out, 'w') as f:
        f.write(f'suit_{out_tag}\nversion=1\nnRows={len(T)}\nnColumns={len(allc)+1}\n'
                f'inDegrees=no\n\nendheader\ntime\t' + '\t'.join(allc) + '\n')
        for i, t in enumerate(T):
            f.write('\t'.join([f'{t:.6f}'] + [f'{data[c][i]:.6f}' for c in allc]) + '\n')
    objs = [f'<ExternalForce name="suit_{sd}{i}"><applied_to_body>{b}</applied_to_body>'
            f'<force_expressed_in_body>ground</force_expressed_in_body>'
            f'<point_expressed_in_body>{b}</point_expressed_in_body>'
            f'<force_identifier>suit{sd}{i}_F_v</force_identifier>'
            f'<point_identifier>suit{sd}{i}_P_p</point_identifier>'
            f'<torque_identifier></torque_identifier></ExternalForce>'
            for sd in ('R', 'L') for i, (b, _) in enumerate(P[sd])]
    objs += grf_objects(grf_src)
    xml_out = f'{OUT}/ext_{out_tag}.xml'
    with open(xml_out, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8" ?>\n<OpenSimDocument Version="40000">'
                '<ExternalLoads name="suit_ext"><objects>\n' + '\n'.join(objs) +
                f'</objects><datafile>{mot_out}</datafile></ExternalLoads></OpenSimDocument>')
    return T, tens, len(P['R'])


def build_couple(top_body, mot, out_tag, grf_src, torque=16.5):
    """토크 커플 조건 — top_body 와 pelvis 에 반대 토크."""
    T, _ = load_mot(mot)
    prof = np.zeros(len(T))
    # 기존 24 N·m 조건과 같은 시간 프로파일을 쓴다 (창 정의가 동일해지도록)
    Tr, Kr = load_mot('/data/romfix_unified/stoop_on/ext_grf_suit_F200.mot')
    prof = np.interp(T, Tr, np.abs(Kr['thor_T_z'])) / 24.0 * torque
    data = {f'{p}_{q}{ax}': np.zeros(len(T))
            for p in ('top', 'pel') for q in ('F_v', 'T_', 'P_p') for ax in 'xyz'}
    data['top_T_z'] = +prof
    data['pel_T_z'] = -prof
    data.update(grf_columns(grf_src, T))
    allc = [c for c in data]
    mot_out = f'{OUT}/ext_{out_tag}.mot'
    with open(mot_out, 'w') as f:
        f.write(f'suit_{out_tag}\nversion=1\nnRows={len(T)}\nnColumns={len(allc)+1}\n'
                f'inDegrees=no\n\nendheader\ntime\t' + '\t'.join(allc) + '\n')
        for i, t in enumerate(T):
            f.write('\t'.join([f'{t:.6f}'] + [f'{data[c][i]:.6f}' for c in allc]) + '\n')
    objs = [f'<ExternalForce name="suit_top"><applied_to_body>{top_body}</applied_to_body>'
            f'<force_expressed_in_body>ground</force_expressed_in_body>'
            f'<point_expressed_in_body>{top_body}</point_expressed_in_body>'
            f'<force_identifier>top_F_v</force_identifier>'
            f'<point_identifier>top_P_p</point_identifier>'
            f'<torque_identifier>top_T_</torque_identifier></ExternalForce>',
            '<ExternalForce name="suit_pel"><applied_to_body>pelvis</applied_to_body>'
            '<force_expressed_in_body>ground</force_expressed_in_body>'
            '<point_expressed_in_body>pelvis</point_expressed_in_body>'
            '<force_identifier>pel_F_v</force_identifier>'
            '<point_identifier>pel_P_p</point_identifier>'
            '<torque_identifier>pel_T_</torque_identifier></ExternalForce>']
    objs += grf_objects(grf_src)
    xml_out = f'{OUT}/ext_{out_tag}.xml'
    with open(xml_out, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8" ?>\n<OpenSimDocument Version="40000">'
                '<ExternalLoads name="suit_ext"><objects>\n' + '\n'.join(objs) +
                f'</objects><datafile>{mot_out}</datafile></ExternalLoads></OpenSimDocument>')
    return T, prof


MOT = '/data/stoop_results/stoop_v5/v5_30fps_armfix.mot'
GRF = '/data/romfix_unified/stoop_on/ext_grf_suit_F200.mot'

if __name__ == '__main__':
    print('=== (ii) 토크커플 · L1↔골반 ===')
    T, prof = build_couple('lumbar1', MOT, 'couple_L1', GRF)
    print(f'  프레임 {len(T)}  토크 최대 {prof.max():.2f} N·m')
    for top in ('T4', 'T8', 'T12'):
        T, tens, npt = build_pathforce(top, MOT, f'path_{top}', GRF)
        print(f'=== 경로힘 · {top}→허벅지 ===  경로점 {npt}개/측  '
              f'장력 {tens.min():.1f}~{tens.max():.1f} N')
    print(f'\nSAVED {OUT}/ext_*.{{mot,xml}}')
