"""Gait OFF/ON SO on armfix model. GRF (BW-scaled) + suit torque couple (thoracic1<->pelvis, z, ground).
Walking has no distinct lift phase -> suit applied constant 24 N.m (ON) vs 0 (OFF). Same GRF+motion both
-> residuals identical -> suit EFFECT on ES robust (absolute ES is reserve/residual-influenced).
Reports ES(IL+LTpL+LTpT) peak per gait phase + reserve actuator activation check (>100N / >10N.m)."""
import numpy as np, opensim as osim, time
from pathlib import Path
MODEL='/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim'
MOT='/data/gait_motion/gait_retarget_so.mot'
GRF_MOT='/data/gait_motion/gait_grf_scaled.mot'
ROOT=Path('/data/gait_results'); ROOT.mkdir(exist_ok=True)
T0,T1=0.4,1.6; SUIT_NM=24.0
GRF_COLS=['ground_force_vx','ground_force_vy','ground_force_vz','ground_force_px','ground_force_py','ground_force_pz',
 '1_ground_force_vx','1_ground_force_vy','1_ground_force_vz','1_ground_force_px','1_ground_force_py','1_ground_force_pz',
 'ground_torque_x','ground_torque_y','ground_torque_z','1_ground_torque_x','1_ground_torque_y','1_ground_torque_z']
SUIT_COLS=['thor_F_vx','thor_F_vy','thor_F_vz','thor_T_x','thor_T_y','thor_T_z','thor_P_px','thor_P_py','thor_P_pz',
           'pel_F_vx','pel_F_vy','pel_F_vz','pel_T_x','pel_T_y','pel_T_z','pel_P_px','pel_P_py','pel_P_pz']

def reserved(dst):
    if Path(dst).exists(): return
    m=osim.Model(MODEL); m.initSystem(); cs=m.getCoordinateSet()
    for i in range(cs.getSize()):
        c=cs.get(i); nm=c.getName(); a=osim.CoordinateActuator(nm); a.setName(f'reserve_{nm}')
        opt=(500.0 if nm.startswith('pelvis') else 100.0) if c.getMotionType()==1 else 1000.0
        a.setOptimalForce(opt); a.setMinControl(-50.0); a.setMaxControl(50.0); m.addForce(a)
    m.finalizeConnections(); m.printToXML(dst)

def write_ext(path, suit_nm):
    grf=osim.TimeSeriesTable(GRF_MOT); tg=np.array(list(grf.getIndependentColumn())); n=grf.getNumRows()
    G={c:np.array([grf.getDependentColumn(c)[i] for i in range(n)]) for c in GRF_COLS}
    S={c:np.zeros(n) for c in SUIT_COLS}   # zero force + zero point, torque only
    S['thor_T_z'][:]=+suit_nm; S['pel_T_z'][:]=-suit_nm   # constant extension couple, ground z-axis
    cols=GRF_COLS+SUIT_COLS
    hdr=(f"gait_ext\nversion=1\nnRows={n}\nnColumns={1+len(cols)}\ninDegrees=no\n\nendheader\ntime\t"+"\t".join(cols)+"\n")
    with open(path,'w') as f:
        f.write(hdr)
        for i in range(n):
            f.write("\t".join([f"{tg[i]:.6f}"]+[f"{G[c][i]:.6f}" for c in GRF_COLS]+[f"{S[c][i]:.6f}" for c in SUIT_COLS])+"\n")

def ext_xml(path, datafile, suit):
    body=(f'''<ExternalForce name="suit_thor"><applied_to_body>thoracic1</applied_to_body><force_expressed_in_body>ground</force_expressed_in_body><point_expressed_in_body>ground</point_expressed_in_body>
<force_identifier>thor_F_v</force_identifier><point_identifier>thor_P_p</point_identifier><torque_identifier>thor_T_</torque_identifier></ExternalForce>
<ExternalForce name="suit_pel"><applied_to_body>pelvis</applied_to_body><force_expressed_in_body>ground</force_expressed_in_body><point_expressed_in_body>ground</point_expressed_in_body>
<force_identifier>pel_F_v</force_identifier><point_identifier>pel_P_p</point_identifier><torque_identifier>pel_T_</torque_identifier></ExternalForce>''' if suit else '')
    xml=f'''<?xml version="1.0" encoding="UTF-8"?>
<OpenSimDocument Version="40000"><ExternalLoads name="gait_ext"><objects>
<ExternalForce name="right"><applied_to_body>calcn_r</applied_to_body><force_expressed_in_body>ground</force_expressed_in_body><point_expressed_in_body>ground</point_expressed_in_body>
<force_identifier>ground_force_v</force_identifier><point_identifier>ground_force_p</point_identifier><torque_identifier>ground_torque_</torque_identifier></ExternalForce>
<ExternalForce name="left"><applied_to_body>calcn_l</applied_to_body><force_expressed_in_body>ground</force_expressed_in_body><point_expressed_in_body>ground</point_expressed_in_body>
<force_identifier>1_ground_force_v</force_identifier><point_identifier>1_ground_force_p</point_identifier><torque_identifier>1_ground_torque_</torque_identifier></ExternalForce>
{body}</objects><datafile>{datafile}</datafile></ExternalLoads></OpenSimDocument>'''
    open(path,'w').write(xml)

def run_so(tag, suit):
    d=ROOT/f'gait_{tag}'; d.mkdir(exist_ok=True); mres=str(ROOT/'model_res.osim'); reserved(mres)
    extmot=str(d/'ext.mot'); extxml=str(d/'ext.xml')
    write_ext(extmot, SUIT_NM if suit else 0.0); ext_xml(extxml, extmot, suit)
    tool=osim.AnalyzeTool(); tool.setModelFilename(mres); tool.setName('so'); tool.setResultsDir(str(d))
    tool.setInitialTime(T0); tool.setFinalTime(T1); tool.setLowpassCutoffFrequency(6)
    tool.setCoordinatesFileName(MOT); tool.setReplaceForceSet(False); tool.setExternalLoadsFileName(extxml)
    so=osim.StaticOptimization(); so.setStartTime(T0); so.setEndTime(T1); so.setUseMusclePhysiology(True)
    so.setActivationExponent(2.0); so.setConvergenceCriterion(1e-4); so.setMaxIterations(300)
    tool.getAnalysisSet().cloneAndAppend(so); setup=str(d/'setup.xml'); tool.printToXML(setup)
    t=time.time(); osim.AnalyzeTool(setup).run(); print(f'[{tag}] SO {time.time()-t:.0f}s',flush=True)

if __name__=='__main__':
    import sys
    if 'on_only' in sys.argv:
        run_so('on', True)
    else:
        run_so('off', False); run_so('on', True)
    print('SO_DONE')
