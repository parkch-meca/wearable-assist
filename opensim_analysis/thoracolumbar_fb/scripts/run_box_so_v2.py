"""Box-lift SO pipeline v2 — runs on stoop_box20kg_v2.mot (semi-squat lift).

Mirrors run_box_so.py but:
  - input motion:   stoop_box20kg_v2.mot (subsampled to 30 fps → box_motion_v2_30fps.mot)
  - output root:    /data/stoop_results/box_lift_v2/
  - same reserved model as v1 (model_with_reserves_box.osim)

4 conditions:
  B_noload  (no box, no suit)
  B_suit0   (20 kg box, no suit)
  B_suit100 (box + 12 N·m suit peak)
  B_suit200 (box + 24 N·m suit peak)
"""
import os, sys, time
from pathlib import Path
import numpy as np
import opensim as osim

MOT_SRC  = '/data/stoop_motion/stoop_box20kg_v2.mot'
MODEL_RES_SRC = '/data/stoop_results/box_lift/model_with_reserves_box.osim'

OUT = Path('/data/stoop_results/box_lift_v2'); OUT.mkdir(parents=True, exist_ok=True)
MOT = OUT / 'box_motion_v2_30fps.mot'
MODEL_RES = OUT / 'model_with_reserves_box.osim'

T_START, T_END = 0.0, 3.0
BOX_FORCE_PER_HAND = 100.0
BOX_START = 2.0
MOMENT_ARM = 0.12
CONDITIONS = {
    'B_noload':  dict(box=False, suit_N=0),
    'B_suit0':   dict(box=True,  suit_N=0),
    'B_suit100': dict(box=True,  suit_N=100),
    'B_suit200': dict(box=True,  suit_N=200),
}


def alpha_spine(t):
    if t < 1.0:  return 0.0
    if t <= 2.0: return (1.0 - np.cos(np.pi * (t - 1.0))) / 2.0
    if t <= 3.0: return (1.0 + np.cos(np.pi * (t - 2.0))) / 2.0
    return 0.0


def subsample_mot(src, dst, fps=30):
    tbl = osim.TimeSeriesTable(str(src))
    times = list(tbl.getIndependentColumn())
    dt = 1.0 / fps
    keep = [0]
    for i in range(1, len(times)):
        if times[i] - times[keep[-1]] >= dt - 1e-9:
            keep.append(i)
    if keep[-1] != len(times) - 1:
        keep.append(len(times) - 1)
    labels = list(tbl.getColumnLabels())
    header = (
        f"stoop_box20kg_v2_30fps\nversion=1\nnRows={len(keep)}\n"
        f"nColumns={1+len(labels)}\ninDegrees=yes\n\n"
        "Units are S.I. units.\n\nendheader\n"
        "time\t" + "\t".join(labels) + "\n"
    )
    with open(dst, 'w') as f:
        f.write(header)
        for i in keep:
            row = tbl.getRowAtIndex(i)
            vals = [f"{times[i]:.6f}"] + [f"{row[j]:.6f}" for j in range(len(labels))]
            f.write("\t".join(vals) + "\n")
    print(f'[sub] {len(times)} -> {len(keep)} frames  -> {dst}')


def write_ext_loads_mot(path, box, suit_N, fps=120):
    n = int((T_END - T_START) * fps) + 1
    times = np.linspace(T_START, T_END, n)
    cols = []
    for tag in ('handR', 'handL', 'thor', 'pel'):
        for k in (f'{tag}_F_vx', f'{tag}_F_vy', f'{tag}_F_vz',
                  f'{tag}_T_x',  f'{tag}_T_y',  f'{tag}_T_z',
                  f'{tag}_P_px', f'{tag}_P_py', f'{tag}_P_pz'):
            cols.append(k)
    data = np.zeros((n, len(cols)))
    if box:
        for i, t in enumerate(times):
            if t >= BOX_START - 1e-9:
                data[i, cols.index('handR_F_vy')] = -BOX_FORCE_PER_HAND
                data[i, cols.index('handL_F_vy')] = -BOX_FORCE_PER_HAND
    T_suit_peak = suit_N * MOMENT_ARM
    if T_suit_peak > 0:
        for i, t in enumerate(times):
            Tz = T_suit_peak * alpha_spine(float(t))
            data[i, cols.index('thor_T_z')] = +Tz
            data[i, cols.index('pel_T_z')]  = -Tz
    header = (
        f"box_v2_ext  box={int(box)}  suit_N={suit_N:.0f}\nversion=1\nnRows={n}\n"
        f"nColumns={1+len(cols)}\ninDegrees=no\n\n"
        "Units are S.I. units.\n\nendheader\n"
        "time\t" + "\t".join(cols) + "\n"
    )
    with open(path, 'w') as f:
        f.write(header)
        for i, t in enumerate(times):
            f.write("\t".join([f"{t:.6f}"] + [f"{v:.6f}" for v in data[i]]) + "\n")


def write_ext_loads_xml(path, data_mot, box, suit):
    entries = ''
    if box:
        for tag, body in [('handR', 'hand_R'), ('handL', 'hand_L')]:
            entries += f"""
      <ExternalForce name="box_{tag}">
        <isDisabled>false</isDisabled>
        <applied_to_body>{body}</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>{body}</point_expressed_in_body>
        <force_identifier>{tag}_F_v</force_identifier>
        <point_identifier>{tag}_P_p</point_identifier>
        <torque_identifier>{tag}_T_</torque_identifier>
        <data_source_name>{data_mot.name}</data_source_name>
      </ExternalForce>"""
    if suit:
        for tag, body in [('thor', 'thoracic1'), ('pel', 'pelvis')]:
            entries += f"""
      <ExternalForce name="suit_{tag}">
        <isDisabled>false</isDisabled>
        <applied_to_body>{body}</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>{tag}_F_v</force_identifier>
        <point_identifier>{tag}_P_p</point_identifier>
        <torque_identifier>{tag}_T_</torque_identifier>
        <data_source_name>{data_mot.name}</data_source_name>
      </ExternalForce>"""
    xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
  <ExternalLoads name="box_v2_loads">
    <objects>{entries}
    </objects>
    <groups />
    <datafile>{data_mot.name}</datafile>
  </ExternalLoads>
</OpenSimDocument>
"""
    Path(path).write_text(xml)


def run_condition(cond, cfg):
    cond_dir = OUT / cond; cond_dir.mkdir(parents=True, exist_ok=True)
    mot_ext = cond_dir / f'ext_{cond}.mot'
    xml_ext = cond_dir / f'ext_{cond}.xml'
    write_ext_loads_mot(mot_ext, cfg['box'], cfg['suit_N'])
    write_ext_loads_xml(xml_ext, mot_ext, cfg['box'], cfg['suit_N'] > 0)

    tool = osim.AnalyzeTool()
    tool.setModelFilename(str(MODEL_RES))
    tool.setName(f'so_{cond}')
    tool.setResultsDir(str(cond_dir))
    tool.setInitialTime(T_START); tool.setFinalTime(T_END)
    tool.setLowpassCutoffFrequency(-1)
    tool.setCoordinatesFileName(str(MOT))
    tool.setReplaceForceSet(False)
    if cfg['box'] or cfg['suit_N'] > 0:
        tool.setExternalLoadsFileName(str(xml_ext))

    so = osim.StaticOptimization()
    so.setStartTime(T_START); so.setEndTime(T_END)
    so.setUseMusclePhysiology(True)
    so.setActivationExponent(2.0)
    so.setConvergenceCriterion(1e-4)
    so.setMaxIterations(300)
    tool.getAnalysisSet().cloneAndAppend(so)

    setup = cond_dir / f'setup_{cond}.xml'
    tool.printToXML(str(setup))
    tool2 = osim.AnalyzeTool(str(setup))
    t0 = time.time()
    ok = tool2.run()
    print(f'[SO {cond}] ok={ok}  {time.time()-t0:.1f}s')
    return ok


def main():
    # step 1: subsample v2 mot to 30 fps if missing
    if not MOT.exists():
        subsample_mot(MOT_SRC, MOT)
    # step 2: copy reserved model from v1 pipeline (same underlying osim)
    if not MODEL_RES.exists():
        import shutil
        shutil.copy(MODEL_RES_SRC, MODEL_RES)
        print(f'[model] copied {MODEL_RES_SRC} -> {MODEL_RES}')
    # step 3: run 4 conditions
    for cond, cfg in CONDITIONS.items():
        run_condition(cond, cfg)


if __name__ == '__main__':
    main()
