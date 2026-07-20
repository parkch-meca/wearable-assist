"""VIZ-ONLY scapula-protraction prototype (NO .osim change).
Natural semi-stoop trunk (biomech ref 8.4). Arm reaches as far as it can toward box
side (falls short by ~D). Export a per-side SHIFT vector = (box_target - hand); render
translates the arm chain (clavicle+scapula+humerus+ulna+radius+hand) by SHIFT to mimic
scapular protraction. Quantitative model unchanged (render-only)."""
import opensim as osim, numpy as np, json, pyvista as pv, os
from scipy.optimize import minimize
from xml.etree import ElementTree as ET
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
GEO="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry"
model=osim.Model(P); state=model.initSystem(); cs=model.getCoordinateSet(); names=[cs.get(i).getName() for i in range(cs.getSize())]
for n in ['pro_sup_r','wrist_flex_r','wrist_dev_r']: cs.get(n).setLocked(state,False)
model.assemble(state); model.realizePosition(state)
comps={c.getName():c for c in (osim.PhysicalFrame.safeDownCast(x) for x in model.getComponentsList()) if c}
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
def realize(): model.assemble(state); model.realizePosition(state)
footloc=np.vstack([np.asarray(pv.read(os.path.join(GEO,f)).points) for f in ['foot.vtp','bofoot.vtp']])
def foot_world():
    bd=model.getBodySet().get('calcn_r'); T=bd.getTransformInGround(state); R=T.R(); p=T.p()
    Rm=np.array([[R.get(i,j) for j in range(3)] for i in range(3)]); pv_=np.array([p.get(0),p.get(1),p.get(2)]); return (Rm@footloc.T).T+pv_
setc({c:0.0 for c in names}); realize(); fstand=Bd('calcn_r'); FLOOR=-0.905
hasskull='skull' in [model.getBodySet().get(i).getName() for i in range(model.getBodySet().getSize())]
EDGE=0.18; TABLE_H=0.30; TOPb=FLOOR+TABLE_H; BOX=0.30; BCX=EDGE+0.16; HALF=BOX/2
LUMB=['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE']
# ===== NATURAL semi-stoop from biomech ref box_grasp_low_table.md 8.4 =====
NAT={'pelvis_tilt':-22.0,'hip_flexion_r':52.0,'hip_flexion_l':52.0,'knee_angle_r':-20.0,'knee_angle_l':-20.0,
     'ankle_angle_r':-7.0,'ankle_angle_l':-7.0}
for L in LUMB: NAT[L]=-5.5
pose={c:0.0 for c in names}; pose.update(NAT)
def ground(p):
    p['pelvis_tx']=0;p['pelvis_ty']=0; setc(p); realize(); fw=foot_world(); p['pelvis_ty']=FLOOR-fw[:,1].min(); p['pelvis_tx']=fstand[0]-Bd('calcn_r')[0]; setc(p); realize(); return p
pose=ground(pose)
def trunk_angle():
    from numpy import arctan2,hypot,degrees
    hip=model.getJointSet().get('hip_r').getChildFrame().getPositionInGround(state); hip=np.array([hip.get(0),hip.get(1),hip.get(2)])
    sh=Bd('humerus_R'); v=sh-hip; return degrees(arctan2(hypot(v[0],v[2]),max(v[1],1e-6)))
print(f"NATURAL trunk_ang={trunk_angle():.1f} shoulderY={Bd('humerus_R')[1]:.3f}")
# arm best-effort reach toward box right side (will fall short at natural trunk)
RC=['shoulder_elv_r','elv_angle_r','shoulder_rot_r','elbow_flexion_r','pro_sup_r','wrist_flex_r','wrist_dev_r']
lb=np.array([0,-90,-90,0,-90,-70,-25]); ub=np.array([155,155,45,150,90,70,35])
GRIP_H=float(os.environ.get('GRIP_H','0.16'))
palmT=np.array([BCX-HALF+0.05,TOPb+GRIP_H,HALF]); tipT=np.array([BCX-HALF+0.05,TOPb+GRIP_H-0.14,HALF])
def aobj(x):
    x=np.clip(x,lb,ub); p=dict(pose)
    for k,v in zip(RC,x): p[k]=v
    setc(p); realize()
    pe=np.linalg.norm(fp(PFR['midmc'])-palmT); te=np.linalg.norm(fp(PFR['midtip'])-tipT); pn=palmR()
    return pe*2+te*2+1.0*(1+pn[2])
ab=None
for s_ in range(40):
    rr=minimize(aobj,lb+(ub-lb)*np.random.RandomState(s_).rand(7),method='Nelder-Mead',options={'maxiter':2500})
    if ab is None or rr.fun<ab.fun: ab=rr
for k,v in zip(RC,np.clip(ab.x,lb,ub)): pose[k]=float(v)
setc(pose); realize()
hand=fp(PFR['midmc']); shift=palmT-hand   # viz shift to close gap (protraction mimic)
print(f"arm best reach: hand={np.round(hand,3)} target={np.round(palmT,3)} shortfall={np.linalg.norm(shift)*100:.1f}cm shift={np.round(shift,3)}")
# neck up
best_fe=0; best_y=-9
for fe in [-40,-30,-20,0,20,30,40]:
    setc({**pose,'T1_head_neck_FE':fe}); realize()
    y=(Bd('skull') if hasskull else Bd('thoracic1'))[1]
    if y>best_y: best_y=y; best_fe=fe
pose['T1_head_neck_FE']=float(best_fe); setc(pose); realize()
# ===== export frame with arm-chain SHIFT (both sides, z-mirrored for L) =====
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
    if any(x in f for x in ('clavicle_r','scapula_r','humerus_r','ulna_r','radius_r','hand_r')): return 'R'
    if any(x in f for x in ('clavicle_l','scapula_l','humerus_l','ulna_l','radius_l','hand_l')): return 'L'
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
           'arm_shift':shift.tolist(),
           'diag':{'trunk_ang':trunk_angle(),'shortfall_cm':float(np.linalg.norm(shift)*100),'grip_h':GRIP_H}},
          open('/tmp/cmp_render/vizproto_frame.json','w'))
print("SAVED vizproto_frame.json  arm_shift=",np.round(shift,3))
