"""[1] 16 N·m 조건 실검증 — 스툽 ON 2종.

조건 통일: /data/romfix_unified/stoop_on 의 setup 을 그대로 쓰고 **외력만** 교체한다.
모델(해시 ca12f321326e), 운동학, tight reserve, SO 옵션, 시간범위 전부 동일.

  path16   : 재산출 모멘트 암(밀착 + 피하 10 mm) 기반 경로힘. 실제 하드웨어 조건.
  couple16 : 순수 토크 커플 16.5 N·m. 기존 F0~F200 sweep 축 위의 점 — 선형성 시험용.

OFF 는 /data/romfix_unified/stoop_off 를 그대로 재사용한다 (재실행 불필요).
"""
import os
import re
import sys
import time
import shutil
from pathlib import Path
import opensim as osim

SRC = Path('/data/romfix_unified/stoop_on')
OUT = Path('/data/suit_16Nm')
OUT.mkdir(exist_ok=True)
JOBS = {
    'path16': ('/data/suit_16Nm/ext_path.xml', '경로힘 (재산출 모멘트 암) — 기준'),
    'couple16': ('/data/suit_16Nm/ext_couple16.xml', '토크 커플 16.5 N·m — 선형성 시험'),
    # ■4 설계 레버
    'leverA': ('/data/suit_16Nm/ext_leverA.xml', '(A) 보조력 200 N'),
    'leverB': ('/data/suit_16Nm/ext_leverB.xml', '(B) 강성 k=20 N/mm'),
    'leverC': ('/data/suit_16Nm/ext_leverC.xml', '(C) 모멘트 암 +20 mm'),
}


def run(tag):
    ext, desc = JOBS[tag]
    d = OUT / tag
    d.mkdir(exist_ok=True)
    mres = str(d / 'model_res_tight.osim')
    shutil.copy(str(SRC / 'model_res_tight.osim'), mres)   # 모델 완전 동일

    tool = osim.AnalyzeTool(str(SRC / 'setup.xml'), False)
    tool.setModelFilename(mres)
    tool.setResultsDir(str(d))
    tool.setExternalLoadsFileName(ext)
    setup = str(d / 'setup.xml')
    tool.printToXML(setup)
    print(f'[{tag}] {desc} | mot={Path(tool.getCoordinatesFileName()).name} '
          f'| t=({tool.getInitialTime()},{tool.getFinalTime()})', flush=True)
    t0 = time.time()
    ok = osim.AnalyzeTool(setup).run()
    print(f'[{tag}] ok={ok}  {time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    for tag in (sys.argv[1:] or list(JOBS)):
        run(tag)
