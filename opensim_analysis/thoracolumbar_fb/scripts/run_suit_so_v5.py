"""SMA suit SO on v5 motion (5s, with GRF).

Combines GRF + suit torque couple in one ExternalLoads XML + data file.
Reuses /data/stoop_results/stoop_v5/model_with_reserves_v5.osim (modified model).

Suit schedule (alpha(t)):
  0.0 - 0.5 s   : 0                        (upright)
  0.5 - 2.5 s   : cosine ramp 0 -> 1       (bend, 2 s)
  2.5 - 3.0 s   : 1                        (hold, 0.5 s)
  3.0 - 5.0 s   : cosine ramp 1 -> 0       (straighten, 2 s)

Applied torque couple (z-axis, ground):
  thoracic1: +T * alpha(t) Nm
  pelvis:    -T * alpha(t) Nm (reaction)
"""
import sys, time
from pathlib import Path
import numpy as np
import opensim as osim

MODEL_V5 = Path('/data/stoop_results/stoop_v5/model_with_reserves_v5.osim')
MOT = '/data/stoop_results/stoop_v5/v5_30fps.mot'
GRF_STO = '/data/stoop_motion/stoop_grf_v5.sto'

OUT_ROOT = Path('/data/stoop_results/suit_sweep_v5')
OUT_ROOT.mkdir(parents=True, exist_ok=True)

MOMENT_ARM = 0.12
T_START, T_END = 0.0, 5.0
FPS_EXT = 120  # match GRF sampling

GRF_COLS = [
    'ground_force_R_vx', 'ground_force_R_vy', 'ground_force_R_vz',
    'ground_force_R_px', 'ground_force_R_py', 'ground_force_R_pz',
    'ground_torque_R_x', 'ground_torque_R_y', 'ground_torque_R_z',
    'ground_force_L_vx', 'ground_force_L_vy', 'ground_force_L_vz',
    'ground_force_L_px', 'ground_force_L_py', 'ground_force_L_pz',
    'ground_torque_L_x', 'ground_torque_L_y', 'ground_torque_L_z',
]

SUIT_COLS = [
    'thor_F_vx', 'thor_F_vy', 'thor_F_vz',
    'thor_T_x',  'thor_T_y',  'thor_T_z',
    'thor_P_px', 'thor_P_py', 'thor_P_pz',
    'pel_F_vx', 'pel_F_vy', 'pel_F_vz',
    'pel_T_x',  'pel_T_y',  'pel_T_z',
    'pel_P_px', 'pel_P_py', 'pel_P_pz',
]


def alpha_v5(t):
    if t < 0.5:  return 0.0
    if t <= 2.5: return (1.0 - np.cos(np.pi * (t - 0.5) / 2.0)) / 2.0
    if t <= 3.0: return 1.0
    if t <= 5.0: return (1.0 + np.cos(np.pi * (t - 3.0) / 2.0)) / 2.0
    return 0.0


def load_grf_rows():
    tbl = osim.TimeSeriesTable(GRF_STO)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    n = tbl.getNumRows()
    out = np.zeros((n, len(GRF_COLS)))
    for i in range(n):
        row = tbl.getRowAtIndex(i)
        for j, col in enumerate(GRF_COLS):
            out[i, j] = row[labels.index(col)]
    return times, out


def write_combined_ext_mot(path: Path, torque_nm: float):
    """GRF columns + suit torque columns in one .sto, aligned on GRF time grid."""
    times, grf = load_grf_rows()
    n = len(times)
    suit = np.zeros((n, len(SUIT_COLS)))
    i_thor_Tz = SUIT_COLS.index('thor_T_z')
    i_pel_Tz  = SUIT_COLS.index('pel_T_z')
    for i, t in enumerate(times):
        Tz = torque_nm * alpha_v5(float(t))
        suit[i, i_thor_Tz] = +Tz
        suit[i, i_pel_Tz]  = -Tz

    all_cols = GRF_COLS + SUIT_COLS
    data = np.hstack([grf, suit])
    header = (
        f"suit_v5_ext_T{torque_nm:.1f}Nm\nversion=1\nnRows={n}\n"
        f"nColumns={1+len(all_cols)}\ninDegrees=no\n\n"
        "Units are S.I. units (second, meters, Newtons, ...)\n\nendheader\n"
        "time\t" + "\t".join(all_cols) + "\n"
    )
    with open(path, 'w') as f:
        f.write(header)
        for i, t in enumerate(times):
            f.write("\t".join([f"{t:.6f}"] + [f"{v:.6f}" for v in data[i]]) + "\n")


def write_combined_ext_xml(path: Path, data_mot: Path):
    xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
  <ExternalLoads name="v5_grf_plus_suit">
    <objects>
      <ExternalForce name="grf_R">
        <isDisabled>false</isDisabled>
        <applied_to_body>calcn_r</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>ground_force_R_v</force_identifier>
        <point_identifier>ground_force_R_p</point_identifier>
        <torque_identifier>ground_torque_R_</torque_identifier>
        <data_source_name>{data_mot.name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="grf_L">
        <isDisabled>false</isDisabled>
        <applied_to_body>calcn_l</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>ground_force_L_v</force_identifier>
        <point_identifier>ground_force_L_p</point_identifier>
        <torque_identifier>ground_torque_L_</torque_identifier>
        <data_source_name>{data_mot.name}</data_source_name>
      </ExternalForce>
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


def run_condition(F: float):
    tag = f'F{int(F)}'
    T_nm = F * MOMENT_ARM
    cond_dir = OUT_ROOT / tag
    cond_dir.mkdir(parents=True, exist_ok=True)

    mot_ext = cond_dir / f'ext_grf_suit_{tag}.mot'
    xml_ext = cond_dir / f'ext_loads_{tag}.xml'
    write_combined_ext_mot(mot_ext, T_nm)
    write_combined_ext_xml(xml_ext, mot_ext)

    tool = osim.AnalyzeTool()
    tool.setModelFilename(str(MODEL_V5))
    tool.setName(f'suit_v5_{tag}')
    tool.setResultsDir(str(cond_dir))
    tool.setInitialTime(T_START); tool.setFinalTime(T_END)
    tool.setLowpassCutoffFrequency(-1)
    tool.setCoordinatesFileName(MOT)
    tool.setReplaceForceSet(False)
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
    forces = [float(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [200.0]
    for F in forces:
        run_condition(F)
