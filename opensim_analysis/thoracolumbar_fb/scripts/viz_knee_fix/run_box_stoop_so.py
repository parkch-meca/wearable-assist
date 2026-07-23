"""OFF/ON SO for the stoop box-lift (M1 model, box_stoop_lift_m1.mot).
Box 20kg applied at both hands during grip window [1.9,5.5]; suit = thoracic1<->pelvis
torque couple (24 N.m ON). No explicit GRF: reserved-model pelvis actuators absorb base
reaction (same recipe as run_box_so_v2). NO max_isometric_force manipulation.
Conditions: B_noload (ref) / B_off (box,0) / B_on (box,24Nm)."""
import os, sys, time
from pathlib import Path
import numpy as np, opensim as osim
MODEL_BASE='/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap.osim'
MOT_SRC='/data/stoop_motion/box_stoop_lift_m1.mot'
OUT=Path('/data/stoop_results/box_stoop_so'); OUT.mkdir(parents=True,exist_ok=True)
MODEL_RES=OUT/'model_with_reserves_m1.osim'
T_START,T_END=0.0,7.5
BOX_KG=20.0; G=9.81; BOX_FORCE_PER_HAND=BOX_KG*G/2.0   # 98.1 N
GRIP_START,GRIP_END=1.9,6.0
SUIT_ON_NM=24.0
CONDITIONS={'B_noload':dict(box=False,suit=0.0),'B_off':dict(box=True,suit=0.0),'B_on':dict(box=True,suit=SUIT_ON_NM)}

def ss(a): a=min(1.0,max(0.0,a)); return a*a*(3-2*a)
def load_alpha(t):
    # box held: ramp on at grasp, hold, ramp off at release
    if t<GRIP_START: return 0.0
    if t<GRIP_START+0.4: return ss((t-GRIP_START)/0.4)
    if t<GRIP_END-0.2: return 1.0
    if t<GRIP_END: return ss((GRIP_END-t)/0.2)
    return 0.0

def build_reserved():
    if MODEL_RES.exists(): return
    m=osim.Model(MODEL_BASE); m.initSystem(); cs=m.getCoordinateSet()
    for i in range(cs.getSize()):
        c=cs.get(i); nm=c.getName(); a=osim.CoordinateActuator(nm); a.setName(f'reserve_{nm}')
        opt=(500.0 if nm.startswith('pelvis') else 100.0) if c.getMotionType()==1 else 1000.0
        a.setOptimalForce(opt); a.setMinControl(-50.0); a.setMaxControl(50.0); m.addForce(a)
    m.finalizeConnections(); m.printToXML(str(MODEL_RES)); print('[model]',MODEL_RES)

def write_ext_mot(path,box,suit,fps=120):
    n=int((T_END-T_START)*fps)+1; times=np.linspace(T_START,T_END,n)
    tags=('handR','handL','thor','pel'); cols=[]
    for tag in tags:
        for k in ('F_vx','F_vy','F_vz','T_x','T_y','T_z','P_px','P_py','P_pz'): cols.append(f'{tag}_{k}')
    data=np.zeros((n,len(cols)))
    for i,t in enumerate(times):
        a=load_alpha(float(t))
        if box:
            data[i,cols.index('handR_F_vy')]=-BOX_FORCE_PER_HAND*a
            data[i,cols.index('handL_F_vy')]=-BOX_FORCE_PER_HAND*a
        if suit>0:
            Tz=suit*a
            data[i,cols.index('thor_T_z')]=+Tz; data[i,cols.index('pel_T_z')]=-Tz
    hdr=(f"box_stoop_ext box={int(box)} suit={suit:.0f}\nversion=1\nnRows={n}\nnColumns={1+len(cols)}\ninDegrees=no\n\nUnits are S.I. units.\n\nendheader\ntime\t"+"\t".join(cols)+"\n")
    with open(path,'w') as f:
        f.write(hdr)
        for i,t in enumerate(times): f.write("\t".join([f"{t:.6f}"]+[f"{v:.6f}" for v in data[i]])+"\n")

def write_ext_xml(path,mot_name,box,suit):
    e=''
    if box:
        for tag,body in [('handR','hand_R'),('handL','hand_L')]:
            e+=f"""
      <ExternalForce name="box_{tag}"><isDisabled>false</isDisabled><applied_to_body>{body}</applied_to_body><force_expressed_in_body>ground</force_expressed_in_body><point_expressed_in_body>{body}</point_expressed_in_body><force_identifier>{tag}_F_v</force_identifier><point_identifier>{tag}_P_p</point_identifier><torque_identifier>{tag}_T_</torque_identifier><data_source_name>{mot_name}</data_source_name></ExternalForce>"""
    if suit>0:
        for tag,body in [('thor','thoracic1'),('pel','pelvis')]:
            e+=f"""
      <ExternalForce name="suit_{tag}"><isDisabled>false</isDisabled><applied_to_body>{body}</applied_to_body><force_expressed_in_body>ground</force_expressed_in_body><point_expressed_in_body>ground</point_expressed_in_body><force_identifier>{tag}_F_v</force_identifier><point_identifier>{tag}_P_p</point_identifier><torque_identifier>{tag}_T_</torque_identifier><data_source_name>{mot_name}</data_source_name></ExternalForce>"""
    Path(path).write_text(f"""<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000"><ExternalLoads name="box_stoop_loads"><objects>{e}
    </objects><groups /><datafile>{mot_name}</datafile></ExternalLoads></OpenSimDocument>
""")

def run_cond(cond,cfg):
    d=OUT/cond; d.mkdir(parents=True,exist_ok=True)
    mot_ext=d/f'ext_{cond}.mot'; xml_ext=d/f'ext_{cond}.xml'
    write_ext_mot(mot_ext,cfg['box'],cfg['suit']); write_ext_xml(xml_ext,mot_ext.name,cfg['box'],cfg['suit'])
    tool=osim.AnalyzeTool(); tool.setModelFilename(str(MODEL_RES)); tool.setName(f'so_{cond}'); tool.setResultsDir(str(d))
    tool.setInitialTime(T_START); tool.setFinalTime(T_END); tool.setLowpassCutoffFrequency(-1)
    tool.setCoordinatesFileName(MOT_SRC); tool.setReplaceForceSet(False)
    if cfg['box'] or cfg['suit']>0: tool.setExternalLoadsFileName(str(xml_ext))
    so=osim.StaticOptimization(); so.setStartTime(T_START); so.setEndTime(T_END); so.setUseMusclePhysiology(True)
    so.setActivationExponent(2.0); so.setConvergenceCriterion(1e-4); so.setMaxIterations(300)
    tool.getAnalysisSet().cloneAndAppend(so)
    setup=d/f'setup_{cond}.xml'; tool.printToXML(str(setup))
    t0=time.time(); ok=osim.AnalyzeTool(str(setup)).run(); print(f'[SO {cond}] ok={ok} {time.time()-t0:.0f}s',flush=True)

if __name__=='__main__':
    build_reserved()
    only=sys.argv[1] if len(sys.argv)>1 else None
    for cond,cfg in CONDITIONS.items():
        if only and cond!=only: continue
        run_cond(cond,cfg)
    print('ALL_SO_DONE')
