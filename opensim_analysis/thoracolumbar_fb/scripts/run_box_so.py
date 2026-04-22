"""Box-lift 4-condition pipeline: ID + SO for each condition via ExternalLoads.

Conditions:
  B_noload   : no box, no suit
  B_suit0    : 20kg box (100 N per hand, t>=2s), no suit
  B_suit100  : box + 12 N·m suit peak (100 N total, moment arm 0.12 m)
  B_suit200  : box + 24 N·m suit peak (200 N total)
"""
import os, sys, time
from pathlib import Path
import numpy as np
import opensim as osim

OUT = Path('/data/stoop_results/box_lift')
MOT = OUT / 'box_motion_30fps.mot'
MODEL_RES = OUT / 'model_with_reserves_box.osim'
T_START, T_END = 0.0, 3.0

BOX_FORCE_PER_HAND = 100.0   # N downward
BOX_START = 2.0              # box grasped at t=2s
MOMENT_ARM = 0.12             # m, for suit torque
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


def write_ext_loads_mot(path: Path, box: bool, suit_N: float, fps: int = 120):
    """Write 37-column ExternalLoads data: hand R/L forces + thor/pel torques."""
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

    T_suit_peak = suit_N * MOMENT_ARM   # N·m
    if T_suit_peak > 0:
        for i, t in enumerate(times):
            Tz = T_suit_peak * alpha_spine(float(t))
            data[i, cols.index('thor_T_z')] = +Tz
            data[i, cols.index('pel_T_z')]  = -Tz

    header = (
        f"box_ext_loads  box={int(box)}  suit_N={suit_N:.0f}\nversion=1\nnRows={n}\n"
        f"nColumns={1+len(cols)}\ninDegrees=no\n\n"
        "Units are S.I. units (second, meters, Newtons, ...)\n\nendheader\n"
        "time\t" + "\t".join(cols) + "\n"
    )
    with open(path, 'w') as f:
        f.write(header)
        for i, t in enumerate(times):
            f.write("\t".join([f"{t:.6f}"] + [f"{v:.6f}" for v in data[i]]) + "\n")


def write_ext_loads_xml(path: Path, data_mot: Path, box: bool, suit: bool):
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
  <ExternalLoads name="box_loads">
    <objects>{entries}
    </objects>
    <groups />
    <datafile>{data_mot.name}</datafile>
  </ExternalLoads>
</OpenSimDocument>
"""
    path.write_text(xml)


def run_id(cond: str, cfg: dict):
    cond_dir = OUT / cond
    cond_dir.mkdir(parents=True, exist_ok=True)
    mot_ext = cond_dir / f'ext_{cond}.mot'
    xml_ext = cond_dir / f'ext_{cond}.xml'
    write_ext_loads_mot(mot_ext, cfg['box'], cfg['suit_N'])
    write_ext_loads_xml(xml_ext, mot_ext, cfg['box'], cfg['suit_N'] > 0)

    id_tool = osim.InverseDynamicsTool()
    id_tool.setModelFileName(str(MODEL_RES))
    id_tool.setCoordinatesFileName(str(MOT))
    id_tool.setStartTime(T_START); id_tool.setEndTime(T_END)
    id_tool.setLowpassCutoffFrequency(-1)
    id_tool.setResultsDir(str(cond_dir))
    id_tool.setOutputGenForceFileName(f'id_{cond}.sto')
    excl = osim.ArrayStr(); excl.append('Muscles')
    id_tool.setExcludedForces(excl)
    if cfg['box'] or cfg['suit_N'] > 0:
        id_tool.setExternalLoadsFileName(str(xml_ext))
    t0 = time.time()
    ok = id_tool.run()
    print(f'[ID {cond}] {time.time()-t0:.1f}s  ok={ok}')
    return ok


def run_so(cond: str, cfg: dict):
    cond_dir = OUT / cond
    cond_dir.mkdir(parents=True, exist_ok=True)
    mot_ext = cond_dir / f'ext_{cond}.mot'
    xml_ext = cond_dir / f'ext_{cond}.xml'

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
    print(f'[SO {cond}] {time.time()-t0:.1f}s  ok={ok}')
    return ok


if __name__ == '__main__':
    conds = sys.argv[1:] if len(sys.argv) > 1 else list(CONDITIONS.keys())
    phase = os.environ.get('PHASE', 'both')   # 'id', 'so', or 'both'
    for c in conds:
        if c not in CONDITIONS:
            print(f'unknown cond {c}'); continue
        cfg = CONDITIONS[c]
        if phase in ('id', 'both'):
            run_id(c, cfg)
        if phase in ('so', 'both'):
            run_so(c, cfg)
