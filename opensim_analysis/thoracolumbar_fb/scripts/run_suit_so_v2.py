"""SMA suit SO via ExternalLoads (torque couple between thoracic1 and pelvis).

Action-reaction pair in ground frame z-axis:
  thoracic1: +T * alpha(t) Nm
  pelvis:    -T * alpha(t) Nm  (reaction)
Applied as ExternalForce entries with a time-varying .mot data source.
"""
import os, sys, time
from pathlib import Path
import numpy as np
import opensim as osim

MODEL_BASE = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4.osim'
MOT = '/data/stoop_results/ik_result_30fps.mot'
OUT_ROOT = Path('/data/stoop_results/suit_sweep_v2')
OUT_ROOT.mkdir(parents=True, exist_ok=True)

MOMENT_ARM = 0.12
FORCES = [0, 50, 100, 150, 200]
T_START, T_END = 0.0, 3.0


def alpha(t):
    if t < 1.0:  return 0.0
    if t <= 2.0: return (1.0 - np.cos(np.pi * (t - 1.0))) / 2.0
    if t <= 3.0: return (1.0 + np.cos(np.pi * (t - 2.0))) / 2.0
    return 0.0


def write_ext_torque_mot(path: Path, torque_nm: float, fps: int = 120):
    """Write storage file with action-reaction torques (z-axis, ground frame)."""
    n = int((T_END - T_START) * fps) + 1
    times = np.linspace(T_START, T_END, n)
    cols = [
        'thor_F_vx', 'thor_F_vy', 'thor_F_vz',
        'thor_T_x',  'thor_T_y',  'thor_T_z',
        'thor_P_px', 'thor_P_py', 'thor_P_pz',
        'pel_F_vx', 'pel_F_vy', 'pel_F_vz',
        'pel_T_x',  'pel_T_y',  'pel_T_z',
        'pel_P_px', 'pel_P_py', 'pel_P_pz',
    ]
    data = np.zeros((n, len(cols)))
    for i, t in enumerate(times):
        Tz = torque_nm * alpha(float(t))
        data[i, cols.index('thor_T_z')] = +Tz
        data[i, cols.index('pel_T_z')]  = -Tz
    header = (
        f"suit_ext_torque_T{torque_nm:.1f}Nm\nversion=1\nnRows={n}\n"
        f"nColumns={1+len(cols)}\ninDegrees=no\n\n"
        "Units are S.I. units (second, meters, Newtons, ...)\n\nendheader\n"
        "time\t" + "\t".join(cols) + "\n"
    )
    with open(path, 'w') as f:
        f.write(header)
        for i, t in enumerate(times):
            f.write("\t".join([f"{t:.6f}"] + [f"{v:.6f}" for v in data[i]]) + "\n")


def write_ext_loads_xml(path: Path, data_mot: Path):
    """Write ExternalLoads XML wiring the two ExternalForce entries to the mot."""
    xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
  <ExternalLoads name="suit_loads">
    <objects>
      <ExternalForce name="suit_thoracic">
        <isDisabled>false</isDisabled>
        <applied_to_body>thoracic1</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>thor_F_v</force_identifier>
        <point_identifier>thor_P_p</point_identifier>
        <torque_identifier>thor_T_</torque_identifier>
        <data_source_name>{data_mot.name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="suit_pelvis">
        <isDisabled>false</isDisabled>
        <applied_to_body>pelvis</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>pel_F_v</force_identifier>
        <point_identifier>pel_P_p</point_identifier>
        <torque_identifier>pel_T_</torque_identifier>
        <data_source_name>{data_mot.name}</data_source_name>
      </ExternalForce>
    </objects>
    <groups />
    <datafile>{data_mot.name}</datafile>
  </ExternalLoads>
</OpenSimDocument>
"""
    path.write_text(xml)


def build_reserved_model(out_osim: Path):
    """Reserved model with NO suit actuator (suit comes from ExternalLoads)."""
    m = osim.Model(MODEL_BASE)
    m.initSystem()
    cs = m.getCoordinateSet()
    for i in range(cs.getSize()):
        c = cs.get(i)
        name = c.getName()
        a = osim.CoordinateActuator(name)
        a.setName(f'reserve_{name}')
        if c.getMotionType() == 1:
            opt = 500.0 if name.startswith('pelvis') else 100.0
        else:
            opt = 1000.0
        a.setOptimalForce(opt)
        a.setMinControl(-50.0); a.setMaxControl(50.0)
        m.addForce(a)
    m.finalizeConnections()
    m.printToXML(str(out_osim))


def run_condition(F: float):
    tag = f'F{int(F)}'
    T_nm = F * MOMENT_ARM
    cond_dir = OUT_ROOT / tag
    cond_dir.mkdir(parents=True, exist_ok=True)

    model_path = cond_dir / f'model_{tag}.osim'
    build_reserved_model(model_path)

    mot_ext = cond_dir / f'ext_torque_{tag}.mot'
    xml_ext = cond_dir / f'ext_loads_{tag}.xml'
    write_ext_torque_mot(mot_ext, T_nm)
    write_ext_loads_xml(xml_ext, mot_ext)

    tool = osim.AnalyzeTool()
    tool.setModelFilename(str(model_path))
    tool.setName(f'suit_{tag}')
    tool.setResultsDir(str(cond_dir))
    tool.setInitialTime(T_START); tool.setFinalTime(T_END)
    tool.setLowpassCutoffFrequency(-1)
    tool.setCoordinatesFileName(MOT)
    tool.setReplaceForceSet(False)
    if T_nm > 0:
        tool.setExternalLoadsFileName(str(xml_ext))

    so = osim.StaticOptimization()
    so.setStartTime(T_START); so.setEndTime(T_END)
    so.setUseMusclePhysiology(True)
    so.setActivationExponent(2.0)
    so.setConvergenceCriterion(1e-4)
    so.setMaxIterations(300)
    tool.getAnalysisSet().cloneAndAppend(so)

    setup = cond_dir / f'setup_{tag}.xml'
    tool.printToXML(str(setup))
    tool2 = osim.AnalyzeTool(str(setup))
    t0 = time.time()
    ok = tool2.run()
    print(f'[SO {tag}] T={T_nm:.1f} Nm  ok={ok}  {time.time()-t0:.1f}s')
    return ok


if __name__ == '__main__':
    forces = [float(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else FORCES
    for F in forces:
        run_condition(F)
