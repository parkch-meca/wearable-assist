import opensim as osim, numpy as np, json, pyvista as pv, os
from scipy.optimize import minimize
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
GEO="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry"
model=osim.Model(P); state=model.initSystem(); cs=model.getCoordinateSet(); names=[cs.get(i).getName() for i in range(cs.getSize())]
# UNLOCK wrist/pronation in MEMORY only (.osim file untouched)
for n in ['pro_sup_r','wrist_flex_r','wrist_dev_r','pro_sup_l','wrist_flex_l','wrist_dev_l']: cs.get(n).setLocked(state, False)
model.assemble(state); model.realizePosition(state)
handR_fr=[pf for pf in (osim.PhysicalFrame.safeDownCast(c) for c in model.getComponentsList()) if pf and 'hand_R_geom' in pf.getName()]
handL_fr=[pf for pf in (osim.PhysicalFrame.safeDownCast(c) for c in model.getComponentsList()) if pf and ('hand_L_geom' in pf.getName() or 'hand_l_geom' in pf.getName())]
def setc(d):
    for k,v in d.items():
        if k in names: c=cs.get(k); c.setValue(state,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def Bd(n): p=model.getBodySet().get(n).getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def Jt(j): p=model.getJointSet().get(j).getChildFrame().getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def handZ(b): T=model.getBodySet().get(b).getTransformInGround(state); R=T.R(); return np.array([R.get(0,2),R.get(1,2),R.get(2,2)])
def comX(): return model.calcMassCenterPosition(state).get(0)
def realize(): model.assemble(state); model.realizePosition(state)
def frpos(pf): p=pf.getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
footloc=np.vstack([np.asarray(pv.read(os.path.join(GEO,f)).points) for f in ['foot.vtp','bofoot.vtp']])
def foot_world():
    bd=model.getBodySet().get('calcn_r'); T=bd.getTransformInGround(state); R=T.R(); p=T.p()
    Rm=np.array([[R.get(i,j) for j in range(3)] for i in range(3)]); pv_=np.array([p.get(0),p.get(1),p.get(2)]); return (Rm@footloc.T).T+pv_
setc({c:0.0 for c in names}); realize(); fstand=Bd('calcn_r'); FLOOR=-0.905
EDGE=0.18; TOPb=FLOOR+0.75; BOX=0.30; BCX=EDGE+0.16; HALF=BOX/2
TR=np.array([BCX, TOPb+0.12, +HALF]); TL=np.array([BCX, TOPb+0.12, -HALF])
LUMB=['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE']
# vars: hip,knee,ankle,tilt,lumbar, R[elv,ang,rot,elb,prosup,wflex,wdev]  (left mirrored)
lb=np.array([0,-125,-25,-65,-40,  0,-90,-90,0,-90,-70,-25]); ub=np.array([120,0,45,0,0, 155,155,45,150,90,70,35])
def apply(x):
    x=np.clip(x,lb,ub); pose={c:0.0 for c in names}
    pose.update({'hip_flexion_r':x[0],'hip_flexion_l':x[0],'knee_angle_r':x[1],'knee_angle_l':x[1],'ankle_angle_r':x[2],'ankle_angle_l':x[2],'pelvis_tilt':x[3],
                 'shoulder_elv_r':x[5],'elv_angle_r':x[6],'shoulder_rot_r':x[7],'elbow_flexion_r':x[8],'pro_sup_r':x[9],'wrist_flex_r':x[10],'wrist_dev_r':x[11],
                 'shoulder_elv_l':-x[5],'elv_angle_l':x[6],'shoulder_rot_l':-x[7],'elbow_flexion_l':x[8],'pro_sup_l':-x[9],'wrist_flex_l':x[10],'wrist_dev_l':-x[11]})
    for L in LUMB: pose[L]=x[4]/5.0
    pose['pelvis_tx']=0;pose['pelvis_ty']=0; setc(pose); realize()
    fw=foot_world(); pose['pelvis_ty']=FLOOR-fw[:,1].min(); pose['pelvis_tx']=fstand[0]-Bd('calcn_r')[0]
    setc(pose); realize(); return x,pose
def cons():
    fw=foot_world(); xs=fw[:,0]; ys=fw[:,1]; xr=xs.max()-xs.min()
    heel=ys[xs<xs.min()+0.25*xr].min(); toe=ys[xs>xs.max()-0.25*xr].min()
    tilt=abs(toe-heel); lift=max(heel,toe)-FLOOR
    hr=np.array([frpos(pf) for pf in handR_fr]); hl=np.array([frpos(pf) for pf in handL_fr])
    def pen(h):
        return ((h[:,0]>BCX-HALF)&(h[:,0]<BCX+HALF)&(h[:,2]>-HALF)&(h[:,2]<HALF)&(h[:,1]>TOPb)&(h[:,1]<TOPb+BOX)).sum()
    rR=np.min(np.linalg.norm(hr-TR,axis=1)); rL=np.min(np.linalg.norm(hl-TL,axis=1))
    # palm faces box center: right hand palm normal -> -Z (into box). reward (handZ[2] -> -1)
    palmR=handZ('hand_R')[2]; palmL=handZ('hand_L')[2]   # want palmR<0, palmL>0
    bal=max(0,comX()-max(Bd('calcn_r')[0],Jt('mtp_r')[0]))+max(0,min(Bd('calcn_r')[0],Jt('mtp_r')[0])-comX())
    interf=max(0,max(Jt('knee_r')[0],Jt('ankle_r')[0])-EDGE)
    return dict(tilt=tilt,lift=lift,penR=pen(hr),penL=pen(hl),rR=rR,rL=rL,palmR=palmR,palmL=palmL,bal=bal,interf=interf)
def obj(x):
    apply(x); g=cons()
    palm=(1+g['palmR'])+(1-g['palmL'])   # minimized when palmR=-1, palmL=+1
    return (g['rR']+g['rL'])*2 + 0.02*(g['penR']+g['penL']) + 10*g['tilt']+8*g['lift']+5*g['bal']+8*g['interf'] + 1.5*palm
best=None
for s in range(26):
    x0=lb+(ub-lb)*np.random.RandomState(s+11).rand(len(lb))
    r=minimize(obj,x0,method='Nelder-Mead',options={'maxiter':3500,'xatol':1e-2,'fatol':1e-3})
    if best is None or r.fun<best.fun: best=r
x,pose=apply(best.x); g=cons()
print("=== 손목 해제 자연 파지 ===")
print(f"  손R도달 {g['rR']*100:.1f}cm 손L도달 {g['rL']*100:.1f}cm | 관통 R{g['penR']}/L{g['penL']}정점")
print(f"  palm R {g['palmR']:.2f}(목표-1) L {g['palmL']:.2f}(목표+1) | 발평평{g['tilt']*100:.1f}/들림{g['lift']*100:.1f} 균형{g['bal']*100:.1f} 침범{g['interf']*100:.1f}")
json.dump({'pose':{k:float(v) for k,v in pose.items()},'geo':{'edge':EDGE,'top':TOPb,'grip':[BCX,TOPb+0.12,0.0],'half':HALF},'resid':{k:float(v) for k,v in g.items()}}, open('/tmp/cmp_render/wf75_pose.json','w'))
print("SAVED wf75_pose.json")
