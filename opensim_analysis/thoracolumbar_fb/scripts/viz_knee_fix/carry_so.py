"""Carry-walk OFF/ON SO on armfix model with 20kg box.
- box 20kg = anterior external force at BOTH hands (98.1 N/hand, down in ground) — loads trunk (ES driver)
- box weight added to vertical GRF (distributed by each foot's vertical share) — person+box supported at ground
- suit torque couple thoracic1<->pelvis (z, ground), constant 24 N.m (ON) vs 0 (OFF)
- reserve TIGHT: spine (_FE/_LB/_AR/Abs_) opt=5 (expensive -> muscles carry box moment -> accurate ES);
  pelvis large (500/1000, absorbs residual, cancels OFF/ON); others 100/1000.
- Same GRF+box+motion in OFF/ON -> residuals identical -> suit EFFECT robust.
Usage: python carry_so.py            # runs off then on
       python carry_so.py check      # pre-exec verification only (no SO)
"""
import numpy as np, opensim as osim, time, sys
from pathlib import Path
MODEL='/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim'
MOT='/data/gait_motion/carry_walk_so.mot'
GRF_MOT='/data/gait_motion/gait_grf_scaled.mot'
ROOT=Path('/data/carry_results'); ROOT.mkdir(exist_ok=True)
T0,T1=0.4,1.6; SUIT_NM=24.0
BOX_KG=20.0; G=9.81; BOX_N=BOX_KG*G           # 196.2 N total
BOX_HAND=BOX_N/2.0                             # 98.1 N per hand

GRF_COLS=['ground_force_vx','ground_force_vy','ground_force_vz','ground_force_px','ground_force_py','ground_force_pz',
 '1_ground_force_vx','1_ground_force_vy','1_ground_force_vz','1_ground_force_px','1_ground_force_py','1_ground_force_pz',
 'ground_torque_x','ground_torque_y','ground_torque_z','1_ground_torque_x','1_ground_torque_y','1_ground_torque_z']
SUIT_COLS=['thor_F_vx','thor_F_vy','thor_F_vz','thor_T_x','thor_T_y','thor_T_z','thor_P_px','thor_P_py','thor_P_pz',
           'pel_F_vx','pel_F_vy','pel_F_vz','pel_T_x','pel_T_y','pel_T_z','pel_P_px','pel_P_py','pel_P_pz']
# box: force at each hand (down in ground), point = hand body origin (point_expressed_in_body=hand)
BOX_COLS=['boxR_F_vx','boxR_F_vy','boxR_F_vz','boxR_P_px','boxR_P_py','boxR_P_pz',
          'boxL_F_vx','boxL_F_vy','boxL_F_vz','boxL_P_px','boxL_P_py','boxL_P_pz']

def reserved_tight(dst):
    m=osim.Model(MODEL); m.initSystem(); cs=m.getCoordinateSet()
    for i in range(cs.getSize()):
        c=cs.get(i); nm=c.getName(); a=osim.CoordinateActuator(nm); a.setName(f'reserve_{nm}')
        if nm.startswith('pelvis'): opt=(500.0 if c.getMotionType()==1 else 1000.0)
        elif any(k in nm for k in ['_FE','_LB','_AR','Abs_']): opt=5.0     # spine tight
        else: opt=(100.0 if c.getMotionType()==1 else 1000.0)
        a.setOptimalForce(opt); a.setMinControl(-50.0); a.setMaxControl(50.0); m.addForce(a)
    m.finalizeConnections(); m.printToXML(dst)

def load_grf():
    grf=osim.TimeSeriesTable(GRF_MOT); tg=np.array(list(grf.getIndependentColumn())); n=grf.getNumRows()
    Graw={c:np.array([grf.getDependentColumn(c)[i] for i in range(n)]) for c in GRF_COLS}
    return tg,n,Graw

def write_ext(path, suit_nm):
    tg,n,Gr=load_grf()
    G={c:Gr[c].copy() for c in GRF_COLS}
    # --- add box weight to vertical GRF, distributed by each foot's vertical share ---
    vyR=G['ground_force_vy']; vyL=G['1_ground_force_vy']; tot=vyR+vyL
    fracR=np.where(tot>1.0, vyR/np.maximum(tot,1e-6), 0.5)
    G['ground_force_vy']=vyR+BOX_N*fracR
    G['1_ground_force_vy']=vyL+BOX_N*(1.0-fracR)
    # --- box force at hands (down in ground), point = hand origin (constant 0 in hand frame) ---
    B={c:np.zeros(n) for c in BOX_COLS}
    B['boxR_F_vy'][:]=-BOX_HAND; B['boxL_F_vy'][:]=-BOX_HAND
    # --- suit couple ---
    S={c:np.zeros(n) for c in SUIT_COLS}
    S['thor_T_z'][:]=+suit_nm; S['pel_T_z'][:]=-suit_nm
    cols=GRF_COLS+BOX_COLS+SUIT_COLS
    hdr=(f"carry_ext\nversion=1\nnRows={n}\nnColumns={1+len(cols)}\ninDegrees=no\n\nendheader\ntime\t"+"\t".join(cols)+"\n")
    with open(path,'w') as f:
        f.write(hdr)
        for i in range(n):
            f.write("\t".join([f"{tg[i]:.6f}"]+[f"{G[c][i]:.6f}" for c in GRF_COLS]
                    +[f"{B[c][i]:.6f}" for c in BOX_COLS]+[f"{S[c][i]:.6f}" for c in SUIT_COLS])+"\n")

def ext_xml(path, datafile, suit):
    box=('''<ExternalForce name="box_R"><applied_to_body>hand_R</applied_to_body><force_expressed_in_body>ground</force_expressed_in_body><point_expressed_in_body>hand_R</point_expressed_in_body>
<force_identifier>boxR_F_v</force_identifier><point_identifier>boxR_P_p</point_identifier><torque_identifier></torque_identifier></ExternalForce>
<ExternalForce name="box_L"><applied_to_body>hand_L</applied_to_body><force_expressed_in_body>ground</force_expressed_in_body><point_expressed_in_body>hand_L</point_expressed_in_body>
<force_identifier>boxL_F_v</force_identifier><point_identifier>boxL_P_p</point_identifier><torque_identifier></torque_identifier></ExternalForce>''')
    suitxml=(f'''<ExternalForce name="suit_thor"><applied_to_body>thoracic1</applied_to_body><force_expressed_in_body>ground</force_expressed_in_body><point_expressed_in_body>ground</point_expressed_in_body>
<force_identifier>thor_F_v</force_identifier><point_identifier>thor_P_p</point_identifier><torque_identifier>thor_T_</torque_identifier></ExternalForce>
<ExternalForce name="suit_pel"><applied_to_body>pelvis</applied_to_body><force_expressed_in_body>ground</force_expressed_in_body><point_expressed_in_body>ground</point_expressed_in_body>
<force_identifier>pel_F_v</force_identifier><point_identifier>pel_P_p</point_identifier><torque_identifier>pel_T_</torque_identifier></ExternalForce>''' if suit else '')
    xml=f'''<?xml version="1.0" encoding="UTF-8"?>
<OpenSimDocument Version="40000"><ExternalLoads name="carry_ext"><objects>
<ExternalForce name="right"><applied_to_body>calcn_r</applied_to_body><force_expressed_in_body>ground</force_expressed_in_body><point_expressed_in_body>ground</point_expressed_in_body>
<force_identifier>ground_force_v</force_identifier><point_identifier>ground_force_p</point_identifier><torque_identifier>ground_torque_</torque_identifier></ExternalForce>
<ExternalForce name="left"><applied_to_body>calcn_l</applied_to_body><force_expressed_in_body>ground</force_expressed_in_body><point_expressed_in_body>ground</point_expressed_in_body>
<force_identifier>1_ground_force_v</force_identifier><point_identifier>1_ground_force_p</point_identifier><torque_identifier>1_ground_torque_</torque_identifier></ExternalForce>
{box}
{suitxml}</objects><datafile>{datafile}</datafile></ExternalLoads></OpenSimDocument>'''
    open(path,'w').write(xml)

def run_so(tag, suit):
    d=ROOT/f'carry_{tag}'; d.mkdir(exist_ok=True); mres=str(ROOT/'model_res_tight.osim')
    if not Path(mres).exists(): reserved_tight(mres)
    extmot=str(d/'ext.mot'); extxml=str(d/'ext.xml')
    write_ext(extmot, SUIT_NM if suit else 0.0); ext_xml(extxml, extmot, suit)
    tool=osim.AnalyzeTool(); tool.setModelFilename(mres); tool.setName('so'); tool.setResultsDir(str(d))
    tool.setInitialTime(T0); tool.setFinalTime(T1); tool.setLowpassCutoffFrequency(6)
    tool.setCoordinatesFileName(MOT); tool.setReplaceForceSet(False); tool.setExternalLoadsFileName(extxml)
    so=osim.StaticOptimization(); so.setStartTime(T0); so.setEndTime(T1); so.setUseMusclePhysiology(True)
    so.setActivationExponent(2.0); so.setConvergenceCriterion(1e-4); so.setMaxIterations(300)
    tool.getAnalysisSet().cloneAndAppend(so); setup=str(d/'setup.xml'); tool.printToXML(setup)
    t=time.time(); osim.AnalyzeTool(setup).run(); print(f'[carry_{tag}] SO {time.time()-t:.0f}s',flush=True)

def check():
    print('=== PRE-EXEC VERIFICATION ===')
    mt=osim.TimeSeriesTable(MOT); tt=np.array(list(mt.getIndependentColumn()))
    print(f'motion {MOT}: {tt[0]:.3f}-{tt[-1]:.3f}s rows {mt.getNumRows()} (SO win {T0}-{T1})')
    assert tt[0]<=T0 and tt[-1]>=T1, 'motion does not cover SO window!'
    tg,n,Gr=load_grf(); print(f'GRF {GRF_MOT}: {tg[0]:.3f}-{tg[-1]:.3f}s rows {n}')
    assert tg[0]<=T0 and tg[-1]>=T1, 'GRF does not cover SO window!'
    win=(tg>=T0)&(tg<=T1)
    vy=Gr['ground_force_vy'][win]+Gr['1_ground_force_vy'][win]
    print(f'person GRF vy sum in win: mean {vy.mean():.0f}N peak {vy.max():.0f}N (weight {77.969*G:.0f}N)')
    print(f'box: {BOX_KG}kg = {BOX_N:.1f}N total ({BOX_HAND:.1f}N/hand). +box GRF mean {vy.mean()+BOX_N:.0f}N')
    # verify hand bodies exist
    m=osim.Model(MODEL); m.initSystem(); bs=[m.getBodySet().get(i).getName() for i in range(m.getBodySet().getSize())]
    for b in ['hand_R','hand_L','calcn_r','calcn_l','thoracic1','pelvis']:
        assert b in bs, f'missing body {b}'
    print('bodies OK: hand_R hand_L calcn_r calcn_l thoracic1 pelvis')
    # dump one ext.mot for inspection
    ROOT.mkdir(exist_ok=True); write_ext(str(ROOT/'ext_check.mot'), 0.0)
    e=osim.TimeSeriesTable(str(ROOT/'ext_check.mot')); ew=(np.array(list(e.getIndependentColumn()))>=T0)&(np.array(list(e.getIndependentColumn()))<=T1)
    eR=np.array([e.getDependentColumn('ground_force_vy')[i] for i in range(e.getNumRows())])[ew]
    eL=np.array([e.getDependentColumn('1_ground_force_vy')[i] for i in range(e.getNumRows())])[ew]
    print(f'+box GRF vy sum: mean {(eR+eL).mean():.0f}N peak {(eR+eL).max():.0f}N (expect ~{vy.mean()+BOX_N:.0f} mean)')
    print('CHECK OK')

if __name__=='__main__':
    if 'check' in sys.argv:
        check()
    else:
        run_so('off', False); run_so('on', True); print('CARRY_SO_DONE')
