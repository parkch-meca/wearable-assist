"""[진단 1c] 동일(미러) 관절값 입력 시 좌우 팔 말단 위치·자세 오차 실측.

모델 수정 없음. 읽기 전용.
여러 자세(내림/앞으로/위로/옆으로)에서 관절공간 미러가 성립하는지 정량 측정한다.
"""
import numpy as np, opensim as osim, json, os

MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim')
OUT = '/data/shoulder_diag'
os.makedirs(OUT, exist_ok=True)

# 검사할 body (팔 말단 사슬)
BODIES = [('humerus_R', 'humerus_L'), ('ulna_R', 'ulna_L'),
          ('radius_R', 'radius_L'), ('hand_R', 'hand_L')]

# 자세 정의: (이름, {좌표기본명: R값(deg)})
POSES = [
    ('팔 내림 (해부학적 자세)', dict(shoulder_elv=5, elv_angle=0, shoulder_rot=0,
                                elbow_flexion=5, pro_sup=0)),
    ('앞으로 뻗음 (90°)', dict(shoulder_elv=90, elv_angle=0, shoulder_rot=0,
                            elbow_flexion=10, pro_sup=0)),
    ('위로 듦 (140°)', dict(shoulder_elv=140, elv_angle=20, shoulder_rot=0,
                          elbow_flexion=10, pro_sup=0)),
    ('옆으로 벌림 (90°, 견갑면)', dict(shoulder_elv=90, elv_angle=90, shoulder_rot=0,
                                 elbow_flexion=10, pro_sup=0)),
    ('박스 파지 유사 (전방·주관절 굴곡)', dict(shoulder_elv=60, elv_angle=20,
                                       shoulder_rot=-20, elbow_flexion=80, pro_sup=45)),
]

# 미러 규칙 후보 — 각 좌표의 좌측 값 = sign * R값
RULES = {
    'A: elv/rot 부호반전, 나머지 동일':
        dict(shoulder_elv=-1, elv_angle=+1, shoulder_rot=-1, elbow_flexion=+1, pro_sup=+1),
    'B: 전부 부호반전':
        dict(shoulder_elv=-1, elv_angle=-1, shoulder_rot=-1, elbow_flexion=-1, pro_sup=-1),
    'C: elv만 부호반전':
        dict(shoulder_elv=-1, elv_angle=+1, shoulder_rot=+1, elbow_flexion=+1, pro_sup=+1),
    'D: elv/rot/pro_sup 부호반전':
        dict(shoulder_elv=-1, elv_angle=+1, shoulder_rot=-1, elbow_flexion=+1, pro_sup=-1),
}

m = osim.Model(MODEL)
st = m.initSystem()
cs = m.getCoordinateSet()
D2R = np.pi / 180


def set_pose(rvals, lvals):
    m.initSystem()
    s = m.initializeState()
    for base, v in rvals.items():
        cs.get(f'{base}_r').setValue(s, v * D2R, False)
    for base, v in lvals.items():
        cs.get(f'{base}_l').setValue(s, v * D2R, False)
    m.assemble(s)
    m.realizePosition(s)
    return s


def pos(s, body):
    b = m.getBodySet().get(body)
    p = b.getPositionInGround(s)
    return np.array([p.get(0), p.get(1), p.get(2)])


# ── 내외측(ML) 축 판별: 중립 자세에서 좌우 humerus 원점 차가 가장 큰 성분 ──
s0 = set_pose({k: 0 for k in POSES[0][1]}, {k: 0 for k in POSES[0][1]})
dh = pos(s0, 'humerus_R') - pos(s0, 'humerus_L')
ML = int(np.argmax(np.abs(dh)))
mid = (pos(s0, 'humerus_R') + pos(s0, 'humerus_L')) / 2
print(f'내외측(ML) 축 = ground 축 {"XYZ"[ML]}  (중립 좌우 humerus 차 {dh.round(4)})')
print(f'좌우 정중면 ML 좌표 = {mid[ML]:.5f} m\n')


def mirror(p):
    """정중면 기준 반사 (ML 성분만 반전)."""
    q = p.copy()
    q[ML] = 2 * mid[ML] - q[ML]
    return q


results = {}
print('=' * 112)
print('[1c] 관절공간 미러 규칙별 좌우 말단 위치 오차 (cm)')
print('=' * 112)
for rule_name, sgn in RULES.items():
    print(f'\n■ 규칙 {rule_name}')
    print(f"  {'자세':32s} " + '  '.join(f'{b[0][:-2]:>9s}' for b in BODIES) + '   최대')
    rule_res = []
    for pname, rv in POSES:
        lv = {k: v * sgn[k] for k, v in rv.items()}
        # ROM 밖이면 표시
        try:
            s = set_pose(rv, lv)
        except Exception as e:
            print(f'  {pname:32s}  ERROR {e}'); continue
        errs = []
        for br, bl in BODIES:
            e = np.linalg.norm(mirror(pos(s, br)) - pos(s, bl)) * 100
            errs.append(e)
        print(f'  {pname:32s} ' + '  '.join(f'{e:9.2f}' for e in errs) + f'  {max(errs):7.2f}')
        rule_res.append(dict(pose=pname, errs=[round(e, 2) for e in errs],
                             max=round(max(errs), 2)))
    results[rule_name] = rule_res
    print(f"  → 규칙 최대 오차 {max(r['max'] for r in rule_res):.2f} cm")

# ── ROM 위반 점검 ──
print('\n' + '=' * 112)
print('[1d] 미러 값이 좌측 ROM을 벗어나는가')
print('=' * 112)
rom_viol = []
for base in POSES[0][1]:
    cl = cs.get(f'{base}_l')
    f = 180 / np.pi
    lo, hi = cl.getRangeMin() * f, cl.getRangeMax() * f
    for rule_name, sgn in RULES.items():
        for pname, rv in POSES:
            v = rv[base] * sgn[base]
            if v < lo - 1e-6 or v > hi + 1e-6:
                rom_viol.append((rule_name, pname, base, round(v, 1), (round(lo, 1), round(hi, 1))))
seen = set()
for rn, pn, b, v, r in rom_viol:
    k = (rn.split(':')[0], b)
    if k in seen: continue
    seen.add(k)
    print(f'  [{rn.split(":")[0]}] {b}_l = {v}° 가 ROM {r} 밖  (자세: {pn})')
if not rom_viol:
    print('  위반 없음')

json.dump(dict(ML_axis='XYZ'[ML], midline=float(mid[ML]), rules=results,
               rom_violations=[list(map(str, x)) for x in rom_viol]),
          open(f'{OUT}/pose_mirror.json', 'w'), ensure_ascii=False, indent=1)
print(f'\nSAVED {OUT}/pose_mirror.json')
