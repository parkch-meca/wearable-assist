"""[정정 3] 조끼 사슬 조건 SO 실행 — 들기 20 kg / 36 kg.

조건 통일: /data/romfix_unified/box_off 의 setup·모델(sha1 ca12f321326e)을 그대로 쓰고
**외력만** 교체한다. 운동학(box_stoop_lift_m1_armfix) · 시간범위 0~7.5 s · SO 옵션 동일.
20 kg OFF 는 기존 결과(/data/romfix_unified/box_off)를 그대로 재사용한다.
"""
import os
import sys
import time
import shutil
import hashlib
from pathlib import Path
import opensim as osim

SRC = Path('/data/romfix_unified/box_off')
EXT = Path('/data/suit_vest/ext')
OUT = Path('/data/suit_vest/so')
OUT.mkdir(parents=True, exist_ok=True)
TAGS = ['cold', 'hot100', 'hot150', 'hot200', 'hot250',
        'k2x2', 'k2x4', 'hot225', 'off_36', 'cold_36', 'hot150_36']


def sha12(p):
    return hashlib.sha1(open(p, errors='ignore').read().encode()).hexdigest()[:12]


def run(tag, mres):
    d = OUT / tag
    d.mkdir(exist_ok=True)
    tool = osim.AnalyzeTool(str(SRC / 'setup.xml'), False)
    tool.setModelFilename(mres)
    tool.setResultsDir(str(d))
    tool.setExternalLoadsFileName(str(EXT / f'ext_{tag}.xml'))
    setup = str(d / 'setup.xml')
    tool.printToXML(setup)
    print(f'[{tag}] 시작 t=({tool.getInitialTime()},{tool.getFinalTime()})', flush=True)
    t0 = time.time()
    ok = osim.AnalyzeTool(setup).run()
    print(f'[{tag}] ok={ok}  {time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    mres = str(OUT / 'model_res_tight.osim')
    if not os.path.exists(mres):
        shutil.copy(str(SRC / 'model_res_tight.osim'), mres)
    h = sha12(mres)
    print(f'모델 해시 {h}  {"✅ 5동작 실행 모델과 동일" if h == "ca12f321326e" else "❌"}',
          flush=True)
    if h != 'ca12f321326e':
        sys.exit(1)
    for tag in ([a for a in sys.argv[1:] if not a.startswith('--')] or TAGS):
        run(tag, mres)
