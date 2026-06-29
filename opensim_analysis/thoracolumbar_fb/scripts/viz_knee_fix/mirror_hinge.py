import opensim as osim, numpy as np, json, pyvista as pv, os
from scipy.optimize import minimize
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
GEO="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry"
model=osim.Model(P); state=model.initSystem(); cs=model.getCoordinateSet(); names=[cs.get(i).getName() for i in range(cs.getSize())]
for n in ['pro_sup_r','wrist_flex_r','wrist_dev_r','pro_sup_l','wrist_flex_l','wrist_dev_l']: cs.get(n).setLocked(state,False)
model.assemble(state); model.realizePosition(state)
comps={c.getName():c for c in (osim.PhysicalFrame.safeDownCast(x) for x in model.getComponentsList()) if c}
hfR=[comps[f'hand_R_geom_frame_{i}'] for i in range(1,30) if f'hand_R_geom_frame_{i}' in comps]
PFR={'thumb':comps.get('hand_R_geom_frame_9'),'pinky':comps.get('hand_R_geom_frame_13'),'midtip':comps.get('hand_R_geom_frame_21'),'midmc':comps.get('hand_R_geom_frame_11')}
def fp(pf): q=pf.getPositionInGround(state); return np.array([q.get(0),q.get(1),q.get(2)])
def palmN():
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
EDGE=0.18; TOPb=FLOOR+0.50; BOX=0.30; BCX=EDGE+0.16; HALF=BOX/2
LUMB=['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE']
# stage1: hip-hinge trunk — hip flexion big, LUMBAR ~0 (straight spine, head up), knee moderate
def tp(x):
    p={c:0.0 for c in names}; p.update({'hip_flexion_r':x[0],'hip_flexion_l':x[0],'knee_angle_r':x[1],'knee_angle_l':x[1],'ankle_angle_r':x[2],'ankle_angle_l':x[2],'pelvis_tilt':x[3]})
    for L in LUMB: p[L]=x[4]/5.0
    return p
def ground(p):
    p['pelvis_tx']=0;p['pelvis_ty']=0; setc(p); realize(); fw=foot_world(); p['pelvis_ty']=FLOOR-fw[:,1].min(); p['pelvis_tx']=fstand[0]-Bd('calcn_r')[0]; setc(p); realize(); return p
tlb=np.array([20,-70,-25,-60,-8]); tub=np.array([100,0,40,0,0])   # lumbar limited to [-8,0] = near-straight spine
def tobj(x):
    p=ground(tp(x)); sh=Bd('humerus_R'); head=Bd('skull') if 'skull' in [model.getBodySet().get(i).getName() for i in range(model.getBodySet().getSize())] else Bd('thoracic1')
    # shoulder low enough to let arms reach box grip(-0.255) but head must stay UP (above shoulder)
    r=abs(sh[1]-(TOPb+0.30))+abs(sh[0]-0.12)
    head_low=max(0,(sh[1])-head[1]+0.10)   # head should be ABOVE shoulder (head_y>sh_y)
    fw=foot_world(); xs=fw[:,0]; ys=fw[:,1]; xr=xs.max()-xs.min()
    heel=ys[xs<xs.min()+0.25*xr].min(); toe=ys[xs>xs.max()-0.25*xr].min()
    bal=max(0,comX()-max(Bd('calcn_r')[0],Jt('mtp_r')[0]))+max(0,min(Bd('calcn_r')[0],Jt('mtp_r')[0])-comX())
    return r+3*head_low+10*abs(toe-heel)+8*(max(heel,toe)-FLOOR)+5*bal+8*max(0,max(Jt('knee_r')[0],Jt('ankle_r')[0])-EDGE)
tb=None
for s_ in range(20):
    r=minimize(tobj,tlb+(tub-tlb)*np.random.RandomState(s_).rand(5),method='Nelder-Mead',options={'maxiter':1500,'xatol':1e-2,'fatol':1e-3})
    if tb is None or r.fun<tb.fun: tb=r
tpose=ground(tp(np.clip(tb.x,tlb,tub)))
print("trunk shoulderR",np.round(Bd('humerus_R'),2),"skull/thx Y",round((Bd('skull') if 'skull' in [model.getBodySet().get(i).getName() for i in range(model.getBodySet().getSize())] else Bd('thoracic1'))[1],2))
# stage2: RIGHT arm to box side, palm in, fingers down
RC=['shoulder_elv_r','elv_angle_r','shoulder_rot_r','elbow_flexion_r','pro_sup_r','wrist_flex_r','wrist_dev_r']
lb=np.array([0,-90,-90,0,-90,-70,-25]); ub=np.array([155,155,45,150,90,70,35])
palmT=np.array([BCX-HALF+0.05,TOPb+0.16,HALF]); tipT=np.array([BCX-HALF+0.05,TOPb+0.02,HALF])
def aobj(x):
    x=np.clip(x,lb,ub); p=dict(tpose)
    for k,v in zip(RC,x): p[k]=v
    setc(p); realize()
    pe=np.linalg.norm(fp(PFR['midmc'])-palmT); te=np.linalg.norm(fp(PFR['midtip'])-tipT)
    pn=palmN(); palm=1+pn[2]  # palm normal -> -Z
    hh=np.array([fp(pf) for pf in hfR]); pen=((hh[:,0]>BCX-HALF)&(hh[:,0]<BCX+HALF)&(np.abs(hh[:,2])<HALF-0.005)&(hh[:,1]>TOPb)&(hh[:,1]<TOPb+BOX)).sum()
    return pe*2+te*2+1.0*palm+0.03*pen
ab=None
for s_ in range(34):
    r=minimize(aobj,lb+(ub-lb)*np.random.RandomState(s_).rand(len(lb)),method='Nelder-Mead',options={'maxiter':2500,'xatol':1e-2,'fatol':1e-3})
    if ab is None or r.fun<ab.fun: ab=r
xr=np.clip(ab.x,lb,ub)
for k,v in zip(RC,xr): tpose[k]=float(v)
setc(tpose); realize()
print("R팔: palm오차",round(np.linalg.norm(fp(PFR['midmc'])-palmT)*100,1),"손끝",round(np.linalg.norm(fp(PFR['midtip'])-tipT)*100,1),"palmN",np.round(palmN(),2))
# mirror to LEFT (signs all +1, validated earlier)
rvals=[np.rad2deg(cs.get(c).getValue(state)) for c in RC]
LC=['shoulder_elv_l','elv_angle_l','shoulder_rot_l','elbow_flexion_l','pro_sup_l','wrist_flex_l','wrist_dev_l']
for c,rv in zip(LC,rvals): tpose[c]=float(rv)
setc(tpose); realize()
print("최종 handR",np.round(Bd('hand_R'),3),"handL",np.round(Bd('hand_L'),3))
json.dump({'pose':tpose,'geo':{'edge':EDGE,'top':TOPb,'grip':[BCX,TOPb+0.13,0.0],'half':HALF}}, open('/tmp/cmp_render/hinge_pose.json','w'))
print("SAVED hinge_pose.json")
