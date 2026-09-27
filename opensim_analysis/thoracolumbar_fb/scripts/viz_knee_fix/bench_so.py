"""[벤치 ■2] 모델·외력 생성 + SO 실행 — 장력을 **입력**으로 둔 역산용.

■ 사용자 승인 사항 반영
  · 자세 변형 A·B 둘 다
  · 다리 구속 (a): 좌표 고정 + 골반 residual 기존대로(500/1000)
    **고관절·무릎·발목 reserve 는 opt 5** (기존 100 → 339 N·m 를 흡수해 버린다)
  · 판정 임계 2 / 5 / 10 N·m 병기
  · 근력 축소 모델: Fmax 전체 스케일 (OFF 최대 하중이 34 kg 이 되도록)

■ 장력 처리 — 사슬 모델에서 풀지 않는다
  한쪽 T ∈ {50, 100, 200, 300, 400, 600} N 을 **자세 내내 일정**하게 경로에 준다.
  실제 하드웨어가 얼마를 내는지는 인라인 로드셀 실측 대상이며(측정 요청서 참조),
  여기서는 "실측을 재현하려면 얼마가 필요한가"를 역산한다.
"""
import os
import re
import sys
import time
import shutil
import hashlib
import numpy as np
import opensim as osim

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suit_vest_geom as VG
import bench_posture as BP
import suit_span_conditions as SC

OUT = '/data/suit_bench'
EXT = f'{OUT}/ext'
SO = f'{OUT}/so'
os.makedirs(EXT, exist_ok=True)
os.makedirs(SO, exist_ok=True)
BASE = VG.MODEL.replace('_rom_elbow.osim', '_rom.osim')
G = 9.80665
D2R = np.pi / 180
SPINE_KEYS = ('_FE', '_LB', '_AR', 'Abs_')
LEG_KEYS = ('hip_flexion', 'hip_adduction', 'hip_rotation', 'knee_angle',
            'ankle_angle', 'subtalar', 'mtp')
OPT_TIGHT = 5.0
TENSIONS = [50.0, 100.0, 200.0, 300.0, 400.0, 600.0]
VARIANTS = ['A_neutral', 'B_half']


def build_model(dst, fmax_scale=1.0):
    m = osim.Model(BASE)
    m.initSystem()
    cs = m.getCoordinateSet()
    n = dict(spine=0, leg=0, pelvis=0, other=0)
    for i in range(cs.getSize()):
        c = cs.get(i)
        nm = c.getName()
        a = osim.CoordinateActuator(nm)
        a.setName(f'reserve_{nm}')
        if nm.startswith('pelvis'):
            opt = 500.0 if c.getMotionType() == 1 else 1000.0
            n['pelvis'] += 1
        elif any(k in nm for k in SPINE_KEYS):
            opt = OPT_TIGHT
            n['spine'] += 1
        elif any(nm.startswith(k) for k in LEG_KEYS):
            opt = OPT_TIGHT
            n['leg'] += 1
        else:
            opt = 100.0 if c.getMotionType() == 1 else 1000.0
            n['other'] += 1
        a.setOptimalForce(opt)
        a.setMinControl(-50.0)
        a.setMaxControl(50.0)
        m.addForce(a)
    if fmax_scale != 1.0:
        ms = m.getMuscles()
        for i in range(ms.getSize()):
            mu = ms.get(i)
            mu.setMaxIsometricForce(mu.getMaxIsometricForce() * fmax_scale)
    m.finalizeConnections()
    m.printToXML(dst)
    return n


def geometry(variant):
    """모션 프레임별 슈트 경로점 ground 좌표 + 손 위치."""
    m0 = osim.Model(BASE)
    m0.initSystem()
    s0 = VG.neutral(m0)
    P = {sd: VG.vest_waist_points(m0, s0, sd) for sd in ('R', 'L')}
    m = osim.Model(BASE)
    m.initSystem()
    cs, bs = m.getCoordinateSet(), m.getBodySet()
    T, K = SC.load_mot(f'{OUT}/bench_{variant}.mot')
    G_all = {sd: [] for sd in P}
    hands = []
    for fi in range(len(T)):
        s = m.initializeState()
        for c in K:
            try:
                co = cs.get(c)
            except Exception:
                continue
            if co.getLocked(s):
                continue
            co.setValue(s, K[c][fi] * D2R if co.getMotionType() == 1 else K[c][fi],
                        False)
        m.realizePosition(s)
        for sd in P:
            G_all[sd].append([np.array([
                (q := bs.get(b).findStationLocationInGround(s, osim.Vec3(*v))).get(0),
                q.get(1), q.get(2)]) for b, v in P[sd]])
        hands.append({h: np.array([(q := bs.get(h).findStationLocationInGround(
            s, osim.Vec3(0, 0, 0))).get(0), q.get(1), q.get(2)])
            for h in ('hand_R', 'hand_L')})
    return T, P, G_all, hands


def build_ext(variant, kb, tension, T, P, G_all, hands):
    tag = f'{variant}_{kb:g}kg_' + ('off' if tension is None else f'T{tension:g}')
    data, objs = {}, []
    # 케틀벨 — 양손에 절반씩 (좌우 손 위치 일치 확인)
    for h in ('hand_R', 'hand_L'):
        for ax in 'xyz':
            data[f'{h}_F_v{ax}'] = np.zeros(len(T))
            data[f'{h}_P_p{ax}'] = np.zeros(len(T))
        for fi in range(len(T)):
            data[f'{h}_F_vy'][fi] = -0.5 * kb * G
        objs.append(f'<ExternalForce name="kb_{h}">'
                    f'<applied_to_body>{h}</applied_to_body>'
                    f'<force_expressed_in_body>ground</force_expressed_in_body>'
                    f'<point_expressed_in_body>{h}</point_expressed_in_body>'
                    f'<force_identifier>{h}_F_v</force_identifier>'
                    f'<point_identifier>{h}_P_p</point_identifier>'
                    f'<torque_identifier></torque_identifier></ExternalForce>')
    if tension is not None:
        for sd, pts in P.items():
            n = len(pts)
            for i in range(n):
                for ax in 'xyz':
                    data[f'v{sd}{i}_F_v{ax}'] = np.zeros(len(T))
                    data[f'v{sd}{i}_P_p{ax}'] = np.zeros(len(T))
            for fi in range(len(T)):
                Gs = G_all[sd][fi]
                for i, g in enumerate(Gs):
                    v = np.zeros(3)
                    if i > 0:
                        u = Gs[i - 1] - g
                        v += u / max(np.linalg.norm(u), 1e-9)
                    if i < n - 1:
                        u = Gs[i + 1] - g
                        v += u / max(np.linalg.norm(u), 1e-9)
                    v *= tension
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
    cols = list(data)
    mot = f'{EXT}/ext_{tag}.mot'
    with open(mot, 'w') as f:
        f.write(f'bench_{tag}\nversion=1\nnRows={len(T)}\nnColumns={len(cols)+1}\n'
                f'inDegrees=no\n\nendheader\ntime\t' + '\t'.join(cols) + '\n')
        for i, t in enumerate(T):
            f.write('\t'.join([f'{t:.6f}'] + [f'{data[c][i]:.6f}' for c in cols]) + '\n')
    with open(f'{EXT}/ext_{tag}.xml', 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8" ?>\n<OpenSimDocument Version="40000">'
                '<ExternalLoads name="bench_ext"><objects>\n' + '\n'.join(objs) +
                f'</objects><datafile>{mot}</datafile></ExternalLoads></OpenSimDocument>')
    return tag


def setup_xml(tag, variant, model, dst_dir, t0=None, t1=None, lowpass=-1.0):
    os.makedirs(dst_dir, exist_ok=True)
    tool = osim.AnalyzeTool()
    tool.setName('so')
    tool.setModelFilename(model)
    tool.setCoordinatesFileName(f'{OUT}/bench_{variant}.mot')
    tool.setLowpassCutoffFrequency(lowpass)
    tool.setExternalLoadsFileName(f'{EXT}/ext_{tag}.xml')
    tool.setResultsDir(dst_dir)
    T, _ = SC.load_mot(f'{OUT}/bench_{variant}.mot')
    tool.setInitialTime(float(T[0]) if t0 is None else t0)
    tool.setFinalTime(float(T[-1]) if t1 is None else t1)
    so = osim.StaticOptimization()
    so.setStartTime(tool.getInitialTime())
    so.setEndTime(tool.getFinalTime())
    so.setUseModelForceSet(True)
    so.setActivationExponent(2.0)
    so.setUseMusclePhysiology(True)
    tool.getAnalysisSet().cloneAndAppend(so)
    path = os.path.join(dst_dir, 'setup.xml')
    tool.printToXML(path)
    return path


def run(tag, variant, model, dst_dir, lowpass=-1.0):
    setup = setup_xml(tag, variant, model, dst_dir, lowpass=lowpass)
    t0 = time.time()
    ok = osim.AnalyzeTool(setup).run()
    print(f'[{tag}] ok={ok}  {time.time()-t0:.0f}s', flush=True)
    return ok


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'build'
    if mode == 'build':
        n = build_model(f'{OUT}/model_tight.osim')
        print(f'모델 생성 (reserve): 척추 {n["spine"]} · 다리 {n["leg"]} · '
              f'골반 {n["pelvis"]} · 기타 {n["other"]}  → opt 척추·다리 = {OPT_TIGHT}')
        for v in VARIANTS:
            T, P, G_all, hands = geometry(v)
            dx = max(abs(h['hand_R'][0] - h['hand_L'][0]) for h in hands)
            dy = max(abs(h['hand_R'][1] - h['hand_L'][1]) for h in hands)
            print(f'  [{v}] 프레임 {len(T)} · 좌우 손 위치 차 x {dx*1000:.2f} mm · '
                  f'y {dy*1000:.2f} mm  {"✅ 대칭" if max(dx,dy) < 1e-4 else "⚠️ 비대칭"}')
            for kb in (23.0, 36.0):
                for tn in [None] + TENSIONS:
                    tag = build_ext(v, kb, tn, T, P, G_all, hands)
            print(f'  [{v}] 외력 {2*(1+len(TENSIONS))} 세트 생성', flush=True)
    else:
        tag, variant, model = sys.argv[2], sys.argv[3], sys.argv[4]
        lp = float(sys.argv[5]) if len(sys.argv) > 5 else -1.0
        sfx = '' if lp < 0 else f'_lp{lp:g}'
        run(tag, variant, model, f'{SO}/{os.path.basename(model)[:-5]}_{tag}{sfx}',
            lowpass=lp)
