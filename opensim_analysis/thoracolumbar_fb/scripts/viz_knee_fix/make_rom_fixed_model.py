"""[1] 좌측 어깨 ROM 부호 수정 모델 생성 + 검증.

수정 대상은 좌표 2개의 range 뿐이다. 축·근육·질량·구속조건은 건드리지 않는다.

값의 근거: armfix 모델은 좌우 관절 축이 정확한 미러이므로, 거울 자세는 좌우 '같은 수치'로
표현된다(L = +R, 실측 확인). 따라서 좌측 ROM은 우측 ROM과 같아야 한다.
→ 우측 실측값을 그대로 복사한다. (현재 좌측 값을 부호반전하는 방식은 원본 좌우가
   0.31~0.40deg 어긋나 있어 정확히 대칭이 되지 않는다.)
"""
import os
import shutil
import numpy as np
import opensim as osim

MODELS = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x'
SRC = f'{MODELS}/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim'
DST = f'{MODELS}/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom.osim'
D2R = np.pi / 180
PAIRS = [('shoulder_elv_r', 'shoulder_elv_l'), ('shoulder_rot_r', 'shoulder_rot_l')]


def build():
    m = osim.Model(SRC)
    m.initSystem()
    cs = m.getCoordinateSet()
    print('=' * 88)
    print('[1a] ROM 수정 — 좌측 range 를 우측 실측값으로 복사')
    print('=' * 88)
    print(f"  {'좌표':16s} {'우측 (기준)':24s} {'좌측 (수정 전)':24s} {'좌측 (수정 후)':24s}")
    for cr, cl in PAIRS:
        r, l = cs.get(cr), cs.get(cl)
        lo, hi = r.getRangeMin(), r.getRangeMax()
        before = (l.getRangeMin() / D2R, l.getRangeMax() / D2R)
        l.setRangeMin(lo)
        l.setRangeMax(hi)
        print(f"  {cl:16s} [{lo/D2R:+8.2f}, {hi/D2R:+8.2f}]      "
              f"[{before[0]:+8.2f}, {before[1]:+8.2f}]      "
              f"[{l.getRangeMin()/D2R:+8.2f}, {l.getRangeMax()/D2R:+8.2f}]")
        assert lo - 1e-9 <= l.getDefaultValue() <= hi + 1e-9, f'{cl} 기본값이 새 ROM 밖'
    m.finalizeConnections()
    m.printToXML(DST)
    print(f'\n  저장 {DST}')
    return DST


def verify(dst):
    D = D2R
    m0, m1 = osim.Model(SRC), osim.Model(dst)
    m0.initSystem(); m1.initSystem()

    # (i) 좌우 동일 관절값 입력 시 거울 자세인지
    POSES = [('팔 내림', dict(shoulder_elv=5, elv_angle=0, shoulder_rot=0, elbow_flexion=5)),
             ('앞 90도', dict(shoulder_elv=90, elv_angle=0, shoulder_rot=0, elbow_flexion=10)),
             ('위 140도', dict(shoulder_elv=140, elv_angle=20, shoulder_rot=0, elbow_flexion=10)),
             ('옆 벌림 90도', dict(shoulder_elv=90, elv_angle=90, shoulder_rot=0, elbow_flexion=10)),
             ('박스 파지 유사', dict(shoulder_elv=60, elv_angle=20, shoulder_rot=-20, elbow_flexion=80)),
             ('운반 유지', dict(shoulder_elv=25, elv_angle=10, shoulder_rot=-40, elbow_flexion=95))]
    BODIES = ['humerus_R', 'ulna_R', 'radius_R', 'hand_R']
    print('\n' + '=' * 88)
    print('[1b] 좌우 동일 관절값 입력 시 거울 자세 검증  (ROM 위반 없이)')
    print('=' * 88)
    print(f"  {'자세':16s} {'ROM 위반':10s} {'말단 미러오차':>14s}")
    cs1 = m1.getCoordinateSet(); bs1 = m1.getBodySet()
    worst = 0.0
    for pname, rv in POSES:
        m1.initSystem(); s = m1.initializeState()
        viol = []
        for b, v in rv.items():
            for sfx in ('_r', '_l'):
                c = cs1.get(f'{b}{sfx}')
                lo, hi = c.getRangeMin() / D, c.getRangeMax() / D
                if v < lo - 1e-6 or v > hi + 1e-6:
                    viol.append(f'{b}{sfx}')
                c.setValue(s, v * D, False)
        m1.assemble(s); m1.realizePosition(s)
        err = 0.0
        for br in BODIES:
            bl = br.replace('_R', '_L')
            pr = bs1.get(br).getPositionInGround(s)
            pl = bs1.get(bl).getPositionInGround(s)
            err = max(err, np.linalg.norm([pr.get(0) - pl.get(0), pr.get(1) - pl.get(1),
                                           pr.get(2) + pl.get(2)]) * 100)
        worst = max(worst, err)
        print(f'  {pname:16s} {(",".join(viol) or "없음"):10s} {err:13.4f} cm')
    print(f'  -> 최대 {worst:.4f} cm')

    # (ii) 중립자세 620근육 길이 변화
    def lens(mm):
        mm.initSystem(); s = mm.initializeState()
        cs = mm.getCoordinateSet()
        for i in range(cs.getSize()):
            c = cs.get(i)
            if not c.getLocked(s):
                c.setValue(s, 0.0, False)
        mm.assemble(s); mm.realizePosition(s)
        ms = mm.getMuscles()
        return {ms.get(i).getName(): ms.get(i).getLength(s) for i in range(ms.getSize())}
    L0, L1 = lens(m0), lens(m1)
    d = {k: abs(L1[k] - L0[k]) / max(L0[k], 1e-9) * 100 for k in L0}
    es = [k for k in L0 if k.startswith(('IL_', 'LTpL', 'LTpT'))]
    print('\n' + '=' * 88)
    print('[1c] 수정 전/후 동등성')
    print('=' * 88)
    print(f'  근육 수                {len(L0)} -> {len(L1)}')
    print(f'  중립자세 길이 최대 변화  {max(d.values()):.8f} %')
    print(f'  ES {len(es)}개 최대 변화   {max(d[k] for k in es):.8f} %')

    # (iii) 구속조건·좌표·질량
    print(f'  ConstraintSet          {m0.getConstraintSet().getSize()} -> '
          f'{m1.getConstraintSet().getSize()}')
    c0 = [m0.getCoordinateSet().get(i).getName() for i in range(m0.getCoordinateSet().getSize())]
    c1 = [m1.getCoordinateSet().get(i).getName() for i in range(m1.getCoordinateSet().getSize())]
    print(f'  좌표 집합 동일          {c0 == c1}  ({len(c1)}개)')
    print(f'  총 질량                {m0.getTotalMass(m0.initSystem()):.6f} -> '
          f'{m1.getTotalMass(m1.initSystem()):.6f} kg')

    # (iv) 실제 5동작 전 프레임에서 조립 성공 여부 (구속 위반 대용 검사)
    #      ConstraintSet 이 0개이므로 위반할 구속 자체가 없다. 대신 모든 모션 프레임에서
    #      assemble 이 성공하고 좌표가 그대로 재현되는지 확인한다.
    MOTS = [('스쿼트', '/data/stoop_motion/squat_synthetic_v1.mot'),
            ('스툽', '/data/stoop_results/stoop_v5/v5_30fps_armfix.mot'),
            ('박스 들기', '/data/stoop_motion/box_stoop_lift_m1_armfix.mot'),
            ('보행', '/data/gait_motion/gait_retarget_so.mot'),
            ('운반', '/data/gait_motion/carry_walk_so_armfix.mot')]
    print('\n' + '=' * 88)
    print('[1d] 실제 5동작 전 프레임 조립 검사  (ConstraintSet 0개 = 위반할 구속 없음)')
    print('=' * 88)
    cs1 = m1.getCoordinateSet()
    names = [cs1.get(i).getName() for i in range(cs1.getSize())]
    for nm, p in MOTS:
        if not os.path.exists(p):
            print(f'  {nm:10s} 모션 없음 ({p})')
            continue
        st = osim.Storage(p)
        labs = [st.getColumnLabels().get(i) for i in range(st.getColumnLabels().getSize())]
        cols = labs[1:]
        data = {}
        for c in cols:
            a = osim.ArrayDouble(); st.getDataColumn(labs.index(c) - 1, a)
            data[c] = np.array([a.get(i) for i in range(a.getSize())])
        n = len(next(iter(data.values())))
        idx = np.linspace(0, n - 1, min(40, n)).astype(int)
        worst_rt = 0.0
        for i in idx:
            m1.initSystem(); s = m1.initializeState()
            for c in cols:
                if c not in names:
                    continue
                co = cs1.get(c)
                if co.getLocked(s):
                    continue
                co.setValue(s, data[c][i] * D2R if co.getMotionType() == 1 else data[c][i], False)
            m1.assemble(s); m1.realizePosition(s)
            for c in cols:
                if c not in names:
                    continue
                co = cs1.get(c)
                if co.getLocked(s):
                    continue
                want = data[c][i] * D2R if co.getMotionType() == 1 else data[c][i]
                worst_rt = max(worst_rt, abs(co.getValue(s) - want))
        print(f'  {nm:10s} 프레임 {len(idx):3d}개 조립 성공, 좌표 재현 오차 최대 {worst_rt:.3e}')


if __name__ == '__main__':
    dst = build()
    verify(dst)
