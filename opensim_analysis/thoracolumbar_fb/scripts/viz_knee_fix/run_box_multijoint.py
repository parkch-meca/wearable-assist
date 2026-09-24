"""[3] 들기 20 kg 다부위 SO 실행 — 5조건.

■ 조건 통일
  · setup   : /data/romfix_unified/box_off 의 setup 을 그대로 쓰고 **모델과 외력만** 교체
              (운동학 box_stoop_lift_m1_armfix.mot · t 0~7.5 s · lowpass 없음 · SO 옵션 원본)
  · 모델    : 운반 다부위와 **같은 파일**을 쓴다 (/data/suit_carry/model_res_tight.osim).
              팔꿈치근 14개 추가 + 척추/팔 reserve·액추에이터 전부 opt 5.
              복사 후 해시를 대조해 동일성을 확인한다 — 다시 만들지 않는다.
■ ⚠️ 기준선이 기존 5동작 들기와 다르다
  팔 측정을 위해 OFF 부터 새로 뽑는다. 5조건 내부 비교만 유효하며
  기존 5동작 들기 −26.3 % 와 직접 비교하지 않는다.
"""
import os
import sys
import time
import shutil
import hashlib
from pathlib import Path
import opensim as osim

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_carry_multijoint as RC

SRC = Path('/data/romfix_unified/box_off')
OUT = Path('/data/suit_box')
CARRY_MODEL = Path('/data/suit_carry/model_res_tight.osim')
CONDS = ['off', 'waist', 'elbow', 'elbow_ext', 'all']


def sha12(p):
    return hashlib.sha1(open(p, errors='ignore').read().encode()).hexdigest()[:12]


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    RC.SRC, RC.OUT = SRC, OUT
    mres = OUT / 'model_res_tight.osim'
    if not mres.exists():
        shutil.copy(str(CARRY_MODEL), str(mres))
    h1, h2 = sha12(CARRY_MODEL), sha12(mres)
    print(f'모델 해시 운반 {h1} · 들기 {h2}  {"✅ 동일" if h1 == h2 else "❌ 불일치"}',
          flush=True)
    if h1 != h2:
        sys.exit(1)
    for tag in ([a for a in sys.argv[1:] if not a.startswith('--')] or CONDS):
        RC.run(tag, str(mres))
