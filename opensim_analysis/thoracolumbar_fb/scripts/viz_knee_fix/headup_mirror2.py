import opensim as osim, numpy as np, json, pyvista as pv, os
from scipy.optimize import minimize
from xml.etree import ElementTree as ET
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
GEO="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry"
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
def foot_world():
    bd=model.getBodySet().get('calcn_r'); T=bd.getTransformInGround(state); R=T.R(); p=T.p()
    Rm=np.array([[R.get(i,j) for j in range(3)] for i in range(3)]); pv_=np.array([p.get(0),p.get(1),p.get(2)]); return (Rm@footloc.T).T+pv_
setc({c:0.0 for c in names}); realize(); fstand=Bd('calcn_r'); FLOOR=-0.905
hasskull='skull' in [model.getBodySet().get(i).getName() for i in range(model.getBodySet().getSize())]
def headY(): return Bd('skull')[1] if hasskull else Bd('thoracic1')[1]
EDGE=0.18; TOPb=FLOOR+0.50; BOX=0.30; BCX=EDGE+0.16; HALF=BOX/2
LUMB=['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE']
# STAGE1 trunk: head UP (head_y >= shoulder_y), straight spine (lumbar~0), shoulders low enough for arm to box
def tp(x):
    p={c:0.0 for c in names}; p.update({'hip_flexion_r':x[0],'hip_flexion_l':x[0],'knee_angle_r':x[1],'knee_angle_l':x[1],'ankle_angle_r':x[2],'ankle_angle_l':x[2],'pelvis_tilt':x[3]})
    for L in LUMB: p[L]=x[4]/5.0
    return p
def ground(p):
    p['pelvis_tx']=0;p['pelvis_ty']=0; setc(p); realize(); fw=foot_world(); p['pelvis_ty']=FLOOR-fw[:,1].min(); p['pelvis_tx']=fstand[0]-Bd('calcn_r')[0]; setc(p); realize(); return p
tlb=np.array([20,-55,-25,-45,-8]); tub=np.array([90,0,40,0,0])  # lumbar near 0 (straight spine)
def tobj(x):
    p=ground(tp(x)); sh=Bd('humerus_R')
    r=abs(sh[1]-(TOPb+0.35))+abs(sh[0]-0.08)        # shoulder low enough + not too forward
    head_up=max(0,(sh[1]-headY())+0.02)             # head should be >= shoulder (head_up=0 good)
    fw=foot_world(); xs=fw[:,0]; ys=fw[:,1]; xr=xs.max()-xs.min()
    heel=ys[xs<xs.min()+0.25*xr].min(); toe=ys[xs>xs.max()-0.25*xr].min()
    bal=max(0,comX()-max(Bd('calcn_r')[0],Jt('mtp_r')[0]))+max(0,min(Bd('calcn_r')[0],Jt('mtp_r')[0])-comX())
    return r+4*head_up+10*abs(toe-heel)+8*(max(heel,toe)-FLOOR)+5*bal+8*max(0,max(Jt('knee_r')[0],Jt('ankle_r')[0])-EDGE)
tb=None
for s_ in range(22):
    rr=minimize(tobj,tlb+(tub-tlb)*np.random.RandomState(s_).rand(5),method='Nelder-Mead',options={'maxiter':1500})
    if tb is None or rr.fun<tb.fun: tb=rr
tpose=ground(tp(np.clip(tb.x,tlb,tub)))
print("trunk: shoulderY",round(Bd('humerus_R')[1],2),"headY",round(headY(),2),"(head>=shoulder?)","headX",round(headY()-Bd('humerus_R')[1],2))
# STAGE2 right arm: box right-front-side, palm -Z, fingers down
RC=['shoulder_elv_r','elv_angle_r','shoulder_rot_r','elbow_flexion_r','pro_sup_r','wrist_flex_r','wrist_dev_r']
lb=np.array([0,-90,-90,0,-90,-70,-25]); ub=np.array([155,155,45,150,90,70,35])
palmT=np.array([BCX-HALF+0.05,TOPb+0.16,HALF]); tipT=np.array([BCX-HALF+0.05,TOPb+0.02,HALF])
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
for k,v in zip(RC,np.clip(ab.x,lb,ub)): tpose[k]=float(v)
setc(tpose); realize()
print("R팔: palm오차",round(np.linalg.norm(fp(PFR['midmc'])-palmT)*100,1),"손끝",round(np.linalg.norm(fp(PFR['midtip'])-tipT)*100,1),"palmN",np.round(palmR(),2))
# neck lift: choose T1_head_neck_FE sign that raises skull (look forward/up)
best_fe=0; best_y=-9
for fe in [-40,-30,-20,0,20,30,40]:
    setc({**tpose,'T1_head_neck_FE':fe}); realize()
    y=(Bd('skull') if hasskull else Bd('thoracic1'))[1]
    if y>best_y: best_y=y; best_fe=fe
tpose['T1_head_neck_FE']=float(best_fe); setc(tpose); realize()
print("neck FE=",best_fe,"skullY",round((Bd('skull') if hasskull else Bd('thoracic1'))[1],2))
json.dump(tpose, open('/tmp/cmp_render/headup_pose.json','w'))
# export with sides for viz-mirror
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
json.dump({'mesh':mesh_x,'sides':sides,'muscles':mus,'hand_R':Bd('hand_R').tolist(),'geo':{'edge':EDGE,'top':TOPb,'grip':[BCX,TOPb+0.13,0.0],'half':HALF}}, open('/tmp/cmp_render/headup_frame.json','w'))
print("SAVED headup_frame.json")
