"""[진단 4] 좌팔 운동학 오류가 기존 5동작 ES 정량에 미치는 영향 추정.

새 SO 실행 없음. 운동학·질량 특성만으로 체간 모멘트 변화를 계산한다.

논리: SO의 ES 요구량은 척추에 걸리는 신전 모멘트에 비례한다. 좌팔이 잘못된 위치에 있으면
(i) 골반보다 위쪽 분절 전체의 자중 모멘트 암, (ii) 손에 부여된 박스 외력의 작용점이 달라져
체간 모멘트가 바뀐다. 그 변화량을 해당 동작의 전체 모멘트와 비교해 영향 등급을 판정한다.

★ 동작마다 '올바른 좌팔'의 정의가 다르다.
   - 들기·운반: 양손 대칭 파지  → L = +R  (armfix 축이 미러이므로 같은 수치가 거울 자세)
   - 보행:      팔 스윙 교대     → L = −R
   보행에 대칭 기준을 적용하면 정상 동작을 오류로 잘못 판정한다 (초기 계산의 실수).
"""
import os
import json
import numpy as np
import opensim as osim

MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim')
OUT = '/data/shoulder_diag'
os.makedirs(OUT, exist_ok=True)
G = 9.81
D2R = np.pi / 180
ARM_COORDS = ['shoulder_elv', 'elv_angle', 'shoulder_rot', 'elbow_flexion']

# (동작명, 모션 파일, 손 외력 N, 의도)  의도 'sym' → L=+R,  'anti' → L=−R
CASES = [
    ('맨몸 스쿼트', '/data/stoop_motion/squat_synthetic_v1.mot', 0.0, 'sym'),
    ('맨몸 스툽', '/data/stoop_results/stoop_v5/v5_30fps.mot', 0.0, 'sym'),
    ('박스 들기', '/data/stoop_motion/box_stoop_lift_m1.mot', 98.1, 'sym'),
    ('맨몸 보행', '/data/gait_motion/gait_retarget_so.mot', 0.0, 'anti'),
    ('박스 운반', '/data/gait_motion/carry_walk_so.mot', 98.1, 'sym'),
]

m = osim.Model(MODEL)
m.initSystem()
cs = m.getCoordinateSet()
bs = m.getBodySet()

# 골반보다 위쪽 분절 = 체간 + 상지 + 머리 (하지 제외)
_EXCL = ('pelvis', 'femur', 'tibia', 'talus', 'calcn', 'toes', 'patella')
UPPER = [bs.get(i).getName() for i in range(bs.getSize())]
UPPER = [b for b in UPPER if not any(k in b.lower() for k in _EXCL)]


def load_mot(path):
    st = osim.Storage(path)
    labs = [st.getColumnLabels().get(i) for i in range(st.getColumnLabels().getSize())]
    out = {}
    for c in labs[1:]:
        a = osim.ArrayDouble()
        st.getDataColumn(labs.index(c) - 1, a)
        out[c] = np.array([a.get(i) for i in range(a.getSize())])
    t = osim.ArrayDouble()
    st.getTimeColumn(t)
    return np.array([t.get(i) for i in range(t.getSize())]), out


def trunk_moment(data, i, hand_N, left_sign=None):
    """골반 기준 시상면 굴곡 모멘트 (N·m). left_sign 이 주어지면 좌팔을 그 규칙으로 덮어쓴다."""
    m.initSystem()
    s = m.initializeState()
    for c in data:
        try:
            co = cs.get(c)
        except Exception:
            continue
        if co.getLocked(s):
            continue
        co.setValue(s, data[c][i] * D2R if co.getMotionType() == 1 else data[c][i], False)
    if left_sign is not None:
        for base in ARM_COORDS:
            co = cs.get(f'{base}_l')
            if not co.getLocked(s) and f'{base}_r' in data:
                co.setValue(s, data[f'{base}_r'][i] * left_sign * D2R, False)
    m.assemble(s)
    m.realizePosition(s)

    px = bs.get('pelvis').getPositionInGround(s).get(0)
    M = 0.0
    for b in UPPER:
        bd = bs.get(b)
        mass = bd.getMass()
        if mass <= 0:
            continue
        p = bd.findStationLocationInGround(s, bd.getMassCenter())
        M += mass * G * (p.get(0) - px)          # 전방 거리 × 무게 → 굴곡 모멘트
    hand_x = {}
    if hand_N > 0:
        for b in ('hand_R', 'hand_L'):
            x = bs.get(b).getPositionInGround(s).get(0)
            hand_x[b] = x
            M += hand_N * (x - px)
    return M, hand_x


def left_state(data, sign):
    """모션 파일의 좌팔이 의도와 맞는지 판정."""
    r, l = data.get('shoulder_elv_r'), data.get('shoulder_elv_l')
    if r is None or l is None:
        return '좌표 없음'
    if np.allclose(l, 0) and not np.allclose(r, 0):
        return '좌팔 미구동'
    if np.allclose(l, r * sign, atol=0.5):
        return '의도와 일치 ✓'
    if np.allclose(l, -r * sign, atol=0.5):
        return '부호 반대 ×'
    return '비대칭'


def main():
    print('=' * 112)
    print('[4] 좌팔 운동학 오류로 인한 체간(골반 기준) 시상면 모멘트 오차 — 동작별 의도 기준')
    print('=' * 112)
    print(f"{'동작':12s} {'의도':6s} {'좌팔 현재 상태':16s} "
          f"{'|Δ모멘트| 최대':>14s} {'전체 대비':>10s} {'24 N·m 대비':>12s}")
    res = {}
    for name, path, hand_N, intent in CASES:
        if not os.path.exists(path):
            print(f'  {name}: 모션 파일 없음 ({path})')
            continue
        T, data = load_mot(path)
        sign = +1 if intent == 'sym' else -1
        idx = np.linspace(0, len(T) - 1, 20).astype(int)

        diffs, totals = [], []
        for i in idx:
            M0, _ = trunk_moment(data, i, hand_N, None)
            M1, _ = trunk_moment(data, i, hand_N, sign)
            diffs.append(abs(M1 - M0))
            totals.append(abs(M0))
        diffs, totals = np.array(diffs), np.array(totals)
        k = int(np.argmax(diffs))
        frac = diffs[k] / totals[k] * 100 if totals[k] > 1 else float('nan')

        state = left_state(data, sign)
        print(f"  {name:12s} {('좌우대칭' if intent == 'sym' else '교대'):6s} {state:16s} "
              f"{diffs[k]:14.1f} {frac:9.1f} % {diffs[k] / 24 * 100:11.1f} %")
        res[name] = dict(intent=intent, state=state, dM_max=float(diffs[k]),
                         frac=float(frac), ratio24=float(diffs[k] / 24 * 100))

    json.dump(res, open(f'{OUT}/es_impact_corrected.json', 'w'), ensure_ascii=False, indent=1)
    print(f'\nSAVED {OUT}/es_impact_corrected.json')
    print('\n판정 기준 (해당 동작 전체 모멘트 대비)')
    print('  < 2 %   → (a) 무시 가능 — 기존 Phase 1a 회귀 유계(max ΔES 1.16 %p) 수준')
    print('  2 ~ 20 % → (b) 논문 각주')
    print('  > 20 %  → (c) 재해석 필요')


if __name__ == '__main__':
    main()
