"""[좌팔 수정] 상지 좌표별 미러 부호를 실측으로 확정하고, 지정 .mot 의 좌팔을 채운다.

원리: armfix 모델은 좌우 관절 축이 정확히 미러(−ax,−ay,+az)이므로 이론상 L = +R 이어야
거울 자세가 된다. 그러나 이론에 기대지 않고 각 좌표를 단독으로 흔들어 말단 미러오차가
최소가 되는 부호를 실측으로 고른다(축 정의를 다시 신뢰하지 않기 위함).

대상: 스툽 / 박스 들기 / 박스 운반.
제외: 스쿼트(이미 L=+R 로 미러오차 0.00 cm), 보행(좌우 교대 스윙이 정상).
"""
import os
import json
import numpy as np
import opensim as osim

MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim')
D2R = np.pi / 180
ARM = ['clav_prot', 'clav_elev', 'shoulder_elv', 'elv_angle', 'shoulder_rot',
       'elbow_flexion', 'pro_sup', 'wrist_flex', 'wrist_dev']
BODIES = ['humerus_R', 'ulna_R', 'radius_R', 'hand_R']

m = osim.Model(MODEL)
m.initSystem()
cs = m.getCoordinateSet()
bs = m.getBodySet()
COORDS = [cs.get(i).getName() for i in range(cs.getSize())]


def _pose(vals):
    m.initSystem()
    s = m.initializeState()
    for c, v in vals.items():
        if c not in COORDS:
            continue
        co = cs.get(c)
        if co.getLocked(s):
            continue
        co.setValue(s, v * D2R if co.getMotionType() == 1 else v, False)
    m.assemble(s)
    m.realizePosition(s)
    return s


def _mirror_err(s):
    """우측 말단을 정중면(z=0) 반사한 위치와 좌측 말단의 거리 (cm)."""
    e = []
    for br in BODIES:
        bl = br.replace('_R', '_L')
        pr = bs.get(br).getPositionInGround(s)
        pl = bs.get(bl).getPositionInGround(s)
        e.append(np.linalg.norm([pr.get(0) - pl.get(0), pr.get(1) - pl.get(1),
                                 pr.get(2) + pl.get(2)]) * 100)
    return max(e)


def resolve_signs(verbose=True):
    """좌표별로 +1 / −1 중 미러오차가 작은 쪽을 고른다."""
    signs = {}
    if verbose:
        print('=' * 78)
        print('[A] 상지 좌표별 미러 부호 실측  (한 좌표씩 단독 시험)')
        print('=' * 78)
        print(f"  {'좌표':16s} {'시험각':>7s} {'L=+R 오차':>12s} {'L=-R 오차':>12s}  채택")
    for base in ARM:
        if f'{base}_r' not in COORDS or f'{base}_l' not in COORDS:
            continue
        cr = cs.get(f'{base}_r')
        lo, hi = cr.getRangeMin() / D2R, cr.getRangeMax() / D2R
        test = float(np.clip(25.0, lo + 1, hi - 1))
        errs = {}
        for sg in (+1, -1):
            errs[sg] = _mirror_err(_pose({f'{base}_r': test, f'{base}_l': test * sg}))
        best = min(errs, key=errs.get)
        signs[base] = best
        if verbose:
            print(f"  {base:16s} {test:+7.1f} {errs[+1]:11.3f}cm {errs[-1]:11.3f}cm  "
                  f"L = {'+' if best > 0 else '-'}R")
    return signs


def load_mot(path):
    st = osim.Storage(path)
    labs = [st.getColumnLabels().get(i) for i in range(st.getColumnLabels().getSize())]
    cols = labs[1:]
    data = {}
    for c in cols:
        a = osim.ArrayDouble()
        st.getDataColumn(labs.index(c) - 1, a)
        data[c] = np.array([a.get(i) for i in range(a.getSize())])
    t = osim.ArrayDouble()
    st.getTimeColumn(t)
    return np.array([t.get(i) for i in range(t.getSize())]), data, cols


def write_mot(path, name, T, data, cols):
    hdr = [name, 'version=1', f'nRows={len(T)}', f'nColumns={len(cols) + 1}',
           'inDegrees=yes', '', 'Units are S.I. units (second, meters, Newtons, ...)',
           'endheader']
    with open(path, 'w') as f:
        f.write('\n'.join(hdr) + '\n')
        f.write('time\t' + '\t'.join(cols) + '\n')
        for i, t in enumerate(T):
            f.write('\t'.join([f'{t:.6f}'] + [f'{data[c][i]:.8f}' for c in cols]) + '\n')


def mirror_left(src, dst, name, signs):
    T, data, cols = load_mot(src)
    changed = []
    for base, sg in signs.items():
        cr, cl = f'{base}_r', f'{base}_l'
        if cr in data and cl in data:
            new = data[cr] * sg
            if not np.allclose(new, data[cl], atol=1e-6):
                changed.append((base, float(np.abs(new - data[cl]).max())))
            data[cl] = new
    write_mot(dst, name, T, data, cols)
    return T, data, cols, changed


def hand_report(T, data, idx=None):
    if idx is None:
        idx = np.linspace(0, len(T) - 1, 15).astype(int)
    out = []
    for i in idx:
        s = _pose({c: data[c][i] for c in data})
        hr = bs.get('hand_R').getPositionInGround(s)
        hl = bs.get('hand_L').getPositionInGround(s)
        out.append(dict(t=float(T[i]),
                        R=[hr.get(0), hr.get(1), hr.get(2)],
                        L=[hl.get(0), hl.get(1), hl.get(2)],
                        err=float(np.linalg.norm([hr.get(0) - hl.get(0),
                                                  hr.get(1) - hl.get(1),
                                                  hr.get(2) + hl.get(2)]) * 100)))
    return out


JOBS = [('스툽', '/data/stoop_results/stoop_v5/v5_30fps.mot',
         '/data/stoop_results/stoop_v5/v5_30fps_armfix.mot', 'stoop_v5_armfix'),
        ('박스 들기', '/data/stoop_motion/box_stoop_lift_m1.mot',
         '/data/stoop_motion/box_stoop_lift_m1_armfix.mot', 'box_stoop_lift_m1_armfix'),
        ('박스 운반', '/data/gait_motion/carry_walk_so.mot',
         '/data/gait_motion/carry_walk_so_armfix.mot', 'carry_walk_so_armfix')]


def main():
    signs = resolve_signs()
    os.makedirs('/data/shoulder_diag', exist_ok=True)
    json.dump(signs, open('/data/shoulder_diag/mirror_signs.json', 'w'), indent=1)

    print('\n' + '=' * 78)
    print('[B] 좌팔 재생성 — 좌측 = 부호 x 우측')
    print('=' * 78)
    summary = {}
    for nm, src, dst, name in JOBS:
        T0, d0, _ = load_mot(src)
        before = hand_report(T0, d0)
        T, d, cols, changed = mirror_left(src, dst, name, signs)
        after = hand_report(T, d)
        eb = max(x['err'] for x in before)
        ea = max(x['err'] for x in after)
        print(f'\n[{nm}]  ->  {dst}')
        print(f'  변경 좌표 {len(changed)}개: ' +
              (', '.join(f'{b}(최대 {v:.1f}deg)' for b, v in changed) or '없음'))
        print(f'  손 미러오차   수정 전 최대 {eb:8.3f} cm  ->  수정 후 최대 {ea:8.3f} cm')
        summary[nm] = dict(src=src, dst=dst, err_before=eb, err_after=ea,
                           changed=changed, after=after)
    json.dump(summary, open('/data/shoulder_diag/leftarm_fix.json', 'w'),
              ensure_ascii=False, indent=1)
    print('\nSAVED /data/shoulder_diag/leftarm_fix.json')


if __name__ == '__main__':
    main()
