"""[진단] 좌우 상지 정량 대칭성 실측 — 다관절 슈트 착수 전 선행 조건.

모델 수정 없음. 읽기 전용 진단.

착수 전제(2026-07-28 carry_walk 시점): "shoulder_elv_l 축 z성분이 미러되지 않았다
(R/L 둘 다 +0.059)". 이 스크립트의 [1a]가 그 전제를 검증한다.

★ 실측 결과 전제는 사실이 아니었다 — 시상면 반사 (ax, ay, az) → (−ax, −ay, +az) 에서
  z(내외측) 성분은 부호가 보존되므로 R/L 이 같은 것이 정답이다. 축은 정상이고,
  실제 장애물은 [1b]가 찾아낸 ROM 부호(shoulder_elv_l, shoulder_rot_l)였다.
  자세한 내용은 docs/shoulder_dof_diagnosis.md 참조.

지금까지는 척추(ES)만 측정 대상이라 무방했으나, 어깨·팔꿈치가 측정 대상이 되면
왼쪽 정량이 부정확할 경우 결과가 무효가 된다.
"""
import re, sys, json
import numpy as np
import opensim as osim

MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim')
OUT = '/data/shoulder_diag'

PAIRS = [('sterR_clavR_jnt', 'sterL_clavL_jnt'), ('shoulder_R', 'shoulder_L'),
         ('elbow', 'elbow_l'), ('radioulnar', 'radioulnar_l'),
         ('radius_hand_r', 'radius_hand_l')]
COORD_PAIRS = [('clav_prot_r', 'clav_prot_l'), ('clav_elev_r', 'clav_elev_l'),
               ('shoulder_elv_r', 'shoulder_elv_l'), ('shoulder_rot_r', 'shoulder_rot_l'),
               ('elv_angle_r', 'elv_angle_l'), ('elbow_flexion_r', 'elbow_flexion_l'),
               ('pro_sup_r', 'pro_sup_l'), ('wrist_dev_r', 'wrist_dev_l'),
               ('wrist_flex_r', 'wrist_flex_l')]


# ══════════════════════ [1a] 축 정의 전수 대조 ══════════════════════
def joint_axes(txt, name):
    """CustomJoint 의 SpatialTransform 축 벡터를 좌표명과 함께 반환."""
    m = re.search(rf'<CustomJoint name="{re.escape(name)}">(.*?)</CustomJoint>', txt, re.S)
    if not m:
        return []
    body = m.group(1)
    out = []
    for tam in re.finditer(r'<TransformAxis name="([^"]+)">(.*?)</TransformAxis>', body, re.S):
        an, ab = tam.group(1), tam.group(2)
        ax = re.search(r'<axis>([^<]+)</axis>', ab)
        co = re.search(r'<coordinates>([^<]*)</coordinates>', ab)
        if ax:
            out.append((an, (co.group(1).strip() if co else ''),
                        tuple(round(float(v), 6) for v in ax.group(1).split())))
    return out


def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    txt = open(MODEL, errors='ignore').read()
    rep = {}

    print('=' * 104)
    print('[1a] 좌우 관절 축 정의 전수 대조   (미러 규칙: ax→−ax, ay→−ay, az→az)')
    print('=' * 104)
    print(f"{'joint pair':30s} {'axis':16s} {'R 축':26s} {'L 축':26s} 판정")
    print('-' * 104)
    axis_issues = []
    for jr, jl in PAIRS:
        AR, AL = joint_axes(txt, jr), joint_axes(txt, jl)
        for (anr, cr, vr), (anl, cl, vl) in zip(AR, AL):
            exp = (-vr[0], -vr[1], vr[2])                 # 기대되는 좌측 축
            ok = all(abs(a - b) < 1e-6 for a, b in zip(exp, vl))
            # 완전 동일(미러 안 됨)인지도 구분
            same = all(abs(a - b) < 1e-6 for a, b in zip(vr, vl))
            verd = 'OK' if ok else ('⚠ 미러 안 됨(동일)' if same else '⚠ 불일치')
            if not ok:
                axis_issues.append(dict(joint=f'{jr}/{jl}', axis=anr, coord=cr,
                                        R=vr, L=vl, expected=exp, identical=same))
            if not ok or anr.startswith('rotation'):
                print(f"{jr+'/'+jl:30s} {anr+'('+cr+')':16s} "
                      f"{str(vr):26s} {str(vl):26s} {verd}")
    rep['axis_issues'] = axis_issues
    print(f"\n  → 축 불일치 {len(axis_issues)}건")

    # ══════════════════════ [1b] ROM 대조 ══════════════════════
    print('\n' + '=' * 104)
    print('[1b] 좌우 좌표 ROM 대조   (미러 기대: L범위 = −R범위 뒤집기, 또는 동일)')
    print('=' * 104)
    m = osim.Model(MODEL); m.initSystem()
    cs = m.getCoordinateSet()

    def rom(nm):
        c = cs.get(nm)
        f = 180 / np.pi if c.getMotionType() == 1 else 1.0
        return round(c.getRangeMin() * f, 2), round(c.getRangeMax() * f, 2), c.getMotionType()

    print(f"{'coord pair':34s} {'R ROM':22s} {'L ROM':22s} {'−R 뒤집기':22s} 판정")
    print('-' * 104)
    rom_issues = []
    for cr, cl in COORD_PAIRS:
        r0, r1, _ = rom(cr); l0, l1, _ = rom(cl)
        mir = (round(-r1, 2), round(-r0, 2))
        same = abs(l0 - r0) < 0.01 and abs(l1 - r1) < 0.01
        mirror_ok = abs(l0 - mir[0]) < 0.01 and abs(l1 - mir[1]) < 0.01
        verd = 'OK(동일)' if same else ('OK(미러)' if mirror_ok else '⚠ 불일치')
        if not (same or mirror_ok):
            rom_issues.append(dict(pair=f'{cr}/{cl}', R=(r0, r1), L=(l0, l1), mirror=mir))
        print(f"{cr+' / '+cl:34s} {f'[{r0}, {r1}]':22s} {f'[{l0}, {l1}]':22s} "
              f"{f'[{mir[0]}, {mir[1]}]':22s} {verd}")
    rep['rom_issues'] = rom_issues
    print(f"\n  → ROM 불일치 {len(rom_issues)}건")

    json.dump(rep, open(f'{OUT}/axis_rom.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print(f'\nSAVED {OUT}/axis_rom.json')


if __name__ == '__main__':
    main()
