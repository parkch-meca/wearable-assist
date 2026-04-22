"""ID + SO on stoop_synthetic_v5 with GRF (slow symmetric 2s bend / 2s straight)."""
import sys, time
from pathlib import Path
import opensim as osim

MODEL_SRC = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim'
MOT_SRC = '/data/stoop_motion/stoop_synthetic_v5.mot'
GRF_XML = '/data/stoop_motion/stoop_grf_v5.xml'

OUT = Path('/data/stoop_results/stoop_v5')
OUT.mkdir(parents=True, exist_ok=True)
MOT_SUB = OUT / 'v5_30fps.mot'
MODEL_RES = OUT / 'model_with_reserves_v5.osim'
T_START, T_END = 0.0, 5.0


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
        f"stoop_v5_30fps\nversion=1\nnRows={len(keep)}\n"
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
    print(f'[sub] {len(times)} -> {len(keep)} frames')


def build_reserved_model():
    m = osim.Model(MODEL_SRC); m.initSystem()
    cs = m.getCoordinateSet()
    for i in range(cs.getSize()):
        c = cs.get(i); name = c.getName()
        a = osim.CoordinateActuator(name)
        a.setName(f'reserve_{name}')
        if c.getMotionType() == 1:
            opt = 500.0 if name.startswith('pelvis') else 100.0
        else:
            opt = 1000.0
        a.setOptimalForce(opt); a.setMinControl(-50.0); a.setMaxControl(50.0)
        m.addForce(a)
    m.finalizeConnections()
    m.printToXML(str(MODEL_RES))
    print(f'[model] {MODEL_RES}')


def run_id():
    t = osim.InverseDynamicsTool()
    t.setModelFileName(str(MODEL_RES))
    t.setCoordinatesFileName(MOT_SRC)
    t.setStartTime(T_START); t.setEndTime(T_END)
    t.setLowpassCutoffFrequency(-1)
    t.setResultsDir(str(OUT))
    t.setOutputGenForceFileName('id_v5.sto')
    excl = osim.ArrayStr(); excl.append('Muscles')
    t.setExcludedForces(excl)
    t.setExternalLoadsFileName(GRF_XML)
    t0 = time.time(); ok = t.run()
    print(f'[ID] {time.time()-t0:.1f}s ok={ok}')


def run_so():
    tool = osim.AnalyzeTool()
    tool.setModelFilename(str(MODEL_RES))
    tool.setName('so_v5')
    tool.setResultsDir(str(OUT))
    tool.setInitialTime(T_START); tool.setFinalTime(T_END)
    tool.setLowpassCutoffFrequency(-1)
    tool.setCoordinatesFileName(str(MOT_SUB))
    tool.setReplaceForceSet(False)
    tool.setExternalLoadsFileName(GRF_XML)
    so = osim.StaticOptimization()
    so.setStartTime(T_START); so.setEndTime(T_END)
    so.setUseMusclePhysiology(True)
    so.setActivationExponent(2.0)
    so.setConvergenceCriterion(1e-4)
    so.setMaxIterations(300)
    tool.getAnalysisSet().cloneAndAppend(so)
    setup = OUT / 'setup_so_v5.xml'
    tool.printToXML(str(setup))
    tool2 = osim.AnalyzeTool(str(setup))
    t0 = time.time(); ok = tool2.run()
    print(f'[SO] {time.time()-t0:.1f}s ok={ok}')


if __name__ == '__main__':
    phase = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if phase in ('prep', 'all'):
        subsample_mot(MOT_SRC, MOT_SUB)
        build_reserved_model()
    if phase in ('id', 'all'):
        run_id()
    if phase in ('so', 'all'):
        run_so()
