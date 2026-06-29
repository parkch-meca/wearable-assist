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
def fn(side,i): return comps.get(f'hand_{side}_geom_frame_{i}')
PFR={s:{'thumb':fn(s,9),'pinky':fn(s,13),'midtip':fn(s,21),'midmc':fn(s,11)} for s in ['R','L']}
def fp(pf): q=pf.getPositionInGround(state); return np.array([q.get(0),q.get(1),q.get(2)])
def palmN(side):
    d=fp(PFR[side]['midtip'])-fp(PFR[side]['midmc']); d/=np.linalg.norm(d)+1e-9
    r=fp(PFR[side]['thumb'])-fp(PFR[side]['pinky']); r/=np.linalg.norm(r)+1e-9
    n=-np.cross(d,r); return n/(np.linalg.norm(n)+1e-9)
def fingerDir(side):
    d=fp(PFR[side]['midtip'])-fp(PFR[side]['midmc']); return d/(np.linalg.norm(d)+1e-9)
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
# stage1 trunk: shoulders ABOVE-BEHIND box (not over it) so arms reach forward-down (no akimbo)
def trunk_pose(x):
    p={c:0.0 for c in names}; p.update({'hip_flexion_r':x[0],'hip_flexion_l':x[0],'knee_angle_r':x[1],'knee_angle_l':x[1],'ankle_angle_r':x[2],'ankle_angle_l':x[2],'pelvis_tilt':x[3]})
    for L in LUMB: p[L]=x[4]/5.0
    return p
def ground(p):
    p['pelvis_tx']=0;p['pelvis_ty']=0; setc(p); realize(); fw=foot_world(); p['pelvis_ty']=FLOOR-fw[:,1].min(); p['pelvis_tx']=fstand[0]-Bd('calcn_r')[0]; setc(p); realize(); return p
tlb=np.array([0,-60,-25,-55,-30]); tub=np.array([95,0,40,0,0])   # moderate stoop, limited knee
def tobj(x):
    p=ground(trunk_pose(x)); sh=Bd('humerus_R')
    # shoulder behind box front (x ~ 0.05) and above box top (y ~ box_top+0.30)
    r=abs(sh[0]-0.05)+abs(sh[1]-(TOPb+0.40))
    fw=foot_world(); xs=fw[:,0]; ys=fw[:,1]; xr=xs.max()-xs.min()
    heel=ys[xs<xs.min()+0.25*xr].min(); toe=ys[xs>xs.max()-0.25*xr].min()
    bal=max(0,comX()-max(Bd('calcn_r')[0],Jt('mtp_r')[0]))+max(0,min(Bd('calcn_r')[0],Jt('mtp_r')[0])-comX())
    return r+10*abs(toe-heel)+8*(max(heel,toe)-FLOOR)+5*bal+8*max(0,max(Jt('knee_r')[0],Jt('ankle_r')[0])-EDGE)
_tb=None
for s_ in range(16):
    r=minimize(tobj, tlb+(tub-tlb)*np.random.RandomState(s_).rand(5),method='Nelder-Mead',options={'maxiter':1400,'xatol':1e-2,'fatol':1e-3})
    if _tb is None or r.fun<_tb.fun: _tb=r
tpose=ground(trunk_pose(np.clip(_tb.x,tlb,tub)))
print("trunk shoulderR",np.round(Bd('humerus_R'),2))
def solve_arm(side):
    sgn=+1 if side=='R' else -1
    palmT=np.array([BCX-HALF+0.04, TOPb+0.16, sgn*HALF])   # palm at FRONT-side, upper
    tipT =np.array([BCX-HALF+0.04, TOPb+0.02, sgn*HALF])   # fingertip FRONT-side, lower
    C=['shoulder_elv_'+side.lower(),'elv_angle_'+side.lower(),'shoulder_rot_'+side.lower(),'elbow_flexion_'+side.lower(),'pro_sup_'+side.lower(),'wrist_flex_'+side.lower(),'wrist_dev_'+side.lower()]
    if side=='R': lb=np.array([0,-90,-90,0,-90,-70,-25]); ub=np.array([155,155,45,150,90,70,35])
    else: lb=np.array([-155,-90,-45,0,-90,-70,-35]); ub=np.array([0,155,91,150,90,70,25])
    def obj(x):
        x=np.clip(x,lb,ub); p=dict(tpose)
        for k,v in zip(C,x): p[k]=v
        setc(p); realize()
        palm_err=np.linalg.norm(fp(PFR[side]['midmc'])-palmT)
        tip_err =np.linalg.norm(fp(PFR[side]['midtip'])-tipT)
        pn=palmN(side); palm=1-(-sgn)*pn[2]      # palm normal toward center (R:-Z,L:+Z)
        hh=np.array([fp(pf) for pf in hf[side]])
        pen=((hh[:,0]>BCX-HALF)&(hh[:,0]<BCX+HALF)&(np.abs(hh[:,2])<HALF-0.005)&(hh[:,1]>TOPb)&(hh[:,1]<TOPb+BOX)).sum()
        return palm_err*2 + tip_err*2 + 1.0*palm + 0.03*pen
    best=None
    for s in range(34):
        r=minimize(obj, lb+(ub-lb)*np.random.RandomState(s).rand(len(lb)),method='Nelder-Mead',options={'maxiter':2500,'xatol':1e-2,'fatol':1e-3})
        if best is None or r.fun<best.fun: best=r
    x=np.clip(best.x,lb,ub)
    for k,v in zip(C,x): tpose[k]=float(v)
    setc(tpose); realize()
    pe=np.linalg.norm(fp(PFR[side]['midmc'])-palmT); te=np.linalg.norm(fp(PFR[side]['midtip'])-tipT); pn=palmN(side); fd=fingerDir(side)
    print(f"  {side}: palm중심오차{pe*100:.1f} 손끝오차{te*100:.1f} 손바닥normal{np.round(pn,2)} 손가락방향{np.round(fd,2)}(아래-Y 기대)")
solve_arm('R'); solve_arm('L')
json.dump({'pose':tpose,'geo':{'edge':EDGE,'top':TOPb,'grip':[BCX,TOPb+0.13,0.0],'half':HALF}}, open('/tmp/cmp_render/wrap50_pose.json','w'))
print("SAVED wrap50_pose.json")
