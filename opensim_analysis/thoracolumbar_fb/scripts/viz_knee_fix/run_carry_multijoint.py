"""[2] 운반 다부위 SO 실행 — 5조건.

■ 조건 통일
  /data/romfix_unified/carry_off 의 setup 을 그대로 쓰고 **모델과 외력만** 교체한다.
  운동학(.mot) · 시간범위(0.4~1.6 s) · lowpass · SO 옵션은 원본 그대로.

■ ⚠️ 기준선이 기존 5동작 운반과 다르다
  팔 부위 효과를 측정하려면 팔 구동 근육이 있어야 하고(기존 모델은 0개),
  팔 액추에이터가 부하를 흡수하지 않아야 한다. 따라서 본 실험은
    · 기저 모델 = ..._armfix_rom_elbow.osim (팔꿈치근 14개 추가)
    · 팔 내장 액추에이터(elbow 300, shoulder 1000) 와 팔 reserve 를 전부 opt = 5
  로 두고 **OFF 부터 새로 뽑는다**. 5조건은 서로 완전히 같은 조건이므로
  내부 비교는 유효하지만, **기존 5동작 논문의 운반 −25.7 % 와 직접 비교하지 않는다.**
"""
import os
import re
import sys
import time
import shutil
from pathlib import Path
import opensim as osim

SRC = Path('/data/romfix_unified/carry_off')
OUT = Path('/data/suit_carry')
OUT.mkdir(exist_ok=True)
BASE = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
        'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom_elbow.osim')
SPINE_KEYS = ('_FE', '_LB', '_AR', 'Abs_')
ARM_COORDS = ('shoulder_elv', 'shoulder_rot', 'elv_angle', 'elbow_flexion', 'pro_sup')
ARM_ACT = ('elbow_R_actuator', 'elbow_L_actuator',
           'shoulder_elv_r_actuator', 'shoulder_elv_l_actuator',
           'shoulder_rot_r_actuator', 'shoulder_rot_l_actuator',
           'elv_angle_r_actuator', 'elv_angle_l_actuator')
OPT_TIGHT = 5.0
CONDS = ['off', 'waist', 'elbow', 'elbow_ext', 'all']


def build_model(dst):
    """reserve 추가 + 척추/팔 조임. rerun_unified_all.reserved_tight 와 같은 규칙."""
    m = osim.Model(BASE)
    m.initSystem()
    cs = m.getCoordinateSet()
    n_spine = n_arm = 0
    for i in range(cs.getSize()):
        c = cs.get(i)
        nm = c.getName()
        a = osim.CoordinateActuator(nm)
        a.setName(f'reserve_{nm}')
        if nm.startswith('pelvis'):
            opt = 500.0 if c.getMotionType() == 1 else 1000.0
        elif any(k in nm for k in SPINE_KEYS):
            opt = OPT_TIGHT
            n_spine += 1
        elif any(nm.startswith(k) for k in ARM_COORDS):
            opt = OPT_TIGHT
            n_arm += 1
        else:
            opt = 100.0 if c.getMotionType() == 1 else 1000.0
        a.setOptimalForce(opt)
        a.setMinControl(-50.0)
        a.setMaxControl(50.0)
        m.addForce(a)
    fs = m.getForceSet()
    n_act = 0
    for i in range(fs.getSize()):
        a = osim.CoordinateActuator.safeDownCast(fs.get(i))
        if a and a.getName() in ARM_ACT:
            a.setOptimalForce(OPT_TIGHT)
            a.setMinControl(-50.0)
            a.setMaxControl(50.0)
            n_act += 1
    m.finalizeConnections()
    m.printToXML(dst)
    return n_spine, n_arm, n_act


def run(tag, mres):
    d = OUT / tag
    d.mkdir(exist_ok=True)
    tool = osim.AnalyzeTool(str(SRC / 'setup.xml'), False)
    tool.setModelFilename(mres)
    tool.setResultsDir(str(d))
    tool.setExternalLoadsFileName(f'{OUT}/ext_{tag}.xml')
    setup = str(d / 'setup.xml')
    tool.printToXML(setup)
    print(f'[{tag}] 시작', flush=True)
    t0 = time.time()
    ok = osim.AnalyzeTool(setup).run()
    print(f'[{tag}] ok={ok}  {time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    mres = str(OUT / 'model_res_tight.osim')
    if not os.path.exists(mres) or '--rebuild' in sys.argv:
        ns, na, nc = build_model(mres)
        print(f'모델 생성: 척추 reserve {ns}개 · 팔 reserve {na}개 · '
              f'팔 내장 액추에이터 {nc}개 모두 opt={OPT_TIGHT}', flush=True)
    for tag in ([a for a in sys.argv[1:] if not a.startswith('--')] or CONDS):
        run(tag, mres)
