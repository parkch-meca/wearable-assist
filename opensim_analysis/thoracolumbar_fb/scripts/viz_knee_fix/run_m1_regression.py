"""M1 scapula-DOF regression gate: run identical stoop SO on baseline (no_coupler) and
M1 (no_coupler + sternoclavicular 2-DOF). Compare ES activation. Pass if max ΔES < 5 %p.
clav coords are absent from the .mot -> held at 0 (== welded state) for this stoop motion."""
import sys, time, os
from pathlib import Path
import numpy as np, opensim as osim

BASE={'baseline':'/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim',
      'm1':'/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap.osim'}
MOT='/data/stoop_motion/stoop_synthetic_v5.mot'
GRF='/data/stoop_motion/stoop_grf_v5.xml'
ROOT=Path('/data/stoop_results/m1_regression'); ROOT.mkdir(parents=True,exist_ok=True)
T0,T1=0.0,5.0

def subsample(src,dst,fps=30):
    tbl=osim.TimeSeriesTable(str(src)); times=list(tbl.getIndependentColumn()); dt=1.0/fps; keep=[0]
    for i in range(1,len(times)):
        if times[i]-times[keep[-1]]>=dt-1e-9: keep.append(i)
    if keep[-1]!=len(times)-1: keep.append(len(times)-1)
    labels=list(tbl.getColumnLabels())
    hdr=f"stoop_v5_30fps\nversion=1\nnRows={len(keep)}\nnColumns={1+len(labels)}\ninDegrees=yes\n\nUnits are S.I. units.\n\nendheader\ntime\t"+"\t".join(labels)+"\n"
    with open(dst,'w') as f:
        f.write(hdr)
        for i in keep:
            row=tbl.getRowAtIndex(i); f.write("\t".join([f"{times[i]:.6f}"]+[f"{row[j]:.6f}" for j in range(len(labels))])+"\n")

def reserved(src,dst):
    m=osim.Model(src); m.initSystem(); cs=m.getCoordinateSet()
    for i in range(cs.getSize()):
        c=cs.get(i); nm=c.getName(); a=osim.CoordinateActuator(nm); a.setName(f'reserve_{nm}')
        opt=(500.0 if nm.startswith('pelvis') else 100.0) if c.getMotionType()==1 else 1000.0
        a.setOptimalForce(opt); a.setMinControl(-50.0); a.setMaxControl(50.0); m.addForce(a)
    m.finalizeConnections(); m.printToXML(dst)

def run_so(tag,src):
    d=ROOT/tag; d.mkdir(exist_ok=True); mot=d/'v5_30fps.mot'; mres=str(d/'model_res.osim')
    subsample(MOT,mot); reserved(src,mres)
    idt=osim.InverseDynamicsTool(); idt.setModelFileName(mres); idt.setCoordinatesFileName(MOT)
    idt.setStartTime(T0); idt.setEndTime(T1); idt.setLowpassCutoffFrequency(-1); idt.setResultsDir(str(d))
    idt.setOutputGenForceFileName('id.sto'); ex=osim.ArrayStr(); ex.append('Muscles'); idt.setExcludedForces(ex)
    idt.setExternalLoadsFileName(GRF); t=time.time(); idt.run(); print(f'[{tag} ID] {time.time()-t:.0f}s')
    tool=osim.AnalyzeTool(); tool.setModelFilename(mres); tool.setName('so'); tool.setResultsDir(str(d))
    tool.setInitialTime(T0); tool.setFinalTime(T1); tool.setLowpassCutoffFrequency(-1)
    tool.setCoordinatesFileName(str(mot)); tool.setReplaceForceSet(False); tool.setExternalLoadsFileName(GRF)
    so=osim.StaticOptimization(); so.setStartTime(T0); so.setEndTime(T1); so.setUseMusclePhysiology(True)
    so.setActivationExponent(2.0); so.setConvergenceCriterion(1e-4); so.setMaxIterations(300)
    tool.getAnalysisSet().cloneAndAppend(so); setup=d/'setup.xml'; tool.printToXML(str(setup))
    t=time.time(); osim.AnalyzeTool(str(setup)).run(); print(f'[{tag} SO] {time.time()-t:.0f}s')
    return d/'so_StaticOptimization_activation.sto'

def load_act(p):
    tbl=osim.TimeSeriesTable(str(p)); labels=list(tbl.getColumnLabels())
    times=np.array(list(tbl.getIndependentColumn()))
    data={lab:np.array([tbl.getDependentColumn(lab)[i] for i in range(tbl.getNumRows())]) for lab in labels}
    return times,data

if __name__=='__main__':
    phase=sys.argv[1] if len(sys.argv)>1 else 'all'
    if phase in ('base','all'): run_so('baseline',BASE['baseline'])
    if phase in ('m1','all'):   run_so('m1',BASE['m1'])
    # compare
    tb,db=load_act(ROOT/'baseline'/'so_StaticOptimization_activation.sto')
    tm,dm=load_act(ROOT/'m1'/'so_StaticOptimization_activation.sto')
    ES=[k for k in db if k.split('/')[-1].startswith(('IL_','LTpL','LTpT'))]
    PH=[('Prebend',0.5,1.0),('Concentric',1.0,1.99),('Hold',2.0,2.4),('Eccentric',2.5,4.0),('Recovery',4.0,5.0)]
    worst=0.0; worst_info=''
    for ph,a,b in PH:
        mb=(tb>=a)&(tb<=b); mm=(tm>=a)&(tm<=b)
        for k in ES:
            if k not in dm: continue
            pb=db[k][mb].max()*100 if mb.any() else 0; pm=dm[k][mm].max()*100 if mm.any() else 0
            d=abs(pm-pb)
            if d>worst: worst=d; worst_info=f'{k.split("/")[-1]} {ph} base={pb:.2f} m1={pm:.2f}'
    # ES mean per phase
    print("=== ES mean activation per phase (baseline -> m1) ===")
    for ph,a,b in PH:
        mb=(tb>=a)&(tb<=b); mm=(tm>=a)&(tm<=b)
        vb=np.mean([db[k][mb].mean() for k in ES if mb.any()])*100
        vm=np.mean([dm[k][mm].mean() for k in ES if k in dm and mm.any()])*100
        print(f"  {ph:12s} base={vb:6.2f}%  m1={vm:6.2f}%  d={vm-vb:+.3f}%p")
    print(f"\nES muscles compared: {len(ES)}")
    print(f"MAX ΔES (peak, any muscle/phase) = {worst:.3f} %p   [{worst_info}]")
    print("REGRESSION:", "PASS (<5%p)" if worst<5.0 else "FAIL (>=5%p)")
