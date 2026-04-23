"""Reserve-actuator sensitivity sweep on B_suit0 (v2 motion, 20 kg box).

Tests 3 non-pelvis-translational rotational-reserve optimalForce values
(1 / 5 / 10 Nm) vs current baseline (100 Nm). Keeps pelvis translation
reserves at 1000 N (kinematic support — muscles cannot replace).

Outputs:
  /data/stoop_results/reserve_sweep/R{X}/
    model_reserves_R{X}.osim
    so_R{X}_StaticOptimization_{activation,force}.sto
    setup_R{X}.xml

Usage:
  python run_reserve_sweep.py 10
  python run_reserve_sweep.py 5
  python run_reserve_sweep.py 1

Parallel run from command line (3 bg shells, ~20 min each instead of 60 serial).
"""
import sys, time
from pathlib import Path
import numpy as np
import opensim as osim

BASE_MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim'
MOT_SRC   = '/data/stoop_results/box_lift_v2/box_motion_v2_30fps.mot'
EXT_MOT   = '/data/stoop_results/box_lift_v2/B_suit0/ext_B_suit0.mot'
EXT_XML_T = '/data/stoop_results/box_lift_v2/B_suit0/ext_B_suit0.xml'

SWEEP_ROOT = Path('/data/stoop_results/reserve_sweep')
# Sweep one time step at peak ES moment (t=2.33 s, liftoff).
# Full trajectory intractable: each step ~30 min under tight reserves.
# One-step snapshot captures the decisive quantities (ES peak, reserve use).
T_START, T_END = 2.32, 2.36


def build_reserved_model(rotational_opt_nm: float, out_osim: Path):
    """Build reserved model with:
       - rotational non-pelvis reserves: optimalForce = rotational_opt_nm
       - pelvis rotation reserves: 500 Nm (unchanged, hip-pelvis stability)
       - translational reserves (pelvis_tx/ty/tz): 1000 N (kinematic support)
    """
    m = osim.Model(BASE_MODEL); m.initSystem()
    cs = m.getCoordinateSet()
    for i in range(cs.getSize()):
        c = cs.get(i); name = c.getName()
        a = osim.CoordinateActuator(name)
        a.setName(f'reserve_{name}')
        if c.getMotionType() == 1:         # rotational
            if name.startswith('pelvis'):
                opt = 500.0                 # pelvis rotational — keep strong
            else:
                opt = rotational_opt_nm     # swept parameter
        else:                               # translational
            opt = 1000.0                    # keep strong (kinematic support)
        a.setOptimalForce(opt)
        a.setMinControl(-50.0); a.setMaxControl(50.0)
        m.addForce(a)
    m.finalizeConnections()
    m.printToXML(str(out_osim))


def make_ext_xml(target_xml: Path, ref_xml: str):
    """Copy the ext_B_suit0.xml, just update data_source_name path."""
    txt = Path(ref_xml).read_text()
    target_xml.write_text(txt)


def run_one(rotational_opt_nm: float):
    tag = f'R{int(rotational_opt_nm)}' if rotational_opt_nm == int(rotational_opt_nm) else f'R{rotational_opt_nm}'
    cond_dir = SWEEP_ROOT / tag
    cond_dir.mkdir(parents=True, exist_ok=True)

    model_path = cond_dir / f'model_reserves_{tag}.osim'
    build_reserved_model(rotational_opt_nm, model_path)
    print(f'[model] {model_path}  (rotational reserve = {rotational_opt_nm} Nm)')

    # Copy ext loads (box only, 0 N suit) next to the SO setup
    ext_mot_dst = cond_dir / 'ext_B_suit0.mot'
    ext_xml_dst = cond_dir / 'ext_B_suit0.xml'
    import shutil
    shutil.copy(EXT_MOT, ext_mot_dst)
    shutil.copy(EXT_XML_T, ext_xml_dst)

    tool = osim.AnalyzeTool()
    tool.setModelFilename(str(model_path))
    tool.setName(f'so_{tag}')
    tool.setResultsDir(str(cond_dir))
    tool.setInitialTime(T_START); tool.setFinalTime(T_END)
    tool.setLowpassCutoffFrequency(-1)
    tool.setCoordinatesFileName(MOT_SRC)
    tool.setReplaceForceSet(False)
    tool.setExternalLoadsFileName(str(ext_xml_dst))

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
    print(f'[SO {tag}] ok={ok}  {time.time()-t0:.1f}s')


if __name__ == '__main__':
    v = float(sys.argv[1])
    run_one(v)
