"""Single-step SO for B_suit200 @ specified reserve level.

Reuses model builder from run_reserve_sweep.py but points to the B_suit200
ext loads (box + 200 N suit torque). Output dir: reserve_sweep/R{X}_suit200/.
"""
import sys, time, shutil
from pathlib import Path
import opensim as osim

from run_reserve_sweep import build_reserved_model

MOT_SRC = '/data/stoop_results/box_lift_v2/box_motion_v2_30fps.mot'
EXT_MOT = '/data/stoop_results/box_lift_v2/B_suit200/ext_B_suit200.mot'
EXT_XML = '/data/stoop_results/box_lift_v2/B_suit200/ext_B_suit200.xml'

SWEEP_ROOT = Path('/data/stoop_results/reserve_sweep')
T_START, T_END = 2.32, 2.36


def run_one(rotational_opt_nm: float):
    tag = f'R{int(rotational_opt_nm)}_suit200'
    cond_dir = SWEEP_ROOT / tag
    cond_dir.mkdir(parents=True, exist_ok=True)

    model_path = cond_dir / f'model_reserves_{tag}.osim'
    build_reserved_model(rotational_opt_nm, model_path)
    print(f'[model] {model_path}  (rotational reserve = {rotational_opt_nm} Nm)')

    ext_mot_dst = cond_dir / 'ext_B_suit200.mot'
    ext_xml_dst = cond_dir / 'ext_B_suit200.xml'
    shutil.copy(EXT_MOT, ext_mot_dst)
    shutil.copy(EXT_XML, ext_xml_dst)

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
