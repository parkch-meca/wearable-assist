"""[2] 직렬탄성 슈트 — 기하·분배·강성 스윕·기존 24 N·m 대조.

새 SO 실행 없음. 운동학·기하만으로 산출한다.
"""
import os
import json
import numpy as np
import opensim as osim
import suit_model as sm

OUT = '/data/suit_multijoint'
os.makedirs(OUT, exist_ok=True)
K_SWEEP = (2.0, 5.0, 8.0, 20.0)
D2R = np.pi / 180
LUMB = ['L5_S1_FE', 'L4_L5_FE', 'L3_L4_FE', 'L2_L3_FE', 'L1_L2_FE']


# ── (2) 기하: 자세별 경로 길이 ────────────────────────────────────
def sweep_waist(m, n=25):
    """스툽 — 기존 stoop 모션의 요추 굴곡 궤적을 재사용한다."""
    st = osim.Storage('/data/stoop_results/stoop_v5/v5_30fps_armfix.mot')
    labs = [st.getColumnLabels().get(i) for i in range(st.getColumnLabels().getSize())]
    data = {}
    for c in labs[1:]:
        a = osim.ArrayDouble()
        st.getDataColumn(labs.index(c) - 1, a)
        data[c] = np.array([a.get(i) for i in range(a.getSize())])
    tot = sum(np.abs(data[c]) for c in LUMB if c in data)
    order = np.argsort(tot)            # 굴곡량 오름차순 = 0 → 최대굴곡
    idx = order[np.linspace(0, len(order) - 1, n).astype(int)]
    rows = []
    for i in idx:
        pose = {c: data[c][i] for c in data}
        s = sm.pose_state(m, pose)
        lum = sum(abs(data[c][i]) for c in LUMB if c in data)
        hip = abs(data.get('hip_flexion_r', np.zeros(1))[i]) if 'hip_flexion_r' in data else 0.0
        rows.append(dict(angle=float(lum), hip=float(hip),
                         L=sm.path_length_mm(m, s, 'suit_waist_R'),
                         ma=float(np.mean([sm.moment_arm_mm(m, s, 'suit_waist_R', c)
                                           for c in LUMB])),
                         ma_hip=sm.moment_arm_mm(m, s, 'suit_waist_R', 'hip_flexion_r')))
    return rows


def sweep_waist_pure(m, n=25, amax=60.0):
    """고관절 통과분을 분리하기 위한 '요추 단독 굴곡' 스윕 (골반 고정)."""
    rows = []
    for a in np.linspace(0, amax, n):
        per = -a / len(LUMB)
        s = sm.pose_state(m, {c: per for c in LUMB})
        rows.append(dict(angle=float(a), L=sm.path_length_mm(m, s, 'suit_waist_R'),
                         ma=float(np.mean([sm.moment_arm_mm(m, s, 'suit_waist_R', c)
                                           for c in LUMB]))))
    return rows


def sweep_joint(m, act, coord, lo, hi, n=25, extra=None):
    rows = []
    for a in np.linspace(lo, hi, n):
        pose = dict(extra or {})
        pose[coord] = a
        s = sm.pose_state(m, pose)
        rows.append(dict(angle=float(a), L=sm.path_length_mm(m, s, act),
                         ma=sm.moment_arm_mm(m, s, act, coord)))
    return rows


# ── (3)(4) 분배·강성 스윕 ─────────────────────────────────────────
def apply_stiffness(rows, k, T0, eps=0.30):
    L0 = rows[0]['L']
    out = []
    for r in rows:
        dL = r['L'] - L0
        F, x_sma, x_s = sm.solve(dL, k, T0, eps)
        slack = (F <= 1e-9)
        out.append(dict(**r, dL=dL, F=F, x_sma=x_sma, x_series=x_s, slack=slack,
                        tau=F * r['ma'] / 1000.0))
    return out


def main():
    m, names = sm.build()
    res = {}

    print('=' * 96)
    print('[2-1] 캘리브레이션 — 직립 60 ℃, 밴드 변위 관찰 10~15 mm')
    print('=' * 96)
    cal = {}
    for k in K_SWEEP:
        T0 = sm.calibrate_T0(k)
        F, x, _ = sm.solve(0.0, k, T0)
        ok = sm.OBS_DISP[0] - 1e-6 <= x <= sm.OBS_DISP[1] + 1e-6
        cal[k] = dict(T0=T0, x=x, F=F, ok=bool(ok))
        tag = 'PASS' if ok else '관찰범위 밖 (고정부 보강 가상 조건)'
        print(f'  k={k:5.1f} N/mm  T0={T0:6.2f} N  변위 {x:6.2f} mm  장력 {F:6.2f} N  {tag}')
    obs_ok = all(cal[k]['ok'] for k in (2.0, 5.0, 8.0))
    print(f'\n  실측 역산 범위(k=2/5/8) 재현: {"PASS" if obs_ok else "FAIL"}')
    if not obs_ok:
        raise SystemExit('캘리브레이션 실패 — 중단')
    res['calibration'] = {str(k): v for k, v in cal.items()}

    print('\n' + '=' * 96)
    print('[2-2] 기하 — 부위별 ROM 전 구간 경로 길이')
    print('=' * 96)
    geo = {
        'waist_stoop': sweep_waist(m),
        'waist_pure': sweep_waist_pure(m),
        'shoulder_flex': sweep_joint(m, 'suit_shoulder_R', 'shoulder_elv_r', 0, 120),
        'shoulder_abd': sweep_joint(m, 'suit_shoulder_R', 'shoulder_elv_r', 0, 90,
                                    extra={'elv_angle_r': 90}),
        'elbow_flex': sweep_joint(m, 'suit_elbow_R', 'elbow_flexion_r', 0, 130),
    }
    LAB = {'waist_stoop': '허리 — 스툽 모션 (고관절 통과분 포함)',
           'waist_pure': '허리 — 요추 단독 굴곡 (골반 고정)',
           'shoulder_flex': '어깨 — 굴곡 0→120°',
           'shoulder_abd': '어깨 — 외전 0→90° (견갑면)',
           'elbow_flex': '팔꿈치 — 굴곡 0→130°'}
    for k_, rows in geo.items():
        L0, L1 = rows[0]['L'], rows[-1]['L']
        print(f'  {LAB[k_]:36s} L {L0:6.1f} → {L1:6.1f} mm   ΔL {L1-L0:+7.1f} mm   '
              f'모멘트암 {rows[0]["ma"]:+6.1f} → {rows[-1]["ma"]:+6.1f} mm')
    r = geo['waist_stoop']
    print(f'\n  ※ 스툽 모션에는 고관절 굴곡이 함께 들어 있다 '
          f'(0 → {r[-1]["hip"]:.1f}°). 허리 구동기는 고관절도 지나며 '
          f'모멘트암 {r[0]["ma_hip"]:+.1f} → {r[-1]["ma_hip"]:+.1f} mm.')
    print(f'  요추 단독 굴곡만 보면 ΔL {geo["waist_pure"][-1]["L"]-geo["waist_pure"][0]["L"]:+.1f} mm '
          f'(스툽 모션 {r[-1]["L"]-r[0]["L"]:+.1f} mm 의 일부).')
    res['geometry'] = geo

    print('\n' + '=' * 96)
    print('[2-3/4] 분배(SMA 신장분 vs 탄성 신장분) 및 강성 스윕')
    print('=' * 96)
    stiff = {}
    for gk, rows in geo.items():
        stiff[gk] = {}
        for k in K_SWEEP:
            stiff[gk][str(k)] = apply_stiffness(rows, k, cal[k]['T0'])
    res['stiffness'] = stiff

    print(f"  {'조건':36s} {'k':>5s} {'최대 ΔL':>9s} {'최대 장력':>9s} "
          f"{'최대 보조토크':>12s} {'이완 시작':>10s}")
    for gk, rows in geo.items():
        for k in K_SWEEP:
            S = stiff[gk][str(k)]
            dl = max(abs(r['dL']) for r in S)
            Fm = max(r['F'] for r in S)
            tm = max(abs(r['tau']) for r in S)
            sl = [r['angle'] for r in S if r['slack']]
            sls = f'{min(sl):.0f}°' if sl else '없음'
            print(f'  {LAB[gk]:36s} {k:5.1f} {dl:8.1f}mm {Fm:8.1f}N {tm:11.1f}N·m {sls:>10s}')

    print('\n' + '=' * 96)
    print('[2-6] 물리 검증 — 신장 구속 시 힘 유지 / 단축 시 이완')
    print('=' * 96)
    for gk in ('waist_stoop', 'shoulder_flex', 'elbow_flex'):
        S = stiff[gk]['5.0']
        d0, dN = S[0]['dL'], S[-1]['dL']
        print(f'  {LAB[gk]:36s} ΔL {d0:+6.1f} → {dN:+6.1f} mm   '
              f'F {S[0]["F"]:5.1f} → {S[-1]["F"]:5.1f} N   '
              f'{"신장 → 힘 유지·증가 (정상)" if dN > 0 else "단축 → 스트로크 소진 후 이완"}')

    print('\n' + '=' * 96)
    print('[2-5] 기존 5동작 24 N·m 상수 가정과의 대조 (스툽)')
    print('=' * 96)
    print(f"  {'k (N/mm)':>9s} {'허리 보조토크 (양측 합, N·m)':>28s} {'24 N·m 대비':>12s}")
    cmp_ = {}
    for k in K_SWEEP:
        S = stiff['waist_stoop'][str(k)]
        tau2 = [abs(r['tau']) * 2 for r in S]          # 좌우 2개
        cmp_[str(k)] = dict(tau_min=min(tau2), tau_max=max(tau2),
                            tau_at_max_flex=tau2[-1])
        print(f'  {k:9.1f} {min(tau2):10.1f} ~ {max(tau2):6.1f}  '
              f'(최대굴곡 {tau2[-1]:5.1f}) {tau2[-1]/24*100:11.0f} %')
    res['vs_24Nm'] = cmp_

    json.dump(res, open(f'{OUT}/suit_analysis.json', 'w'), ensure_ascii=False, indent=1)
    print(f'\nSAVED {OUT}/suit_analysis.json')


if __name__ == '__main__':
    main()
