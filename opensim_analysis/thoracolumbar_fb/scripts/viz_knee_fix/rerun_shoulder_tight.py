"""[4] 어깨 CoordinateActuator tight 재실행 — 삼각근 측정 가능성 게이트.

■ 문제
  모델에 내장된 shoulder_elv / shoulder_rot / elv_angle 좌우 6개 CoordinateActuator 는
  optimal_force = 1000, min/max control = ±inf 로 사실상 무제한이다.
  SO 비용함수에서 거의 공짜이므로 어깨 부하를 근육 대신 이 액추에이터가 가져간다.
  척추에서 표준 reserve 가 ES 를 3배 과소평가했던 것과 같은 구조다.

■ 처치
  척추 tight 와 동일하게 optimal_force 를 5 로 낮춘다. 하드 캡이 아니라 비용 기반 억제다.
  ★ 내장 액추에이터만 조이면 부하가 reserve_shoulder_* (opt=100) 로 옮겨갈 뿐이다
    (1차 실행에서 실측 확인: 액추에이터 3.545 → 0.006 N·m, reserve 0.035 → 2.557 N·m).
    따라서 어깨 자유도의 **reserve 도 함께** opt=5 로 조인다 — 척추와 동일 기준.
  그 외 조건(운동학·외력·척추 reserve·SO 옵션)은 romfix_unified 와 완전히 동일하게 둔다.

■ 판정
  tight 후 어깨 굴곡 토크에서 근육이 차지하는 비율이 90 % 이상이면 삼각근 측정 가능.
"""
import os
import re
import sys
import time
import shutil
from pathlib import Path
import opensim as osim

SRC = Path('/data/romfix_unified')
OUT = Path('/data/shoulder_tight')
OUT.mkdir(exist_ok=True)
SHOULDER_ACT = ('shoulder_elv_r_actuator', 'shoulder_elv_l_actuator',
                'shoulder_rot_r_actuator', 'shoulder_rot_l_actuator',
                'elv_angle_r_actuator', 'elv_angle_l_actuator')
SHOULDER_RES = tuple(f'reserve_{c}_{s}' for c in ('shoulder_elv', 'shoulder_rot', 'elv_angle')
                     for s in ('r', 'l'))
OPT_TIGHT = 5.0
JOBS = ('box_off', 'box_on')


def tighten(src_model, dst):
    m = osim.Model(src_model)
    m.initSystem()
    fs = m.getForceSet()
    n = 0
    for i in range(fs.getSize()):
        a = osim.CoordinateActuator.safeDownCast(fs.get(i))
        if a and a.getName() in (SHOULDER_ACT + SHOULDER_RES):
            a.setOptimalForce(OPT_TIGHT)
            a.setMinControl(-50.0)
            a.setMaxControl(50.0)
            n += 1
    m.finalizeConnections()
    m.printToXML(dst)
    return n


def run(tag):
    d = OUT / tag
    d.mkdir(exist_ok=True)
    src = SRC / tag
    mres = str(d / 'model_res_tight.osim')
    n = tighten(str(src / 'model_res_tight.osim'), mres)

    # 원본 setup.xml 에서 조건을 그대로 읽어 모델만 교체한다
    tool = osim.AnalyzeTool(str(src / 'setup.xml'), False)
    ext = tool.getExternalLoadsFileName()
    ext_src = Path(ext if ext.startswith('/') else str(src / ext))
    ext_dst = d / ext_src.name
    shutil.copy(ext_src, ext_dst)
    for fn in set(re.findall(r'<(?:datafile|data_source_name)>([^<]+)<', ext_dst.read_text())):
        fn = fn.strip()
        if not fn or fn.startswith('/'):
            continue
        cand = ext_src.parent / fn
        if cand.exists() and not (d / fn).exists():
            shutil.copy(cand, d / fn)

    tool.setModelFilename(mres)
    tool.setResultsDir(str(d))
    tool.setExternalLoadsFileName(str(ext_dst))
    setup = str(d / 'setup.xml')
    tool.printToXML(setup)
    print(f'[{tag}] 어깨 액추에이터+reserve {n}개 opt={OPT_TIGHT} | '
          f'mot={Path(tool.getCoordinatesFileName()).name}', flush=True)
    t0 = time.time()
    ok = osim.AnalyzeTool(setup).run()
    print(f'[{tag}] ok={ok}  {time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    for tag in (sys.argv[1:] or JOBS):
        run(tag)
