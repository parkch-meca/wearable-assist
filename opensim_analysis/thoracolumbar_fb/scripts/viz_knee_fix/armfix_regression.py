"""Isolate the left-arm axis fix effect on stoop/squat ES.
Run stoop_v5 + squat_v1 SO (F0 baseline, GRF, no suit) on DEFECTIVE (_M1scap) vs FIXED (_M1scap_armfix),
identical pipeline (M1 common -> delta = pure arm fix). Compare ES(IL+LTpL+LTpT) peak/mean.
Box is skipped (left arm=0 -> unaffected). NOT M1-style pass/fail: report the value change (defect correction)."""
import sys, time
from pathlib import Path
import numpy as np, opensim as osim
BASE={'def':'/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap.osim',
      'fix':'/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim'}
MOTIONS={'stoop':'/data/stoop_motion/stoop_synthetic_v5.mot','squat':'/data/stoop_motion/squat_synthetic_v1.mot'}
GRF='/data/stoop_motion/stoop_grf_v5.xml'
ROOT=Path('/data/stoop_results/armfix_regression'); ROOT.mkdir(parents=True,exist_ok=True)
T0,T1=0.0,5.0
def subsample(src,dst,fps=30):
    tbl=osim.TimeSeriesTable(str(src)); times=list(tbl.getIndependentColumn()); dt=1.0/fps; keep=[0]
    for i in range(1,len(times)):
        if times[i]-times[keep[-1]]>=dt-1e-9: keep.append(i)
    if keep[-1]!=len(times)-1: keep.append(len(times)-1)
    labs=list(tbl.getColumnLabels())
    hdr=f"sub\nversion=1\nnRows={len(keep)}\nnColumns={1+len(labs)}\ninDegrees=yes\n\nUnits are S.I. units.\n\nendheader\ntime\t"+"\t".join(labs)+"\n"
    with open(dst,'w') as f:
        f.write(hdr)
        for i in keep:
            r=tbl.getRowAtIndex(i); f.write("\t".join([f"{times[i]:.6f}"]+[f"{r[j]:.6f}" for j in range(len(labs))])+"\n")
def reserved(src,dst):
    if Path(dst).exists(): return
    m=osim.Model(src); m.initSystem(); cs=m.getCoordinateSet()
    for i in range(cs.getSize()):
        c=cs.get(i); nm=c.getName(); a=osim.CoordinateActuator(nm); a.setName(f'reserve_{nm}')
        opt=(500.0 if nm.startswith('pelvis') else 100.0) if c.getMotionType()==1 else 1000.0
        a.setOptimalForce(opt); a.setMinControl(-50.0); a.setMaxControl(50.0); m.addForce(a)
    m.finalizeConnections(); m.printToXML(str(dst))
def run_so(tag,src,mot):
    d=ROOT/tag; d.mkdir(exist_ok=True); mres=str(d/'model_res.osim'); msub=str(d/'kin_30fps.mot')
    reserved(src,mres); subsample(mot,msub)
    idt=osim.InverseDynamicsTool(); idt.setModelFileName(mres); idt.setCoordinatesFileName(mot)
    idt.setStartTime(T0); idt.setEndTime(T1); idt.setLowpassCutoffFrequency(-1); idt.setResultsDir(str(d))
    idt.setOutputGenForceFileName('id.sto'); ex=osim.ArrayStr(); ex.append('Muscles'); idt.setExcludedForces(ex)
    idt.setExternalLoadsFileName(GRF); idt.run()
    tool=osim.AnalyzeTool(); tool.setModelFilename(mres); tool.setName('so'); tool.setResultsDir(str(d))
    tool.setInitialTime(T0); tool.setFinalTime(T1); tool.setLowpassCutoffFrequency(-1)
    tool.setCoordinatesFileName(msub); tool.setReplaceForceSet(False); tool.setExternalLoadsFileName(GRF)
    so=osim.StaticOptimization(); so.setStartTime(T0); so.setEndTime(T1); so.setUseMusclePhysiology(True)
    so.setActivationExponent(2.0); so.setConvergenceCriterion(1e-4); so.setMaxIterations(300)
    tool.getAnalysisSet().cloneAndAppend(so); setup=d/'setup.xml'; tool.printToXML(str(setup))
    t=time.time(); osim.AnalyzeTool(str(setup)).run(); print(f'[{tag}] {time.time()-t:.0f}s',flush=True)
def es_stats(tag):
    p=ROOT/tag/'so_StaticOptimization_activation.sto'
    tbl=osim.TimeSeriesTable(str(p)); labs=list(tbl.getColumnLabels()); t=np.array(list(tbl.getIndependentColumn()))
    es=[l for l in labs if l.startswith(('IL_','LTpL','LTpT'))]
    A=np.array([[tbl.getDependentColumn(e)[i] for e in es] for i in range(tbl.getNumRows())])*100
    peak=A.max(axis=1); mean=A.mean(axis=1)  # over muscles per time
    return peak.max(), mean.max(), len(es)  # peak-of-peak, peak-of-mean over whole motion

if __name__=='__main__':
    for mn,mot in MOTIONS.items():
        for mk,src in BASE.items():
            run_so(f'{mn}_{mk}',src,mot)
    print("\n=== ARM FIX effect on stoop/squat ES (F0 baseline, IL+LTpL+LTpT) ===")
    for mn in MOTIONS:
        pd_,md_,n=es_stats(f'{mn}_def'); pf,mf,_=es_stats(f'{mn}_fix')
        print(f"{mn:6s}  ES peak(max muscle): def {pd_:.1f}% -> fix {pf:.1f}%  (Δ {pf-pd_:+.1f}%p)")
        print(f"        ES mean(muscle avg): def {md_:.1f}% -> fix {mf:.1f}%  (Δ {mf-md_:+.1f}%p)  [{n} ES muscles]")
    print("ALL_DONE")
