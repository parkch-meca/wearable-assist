import opensim as osim, numpy as np, json, pyvista as pv, os
from scipy.optimize import minimize
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
GEO="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry"
model=osim.Model(P); state=model.initSystem(); cs=model.getCoordinateSet(); names=[cs.get(i).getName() for i in range(cs.getSize())]
for n in ['pro_sup_r','wrist_flex_r','wrist_dev_r','pro_sup_l','wrist_flex_l','wrist_dev_l']: cs.get(n).setLocked(state,False)
model.assemble(state); model.realizePosition(state)
comps={c.getName():c for c in (osim.PhysicalFrame.safeDownCast(x) for x in model.getComponentsList()) if c}
hf={'R':[comps[f'hand_R_geom_frame_{i}'] for i in range(1,30) if f'hand_R_geom_frame_{i}' in comps],
    'L':[comps[n] for n in comps if 'hand_L_geom' in n or 'hand_l_geom' in n]}
# palm-normal frames (R): thumb=9, pinky=13, midtip=21, midmc=11 ; mirror for L
def fname(side,i): return f'hand_{side}_geom_frame_{i}'
PF={s:{'thumb':comps.get(fname(s,9)),'pinky':comps.get(fname(s,13)),'midtip':comps.get(fname(s,21)),'midmc':comps.get(fname(s,11))} for s in ['R','L']}
def fp(pf): q=pf.getPositionInGround(state); return np.array([q.get(0),q.get(1),q.get(2)])
def palm_normal(side):
    d=fp(PF[side]['midtip'])-fp(PF[side]['midmc']); d/=np.linalg.norm(d)+1e-9
    r=fp(PF[side]['thumb'])-fp(PF[side]['pinky']); r/=np.linalg.norm(r)+1e-9
    n=-np.cross(d,r); return n/(np.linalg.norm(n)+1e-9)   # sign=-1 (실측)
def setc(d):
    for k,v in d.items():
        if k in names: c=cs.get(k); c.setValue(state,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def Bd(n): p=model.getBodySet().get(n).getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def Jt(j): p=model.getJointSet().get(j).getChildFrame().getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def comX(): return model.calcMassCenterPosition(state).get(0)
def realize(): model.assemble(state); model.realizePosition(state)
def frpos(pf): p=pf.getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
footloc=np.vstack([np.asarray(pv.read(os.path.join(GEO,f)).points) for f in ['foot.vtp','bofoot.vtp']])
def foot_world():
    bd=model.getBodySet().get('calcn_r'); T=bd.getTransformInGround(state); R=T.R(); p=T.p()
    Rm=np.array([[R.get(i,j) for j in range(3)] for i in range(3)]); pv_=np.array([p.get(0),p.get(1),p.get(2)]); return (Rm@footloc.T).T+pv_
setc({c:0.0 for c in names}); realize(); fstand=Bd('calcn_r'); FLOOR=-0.905
EDGE=0.18; TOPb=FLOOR+0.50; BOX=0.30; BCX=EDGE+0.16; HALF=BOX/2   # TABLE 50cm FIXED
TR=np.array([BCX, TOPb+0.13, +HALF]); TL=np.array([BCX, TOPb+0.13, -HALF])
LUMB=['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE']
def trunk_pose(x):
    pose={c:0.0 for c in names}
    pose.update({'hip_flexion_r':x[0],'hip_flexion_l':x[0],'knee_angle_r':x[1],'knee_angle_l':x[1],'ankle_angle_r':x[2],'ankle_angle_l':x[2],'pelvis_tilt':x[3]})
    for L in LUMB: pose[L]=x[4]/5.0
    return pose
def ground(pose):
    pose['pelvis_tx']=0;pose['pelvis_ty']=0; setc(pose); realize()
    fw=foot_world(); pose['pelvis_ty']=FLOOR-fw[:,1].min(); pose['pelvis_tx']=fstand[0]-Bd('calcn_r')[0]; setc(pose); realize(); return pose
# stage1: trunk/legs to bring shoulders over table (reduce arm reach), feet flat+behind edge, balance
tlb=np.array([0,-125,-25,-65,-40]); tub=np.array([120,0,45,0,0])
def trunk_obj(x):
    pose=ground(trunk_pose(x))
    sh=Bd('humerus_R')
    # want shoulder near box x (over table) so arms hang to box; shoulder above box height
    reach=abs(sh[0]-BCX)+abs(sh[1]-(TOPb+0.45))
    fw=foot_world(); xs=fw[:,0]; ys=fw[:,1]; xr=xs.max()-xs.min()
    heel=ys[xs<xs.min()+0.25*xr].min(); toe=ys[xs>xs.max()-0.25*xr].min()
    tilt=abs(toe-heel); lift=max(heel,toe)-FLOOR
    bal=max(0,comX()-max(Bd('calcn_r')[0],Jt('mtp_r')[0]))+max(0,min(Bd('calcn_r')[0],Jt('mtp_r')[0])-comX())
    interf=max(0,max(Jt('knee_r')[0],Jt('ankle_r')[0])-EDGE)
    return reach+10*tilt+8*lift+5*bal+8*interf
tb=None
for s in range(18):
    r=minimize(trunk_obj, tlb+(tub-tlb)*np.random.RandomState(s).rand(5),method='Nelder-Mead',options={'maxiter':1500,'xatol':1e-2,'fatol':1e-3})
    if tb is None or r.fun<tb.fun: tb=r
tpose=ground(trunk_pose(np.clip(tb.x,tlb,tub)))
print("trunk: shoulderR",np.round(Bd('humerus_R'),2),"발평평 ok")
# stage2: each arm -> hand at box side face + PALM (correct) toward center + finger wrap
def solve_arm(side):
    sgn=+1 if side=='R' else -1; T=TR if side=='R' else TL
    C=['shoulder_elv_'+side.lower(),'elv_angle_'+side.lower(),'shoulder_rot_'+side.lower(),'elbow_flexion_'+side.lower(),'pro_sup_'+side.lower(),'wrist_flex_'+side.lower(),'wrist_dev_'+side.lower()]
    if side=='R': lb=np.array([0,-90,-90,0,-90,-70,-25]); ub=np.array([155,155,45,150,90,70,35])
    else: lb=np.array([-155,-90,-45,0,-90,-70,-35]); ub=np.array([0,155,91,150,90,70,25])
    def obj(x):
        x=np.clip(x,lb,ub); p=dict(tpose)
        for k,v in zip(C,x): p[k]=v
        setc(p); realize()
        hh=np.array([frpos(pf) for pf in hf[side]]); reach=np.min(np.linalg.norm(hh-T,axis=1))
        pen=((hh[:,0]>BCX-HALF)&(hh[:,0]<BCX+HALF)&(np.abs(hh[:,2])<HALF)&(hh[:,1]>TOPb)&(hh[:,1]<TOPb+BOX)).sum()
        pn=palm_normal(side); palm=1-(-sgn)*pn[2]   # want palm normal toward center: R->-Z(pn[2]<0), L->+Z(pn[2]>0)
        return reach+0.02*pen+1.2*palm
    best=None
    for s in range(30):
        r=minimize(obj, lb+(ub-lb)*np.random.RandomState(s).rand(len(lb)),method='Nelder-Mead',options={'maxiter':2200,'xatol':1e-2,'fatol':1e-3})
        if best is None or r.fun<best.fun: best=r
    x=np.clip(best.x,lb,ub)
    for k,v in zip(C,x): tpose[k]=float(v)
    setc(tpose); realize(); hh=np.array([frpos(pf) for pf in hf[side]]); reach=np.min(np.linalg.norm(hh-T,axis=1)); pn=palm_normal(side)
    print(f"  {side}: 도달{reach*100:.1f}cm 손바닥normal{np.round(pn,2)} (중심향 목표 {'-Z' if side=='R' else '+Z'})")
solve_arm('R'); solve_arm('L')
json.dump({'pose':tpose,'geo':{'edge':EDGE,'top':TOPb,'grip':[BCX,TOPb+0.13,0.0],'half':HALF}}, open('/tmp/cmp_render/palm50_pose.json','w'))
print("SAVED palm50_pose.json")
