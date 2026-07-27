"""Re-run gait OFF/ON SO with TIGHT spine reserves (opt 100->5 -> reserve force expensive -> muscles carry
spine load -> accurate absolute ES). Confirms suit effect robustness. Reuses existing ext.xml/ext.mot."""
import numpy as np, opensim as osim, time
from pathlib import Path
MODEL='/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim'
MOT='/data/gait_motion/gait_retarget_so.mot'; ROOT=Path('/data/gait_results'); T0,T1=0.4,1.6
def reserved_tight(dst):
    m=osim.Model(MODEL); m.initSystem(); cs=m.getCoordinateSet()
    for i in range(cs.getSize()):
        c=cs.get(i); nm=c.getName(); a=osim.CoordinateActuator(nm); a.setName(f'reserve_{nm}')
        if nm.startswith('pelvis'): opt=(500.0 if c.getMotionType()==1 else 1000.0)   # keep large (absorb residual)
        elif any(k in nm for k in ['_FE','_LB','_AR','Abs_']): opt=5.0                  # spine: tight -> muscles carry
        else: opt=(100.0 if c.getMotionType()==1 else 1000.0)
        a.setOptimalForce(opt); a.setMinControl(-50.0); a.setMaxControl(50.0); m.addForce(a)
    m.finalizeConnections(); m.printToXML(dst)
mres=str(ROOT/'model_res_tight.osim'); reserved_tight(mres)
def run(tag):
    d=ROOT/f'gait_{tag}_tight'; d.mkdir(exist_ok=True)
    extxml=str(ROOT/f'gait_{tag}/ext.xml')   # reuse existing external loads
    tool=osim.AnalyzeTool(); tool.setModelFilename(mres); tool.setName('so'); tool.setResultsDir(str(d))
    tool.setInitialTime(T0); tool.setFinalTime(T1); tool.setLowpassCutoffFrequency(6)
    tool.setCoordinatesFileName(MOT); tool.setReplaceForceSet(False); tool.setExternalLoadsFileName(extxml)
    so=osim.StaticOptimization(); so.setStartTime(T0); so.setEndTime(T1); so.setUseMusclePhysiology(True)
    so.setActivationExponent(2.0); so.setConvergenceCriterion(1e-4); so.setMaxIterations(300)
    tool.getAnalysisSet().cloneAndAppend(so); setup=str(d/'setup.xml'); tool.printToXML(setup)
    t=time.time(); osim.AnalyzeTool(setup).run(); print(f'[{tag}_tight] {time.time()-t:.0f}s',flush=True)
run('off'); run('on'); print('TIGHT_DONE')
