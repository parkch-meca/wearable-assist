"""[3] 5동작 OFF/ON 재실행 — ROM 수정 모델 + 좌팔 수정 운동학.

■ 직전 확정본(/data/tight_unified · gait_results/*_tight · carry_results/*)에서 바뀌는 것
   (1) 기저 모델: ..._M1scap_armfix.osim  ->  ..._M1scap_armfix_rom.osim
       (좌표 2개의 range 부호만 다름. 축·근육·질량·구속 동일, 중립자세 근육길이 변화 0.00000000 %)
   (2) 운동학: 스툽·박스 들기·박스 운반의 좌팔 좌표를 우측의 거울(L = +R)로 채움
       스쿼트·보행은 원본 그대로 (스쿼트는 이미 대칭, 보행은 교대 스윙이 정상)

■ 그 외는 전부 원본과 동일하게 유지한다
   reserve tight(척추 5 N·m), 외력/GRF 파일, 시간 범위, lowpass, SO 옵션.

■ 스쿼트·보행은 운동학이 안 바뀌므로, 이 재실행은 그 자체가 ROM 수정의 회귀 검증이 된다
   (기존 결과와 일치해야 함).

병렬 실행 시 OMP_NUM_THREADS=1 필수 — BLAS 스레드 경합으로 수십 배 느려진다.
"""
import os
import re
import sys
import time
import shutil
from pathlib import Path
import opensim as osim

MODELS = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x'
BASE = f'{MODELS}/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom.osim'
OUT = Path('/data/romfix_unified')
OUT.mkdir(exist_ok=True)
SPINE_KEYS = ('_FE', '_LB', '_AR', 'Abs_')

# lowpass: 스쿼트·스툽·박스는 원본이 -1(무필터), 보행·운반은 6 Hz
JOBS = {
 'squat_off': dict(mot='/data/stoop_motion/squat_synthetic_v1.mot',
                   ext='/data/squat_results/suit_sweep/F0/ext_loads_F0.xml',
                   t=(0.0, 5.0), lp=-1, prev='/data/tight_unified/squat_off'),
 'squat_on':  dict(mot='/data/stoop_motion/squat_synthetic_v1.mot',
                   ext='/data/squat_results/suit_sweep/F200/ext_loads_F200.xml',
                   t=(0.0, 5.0), lp=-1, prev='/data/tight_unified/squat_on'),
 'stoop_off': dict(mot='/data/stoop_results/stoop_v5/v5_30fps_armfix.mot',
                   ext='/data/stoop_motion/stoop_grf_v5.xml',
                   t=(0.0, 5.0), lp=-1, prev='/data/tight_unified/stoop_off'),
 'stoop_on':  dict(mot='/data/stoop_results/stoop_v5/v5_30fps_armfix.mot',
                   ext='/data/stoop_results/suit_sweep_v5/F200/ext_loads_F200.xml',
                   t=(0.0, 5.0), lp=-1, prev='/data/tight_unified/stoop_on'),
 'box_off':   dict(mot='/data/stoop_motion/box_stoop_lift_m1_armfix.mot',
                   ext='/data/stoop_results/box_stoop_so/B_off/ext_B_off.xml',
                   t=(0.0, 7.5), lp=-1, prev='/data/tight_unified/box_off'),
 'box_on':    dict(mot='/data/stoop_motion/box_stoop_lift_m1_armfix.mot',
                   ext='/data/stoop_results/box_stoop_so/B_on/ext_B_on.xml',
                   t=(0.0, 7.5), lp=-1, prev='/data/tight_unified/box_on'),
 'gait_off':  dict(mot='/data/gait_motion/gait_retarget_so.mot',
                   ext='/data/gait_results/gait_off/ext.xml',
                   t=(0.4, 1.6), lp=6, prev='/data/gait_results/gait_off_tight'),
 'gait_on':   dict(mot='/data/gait_motion/gait_retarget_so.mot',
                   ext='/data/gait_results/gait_on/ext.xml',
                   t=(0.4, 1.6), lp=6, prev='/data/gait_results/gait_on_tight'),
 'carry_off': dict(mot='/data/gait_motion/carry_walk_so_armfix.mot',
                   ext='/data/carry_results/carry_off/ext.xml',
                   t=(0.4, 1.6), lp=6, prev='/data/carry_results/carry_off'),
 'carry_on':  dict(mot='/data/gait_motion/carry_walk_so_armfix.mot',
                   ext='/data/carry_results/carry_on/ext.xml',
                   t=(0.4, 1.6), lp=6, prev='/data/carry_results/carry_on'),
}


def reserved_tight(src, dst):
    """gait_so_tight.py / carry_so.py / rerun_unified_all.py 와 문자 그대로 동일."""
    m = osim.Model(src)
    m.initSystem()
    cs = m.getCoordinateSet()
    n_spine = 0
    for i in range(cs.getSize()):
        c = cs.get(i)
        nm = c.getName()
        a = osim.CoordinateActuator(nm)
        a.setName(f'reserve_{nm}')
        if nm.startswith('pelvis'):
            opt = 500.0 if c.getMotionType() == 1 else 1000.0
        elif any(k in nm for k in SPINE_KEYS):
            opt = 5.0
            n_spine += 1
        else:
            opt = 100.0 if c.getMotionType() == 1 else 1000.0
        a.setOptimalForce(opt)
        a.setMinControl(-50.0)
        a.setMaxControl(50.0)
        m.addForce(a)
    m.finalizeConnections()
    m.printToXML(dst)
    return n_spine


def run(tag):
    j = JOBS[tag]
    d = OUT / tag
    d.mkdir(exist_ok=True)
    mres = str(d / 'model_res_tight.osim')
    n_spine = reserved_tight(BASE, mres)

    ext_src = Path(j['ext'])
    ext_dst = d / ext_src.name
    shutil.copy(ext_src, ext_dst)
    # 압축 XML(한 줄)도 처리되도록 전체 텍스트 정규식으로 참조 파일 수집
    for fn in set(re.findall(r'<(?:datafile|data_source_name)>([^<]+)<', ext_dst.read_text())):
        fn = fn.strip()
        if not fn:
            continue
        if fn.startswith('/'):
            continue
        cand = ext_src.parent / fn
        if cand.exists() and not (d / fn).exists():
            shutil.copy(cand, d / fn)

    t0, t1 = j['t']
    tool = osim.AnalyzeTool()
    tool.setModelFilename(mres)
    tool.setName('so')
    tool.setResultsDir(str(d))
    tool.setInitialTime(t0)
    tool.setFinalTime(t1)
    tool.setLowpassCutoffFrequency(j['lp'])
    tool.setCoordinatesFileName(j['mot'])
    tool.setReplaceForceSet(False)
    tool.setExternalLoadsFileName(str(ext_dst))
    so = osim.StaticOptimization()
    so.setStartTime(t0)
    so.setEndTime(t1)
    so.setUseMusclePhysiology(True)
    so.setActivationExponent(2.0)
    so.setConvergenceCriterion(1e-4)
    so.setMaxIterations(300)
    tool.getAnalysisSet().cloneAndAppend(so)
    setup = str(d / 'setup.xml')
    tool.printToXML(setup)
    print(f'[{tag}] 척추 reserve {n_spine}개 opt=5.0 | mot={Path(j["mot"]).name} '
          f'| lp={j["lp"]} | t=({t0},{t1})', flush=True)
    st = time.time()
    ok = osim.AnalyzeTool(setup).run()
    print(f'[{tag}] ok={ok}  {time.time() - st:.0f}s', flush=True)


if __name__ == '__main__':
    tags = sys.argv[1:] or list(JOBS)
    for tag in tags:
        run(tag)
