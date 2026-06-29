import opensim as osim, numpy as np, json, pyvista as pv, os
from scipy.optimize import minimize
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
GEO="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry"
model=osim.Model(P); state=model.initSystem(); cs=model.getCoordinateSet(); names=[cs.get(i).getName() for i in range(cs.getSize())]
handR_fr=[pf for pf in (osim.PhysicalFrame.safeDownCast(c) for c in model.getComponentsList()) if pf and 'hand_R_geom' in pf.getName()]
handL_fr=[pf for pf in (osim.PhysicalFrame.safeDownCast(c) for c in model.getComponentsList()) if pf and ('hand_L_geom' in pf.getName() or 'hand_l_geom' in pf.getName())]
def setc(d):
    for k,v in d.items():
        if k in names: c=cs.get(k); c.setValue(state,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def Bd(n): p=model.getBodySet().get(n).getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def Jt(j): p=model.getJointSet().get(j).getChildFrame().getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def handZ(b):
    T=model.getBodySet().get(b).getTransformInGround(state); R=T.R(); return np.array([R.get(0,2),R.get(1,2),R.get(2,2)])
def comX(): return model.calcMassCenterPosition(state).get(0)
def realize(): model.assemble(state); model.realizePosition(state)
def frpos(pf): p=pf.getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
footloc=np.vstack([np.asarray(pv.read(os.path.join(GEO,f)).points) for f in ['foot.vtp','bofoot.vtp']])
def foot_world():
    bd=model.getBodySet().get('calcn_r'); T=bd.getTransformInGround(state); R=T.R(); p=T.p()
    Rm=np.array([[R.get(i,j) for j in range(3)] for i in range(3)]); pv_=np.array([p.get(0),p.get(1),p.get(2)]); return (Rm@footloc.T).T+pv_
setc({c:0.0 for c in names}); realize(); fstand=Bd('calcn_r'); FLOOR=-0.905
EDGE=0.18; TABLE_H=0.50; TOPb=FLOOR+TABLE_H; BOX=0.30; BCX=EDGE+0.16; HALF=BOX/2
# METHOD 2: hands cup the box front-bottom corners, palm facing UP(+Y)
FRONT=BCX-HALF      # box front face x
BOTY=TOPb           # box bottom (on table top)
TR=np.array([FRONT+0.02, BOTY+0.02, +0.11])  # right front-bottom corner
TL=np.array([FRONT+0.02, BOTY+0.02, -0.11])
lb=np.array([0,-125,-25,-65,-40, 0,-90,-90,0, -155,-90,-45,0])
ub=np.array([120,0,45,0,0, 155,155,45,150, 0,155,91,150])
LUMB=['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE']
def apply(x):
    x=np.clip(x,lb,ub); pose={c:0.0 for c in names}
    pose.update({'hip_flexion_r':x[0],'hip_flexion_l':x[0],'knee_angle_r':x[1],'knee_angle_l':x[1],'ankle_angle_r':x[2],'ankle_angle_l':x[2],'pelvis_tilt':x[3],
                 'shoulder_elv_r':x[5],'elv_angle_r':x[6],'shoulder_rot_r':x[7],'elbow_flexion_r':x[8],
                 'shoulder_elv_l':x[9],'elv_angle_l':x[10],'shoulder_rot_l':x[11],'elbow_flexion_l':x[12]})
    for L in LUMB: pose[L]=x[4]/5.0
    pose['pelvis_tx']=0;pose['pelvis_ty']=0; setc(pose); realize()
    fw=foot_world(); pose['pelvis_ty']=FLOOR-fw[:,1].min(); pose['pelvis_tx']=fstand[0]-Bd('calcn_r')[0]
    setc(pose); realize(); return x,pose
def cons():
    fw=foot_world(); xs=fw[:,0]; ys=fw[:,1]; xr=xs.max()-xs.min()
    heel=ys[xs<xs.min()+0.25*xr].min(); toe=ys[xs>xs.max()-0.25*xr].min()
    tilt=abs(toe-heel); lift=max(heel,toe)-FLOOR
    hr=np.array([frpos(pf) for pf in handR_fr]); hl=np.array([frpos(pf) for pf in handL_fr])
    def pen(h,sign):
        inside=(h[:,0]>BCX-HALF)&(h[:,0]<BCX+HALF)&(h[:,2]>-HALF)&(h[:,2]<HALF)&(h[:,1]>TOPb)&(h[:,1]<TOPb+BOX)
        return inside.sum()
    # reach: closest hand frame to target corner
    rR=np.min(np.linalg.norm(hr-TR,axis=1)); rL=np.min(np.linalg.norm(hl-TL,axis=1))
    # palm up: handZ should point +Y (palm normal ~ handZ). reward (1 - handZ·+Y)
    puR=1-handZ('hand_R')[1]; puL=1-handZ('hand_L')[1]
    bal=max(0,comX()-max(Bd('calcn_r')[0],Jt('mtp_r')[0]))+max(0,min(Bd('calcn_r')[0],Jt('mtp_r')[0])-comX())
    interf=max(0,max(Jt('knee_r')[0],Jt('ankle_r')[0])-EDGE)
    return dict(tilt=tilt,lift=lift,penR=pen(hr,1),penL=pen(hl,-1),rR=rR,rL=rL,puR=puR,puL=puL,bal=bal,interf=interf)
def obj(x):
    apply(x); g=cons()
    return (g['rR']+g['rL'])*2+6*(g['penR']+g['penL'])*0.01+10*g['tilt']+8*g['lift']+5*g['bal']+8*g['interf']+1.2*(g['puR']+g['puL'])
best=None
for s in range(20):
    x0=lb+(ub-lb)*np.random.RandomState(s+7).rand(len(lb))
    r=minimize(obj,x0,method='Nelder-Mead',options={'maxiter':3000,'xatol':1e-2,'fatol':1e-3})
    if best is None or r.fun<best.fun: best=r
x,pose=apply(best.x); g=cons()
print("=== 방식2 바닥받침 (palm up) ===")
print(f"  손R도달 {g['rR']*100:.1f}cm 손L도달 {g['rL']*100:.1f}cm | 관통 R{g['penR']}/L{g['penL']}정점")
print(f"  palm-up R {(1-g['puR']):.2f} L {(1-g['puL']):.2f} (1=완전 위) | 발평평{g['tilt']*100:.1f}/들림{g['lift']*100:.1f} 균형{g['bal']*100:.1f} 침범{g['interf']*100:.1f}cm")
json.dump({'pose':{k:float(v) for k,v in pose.items()},'geo':{'edge':EDGE,'top':TOPb,'grip':[BCX,TOPb+0.05,0.0],'half':HALF},'resid':{k:float(v) for k,v in g.items()}}, open('/tmp/cmp_render/m2_pose.json','w'))
print("SAVED m2_pose.json")
