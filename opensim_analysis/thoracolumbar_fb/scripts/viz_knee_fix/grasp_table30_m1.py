"""Distributed full-spine flexion + semi-squat box-side grasp (NO .osim change).
Spread the 15-20cm reach shortfall across thoracic(12)+lumbar(5)+hip+knee(squat)+ankle
so the TRUNK stays natural (visual back-line < ~55 deg, pelvis kept fairly upright) instead
of folding near-horizontal. Vertical shoulder drop comes mainly from KNEE squat, not from
tilting the trunk over. Hard leg-table interference constraint. Arm IK to box side face."""
import opensim as osim, numpy as np, json, pyvista as pv, os
from scipy.optimize import minimize
from xml.etree import ElementTree as ET
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap.osim"
GEO="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry"
os.makedirs('/tmp/cmp_render',exist_ok=True)
model=osim.Model(P); state=model.initSystem(); cs=model.getCoordinateSet(); names=[cs.get(i).getName() for i in range(cs.getSize())]
for n in ['pro_sup_r','wrist_flex_r','wrist_dev_r']: cs.get(n).setLocked(state,False)
model.assemble(state); model.realizePosition(state)
comps={c.getName():c for c in (osim.PhysicalFrame.safeDownCast(x) for x in model.getComponentsList()) if c}
hfR=[comps[f'hand_R_geom_frame_{i}'] for i in range(1,30) if f'hand_R_geom_frame_{i}' in comps]
PFR={'thumb':comps['hand_R_geom_frame_9'],'pinky':comps['hand_R_geom_frame_13'],'midtip':comps['hand_R_geom_frame_21'],'midmc':comps['hand_R_geom_frame_11']}
def fp(pf): q=pf.getPositionInGround(state); return np.array([q.get(0),q.get(1),q.get(2)])
def palmR():
    d=fp(PFR['midtip'])-fp(PFR['midmc']); d/=np.linalg.norm(d)+1e-9
    r=fp(PFR['thumb'])-fp(PFR['pinky']); r/=np.linalg.norm(r)+1e-9
    n=-np.cross(d,r); return n/(np.linalg.norm(n)+1e-9)
def setc(d):
    for k,v in d.items():
        if k in names: c=cs.get(k); c.setValue(state,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def Bd(n): p=model.getBodySet().get(n).getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def Jt(j): p=model.getJointSet().get(j).getChildFrame().getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def comX(): return model.calcMassCenterPosition(state).get(0)
def realize(): model.assemble(state); model.realizePosition(state)
footloc=np.vstack([np.asarray(pv.read(os.path.join(GEO,f)).points) for f in ['foot.vtp','bofoot.vtp']])
shinloc=np.vstack([np.asarray(pv.read(os.path.join(GEO,f)).points) for f in ['tibia_r.vtp','fibula_r.vtp']])
thighloc=np.asarray(pv.read(os.path.join(GEO,'femur_r.vtp')).points)
def body_world(bn,loc):
    bd=model.getBodySet().get(bn); T=bd.getTransformInGround(state); R=T.R(); p=T.p()
    Rm=np.array([[R.get(i,j) for j in range(3)] for i in range(3)]); pv_=np.array([p.get(0),p.get(1),p.get(2)]); return (Rm@loc.T).T+pv_
def foot_world(): return body_world('calcn_r',footloc)
def shin_world(): return body_world('tibia_r',shinloc)
def thigh_world(): return body_world('femur_r',thighloc)
setc({c:0.0 for c in names}); realize(); fstand=Bd('calcn_r'); FLOOR=-0.905
hasskull='skull' in [model.getBodySet().get(i).getName() for i in range(model.getBodySet().getSize())]
def headY(): return Bd('skull')[1] if hasskull else Bd('thoracic1')[1]
EDGE=0.18; TABLE_H=0.30; TOPb=FLOOR+TABLE_H; BOX=0.30; BCX=EDGE+0.16; HALF=BOX/2
LUMB=['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE']
THOR=['T12_L1_FE','T11_T12_FE','T10_T11_FE','T9_T10_FE','T8_T9_FE','T7_T8_FE','T6_T7_FE','T5_T6_FE','T4_T5_FE','T3_T4_FE','T2_T3_FE','T1_T2_FE']
GRIP_H=float(os.environ.get('GRIP_H','0.16'))
print(f"SCENE 30cm table, grip h={TOPb+GRIP_H-FLOOR:.2f}m")
# ---- table slab for interference: x in [EDGE, EDGE+0.55], h in [0,TABLE_H] ----
def table_pen(pts):  # count pts inside table slab
    return int(((pts[:,0]>EDGE)&(pts[:,0]<EDGE+0.55)&(pts[:,1]>FLOOR)&(pts[:,1]<TOPb)&(np.abs(pts[:,2])<0.45)).sum())
def back_angle():   # visual back line: pelvis(sacrum) -> upper thorax, from vertical
    v=Bd('thoracic1')-Bd('pelvis'); return np.degrees(np.arctan2(np.hypot(v[0],v[2]),max(v[1],1e-6)))
# variables: [hip, knee, ankle, pelvis_tilt, lumbar_tot, thoracic_tot]
def bp(x):
    p={c:0.0 for c in names}
    p.update({'hip_flexion_r':x[0],'hip_flexion_l':x[0],'knee_angle_r':x[1],'knee_angle_l':x[1],'ankle_angle_r':x[2],'ankle_angle_l':x[2],'pelvis_tilt':x[3]})
    for L in LUMB: p[L]=x[4]/len(LUMB)
    for T in THOR: p[T]=x[5]/len(THOR)
    return p
def ground(p):
    p['pelvis_tx']=0;p['pelvis_ty']=0; setc(p); realize(); fw=foot_world(); p['pelvis_ty']=FLOOR-fw[:,1].min(); p['pelvis_tx']=fstand[0]-Bd('calcn_r')[0]; setc(p); realize(); return p
# bounds: pelvis fairly upright (>-30), lumbar moderate, thoracic distributed, DEEP knee squat ok
# keep pelvis MORE UPRIGHT (protraction, not lean, provides forward reach); deep knee for vertical drop
lb=np.array([20,-125,-32,-26,-30,-26]); ub=np.array([125,0,8,0,0,0])
SH_TGT=TOPb+GRIP_H+0.50   # shoulder height; protraction adds the FORWARD reach
def tobj(x):
    x=np.clip(x,lb,ub); p=ground(bp(x)); sh=Bd('humerus_R'); pel=Bd('pelvis')
    reach=abs(sh[1]-SH_TGT)*1.4                    # drop shoulder to reachable height (via squat)
    ba=back_angle(); lean=max(0,ba-40)*2.2        # target UPRIGHT back ~40 deg (strong)
    sh_fwd=max(0,(sh[0]-pel[0])-0.16)*3.0          # shoulder not far forward of pelvis (let protraction do it)
    head_up=max(0,(sh[1]-headY())+0.02)
    fw=foot_world(); xs=fw[:,0]; ys=fw[:,1]; xr=xs.max()-xs.min()+1e-9
    heel=ys[xs<xs.min()+0.25*xr].min(); toe=ys[xs>xs.max()-0.25*xr].min()
    bal=max(0,comX()-max(Bd('calcn_r')[0],Jt('mtp_r')[0]))+max(0,min(Bd('calcn_r')[0],Jt('mtp_r')[0])-comX())
    pen=table_pen(shin_world())+table_pen(thigh_world())   # HARD leg-table interference
    return 3*reach+lean+sh_fwd+4*head_up+10*abs(toe-heel)+8*(max(heel,toe)-FLOOR)+6*bal+0.5*pen
tb=None
for s_ in range(60):
    x0=lb+(ub-lb)*np.random.RandomState(s_).rand(6)
    rr=minimize(tobj,x0,method='Nelder-Mead',options={'maxiter':2500})
    if tb is None or rr.fun<tb.fun: tb=rr
xopt=np.clip(tb.x,lb,ub); pose=ground(bp(xopt)); realize()
print(f"BODY hip={xopt[0]:.0f} knee={xopt[1]:.0f} ankle={xopt[2]:.0f} pelvis_tilt={xopt[3]:.0f} lumbar_tot={xopt[4]:.0f} thoracic_tot={xopt[5]:.0f}")
print(f"  back_angle(visual)={back_angle():.1f} shoulderY={Bd('humerus_R')[1]:.3f}(tgt {SH_TGT:.3f}) headY-shY={headY()-Bd('humerus_R')[1]:.3f}")
# ---- arm IK to box RIGHT side face, palm -Z, fingers down ----
RC=['clav_prot_r','clav_elev_r','shoulder_elv_r','elv_angle_r','shoulder_rot_r','elbow_flexion_r','pro_sup_r','wrist_flex_r','wrist_dev_r']
alb=np.array([0,-25,0,-90,-90,0,-90,-70,-25]); aub=np.array([48,25,155,155,45,150,90,70,35])  # clav_prot 0..48, clav_elev -25..25 prepended
palmT=np.array([BCX-HALF+0.05,TOPb+GRIP_H,HALF]); tipT=np.array([BCX-HALF+0.05,TOPb+GRIP_H-0.14,HALF])
def aobj(y):
    y=np.clip(y,alb,aub); p=dict(pose)
    for k,v in zip(RC,y): p[k]=v
    setc(p); realize()
    pe=np.linalg.norm(fp(PFR['midmc'])-palmT); te=np.linalg.norm(fp(PFR['midtip'])-tipT); pn=palmR()
    hh=np.array([fp(pf) for pf in hfR]); pen=((hh[:,0]>BCX-HALF)&(hh[:,0]<BCX+HALF)&(np.abs(hh[:,2])<HALF-0.005)&(hh[:,1]>TOPb)&(hh[:,1]<TOPb+BOX)).sum()
    return pe*2+te*2+1.0*(1+pn[2])+0.03*pen
ab=None
for s_ in range(40):
    rr=minimize(aobj,alb+(aub-alb)*np.random.RandomState(s_).rand(len(RC)),method='Nelder-Mead',options={'maxiter':2500})
    if ab is None or rr.fun<ab.fun: ab=rr
for k,v in zip(RC,np.clip(ab.x,alb,aub)): pose[k]=float(v)
pose['clav_prot_l']=-pose.get('clav_prot_r',0.0); pose['clav_elev_l']=pose.get('clav_elev_r',0.0)
setc(pose); realize()
cl_r=Bd('clavicle_R'); cl_l=Bd('clavicle_L')
print(f'  clav_prot_r={pose.get("clav_prot_r",0):.0f} clav_elev_r={pose.get("clav_elev_r",0):.0f} clavR_z={cl_r[2]:.3f} clavL_z={cl_l[2]:.3f} clavR_x={cl_r[0]:.3f} clavL_x={cl_l[0]:.3f}')
pe=np.linalg.norm(fp(PFR['midmc'])-palmT)*100; te=np.linalg.norm(fp(PFR['midtip'])-tipT)*100
print(f"ARM palm_err={pe:.1f}cm tip_err={te:.1f}cm palmN={np.round(palmR(),2)}")
# neck up
best_fe=0; best_y=-9
for fe in [-40,-30,-20,0,20,30,40]:
    setc({**pose,'T1_head_neck_FE':fe}); realize()
    y=(Bd('skull') if hasskull else Bd('thoracic1'))[1]
    if y>best_y: best_y=y; best_fe=fe
pose['T1_head_neck_FE']=float(best_fe); setc(pose); realize()
# ---- final interference ----
sw=shin_world(); tw=thigh_world(); n_shin=table_pen(sw); n_thigh=table_pen(tw)
below=sw[sw[:,1]<TOPb]; gap=(EDGE-below[:,0].max())*100 if len(below) else 999
print(f"INTERF shin_pen={n_shin} thigh_pen={n_thigh} shin_gap_to_edge={gap:.1f}cm kneeX={Jt('knee_r')[0]:.3f}")
interf_ok=(n_shin==0 and n_thigh==0)
reach_ok=max(pe,te)<3.5
back_ok=back_angle()<58
print(f"VERDICT reach_ok={reach_ok} interf_ok={interf_ok} back_natural={back_ok} back={back_angle():.1f}")
# joint contribution breakdown (for report)
contrib={'thoracic_tot':round(xopt[5],1),'lumbar_tot':round(xopt[4],1),'hip':round(xopt[0],1),'knee':round(xopt[1],1),'ankle':round(xopt[2],1),'pelvis_tilt':round(xopt[3],1)}
json.dump(pose, open('/tmp/cmp_render/m1_pose.json','w'))
# ---- export frame for viz-mirror render (opaque blue table) ----
def parse_mesh_frames(p):
    root=ET.parse(p).getroot(); pm={c:par for par in root.iter() for c in par}; out=[]
    for mesh in root.iter('Mesh'):
        mf=mesh.find('mesh_file')
        if mf is None or not mf.text: continue
        base=os.path.basename(mf.text.strip()); node=mesh; fr=None
        while node in pm:
            node=pm[node]
            if node.tag in ('Body','PhysicalOffsetFrame'): fr=node.get('name'); break
        out.append((base,fr))
    return out
MF=parse_mesh_frames(P)
def side_of(fr):
    f=(fr or '').lower()
    if any(x in f for x in ('humerus_r','ulna_r','radius_r','hand_r')): return 'R'
    if any(x in f for x in ('humerus_l','ulna_l','radius_l','hand_l')): return 'L'
    return 'other'
SPINE=['il_','iliocost','longissi','ltpl','ltpt','long_col','mf_','multifidus','deepmult','supmult','ql_','ps_','semi','splen']
isS=lambda n: any(n.lower().startswith(t) or ('_'+t) in n.lower() for t in SPINE)
fm={}
for fr in model.getComponentsList():
    pf=osim.PhysicalFrame.safeDownCast(fr)
    if pf is None: continue
    T=pf.getTransformInGround(state); R=T.R(); p=T.p(); fm[pf.getName()]=([R.get(rr,cc) for rr in range(3) for cc in range(3)],[p.get(0),p.get(1),p.get(2)])
mesh_x={}; sides={}
for b,fr in MF:
    if fr in fm: mesh_x[b]={'R':fm[fr][0],'p':fm[fr][1]}; sides[b]=side_of(fr)
mus={}
for i in range(model.getMuscles().getSize()):
    nm=model.getMuscles().get(i).getName()
    if isS(nm):
        pts=model.getMuscles().get(i).getGeometryPath().getCurrentPath(state)
        mus[nm]={'pts':[[pts.get(k).getLocationInGround(state).get(j) for j in range(3)] for k in range(pts.getSize())]}
json.dump({'mesh':mesh_x,'sides':sides,'muscles':mus,
           'geo':{'edge':EDGE,'top':TOPb,'grip':[BCX,TOPb+0.15,0.0],'half':HALF},
           'diag':{'back_angle':back_angle(),'palm_err_cm':pe,'tip_err_cm':te,'shin_pen':n_shin,'thigh_pen':n_thigh,
                   'shin_gap_cm':float(gap),'contrib':contrib,'reach_ok':bool(reach_ok),'interf_ok':bool(interf_ok),'back_ok':bool(back_ok),
                   'grip_h_above_floor':float(TOPb+GRIP_H-FLOOR)}},
          open('/tmp/cmp_render/m1_frame.json','w'))
print("SAVED dist_frame.json")
