"""[정정 2] 조끼 허리 사슬 외력 생성 — 새 힘 모델(구동부 + 사슬) 적용.

■ 이전과 무엇이 다른가
  경로   : 상단이 L1 뼈가 아니라 **견봉(어깨끈)** — 흉추까지 스팬이 덮인다 (Z_LAT 55 mm)
  힘     : 100 N 일괄 상한 제거. 프레임별 ΔL(t) 를 구동부(SMA) + 사슬 직렬 평형으로 풀어
           미가열(평탄 응력)과 가열(구속 가열 힘)을 **다른 힘**으로 만든다

■ 조건
  off            슈트 없음 (기존 들기 OFF 재사용 — 20 kg 은 /data/romfix_unified/box_off)
  cold           미가열 착용
  hot100…hot250  구속 가열 힘 스윕
  k2x2 / k2x4    ■4 설계 레버 — 사슬 경질 구간 강성만 2·4배 (고정부 개선 모사)
  hot300         ■4 대조 — 구동기 힘 1.5배 (200 → 300 N)
  *_36           박스 36 kg (손 외력 1.8배). 운동학은 동일.
"""
import os
import re
import sys
import json
import numpy as np
import opensim as osim

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suit_vest_geom as VG
import suit_span_conditions as SC
import suit_force_v2 as FV

OUT = '/data/suit_vest/ext'
os.makedirs(OUT, exist_ok=True)
MOT = '/data/stoop_motion/box_stoop_lift_m1_armfix.mot'
EXT_SRC = '/data/romfix_unified/box_off/ext_B_off.xml'
EXT_DATA = '/data/romfix_unified/box_off/ext_B_off.mot'
D2R = np.pi / 180
MASS_REF = 20.0

# ── 캘리브레이션 통과 대표 조합 (force_scan.json 상위) ─────────────
# 선정 근거: O1·O2 통과 16조합 중, 들기 실제 최대 ΔL(166 mm)에서도
#   미가열이 사슬 연질 구간에 머물러(35 N) 수동/능동 분리가 가장 뚜렷한 조합.
REP = dict(L_stand=160.0, F_plat=10.0, F_hot=150.0,
           chain=dict(kind='bi', k1=0.2, xk=180.0, k2=20.0))


def chain_of(d):
    return FV.Chain(d['kind'], **{k: v for k, v in d.items() if k != 'kind'})


def prm(F_hot=None, chain=None):
    c = dict(REP['chain'])
    if chain:
        c.update(chain)
    return dict(L_stand=REP['L_stand'], F_plat=REP['F_plat'],
                F_hot=F_hot if F_hot is not None else REP['F_hot'],
                chain=chain_of(c))


CONDS = {
    'cold':   dict(heated=False, p=prm(), mass=20.0),
    'hot100': dict(heated=True, p=prm(F_hot=100.0), mass=20.0),
    'hot150': dict(heated=True, p=prm(F_hot=150.0), mass=20.0),
    'hot200': dict(heated=True, p=prm(F_hot=200.0), mass=20.0),
    'hot250': dict(heated=True, p=prm(F_hot=250.0), mass=20.0),
    # ■4 설계 레버 — 기준은 O1 을 통과하는 F_hot=150
    'k2x2':   dict(heated=True, p=prm(chain=dict(k2=40.0)), mass=20.0),
    'k2x4':   dict(heated=True, p=prm(chain=dict(k2=80.0)), mass=20.0),
    'hot225': dict(heated=True, p=prm(F_hot=225.0), mass=20.0),
    # 36 kg
    'off_36':  dict(heated=None, p=None, mass=36.0),
    'cold_36': dict(heated=False, p=prm(), mass=36.0),
    'hot150_36': dict(heated=True, p=prm(F_hot=150.0), mass=36.0),
}


def box_force_objects():
    txt = open(EXT_SRC).read()
    objs = re.findall(r'<ExternalForce name="[^"]*">.*?</ExternalForce>', txt, re.S)
    return [re.sub(r'<data_source_name>[^<]*</data_source_name>', '', o) for o in objs]


def box_columns(T, mass):
    """기존 박스 손 외력 — 질량비로 스케일 (운동학 동일 → 힘 비례)."""
    Tg, K = SC.load_mot(EXT_DATA)
    f = mass / MASS_REF
    out = {}
    for c in K:
        v = np.interp(T, Tg, K[c])
        out[c] = v * f if ('_F_v' in c or '_T_' in c) else v
    return out


def geometry():
    m0 = osim.Model(VG.MODEL)
    m0.initSystem()
    s0 = VG.neutral(m0)
    P = {sd: VG.vest_waist_points(m0, s0, sd) for sd in ('R', 'L')}
    m = osim.Model(VG.MODEL)
    m.initSystem()
    cs, bs = m.getCoordinateSet(), m.getBodySet()
    T, K = SC.load_mot(MOT)
    G_all = {sd: [] for sd in P}
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
        for sd in P:
            G_all[sd].append([np.array([
                (q := bs.get(b).findStationLocationInGround(s, osim.Vec3(*v))).get(0),
                q.get(1), q.get(2)]) for b, v in P[sd]])
    # 중립 기립 기준장
    m.initSystem()
    s = VG.pose(m)
    L0 = {}
    for sd in P:
        G = [np.array([(q := bs.get(b).findStationLocationInGround(s, osim.Vec3(*v))).get(0),
                       q.get(1), q.get(2)]) for b, v in P[sd]]
        L0[sd] = sum(np.linalg.norm(G[i + 1] - G[i]) for i in range(len(G) - 1)) * 1000
    return T, P, G_all, L0


def build(tag, cfg, T, P, G_all, L0):
    data, objs, info = {}, [], {}
    if cfg['p'] is not None:
        for sd in P:
            pts = P[sd]
            n = len(pts)
            for i in range(n):
                for ax in 'xyz':
                    data[f'v{sd}{i}_F_v{ax}'] = np.zeros(len(T))
                    data[f'v{sd}{i}_P_p{ax}'] = np.zeros(len(T))
            Fs, dLs = [], []
            for fi in range(len(T)):
                G = G_all[sd][fi]
                L = sum(np.linalg.norm(G[i + 1] - G[i]) for i in range(n - 1)) * 1000
                dL = L - L0[sd]
                r = FV.solve(max(0.0, dL), cfg['p'], cfg['heated'])
                F = r['F']
                Fs.append(F)
                dLs.append(dL)
                for i, g in enumerate(G):
                    v = np.zeros(3)
                    if i > 0:
                        u = G[i - 1] - g
                        v += u / max(np.linalg.norm(u), 1e-9)
                    if i < n - 1:
                        u = G[i + 1] - g
                        v += u / max(np.linalg.norm(u), 1e-9)
                    v *= F
                    for j, ax in enumerate('xyz'):
                        data[f'v{sd}{i}_F_v{ax}'][fi] = v[j]
                        data[f'v{sd}{i}_P_p{ax}'][fi] = pts[i][1][j]
            objs += [f'<ExternalForce name="vest_{sd}{i}">'
                     f'<applied_to_body>{b}</applied_to_body>'
                     f'<force_expressed_in_body>ground</force_expressed_in_body>'
                     f'<point_expressed_in_body>{b}</point_expressed_in_body>'
                     f'<force_identifier>v{sd}{i}_F_v</force_identifier>'
                     f'<point_identifier>v{sd}{i}_P_p</point_identifier>'
                     f'<torque_identifier></torque_identifier></ExternalForce>'
                     for i, (b, _) in enumerate(pts)]
            info[sd] = dict(F_min=float(np.min(Fs)), F_max=float(np.max(Fs)),
                            F_mean=float(np.mean(Fs)), dL_max=float(np.max(dLs)),
                            n_pts=n)
    data.update(box_columns(T, cfg['mass']))
    objs += box_force_objects()
    cols = list(data)
    mot_out = f'{OUT}/ext_{tag}.mot'
    with open(mot_out, 'w') as f:
        f.write(f'vest_{tag}\nversion=1\nnRows={len(T)}\nnColumns={len(cols)+1}\n'
                f'inDegrees=no\n\nendheader\ntime\t' + '\t'.join(cols) + '\n')
        for i, t in enumerate(T):
            f.write('\t'.join([f'{t:.6f}'] + [f'{data[c][i]:.6f}' for c in cols]) + '\n')
    with open(f'{OUT}/ext_{tag}.xml', 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8" ?>\n<OpenSimDocument Version="40000">'
                '<ExternalLoads name="vest_ext"><objects>\n' + '\n'.join(objs) +
                f'</objects><datafile>{mot_out}</datafile></ExternalLoads></OpenSimDocument>')
    return info


if __name__ == '__main__':
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    T, P, G_all, L0 = geometry()
    print(f'중립 기준장 R {L0["R"]:.1f} · L {L0["L"]:.1f} mm · 프레임 {len(T)}', flush=True)
    summary = {}
    for tag, cfg in CONDS.items():
        if only and tag not in only:
            continue
        info = build(tag, cfg, T, P, G_all, L0)
        summary[tag] = info
        if info:
            r = info['R']
            if cfg['heated']:
                o1 = FV.solve(0.0, cfg['p'], True)
                band = cfg['p']['L_stand'] - o1['L_act']
                r['o1_band'] = float(band)
                r['o1_pass'] = bool(10.0 <= band <= 15.0)
            print(f"[{tag}] 박스 {cfg['mass']:.0f} kg · ΔL 최대 {r['dL_max']:.1f} mm · "
                  f"장력 {r['F_min']:.1f}~{r['F_max']:.1f} N (평균 {r['F_mean']:.1f})"
                  + (f"  · O1 밴드 {r['o1_band']:.1f} mm "
                     f"{'✅' if r['o1_pass'] else '❌ (O1 이탈)'}" if 'o1_band' in r else ''),
                  flush=True)
        else:
            print(f"[{tag}] 슈트 없음 · 박스 {cfg['mass']:.0f} kg", flush=True)
    json.dump(summary, open(f'{OUT}/build_info.json', 'w'), ensure_ascii=False, indent=1)
    print(f'\nSAVED {OUT}/ext_*.{{mot,xml}}')
