import opensim as osim, numpy as np, json, pyvista as pv, os
from scipy.optimize import minimize
from xml.etree import ElementTree as ET
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
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
# --- mesh point clouds in body-local frame for interference / floor contact ---
footloc=np.vstack([np.asarray(pv.read(os.path.join(GEO,f)).points) for f in ['foot.vtp','bofoot.vtp']])
shinloc=np.vstack([np.asarray(pv.read(os.path.join(GEO,f)).points) for f in ['tibia_r.vtp','fibula_r.vtp']])
def body_world(bname,loc):
    bd=model.getBodySet().get(bname); T=bd.getTransformInGround(state); R=T.R(); p=T.p()
    Rm=np.array([[R.get(i,j) for j in range(3)] for i in range(3)]); pv_=np.array([p.get(0),p.get(1),p.get(2)]); return (Rm@loc.T).T+pv_
def foot_world(): return body_world('calcn_r',footloc)
def shin_world(): return body_world('tibia_r',shinloc)
setc({c:0.0 for c in names}); realize(); fstand=Bd('calcn_r'); FLOOR=-0.905
hasskull='skull' in [model.getBodySet().get(i).getName() for i in range(model.getBodySet().getSize())]
def headY(): return Bd('skull')[1] if hasskull else Bd('thoracic1')[1]
# ================= SCENE: 30 cm table + 30 cm box (USER-CONFIRMED) =================
EDGE=0.18; TABLE_H=0.30; TOPb=FLOOR+TABLE_H; BOX=0.30; BCX=EDGE+0.16; HALF=BOX/2
# grip point ~ box side vertical middle = TOPb + BOX/2 = FLOOR+0.45
LUMB=['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE']
print(f"SCENE table_h={TABLE_H} TOPb={TOPb:.3f} box_top={TOPb+BOX:.3f} grip_y={TOPb+HALF:.3f} (={TOPb+HALF-FLOOR:.3f} m above floor)")

def tp(x):
    p={c:0.0 for c in names}; p.update({'hip_flexion_r':x[0],'hip_flexion_l':x[0],'knee_angle_r':x[1],'knee_angle_l':x[1],'ankle_angle_r':x[2],'ankle_angle_l':x[2],'pelvis_tilt':x[3]})
    for L in LUMB: p[L]=x[4]/5.0
    return p
def ground(p):
    p['pelvis_tx']=0;p['pelvis_ty']=0; setc(p); realize(); fw=foot_world(); p['pelvis_ty']=FLOOR-fw[:,1].min(); p['pelvis_tx']=fstand[0]-Bd('calcn_r')[0]; setc(p); realize(); return p
def trunk_angle():
    hip=Jt('hip_r'); sh=Bd('humerus_R'); v=sh-hip
    return np.degrees(np.arctan2(np.hypot(v[0],v[2]),max(v[1],1e-6)))
# semi-squat lift: deeper knee allowed so pelvis+shoulder drop (drop body, not only fold trunk)
tlb=np.array([20,-80,-25,-60,-12]); tub=np.array([110,0,40,0,0])
def tobj(x,TSH):
    # TSH = target shoulder height (so arm can reach grip); trunk angle kept in natural 42-58 band
    p=ground(tp(x)); ta=trunk_angle(); sh=Bd('humerus_R')
    reach=abs(sh[1]-TSH)                             # lower shoulder to reachable height
    ang=max(0,42-ta)+max(0,ta-58)                    # keep trunk lean natural (40-55 area)
    fwd=max(0,sh[0]-0.14)                            # shoulder not dumped too far forward
    head_up=max(0,(sh[1]-headY())+0.02)              # head at/above shoulder
    fw=foot_world(); xs=fw[:,0]; ys=fw[:,1]; xr=xs.max()-xs.min()+1e-9
    heel=ys[xs<xs.min()+0.25*xr].min(); toe=ys[xs>xs.max()-0.25*xr].min()
    bal=max(0,comX()-max(Bd('calcn_r')[0],Jt('mtp_r')[0]))+max(0,min(Bd('calcn_r')[0],Jt('mtp_r')[0])-comX())
    knee_edge=8*max(0,max(Jt('knee_r')[0],Jt('ankle_r')[0])-EDGE)
    return 3*reach+0.6*ang+2*fwd+4*head_up+10*abs(toe-heel)+8*(max(heel,toe)-FLOOR)+6*bal+knee_edge

# right-arm IK: reach box RIGHT side face, palm facing -Z (into box side), fingers down
RC=['shoulder_elv_r','elv_angle_r','shoulder_rot_r','elbow_flexion_r','pro_sup_r','wrist_flex_r','wrist_dev_r']
lb=np.array([0,-90,-90,0,-90,-70,-25]); ub=np.array([155,155,45,150,90,70,35])
# GRIP_Y: side-face grip height above table top. 0.16=mid-side(45cm), 0.24=upper-side(54cm, less fold)
GRIP_H=float(os.environ.get('GRIP_H','0.16'))
palmT=np.array([BCX-HALF+0.05,TOPb+GRIP_H,HALF]); tipT=np.array([BCX-HALF+0.05,TOPb+GRIP_H-0.14,HALF])
def arm_reach(tpose):
    def aobj(x):
        x=np.clip(x,lb,ub); p=dict(tpose)
        for k,v in zip(RC,x): p[k]=v
        setc(p); realize()
        pe=np.linalg.norm(fp(PFR['midmc'])-palmT); te=np.linalg.norm(fp(PFR['midtip'])-tipT); pn=palmR()
        hh=np.array([fp(pf) for pf in hfR]); pen=((hh[:,0]>BCX-HALF)&(hh[:,0]<BCX+HALF)&(np.abs(hh[:,2])<HALF-0.005)&(hh[:,1]>TOPb)&(hh[:,1]<TOPb+BOX)).sum()
        return pe*2+te*2+1.0*(1+pn[2])+0.03*pen
    ab=None
    for s_ in range(34):
        rr=minimize(aobj,lb+(ub-lb)*np.random.RandomState(s_).rand(7),method='Nelder-Mead',options={'maxiter':2500})
        if ab is None or rr.fun<ab.fun: ab=rr
    return np.clip(ab.x,lb,ub)

# ===== semi-squat: drop shoulder to reachable height, keep trunk lean natural, arm IK reaches box =====
# grip at TOPb+0.16 (-0.445); reachable shoulder ~ grip + 0.45 (arm span) -> sweep candidate heights
GRIPY=TOPb+GRIP_H
best=None
for TSH in [GRIPY+0.50, GRIPY+0.44, GRIPY+0.38, GRIPY+0.32]:
    tb=None
    for s_ in range(20):
        rr=minimize(lambda x:tobj(x,TSH),tlb+(tub-tlb)*np.random.RandomState(int(s_+TSH*100)%10000).rand(5),method='Nelder-Mead',options={'maxiter':1600})
        if tb is None or rr.fun<tb.fun: tb=rr
    tpose=ground(tp(np.clip(tb.x,tlb,tub))); ta=trunk_angle()
    armx=arm_reach(tpose)
    for k,v in zip(RC,armx): tpose[k]=float(v)
    setc(tpose); realize()
    pe=np.linalg.norm(fp(PFR['midmc'])-palmT)*100; te=np.linalg.norm(fp(PFR['midtip'])-tipT)*100
    knee=np.degrees(cs.get('knee_angle_r').getValue(state)); pt=np.degrees(cs.get('pelvis_tilt').getValue(state))
    print(f"  TSH={TSH:.3f} trunk_ang={ta:.1f} shY={Bd('humerus_R')[1]:.3f} knee={knee:.0f} pelvis_tilt={pt:.0f} palm_err={pe:.1f}cm tip_err={te:.1f}cm palmN={np.round(palmR(),2)}")
    rec=dict(pose=dict(tpose),ta=ta,pe=pe,te=te,palmN=palmR().tolist())
    # prefer MOST NATURAL (smallest trunk lean) among candidates that reach (max(palm,tip)<=4.5cm);
    # fall back to smallest reach error if none reach
    reach_ok=max(pe,te)<=4.5
    if best is None: best=rec
    else:
        best_ok=max(best['pe'],best['te'])<=4.5
        if reach_ok and not best_ok: best=rec
        elif reach_ok and best_ok and ta<best['ta']: best=rec
        elif (not reach_ok) and (not best_ok) and max(pe,te)<max(best['pe'],best['te']): best=rec
tpose=best['pose']; setc(tpose); realize()
print(f"CHOSEN trunk_ang={best['ta']:.1f} palm_err={best['pe']:.1f}cm tip_err={best['te']:.1f}cm")

# neck lift: raise skull (look forward/up)
best_fe=0; best_y=-9
for fe in [-40,-30,-20,0,20,30,40]:
    setc({**tpose,'T1_head_neck_FE':fe}); realize()
    y=(Bd('skull') if hasskull else Bd('thoracic1'))[1]
    if y>best_y: best_y=y; best_fe=fe
tpose['T1_head_neck_FE']=float(best_fe); setc(tpose); realize()
print("neck FE=",best_fe,"skullY",round((Bd('skull') if hasskull else Bd('thoracic1'))[1],2))

# ===== LEG-TABLE INTERFERENCE CHECK (30 cm table) =====
sw=shin_world()  # right shin points in ground
# table slab: x in [EDGE, EDGE+0.55], y in [FLOOR, TOPb], |z| in [0,0.45]
inside=(sw[:,0]>EDGE)&(sw[:,0]<EDGE+0.55)&(sw[:,1]>FLOOR)&(sw[:,1]<TOPb)&(np.abs(sw[:,2])<0.45)
n_pen=int(inside.sum())
# nearest approach in x among shin points that are below table top (potential collision band)
below=sw[sw[:,1]<TOPb]
gap_x=(EDGE-below[:,0].max())*100 if len(below) else 999.0   # +: shin behind edge (clear), -: penetrating
kneeX=Jt('knee_r')[0]; ankleX=Jt('ankle_r')[0]; kneeY=Jt('knee_r')[1]
print(f"INTERF shin_pts_in_table={n_pen} shin_maxX={sw[:,0].max():.3f} kneeX={kneeX:.3f} kneeY={kneeY:.3f}(={kneeY-FLOOR:.2f}m) ankleX={ankleX:.3f} EDGE={EDGE} gap_to_edge={gap_x:.1f}cm")
interf_ok = (n_pen==0)

json.dump(tpose, open('/tmp/cmp_render/headup_pose.json','w'))

# ===== export frame for viz-mirror render =====
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
        mus[nm]={'pts':[[pts.get(k).getLocationInGround(state).get(j) for j in range(3)] for k in range(pts.getSize())],'off':0,'on':0}
json.dump({'mesh':mesh_x,'sides':sides,'muscles':mus,'hand_R':Bd('hand_R').tolist(),
           'geo':{'edge':EDGE,'top':TOPb,'grip':[BCX,TOPb+0.15,0.0],'half':HALF},
           'diag':{'trunk_ang':best['ta'],'palm_err_cm':best['pe'],'tip_err_cm':best['te'],
                   'shin_pen':n_pen,'gap_to_edge_cm':gap_x,'kneeX':kneeX,'interf_ok':interf_ok,
                   'grip_above_floor':TOPb+HALF-FLOOR}},
          open('/tmp/cmp_render/headup_frame.json','w'))
print("SAVED headup_frame.json  interf_ok=",interf_ok,"palm_reach_ok=",best['pe']<3.0)
