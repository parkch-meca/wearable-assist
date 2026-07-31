"""[진단 2] 어깨·팔꿈치 근육의 좌우 정량 정확도 측정. 모델 수정 없음(읽기 전용).

명명 규칙 주의: 이 모델의 상지 근육은 우측이 무접미(DELT1), 좌측이 _l(DELT1_l).
하지·체간은 _r/_l 를 쓴다.
"""
import numpy as np, opensim as osim, json, os

MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim')
OUT = '/data/shoulder_diag'; os.makedirs(OUT, exist_ok=True)
D2R = np.pi / 180
m = osim.Model(MODEL); m.initSystem(); cs = m.getCoordinateSet(); ms = m.getMuscles()
names = [ms.get(i).getName() for i in range(ms.getSize())]
s0 = m.initializeState(); m.realizePosition(s0)

# ── 관절을 실제로 지나는 근육으로 정의 (모멘트암 기준, 이름 규칙 무관) ──
JOINTS = [('어깨 거상', 'shoulder_elv_r', 'shoulder_elv_l'),
          ('어깨 회전', 'shoulder_rot_r', 'shoulder_rot_l'),
          ('견갑면각', 'elv_angle_r', 'elv_angle_l'),
          ('팔꿈치 굴곡', 'elbow_flexion_r', 'elbow_flexion_l'),
          ('전완 회내외', 'pro_sup_r', 'pro_sup_l')]

def crossing(coord, thr=0.002):
    out = []
    for nm in names:
        try:
            r = ms.get(nm).computeMomentArm(s0, cs.get(coord))
        except Exception:
            continue
        if abs(r) > thr: out.append(nm)
    return out

print('=' * 104)
print('[2a] 각 상지 관절을 지나는 근육 수 (모멘트암 |r| > 2 mm 기준, 중립 자세)')
print('=' * 104)
print(f"{'관절':12s} {'우측':>5s} {'좌측':>5s}  판정")
cross = {}
for lbl, cr, cl in JOINTS:
    a, b = crossing(cr), crossing(cl)
    cross[lbl] = (a, b)
    verd = 'OK' if len(a) == len(b) else f'⚠ 불일치 ({len(a)} vs {len(b)})'
    if len(a) == 0: verd = '❌ 구동 근육 없음'
    print(f'{lbl:12s} {len(a):5d} {len(b):5d}  {verd}')
print('\n  어깨 거상 우측 근육:', sorted(cross['어깨 거상'][0]))
print('  어깨 거상 좌측 근육:', sorted(cross['어깨 거상'][1]))
print('  팔꿈치 굴곡 우측 근육:', sorted(cross['팔꿈치 굴곡'][0]) or '(없음)')

# ── 좌우 짝짓기: 우측 무접미 ↔ 좌측 _l ──
sh_r = sorted(cross['어깨 거상'][0]); sh_l = sorted(cross['어깨 거상'][1])
pairs = [(r, r + '_l') for r in sh_r if r + '_l' in names]
unpaired = [r for r in sh_r if r + '_l' not in names]
print(f'\n  짝 성립 {len(pairs)} / 우측 {len(sh_r)}   짝 없음 {unpaired}')

# ── 경로점 대조 ──
def path_pts(nm):
    gp = ms.get(nm).getGeometryPath(); ps = gp.getPathPointSet()
    return [(ps.get(i).getBody().getName(),
             np.array([ps.get(i).getLocation(s0).get(k) for k in range(3)]))
            for i in range(ps.getSize())]

print('\n' + '=' * 104)
print('[2b] 경로점 개수·부착 body·국소좌표 미러 대조   (미러 기대: 국소 z → −z)')
print('=' * 104)
bad_n, bad_body, bad_loc, locerr = [], [], [], []
for pr, pl in pairs:
    A, B = path_pts(pr), path_pts(pl)
    if len(A) != len(B):
        bad_n.append((pr, len(A), len(B))); continue
    for (br, vr), (bl, vl) in zip(A, B):
        exp = br + '_l' if (br + '_l') in [bl, br + '_l'] else br.replace('_R', '_L')
        if bl not in (exp, br, br + '_l', br.replace('_R', '_L')):
            bad_body.append((pr, br, bl))
        e = np.abs(np.array([vr[0], vr[1], -vr[2]]) - vl).max() * 1000
        locerr.append(e)
        if e > 1.0: bad_loc.append((pr, br, round(e, 2)))
le = np.array(locerr) if locerr else np.array([0.0])
print(f'  경로점 개수 불일치 {len(bad_n)}건 {bad_n[:6]}')
print(f'  부착 body 불일치 {len(bad_body)}건 {bad_body[:6]}')
print(f'  국소좌표 미러오차 (z반전 기준): 중앙 {np.median(le):.4f} mm  최대 {le.max():.4f} mm  '
      f'1 mm 초과 {len(bad_loc)}건')
if bad_loc: print('   ', bad_loc[:8])

# ── 파라미터 대조 ──
print('\n' + '=' * 104)
print('[2c] 근육 파라미터 좌우 대조')
print('=' * 104)
P = (('Fmax', lambda x: x.getMaxIsometricForce()),
     ('Lopt', lambda x: x.getOptimalFiberLength()),
     ('Lts',  lambda x: x.getTendonSlackLength()),
     ('alpha', lambda x: x.getPennationAngleAtOptimalFiberLength()))
for k, f in P:
    d = []
    for pr, pl in pairs:
        va, vb = f(ms.get(pr)), f(ms.get(pl))
        d.append((abs(va - vb) / max(abs(va), 1e-9) * 100, pr))
    mx = max(d)
    print(f'  {k:6s} 최대 상대차 {mx[0]:8.4f} % ({mx[1]})   0.5 % 초과 {sum(1 for x,_ in d if x>0.5)}/{len(d)}')

# ── 대칭 자세에서 길이·모멘트암 ──
print('\n' + '=' * 104)
print('[2d] 대칭 자세에서 근육 길이·모멘트암 좌우 대조   (미러 규칙 L = +R)')
print('=' * 104)
POSES = [('팔 내림',        dict(shoulder_elv=5,  elv_angle=0,  shoulder_rot=0,   elbow_flexion=5)),
         ('앞 90°',         dict(shoulder_elv=90, elv_angle=0,  shoulder_rot=0,   elbow_flexion=10)),
         ('박스 파지 유사', dict(shoulder_elv=60, elv_angle=20, shoulder_rot=-20, elbow_flexion=80))]
res = {}
for pname, rv in POSES:
    m.initSystem(); st = m.initializeState()
    clipped = []
    for bnm, v in rv.items():
        for sfx in ('_r', '_l'):
            c = cs.get(f'{bnm}{sfx}')
            lo, hi = c.getRangeMin() / D2R, c.getRangeMax() / D2R
            if v < lo - 1e-6 or v > hi + 1e-6: clipped.append(f'{bnm}{sfx}')
            c.setValue(st, np.clip(v, lo, hi) * D2R, False)
    m.assemble(st); m.realizePosition(st)
    dl, dma = [], []
    for pr, pl in pairs:
        a, b = ms.get(pr), ms.get(pl)
        la, lb = a.getLength(st), b.getLength(st)
        dl.append(abs(la - lb) / max(la, 1e-9) * 100)
        ra = a.computeMomentArm(st, cs.get('shoulder_elv_r'))
        rb = b.computeMomentArm(st, cs.get('shoulder_elv_l'))
        if abs(ra) > 1e-3: dma.append(abs(abs(ra) - abs(rb)) / abs(ra) * 100)
    dl = np.array(dl); dma = np.array(dma) if dma else np.array([np.nan])
    print(f'  {pname:14s} ROM클립 {clipped if clipped else "없음"}')
    print(f'                 길이차 중앙 {np.median(dl):7.4f} % 최대 {dl.max():8.4f} %  | '
          f'모멘트암차 중앙 {np.nanmedian(dma):7.4f} % 최대 {np.nanmax(dma):8.4f} % (n={len(dma)})')
    res[pname] = dict(clipped=clipped, len_max=float(dl.max()), ma_max=float(np.nanmax(dma)))

json.dump(dict(crossing={k: [len(v[0]), len(v[1])] for k, v in cross.items()},
               shoulder_R=sh_r, shoulder_L=sh_l, pairs=len(pairs), unpaired=unpaired,
               pathpt_bad_n=bad_n, pathpt_bad_body=[list(map(str, x)) for x in bad_body],
               loc_err_max_mm=float(le.max()), poses=res),
          open(f'{OUT}/muscles.json', 'w'), ensure_ascii=False, indent=1)
print(f'\nSAVED {OUT}/muscles.json')
