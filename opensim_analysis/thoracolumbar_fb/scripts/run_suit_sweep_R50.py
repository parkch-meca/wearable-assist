"""Single-step SO on suit_sweep_v2 motion with R=50 Nm spine reserves.

Motion: /data/stoop_results/ik_result_30fps.mot (3 s synthetic stoop, no box)
Ext loads: existing suit_sweep_v2/F{X}/ext_loads_F{X}.xml
Reserves: rotational non-pelvis = 50 Nm (vs baseline 100)
Time: t = 2.32..2.36 (single step at ~peak of alpha schedule)

Usage: python run_suit_sweep_R50.py <force>  where force ∈ {0, 50, 100, 150, 200}
"""
import sys, time, shutil
from pathlib import Path
import opensim as osim

from run_reserve_sweep import build_reserved_model

MOT_SRC = '/data/stoop_results/ik_result_30fps.mot'
SWEEP_OLD = Path('/data/stoop_results/suit_sweep_v2')
OUT_ROOT = Path('/data/stoop_results/suit_sweep_R50')
OUT_ROOT.mkdir(parents=True, exist_ok=True)

T_START, T_END = 2.32, 2.36


def run_one(force_n: int):
    tag = f'F{force_n}'
    cond_dir = OUT_ROOT / tag
    cond_dir.mkdir(parents=True, exist_ok=True)

    # build R50 reserved model
    model_path = cond_dir / f'model_R50_{tag}.osim'
    build_reserved_model(50.0, model_path)
    print(f'[model] {model_path}')

    # Copy existing ext loads (suit torque only, no box)
    src_dir = SWEEP_OLD / tag
    # filename conventions in suit_sweep_v2: ext_loads_F{X}.xml and ext_torque_F{X}.mot
    src_xml = src_dir / f'ext_loads_{tag}.xml'
    src_mot = src_dir / f'ext_torque_{tag}.mot'
    if not src_xml.exists() or not src_mot.exists():
        print(f'[miss] {src_xml} or {src_mot}')
        return
    dst_xml = cond_dir / src_xml.name
    dst_mot = cond_dir / src_mot.name
    shutil.copy(src_xml, dst_xml)
    shutil.copy(src_mot, dst_mot)

    tool = osim.AnalyzeTool()
    tool.setModelFilename(str(model_path))
    tool.setName(f'so_R50_{tag}')
    tool.setResultsDir(str(cond_dir))
    tool.setInitialTime(T_START); tool.setFinalTime(T_END)
    tool.setLowpassCutoffFrequency(-1)
    tool.setCoordinatesFileName(MOT_SRC)
    tool.setReplaceForceSet(False)
    # F=0 has no external load — keep consistent with baseline (if force > 0 set loads)
    if force_n > 0:
        tool.setExternalLoadsFileName(str(dst_xml))

    so = osim.StaticOptimization()
    so.setStartTime(T_START); so.setEndTime(T_END)
    so.setUseMusclePhysiology(True)
    so.setActivationExponent(2.0)
    so.setConvergenceCriterion(1e-4)
    so.setMaxIterations(300)
    tool.getAnalysisSet().cloneAndAppend(so)

    setup = cond_dir / f'setup_R50_{tag}.xml'
    tool.printToXML(str(setup))
    tool2 = osim.AnalyzeTool(str(setup))
    t0 = time.time()
    ok = tool2.run()
    print(f'[SO R50 {tag}] ok={ok}  {time.time()-t0:.1f}s')


if __name__ == '__main__':
    F = int(sys.argv[1])
    run_one(F)
