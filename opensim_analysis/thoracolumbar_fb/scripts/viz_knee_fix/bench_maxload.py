"""[벤치 ■0-4] OFF 최대 가능 하중 탐색 — 근력 축소 스케일 산출용.

최저점(들기 시작 자세)이 가장 힘든 지점이므로 **처음 5 프레임**만 쓴다.
판정: 전 근육 활성도 ≤ 1.0 그리고 (고관절 + 척추) reserve 최대 |M| ≤ 임계값.
임계 2 / 5 / 10 N·m 를 병기한다 (사용자 지정).
"""
import os
import sys
import json
import numpy as np
import opensim as osim

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench_so as BS

OUT = '/data/suit_bench'
NBOT = 12          # GCV 스플라인이 최소 10점을 요구한다 (t=3.00~3.37 s, 최저점 구간)
THRESH = (2.0, 5.0, 10.0)


def bottom_motion(variant):
    src = f'{OUT}/bench_{variant}.mot'
    dst = f'{OUT}/bench_{variant}_bottom.mot'
    lines = open(src).read().split('\n')
    i = next(i for i, l in enumerate(lines) if l.strip() == 'endheader')
    head, cols = lines[:i + 1], lines[i + 1]
    rows = [l for l in lines[i + 2:] if l.strip()][:NBOT]
    head = [('nRows=%d' % len(rows)) if l.startswith('nRows') else l for l in head]
    open(dst, 'w').write('\n'.join(head) + '\n' + cols + '\n' + '\n'.join(rows) + '\n')
    return dst


def metrics(d):
    t = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_force.sto')
    res = {}
    for c in t.getColumnLabels():
        if not c.startswith('reserve_'):
            continue
        base = c[len('reserve_'):]
        if base.startswith('hip_flexion') or '_FE' in base:
            v = max(abs(float(t.getDependentColumn(c)[i]))
                    for i in range(t.getNumRows()))
            res[c] = float(v)
    a = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_activation.sto')
    amax = 0.0
    for c in a.getColumnLabels():
        if c.startswith('reserve_'):
            continue
        amax = max(amax, max(float(a.getDependentColumn(c)[i])
                             for i in range(a.getNumRows())))
    hip = max((v for k, v in res.items() if 'hip' in k), default=0.0)
    spine = max((v for k, v in res.items() if 'hip' not in k), default=0.0)
    return dict(act_max=float(amax), hip_res=hip, spine_res=spine,
                worst=max(hip, spine))


def run_one(variant, kb, model, mot, T, P, G_all, hands, prefix='maxload'):
    tag = BS.build_ext(f'{variant}bot', kb, None, T, P, G_all, hands)
    d = f'{OUT}/so/{prefix}_{tag}'
    os.makedirs(d, exist_ok=True)
    tool = osim.AnalyzeTool()
    tool.setName('so')
    tool.setModelFilename(model)
    tool.setCoordinatesFileName(mot)
    tool.setLowpassCutoffFrequency(-1)
    tool.setExternalLoadsFileName(f'{BS.EXT}/ext_{tag}.xml')
    tool.setResultsDir(d)
    tool.setInitialTime(float(T[0]))
    tool.setFinalTime(float(T[-1]))
    so = osim.StaticOptimization()
    so.setStartTime(float(T[0]))
    so.setEndTime(float(T[-1]))
    so.setUseModelForceSet(True)
    so.setActivationExponent(2.0)
    so.setUseMusclePhysiology(True)
    tool.getAnalysisSet().cloneAndAppend(so)
    sp = os.path.join(d, 'setup.xml')
    tool.printToXML(sp)
    ok = osim.AnalyzeTool(sp).run()
    mm = metrics(d)
    mm.update(kb=float(kb), ok=bool(ok))
    return mm


if __name__ == '__main__':
    variant = sys.argv[1] if len(sys.argv) > 1 else 'A_neutral'
    model = sys.argv[2] if len(sys.argv) > 2 else f'{OUT}/model_tight.osim'
    loads = [float(x) for x in sys.argv[3:]] or [30., 60., 90., 120.]
    mot = bottom_motion(variant)
    T, P, G_all, hands = BS.geometry(variant)
    T = T[:NBOT]
    G_all = {k: v[:NBOT] for k, v in G_all.items()}
    hands = hands[:NBOT]
    rows = []
    for kb in loads:
        mm = run_one(variant, kb, model, mot, T, P, G_all, hands)
        rows.append(mm)
        judg = ' '.join(f'{th:.0f}:{"가능" if mm["worst"] <= th else "불가"}'
                        for th in THRESH)
        print(f'  {kb:6.1f} kg  활성도max {mm["act_max"]:.3f}  '
              f'고관절 reserve {mm["hip_res"]:7.2f}  척추 {mm["spine_res"]:6.2f} N·m  '
              f'[{judg}]', flush=True)
    tag = os.path.basename(model)[:-5]
    json.dump(rows, open(f'{OUT}/maxload_{variant}_{tag}.json', 'w'), indent=1)
    print(f'SAVED {OUT}/maxload_{variant}_{tag}.json')
