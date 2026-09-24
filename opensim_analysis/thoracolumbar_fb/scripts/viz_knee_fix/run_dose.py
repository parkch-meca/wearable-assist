"""[2] 용량–반응 곡선 실측 — 스툽 토크커플 0 / 8 / 16.5 / 24 N·m.

■ 왜
  L-01 은 24 N·m(설계 목표)와 16.5 N·m(현 하드웨어)를 "두 점"으로 병기하기로 했는데,
  실검증에서 곡선이 **오목**함이 드러났다(16.5 가 24 효과의 83 %). 두 점만으로는
  비례 배분이 과소평가가 되므로, 점을 늘려 **곡선**으로 제시한다.

■ 조건 통일 — 축 위의 점만 다르다
  부여 방식 : 순수 토크 커플 (thoracic1 +Tz · pelvis −Tz), 시간 프로파일 alpha_v5(t) 동일
  모델      : /data/romfix_unified/stoop_on/model_res_tight.osim (sha1 ca12f321326e)
  운동학·시간범위·SO 옵션 : stoop_on setup 그대로
  0 N·m     = /data/romfix_unified/stoop_off  (재사용)
  16.5 N·m  = /data/suit_16Nm/couple16        (재사용)
  24 N·m    = /data/romfix_unified/stoop_on   (재사용)
  8 N·m     = 이번 신규 실행  ← F200 외력 파일의 토크 열만 8/24 로 비례 축소

⚠️ 5동작 논문 수치·주 지표는 건드리지 않는다. 24 N·m 조건 결과를 그대로 인용만 한다.
"""
import os
import re
import sys
import time
import shutil
from pathlib import Path
import numpy as np
import opensim as osim

SRC = Path('/data/romfix_unified/stoop_on')
F200_MOT = SRC / 'ext_grf_suit_F200.mot'
F200_XML = SRC / 'ext_loads_F200.xml'
OUT = Path('/data/suit_dose')
OUT.mkdir(exist_ok=True)
TQ_COLS = ('thor_T_x', 'thor_T_y', 'thor_T_z', 'pel_T_x', 'pel_T_y', 'pel_T_z')
BASE_TQ = 24.0


def read_mot(p):
    lines = open(p).read().split('\n')
    i = next(i for i, l in enumerate(lines) if l.strip() == 'endheader')
    head = lines[:i + 1]
    cols = lines[i + 1].split('\t')
    rows = [l.split('\t') for l in lines[i + 2:] if l.strip()]
    return head, cols, rows


def make_ext(torque):
    """F200(24 N·m) 외력 파일의 토크 열만 비례 축소. GRF 열은 한 글자도 바꾸지 않는다."""
    head, cols, rows = read_mot(F200_MOT)
    idx = [cols.index(c) for c in TQ_COLS if c in cols]
    f = torque / BASE_TQ
    tag = f'couple{torque:g}'.replace('.', 'p')
    out_mot = OUT / f'ext_{tag}.mot'
    with open(out_mot, 'w') as fh:
        fh.write('\n'.join(head) + '\n' + '\t'.join(cols) + '\n')
        for r in rows:
            v = list(r)
            for j in idx:
                v[j] = f'{float(r[j]) * f:.6f}'
            fh.write('\t'.join(v) + '\n')
    xml = open(F200_XML).read()
    xml = xml.replace('ext_grf_suit_F200.mot', str(out_mot))
    out_xml = OUT / f'ext_{tag}.xml'
    open(out_xml, 'w').write(xml)
    # 검산 — 실제 기록된 최대 토크
    t = osim.TimeSeriesTable(str(out_mot))
    mx = max(abs(float(t.getDependentColumn('thor_T_z')[i]))
             for i in range(t.getNumRows()))
    return tag, out_xml, mx


def verify_couple16():
    """기존 16.5 N·m 조건이 같은 방식으로 만들어졌는지 확인 (축 정합)."""
    a = osim.TimeSeriesTable(str(F200_MOT))
    b = osim.TimeSeriesTable('/data/suit_16Nm/ext_couple16.mot')
    if a.getNumRows() != b.getNumRows():
        return False, '행 수 불일치'
    va = np.array([float(a.getDependentColumn('thor_T_z')[i]) for i in range(a.getNumRows())])
    vb = np.array([float(b.getDependentColumn('thor_T_z')[i]) for i in range(b.getNumRows())])
    m = np.abs(va) > 1e-6
    r = vb[m] / va[m]
    return (float(r.std()) < 1e-6), f'비율 {r.mean():.4f} ± {r.std():.2e} (기대 {16.5/24:.4f})'


def run(tag, xml):
    d = OUT / tag
    d.mkdir(exist_ok=True)
    mres = str(d / 'model_res_tight.osim')
    shutil.copy(str(SRC / 'model_res_tight.osim'), mres)     # 모델 완전 동일
    tool = osim.AnalyzeTool(str(SRC / 'setup.xml'), False)
    tool.setModelFilename(mres)
    tool.setResultsDir(str(d))
    tool.setExternalLoadsFileName(str(xml))
    setup = str(d / 'setup.xml')
    tool.printToXML(setup)
    print(f'[{tag}] mot={Path(tool.getCoordinatesFileName()).name} '
          f't=({tool.getInitialTime()},{tool.getFinalTime()})', flush=True)
    t0 = time.time()
    ok = osim.AnalyzeTool(setup).run()
    print(f'[{tag}] ok={ok}  {time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    ok, msg = verify_couple16()
    print(f'{"✅" if ok else "⚠️"} 기존 couple16 축 정합 검산: {msg}', flush=True)
    for tq in [float(a) for a in sys.argv[1:]] or [8.0]:
        tag, xml, mx = make_ext(tq)
        print(f'생성 {tag}: 기록된 최대 토크 {mx:.3f} N·m (목표 {tq:g})', flush=True)
        run(tag, xml)
