"""[사전검증] 스툽 동작의 어깨·팔꿈치 부하 실측 — 슈트를 붙일 값어치가 있는가.

■ 왜 먼저 하는가
  사용자 지적대로 스툽은 팔에 짐이 없다. 어깨·팔꿈치 모멘트가 미미하면
  "부위별 기여 분해"의 어깨·팔꿈치 항이 0 근처에서 노이즈만 비교하게 된다.
  SO 5조건(수십 분)을 돌리기 전에 역동역학으로 요구 모멘트를 먼저 잰다.

■ 방법
  InverseDynamicsTool — 모델 + 운동학 + GRF(OFF). 근육·reserve 와 무관한
  순수 요구 일반화력이다.

■ 판정 기준
  허리(L5_S1_FE 등) 대비 어깨(elv_angle) · 팔꿈치(elbow_flexion) 요구 모멘트의 비.
  창(허리 최대 굴곡 구간) 안에서 평가한다.
"""
import os
import json
import numpy as np
import opensim as osim

MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom_elbow.osim')
MOT = '/data/stoop_results/stoop_v5/v5_30fps_armfix.mot'
EXT = '/data/romfix_unified/stoop_off/stoop_grf_v5.xml'
OUT = '/data/suit_multijoint'
WIN = (2.091667, 3.408333)
T0, T1 = 0.0, 5.0

WATCH = ['L5_S1_FE', 'L4_L5_FE', 'L1_L2_FE', 'T8_T9_FE',
         'elv_angle_r', 'elv_angle_l', 'shoulder_elv_r', 'shoulder_rot_r',
         'elbow_flexion_r', 'elbow_flexion_l']


def run_id(d):
    os.makedirs(d, exist_ok=True)
    tool = osim.InverseDynamicsTool()
    tool.setModelFileName(MODEL)
    tool.setStartTime(T0)
    tool.setEndTime(T1)
    tool.setCoordinatesFileName(MOT)
    tool.setLowpassCutoffFrequency(6.0)
    tool.setExternalLoadsFileName(EXT)
    tool.setResultsDir(d)
    tool.setOutputGenForceFileName('id_stoop.sto')
    setup = f'{d}/id_setup.xml'
    tool.printToXML(setup)
    ok = osim.InverseDynamicsTool(setup).run()
    return ok, f'{d}/id_stoop.sto'


def read(p):
    t = osim.TimeSeriesTable(p)
    T = np.array(list(t.getIndependentColumn()))
    L = list(t.getColumnLabels())
    D = {c: np.array([float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())])
         for c in L}
    return T, D


def main():
    d = f'{OUT}/id'
    ok, p = run_id(d)
    print(f'ID ok={ok}')
    T, D = read(p)
    m = (T >= WIN[0]) & (T <= WIN[1])
    print('=' * 84)
    print('스툽 · 창내 요구 모멘트 (역동역학, GRF OFF)')
    print('=' * 84)
    print(f"{'좌표':18s} {'창내 |M| 평균':>13s} {'창내 |M| 최대':>13s} {'전구간 최대':>12s}")
    res = {}
    for c in WATCH:
        k = next((x for x in D if x.startswith(c)), None)
        if k is None:
            print(f'  {c:18s} — 없음')
            continue
        v = D[k]
        res[c] = dict(win_mean=float(np.abs(v[m]).mean()),
                      win_max=float(np.abs(v[m]).max()),
                      all_max=float(np.abs(v).max()),
                      signed_win_mean=float(v[m].mean()))
        print(f'  {c:18s} {res[c]["win_mean"]:12.2f} {res[c]["win_max"]:13.2f} '
              f'{res[c]["all_max"]:12.2f}   N·m')

    ref = res['L5_S1_FE']['win_mean']
    print('\n' + '=' * 84)
    print('판정 — 허리 L5_S1 대비 비율')
    print('=' * 84)
    for c in ('elv_angle_r', 'shoulder_elv_r', 'elbow_flexion_r'):
        r = 100 * res[c]['win_mean'] / ref
        tag = ('유의 (≥10 %)' if r >= 10 else
               '작음 (3~10 %)' if r >= 3 else '무시 가능 (<3 %)')
        print(f'  {c:18s} {r:6.1f} %  → {tag}')
    print(f'\n  부호(창내 평균): elv_angle_r {res["elv_angle_r"]["signed_win_mean"]:+.2f}, '
          f'elbow_flexion_r {res["elbow_flexion_r"]["signed_win_mean"]:+.2f} N·m')
    json.dump(dict(win=WIN, res=res), open(f'{OUT}/arm_demand.json', 'w'),
              ensure_ascii=False, indent=1)
    print(f'\nSAVED {OUT}/arm_demand.json')


if __name__ == '__main__':
    main()
