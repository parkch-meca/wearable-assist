"""[1] 재산출 모멘트 암 기반 슈트를 ExternalForce 집합으로 구현.

■ 왜 ExternalForce 인가
  PathActuator 를 모델에 넣으면 SO 가 그 활성도까지 최적화 대상으로 삼는다.
  슈트는 처방된 외력이므로 최적화 대상이 되면 안 된다. 장력이 걸린 케이블은
  각 경로점에 정확히 계산 가능한 힘을 주므로, 그 힘들을 ExternalForce 로 부여한다.

  경로점 P0..Pn 에 장력 T 가 걸릴 때
    양 끝점 : F = T · û(이웃 방향)
    중간점  : F = T · (û(이전) + û(다음))
  합력·합모멘트가 0 인 자기평형계이며, PathActuator 와 역학적으로 동일하다.

■ 장력
  suit_model 의 직렬탄성 해에서 프레임별로 구한다 (직립 79 N → 굴곡 100 N 포화).

■ 경로
  suit_moment_arm_fix 의 '밀착 + 피하 10 mm' 배치 (요추 5레벨 경유 + 대퇴).
  검증 게이트 5/5 통과 조건이다.
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
LUMB = F.LUMB
ORDER = ['L1_L2_FE', 'L2_L3_FE', 'L3_L4_FE', 'L4_L5_FE', 'L5_S1_FE']
K_SER = 5.0                       # N/mm — 직렬 강성 (캘리브레이션 중앙)


EXTRA_OFF = [0.0]          # build() 가 설정하는 추가 오프셋 (설계 레버 (C))


def path_bodies_locals(m0, s0, env, side='R'):
    """'밀착 + 피하' 배치의 (body, 국소좌표) 목록."""
    sg = 1.0 if side == 'R' else -1.0
    off = F.GARMENT + F.SUBCUT + EXTRA_OFF[0]
    pts = []
    for c in ORDER:
        g = np.array([env[c]['es_x'] - off, env[c]['jc'][1], sg * F.Z_LAT])
        b = F.BODY[c]
        pts.append((b, F.ground_to_local(m0, s0, b, g)))
    fem = 'femur_r' if side == 'R' else 'femur_l'
    pts.append((fem, (-0.060 - F.SUBCUT - EXTRA_OFF[0], -0.150, 0.0)))
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


def build(mot_path, out_mot, out_xml, grf_src=None, scale=1.0, k_ser=K_SER, extra=0.0):
    """슈트 경로힘 + (있으면) 원본 GRF 를 합쳐 ExternalLoads 데이터 생성."""
    EXTRA_OFF[0] = extra
    m0 = osim.Model(F.MODEL)
    m0.initSystem()
    s0 = F.neutral(m0)
    env = F.es_envelope(m0, s0)
    P = {sd: path_bodies_locals(m0, s0, env, sd) for sd in ('R', 'L')}

    m = osim.Model(F.MODEL)
    m.initSystem()
    cs = m.getCoordinateSet()
    bs = m.getBodySet()
    T, K = load_mot(mot_path)

    # 프레임별 경로점 ground 좌표 → 장력 → 점별 힘
    cols, data = [], {}
    for sd in ('R', 'L'):
        for i in range(len(P[sd])):
            for ax in 'xyz':
                cols.append(f'suit{sd}{i}_F_v{ax}')
                cols.append(f'suit{sd}{i}_P_p{ax}')
    for c in cols:
        data[c] = np.zeros(len(T))
    L0 = {}
    tens = np.zeros(len(T))
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
            G = []
            for b, loc in P[sd]:
                q = bs.get(b).findStationLocationInGround(s, osim.Vec3(*loc))
                G.append(np.array([q.get(0), q.get(1), q.get(2)]))
            L = sum(np.linalg.norm(G[i + 1] - G[i]) for i in range(len(G) - 1)) * 1000
            if sd not in L0:
                L0[sd] = L
            dL = L - L0[sd]
            T0 = sm.calibrate_T0(k_ser)
            Ften, _, _ = sm.solve(dL, k_ser, T0)
            Ften *= scale
            if sd == 'R':
                tens[fi] = Ften
            for i, g in enumerate(G):
                v = np.zeros(3)
                if i > 0:
                    u = G[i - 1] - g
                    v += u / max(np.linalg.norm(u), 1e-9)
                if i < len(G) - 1:
                    u = G[i + 1] - g
                    v += u / max(np.linalg.norm(u), 1e-9)
                v *= Ften
                for j, ax in enumerate('xyz'):
                    data[f'suit{sd}{i}_F_v{ax}'][fi] = v[j]
                    data[f'suit{sd}{i}_P_p{ax}'][fi] = P[sd][i][1][j]

    # 원본 GRF 병합
    gcols = []
    if grf_src:
        Tg, Kg = load_mot(grf_src)
        for c in Kg:
            if c.startswith(('suit', 'thor_', 'pel_')):
                continue
            gcols.append(c)
            data[c] = np.interp(T, Tg, Kg[c])
    allc = gcols + cols
    with open(out_mot, 'w') as f:
        f.write(f'suit_pathforce\nversion=1\nnRows={len(T)}\nnColumns={len(allc)+1}\n'
                f'inDegrees=no\n\nendheader\ntime\t' + '\t'.join(allc) + '\n')
        for i, t in enumerate(T):
            f.write('\t'.join([f'{t:.6f}'] + [f'{data[c][i]:.6f}' for c in allc]) + '\n')

    # XML
    objs = []
    for sd in ('R', 'L'):
        for i, (b, _) in enumerate(P[sd]):
            objs.append(
                f'<ExternalForce name="suit_{sd}{i}"><applied_to_body>{b}</applied_to_body>'
                f'<force_expressed_in_body>ground</force_expressed_in_body>'
                f'<point_expressed_in_body>{b}</point_expressed_in_body>'
                f'<force_identifier>suit{sd}{i}_F_v</force_identifier>'
                f'<point_identifier>suit{sd}{i}_P_p</point_identifier>'
                f'<torque_identifier></torque_identifier></ExternalForce>')
    if grf_src:
        import re
        src_xml = os.path.join(os.path.dirname(grf_src), 'ext_loads_F200.xml')
        if os.path.exists(src_xml):
            txt = open(src_xml).read()
            for mm in re.finditer(r'<ExternalForce name="(?!suit|thor|pel)[^"]*">.*?</ExternalForce>',
                                  txt, re.S):
                objs.append(mm.group(0))
    with open(out_xml, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8" ?>\n<OpenSimDocument Version="40000">'
                '<ExternalLoads name="suit_ext"><objects>\n' + '\n'.join(objs) +
                f'</objects><datafile>{out_mot}</datafile></ExternalLoads></OpenSimDocument>')
    return T, tens


if __name__ == '__main__':
    os.makedirs('/data/suit_16Nm', exist_ok=True)
    T, tens = build('/data/stoop_results/stoop_v5/v5_30fps_armfix.mot',
                    '/data/suit_16Nm/ext_path.mot', '/data/suit_16Nm/ext_path.xml',
                    grf_src='/data/romfix_unified/stoop_on/ext_grf_suit_F200.mot')
    print(f'프레임 {len(T)}   장력 {tens.min():.1f} ~ {tens.max():.1f} N')
    print('SAVED /data/suit_16Nm/ext_path.{mot,xml}')
