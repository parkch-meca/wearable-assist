"""[진단 3] ROM 부호 수정이 문제를 해결하는지 메모리상에서만 검증.

★ 디스크의 .osim 파일은 절대 쓰지 않는다 (진단 단계). osim.Model 객체를
   메모리에서 고쳐 시험만 하고 버린다.
"""
import numpy as np, opensim as osim, json, os
MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim')
OUT = '/data/shoulder_diag'; os.makedirs(OUT, exist_ok=True)
D = np.pi / 180
FIX = {'shoulder_elv_l': (0.0, 154.70), 'shoulder_rot_l': (-90.44, 44.69)}
POSES = [('팔 내림',        dict(shoulder_elv=5,  elv_angle=0,  shoulder_rot=0,   elbow_flexion=5)),
         ('앞 90°',         dict(shoulder_elv=90, elv_angle=0,  shoulder_rot=0,   elbow_flexion=10)),
         ('위 140°',        dict(shoulder_elv=140,elv_angle=20, shoulder_rot=0,   elbow_flexion=10)),
         ('옆 벌림 90°',    dict(shoulder_elv=90, elv_angle=90, shoulder_rot=0,   elbow_flexion=10)),
         ('박스 파지 유사', dict(shoulder_elv=60, elv_angle=20, shoulder_rot=-20, elbow_flexion=80)),
         ('운반 유지',      dict(shoulder_elv=25, elv_angle=10, shoulder_rot=-40, elbow_flexion=95))]
PAIRS = [(n, n + '_l') for n in ('CORB','DELT1','DELT2','DELT3','INFSP','PECM1',
                                 'PECM2','PECM3','SUBSC','SUPSP','TMAJ','TMIN')]
BODIES = [('humerus_R','humerus_L'), ('ulna_R','ulna_L'),
          ('radius_R','radius_L'), ('hand_R','hand_L')]

def build(fix):
    m = osim.Model(MODEL); m.initSystem(); cs = m.getCoordinateSet()
    if fix:
        for nm, (lo, hi) in FIX.items():
            c = cs.get(nm); c.setRangeMin(lo * D); c.setRangeMax(hi * D)
            if c.getDefaultValue() < lo * D or c.getDefaultValue() > hi * D:
                c.setDefaultValue(np.clip(c.getDefaultValue(), lo * D, hi * D))
    m.initSystem()
    return m

def evaluate(m, tag):
    cs = m.getCoordinateSet(); bs = m.getBodySet(); ms = m.getMuscles()
    rows = []
    for pname, rv in POSES:
        m.initSystem(); s = m.initializeState(); clip = []
        for b, v in rv.items():
            for sfx in ('_r', '_l'):
                c = cs.get(f'{b}{sfx}'); lo, hi = c.getRangeMin()/D, c.getRangeMax()/D
                if v < lo - 1e-6 or v > hi + 1e-6: clip.append(f'{b}{sfx}')
                c.setValue(s, np.clip(v, lo, hi) * D, False)
        m.assemble(s); m.realizePosition(s)
        # 말단 위치 미러 오차 (정중면 z=0)
        perr = []
        for br, bl in BODIES:
            pr = bs.get(br).getPositionInGround(s); pl = bs.get(bl).getPositionInGround(s)
            a = np.array([pr.get(0), pr.get(1), -pr.get(2)])
            b_ = np.array([pl.get(0), pl.get(1), pl.get(2)])
            perr.append(np.linalg.norm(a - b_) * 100)
        # 근육 길이·모멘트암 좌우차
        dl, dm = [], []
        for a_, b_ in PAIRS:
            A, B = ms.get(a_), ms.get(b_)
            la, lb = A.getLength(s), B.getLength(s); dl.append(abs(la-lb)/la*100)
            ra = A.computeMomentArm(s, cs.get('shoulder_elv_r'))
            rb = B.computeMomentArm(s, cs.get('shoulder_elv_l'))
            if abs(ra) > 1e-3: dm.append(abs(abs(ra)-abs(rb))/abs(ra)*100)
        rows.append(dict(pose=pname, clip=clip, pos_max=max(perr), hand=perr[-1],
                         len_max=max(dl), ma_max=max(dm) if dm else float('nan')))
    print(f'\n■ {tag}')
    print(f"  {'자세':16s} {'ROM클립':18s} {'말단위치오차':>10s} {'손오차':>8s} {'길이차':>8s} {'모멘트암차':>10s}")
    for r in rows:
        print(f"  {r['pose']:16s} {(','.join(r['clip']) or '없음'):18s} "
              f"{r['pos_max']:9.3f}cm {r['hand']:7.3f}cm {r['len_max']:7.3f}% {r['ma_max']:9.3f}%")
    return rows

print('=' * 108)
print('[3] ROM 부호 수정 전/후 — 관절공간 미러(L = +R) 성립 여부')
print('=' * 108)
before = evaluate(build(False), '수정 전 (현재 armfix 모델)')
after  = evaluate(build(True),  '수정 후 (shoulder_elv_l·shoulder_rot_l ROM 부호 반전, 메모리상)')

print('\n' + '=' * 108)
print('[3b] 부작용 점검 — 수정이 다른 것을 건드리는가')
print('=' * 108)
m0, m1 = build(False), build(True)
# (i) 좌표 개수·이름
c0 = [m0.getCoordinateSet().get(i).getName() for i in range(m0.getCoordinateSet().getSize())]
c1 = [m1.getCoordinateSet().get(i).getName() for i in range(m1.getCoordinateSet().getSize())]
print(f'  좌표 집합 동일: {c0 == c1}   ({len(c0)}개)')
# (ii) 중립 자세에서 근육 길이 변화 (전체 620개)
def lens(m):
    m.initSystem(); s = m.initializeState()
    cs = m.getCoordinateSet()
    for i in range(cs.getSize()):
        c = cs.get(i)
        if not c.getLocked(s): c.setValue(s, 0.0, False)
    m.assemble(s); m.realizePosition(s)
    ms = m.getMuscles()
    return {ms.get(i).getName(): ms.get(i).getLength(s) for i in range(ms.getSize())}
L0, L1 = lens(m0), lens(m1)
d = {k: abs(L1[k]-L0[k])/max(L0[k],1e-9)*100 for k in L0}
mx = max(d, key=d.get)
print(f'  중립자세 620근육 길이 최대 변화 {d[mx]:.6f} % ({mx})')
es = [k for k in L0 if k.startswith(('IL_','LTpL','LTpT'))]
print(f'  ES {len(es)}개 길이 최대 변화 {max(d[k] for k in es):.6f} %')
# (iii) 구속조건
print(f'  ConstraintSet 개수: 수정전 {m0.getConstraintSet().getSize()} / 수정후 {m1.getConstraintSet().getSize()}')
# (iv) 기본자세가 새 ROM 안에 있는가
for nm,(lo,hi) in FIX.items():
    c=m1.getCoordinateSet().get(nm)
    print(f'  {nm} 기본값 {c.getDefaultValue()/D:+.2f}° ∈ [{lo}, {hi}] : '
          f'{lo-1e-6 <= c.getDefaultValue()/D <= hi+1e-6}')
json.dump(dict(before=before, after=after, fix=FIX,
               neutral_len_change_max_pct=d[mx], es_len_change_max_pct=max(d[k] for k in es)),
          open(f'{OUT}/fix_test.json','w'), ensure_ascii=False, indent=1, default=str)
print(f'\nSAVED {OUT}/fix_test.json')
print('\n※ 디스크의 .osim 파일은 수정하지 않았음 (메모리 객체만 변경 후 폐기).')
