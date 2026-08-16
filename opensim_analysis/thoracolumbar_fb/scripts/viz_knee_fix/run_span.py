"""[1]/[2] 부여 스팬 조건 SO 실행.

조건 통일: /data/romfix_unified/stoop_on 의 setup 을 그대로 쓰고 **외력만** 교체.
모델(해시 ca12f321326e) · 운동학 · tight reserve · SO 옵션 · 시간범위 전부 동일.
OFF 는 /data/romfix_unified/stoop_off 재사용.
"""
import re
import sys
import time
import shutil
from pathlib import Path
import opensim as osim

SRC = Path('/data/romfix_unified/stoop_on')
OUT = Path('/data/suit_span')
OUT.mkdir(exist_ok=True)
JOBS = {
    'couple_L1': ('(ii) 토크커플 · L1↔골반 — 스팬 좁음 · 커플',),
    'path_T4': ('상부 앵커 T4 — 설계 제안',),
    'path_T8': ('(iv) 경로힘 · T8→허벅지 — 스팬 넓음 · 경로힘',),
    'path_T12': ('상부 앵커 T12 — 설계 제안',),
    # 하단 고정 스윕 — 현 하드웨어는 허벅지(안전하네스). 나머지는 설계 제안
    'path_T8_sacrum': ('T8 → 천골 — 설계 제안',),
    'path_T8_pelvis': ('T8 → 장골능 — 설계 제안',),
    'path_T8_sacfem': ('T8 → 천골 경유 → 허벅지 — 설계 제안',),
    'path_L1_sacfem': ('L1 → 천골 경유 → 허벅지 — 설계 제안',),
}


def run(tag):
    d = OUT / tag
    d.mkdir(exist_ok=True)
    shutil.copy(str(SRC / 'model_res_tight.osim'), str(d / 'model_res_tight.osim'))
    tool = osim.AnalyzeTool(str(SRC / 'setup.xml'), False)
    tool.setModelFilename(str(d / 'model_res_tight.osim'))
    tool.setResultsDir(str(d))
    tool.setExternalLoadsFileName(f'{OUT}/ext_{tag}.xml')
    setup = str(d / 'setup.xml')
    tool.printToXML(setup)
    print(f'[{tag}] {JOBS[tag][0]}', flush=True)
    t0 = time.time()
    ok = osim.AnalyzeTool(setup).run()
    print(f'[{tag}] ok={ok}  {time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    for tag in (sys.argv[1:] or list(JOBS)):
        run(tag)
