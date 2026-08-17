"""[2] 운반 동작 다부위 조건 생성 — 허리(조건 B) + 팔꿈치.

■ 기준 동작을 운반으로 바꾼 이유
  스툽·스쿼트는 팔이 매달려 있어 어깨·팔꿈치 요구가 0.1~0.7 N·m 다 (L-09).
  운반(20 kg)만 세 부위가 모두 유의하게 실린다 — 팔꿈치 24.7 · 어깨 23.1 N·m.

■ 어깨는 제외
  캡 재설계 1회 시도 후에도 50° 에서 모멘트 암 부호가 반전한다 (L-08).
  사용자 판정 규칙에 따라 이번 범위에서 제외하고 허리 + 팔꿈치로 진행한다.

■ ⚠️ 팔꿈치 피팅 자세 — 0° 피팅이면 운반 중 장력이 0 이다
  운반 창내 팔꿈치각은 **97.9° 고정**이고 0° 피팅 슈트의 이완각은 70° 다.
  즉 해부학적 중립에서 착용하면 운반 내내 아무 힘도 내지 못한다.
  → 본 해석은 **작업 자세(97.9°)에서 착용**한 것으로 기준장 L0 를 잡는다.
     굴곡 보조 슈트를 작업 자세에서 조여 입는 것에 해당한다.
     ⚠️ 팔을 펴면 경로가 L0 보다 길어져 장력이 상한(100 N)에 닿는다 — 착용감 제약으로 기록.

■ 조건
  off          외력 = 발 GRF + 박스만 (기존 운반과 동일)
  waist        + 허리 T8 → 천골 경유 → 허벅지
  elbow        + 팔꿈치 상완→전완 (기본안)
  elbow_ext    + 팔꿈치 견갑→상완→전완 (스팬 정합 연장안)
  all          허리 + 팔꿈치 연장안
"""
import os
import re
import sys
import json
import numpy as np
import opensim as osim

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suit_model as sm
import suit_moment_arm_fix as F
import suit_span_conditions as SC
import suit_arm_geom as AG

OUT = '/data/suit_carry'
os.makedirs(OUT, exist_ok=True)
MODEL = AG.MODEL
MOT = '/data/gait_motion/carry_walk_so_armfix.mot'
EXT_SRC = '/data/romfix_unified/carry_off/ext.xml'
T0, T1 = 0.4, 1.6
K_SER = 5.0
D2R = np.pi / 180


def carry_force_objects():
    """운반의 기존 외력(발 GRF 좌우 + 박스 좌우) ExternalForce 블록을 그대로 가져온다."""
    txt = open(EXT_SRC).read()
    objs = re.findall(r'<ExternalForce name="[^"]*">.*?</ExternalForce>', txt, re.S)
    data = re.findall(r'<datafile>([^<]*)</datafile>', txt)[0].strip()
    return objs, data


def carry_data_columns(T):
    """기존 외력 데이터 파일을 해석 시간축에 맞춰 보간."""
    Tg, K = SC.load_mot(carry_force_objects()[1])
    return {c: np.interp(T, Tg, K[c]) for c in K}


def elbow_points(side, extended):
    """팔꿈치 슈트 경유점 — 우측 국소좌표를 만들고 좌측은 z 부호만 뒤집는다."""
    m0 = osim.Model(MODEL)
    m0.initSystem()
    s0 = AG.pose(m0)
    design = 'elbow_ext_bow' if extended else 'elbow_bow'
    (pts, _), _ = AG.build(m0, s0, design)
    out = []
    for b, v in pts:
        if side == 'R':
            out.append((b, tuple(float(x) for x in v)))
        else:
            out.append((b.replace('_R', '_L'), (float(v[0]), float(v[1]), -float(v[2]))))
    return out


def waist_points(side):
    m0 = osim.Model(MODEL)
    m0.initSystem()
    s0 = F.neutral(m0)
    return SC.path_points(m0, s0, 'T8', side, bottom='sacrum_femur')


def neutral_length(P):
    """중립 기립 자세에서의 경로장 (mm) — 슈트를 착용하는 시점의 기준장."""
    m = osim.Model(MODEL)
    m.initSystem()
    s = F.neutral(m)
    bs = m.getBodySet()
    G = [np.array([(q := bs.get(b).findStationLocationInGround(s, osim.Vec3(*loc))).get(0),
                   q.get(1), q.get(2)]) for b, loc in P]
    return sum(np.linalg.norm(G[i + 1] - G[i]) for i in range(len(G) - 1)) * 1000


def path_series(m, cs, bs, K, T, P, k_ser, fit='neutral'):
    """프레임별 (경로점 ground 좌표, 장력).

    fit='neutral' : 중립 기립에서 착용 — 허리용. 보행은 프레임 0 에서 좌우 위상이
                    달라, 첫 프레임을 기준으로 잡으면 좌우 장력이 인공적으로 갈린다.
    fit='work'    : 작업 자세에서 착용 — 팔꿈치용 (운반 97.9° 고정).
    """
    G_all, L_all = [], []
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
        G_all.append(G)
        L_all.append(sum(np.linalg.norm(G[i + 1] - G[i]) for i in range(len(G) - 1)) * 1000)
    L0 = neutral_length(P) if fit == 'neutral' else L_all[0]
    T0c = sm.calibrate_T0(k_ser)
    tens = np.array([sm.solve(L - L0, k_ser, T0c)[0] for L in L_all])
    return G_all, np.array(L_all), tens


def build(tag, parts):
    """parts ⊂ {'waist','elbow','elbow_ext'} 조합의 외력 세트를 만든다."""
    T, K = SC.load_mot(MOT)
    sel = (T >= T0 - 0.05) & (T <= T1 + 0.05)
    T = T[sel]
    K = {c: v[sel] for c, v in K.items()}

    paths = {}
    for sd in ('R', 'L'):
        if 'waist' in parts:
            paths[f'w{sd}'] = waist_points(sd)
        if 'elbow' in parts:
            paths[f'e{sd}'] = elbow_points(sd, extended=False)
        if 'elbow_ext' in parts:
            paths[f'e{sd}'] = elbow_points(sd, extended=True)

    m = osim.Model(MODEL)
    m.initSystem()
    cs, bs = m.getCoordinateSet(), m.getBodySet()

    data = {}
    objs = []
    info = {}
    for key, P in paths.items():
        fit = 'neutral' if key.startswith('w') else 'work'
        G_all, L, tens = path_series(m, cs, bs, K, T, P, K_SER, fit)
        info[key] = dict(fit=fit, L0=float(neutral_length(P) if fit == 'neutral' else L[0]), L_min=float(L.min()), L_max=float(L.max()),
                         tens_mean=float(tens.mean()), tens_min=float(tens.min()),
                         tens_max=float(tens.max()), n_pts=len(P))
        for i, (b, loc) in enumerate(P):
            for ax in 'xyz':
                data[f'{key}{i}_F_v{ax}'] = np.zeros(len(T))
                data[f'{key}{i}_P_p{ax}'] = np.zeros(len(T))
        for fi in range(len(T)):
            G = G_all[fi]
            for i, gpt in enumerate(G):
                v = np.zeros(3)
                if i > 0:
                    u = G[i - 1] - gpt
                    v += u / max(np.linalg.norm(u), 1e-9)
                if i < len(G) - 1:
                    u = G[i + 1] - gpt
                    v += u / max(np.linalg.norm(u), 1e-9)
                v *= tens[fi]
                for j, ax in enumerate('xyz'):
                    data[f'{key}{i}_F_v{ax}'][fi] = v[j]
                    data[f'{key}{i}_P_p{ax}'][fi] = P[i][1][j]
        objs += [f'<ExternalForce name="suit_{key}{i}">'
                 f'<applied_to_body>{b}</applied_to_body>'
                 f'<force_expressed_in_body>ground</force_expressed_in_body>'
                 f'<point_expressed_in_body>{b}</point_expressed_in_body>'
                 f'<force_identifier>{key}{i}_F_v</force_identifier>'
                 f'<point_identifier>{key}{i}_P_p</point_identifier>'
                 f'<torque_identifier></torque_identifier></ExternalForce>'
                 for i, (b, _) in enumerate(P)]

    data.update(carry_data_columns(T))
    objs += carry_force_objects()[0]

    cols = list(data)
    mot_out = f'{OUT}/ext_{tag}.mot'
    with open(mot_out, 'w') as f:
        f.write(f'carry_{tag}\nversion=1\nnRows={len(T)}\nnColumns={len(cols)+1}\n'
                f'inDegrees=no\n\nendheader\ntime\t' + '\t'.join(cols) + '\n')
        for i, t in enumerate(T):
            f.write('\t'.join([f'{t:.6f}'] + [f'{data[c][i]:.6f}' for c in cols]) + '\n')
    xml_out = f'{OUT}/ext_{tag}.xml'
    with open(xml_out, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8" ?>\n<OpenSimDocument Version="40000">'
                '<ExternalLoads name="carry_ext"><objects>\n' + '\n'.join(objs) +
                f'</objects><datafile>{mot_out}</datafile></ExternalLoads></OpenSimDocument>')
    return info


CONDS = {
    'off': [],
    'waist': ['waist'],
    'elbow': ['elbow'],
    'elbow_ext': ['elbow_ext'],
    'all': ['waist', 'elbow_ext'],
}

if __name__ == '__main__':
    summary = {}
    for tag, parts in CONDS.items():
        info = build(tag, parts)
        summary[tag] = info
        desc = ' + '.join(parts) if parts else '외력 없음(기존 운반과 동일)'
        print(f'[{tag}] {desc}')
        for k, v in info.items():
            print(f"    {k}: 경로점 {v['n_pts']}개  L {v['L_min']:.1f}~{v['L_max']:.1f} mm "
                  f"(기준 {v['L0']:.1f})  장력 {v['tens_min']:.1f}~{v['tens_max']:.1f} N")
    json.dump(summary, open(f'{OUT}/build_info.json', 'w'), ensure_ascii=False, indent=1)
    print(f'\nSAVED {OUT}/ext_*.{{mot,xml}}  +  build_info.json')
