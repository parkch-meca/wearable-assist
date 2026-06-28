import opensim as osim, numpy as np, json, pyvista as pv, os
from scipy.optimize import minimize
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
GEO="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry"
model=osim.Model(P); state=model.initSystem(); cs=model.getCoordinateSet(); names=[cs.get(i).getName() for i in range(cs.getSize())]
from xml.etree import ElementTree as ET
# collect hand frame components (PhysicalOffsetFrame) for hand_R/hand_L
comps=[]
for c in model.getComponentsList():
    pf=osim.PhysicalFrame.safeDownCast(c)
    if pf is None: continue
    nm=pf.getName()
    if 'hand_R_geom' in nm: comps.append(('R',pf))
    elif 'hand_L_geom' in nm or 'hand_l_geom' in nm: comps.append(('L',pf))
handR_fr=[pf for s,pf in comps if s=='R']; handL_fr=[pf for s,pf in comps if s=='L']
print("hand frames R/L:",len(handR_fr),len(handL_fr))
def setc(d):
    for k,v in d.items():
        if k in names: c=cs.get(k); c.setValue(state,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def Bd(n): p=model.getBodySet().get(n).getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def Jt(j): p=model.getJointSet().get(j).getChildFrame().getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def comX(): return model.calcMassCenterPosition(state).get(0)
def realize(): model.assemble(state); model.realizePosition(state)
def frpos(pf): p=pf.getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
# foot meshes local on calcn (load once)
footloc=np.vstack([np.asarray(pv.read(os.path.join(GEO,f)).points) for f in ['foot.vtp','bofoot.vtp']])
def foot_world():
    bd=model.getBodySet().get('calcn_r'); T=bd.getTransformInGround(state); R=T.R(); p=T.p()
    Rm=np.array([[R.get(i,j) for j in range(3)] for i in range(3)]); pv_=np.array([p.get(0),p.get(1),p.get(2)])
    return (Rm@footloc.T).T+pv_
setc({c:0.0 for c in names}); realize(); fstand=Bd('calcn_r'); FLOOR=-0.905
# geometry
EDGE=0.18; TABLE_H=0.50; TOPb=FLOOR+TABLE_H; BOX=0.30; BCX=EDGE+0.16; HALF=BOX/2
GY_LOW=TOPb+0.05      # grip lower-side (fingers under) ~ box bottom region
# DOF
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
    # ground by LOWEST foot point
    fw=foot_world(); low=fw[:,1].min(); pose['pelvis_ty']=FLOOR-low
    f=Bd('calcn_r'); pose['pelvis_tx']=fstand[0]-f[0]
    setc(pose); realize(); return x,pose
def constraints():
    fw=foot_world(); xs=fw[:,0]; ys=fw[:,1]; xr=xs.max()-xs.min()
    heel=ys[xs<xs.min()+0.25*xr].min(); toe=ys[xs>xs.max()-0.25*xr].min()
    foot_tilt=abs(toe-heel)                       # 0 = flat
    foot_lift=max(heel,toe)-FLOOR                  # lift of the higher contact
    # hands: frame origins
    hr=np.array([frpos(pf) for pf in handR_fr]); hl=np.array([frpos(pf) for pf in handL_fr])
    def penetration(h,side):
        inside=(h[:,0]>BCX-HALF)&(h[:,0]<BCX+HALF)&(h[:,2]>-HALF)&(h[:,2]<HALF)&(h[:,1]>TOPb)&(h[:,1]<TOPb+BOX)
        if side=='R': depth=np.where(inside,HALF-h[:,2],0)
        else: depth=np.where(inside,h[:,2]+HALF,0)
        face=HALF if side=='R' else -HALF
        contact=np.min(np.abs(h[:,2]-face)) ; reach=np.min(np.linalg.norm(h-np.array([BCX,GY_LOW,face]),axis=1))
        return inside.sum(), depth.max(), contact, reach
    nR,dR,cR,rR=penetration(hr,'R'); nL,dL,cL,rL=penetration(hl,'L')
    heelx=Bd('calcn_r')[0]; toex=Jt('mtp_r')[0]; cmx=comX()
    bal=max(0,cmx-max(heelx,toex))+max(0,min(heelx,toex)-cmx)
    legx=max(Jt('knee_r')[0],Jt('ankle_r')[0]); interf=max(0,legx-EDGE)
    return dict(foot_tilt=foot_tilt,foot_lift=foot_lift,penR=dR,penL=dL,reachR=rR,reachL=rL,bal=bal,interf=interf,nR=nR,nL=nL)
def obj(x):
    apply(x); g=constraints()
    return (g['reachR']+g['reachL'])*2 + 8*g['penR']+8*g['penL'] + 10*g['foot_tilt']+8*g['foot_lift'] + 5*g['bal']+8*g['interf']
best=None
for s in range(24):
    x0=lb+(ub-lb)*np.random.RandomState(s).rand(len(lb))
    r=minimize(obj,x0,method='Nelder-Mead',options={'maxiter':3000,'xatol':1e-2,'fatol':1e-3})
    if best is None or r.fun<best.fun: best=r
x,pose=apply(best.x); g=constraints()
print("\n=== [0단계] 전 제약 동시 만족 해 (최적점 잔차) ===")
print(f"  손R 박스도달 reach={g['reachR']*100:.1f}cm  관통깊이={g['penR']*100:.1f}cm (내부정점{g['nR']})")
print(f"  손L 박스도달 reach={g['reachL']*100:.1f}cm  관통깊이={g['penL']*100:.1f}cm (내부정점{g['nL']})")
print(f"  발 평평도 tilt={g['foot_tilt']*100:.1f}cm  발 들림 lift={g['foot_lift']*100:.1f}cm")
print(f"  균형 bal={g['bal']*100:.1f}cm  다리침범 interf={g['interf']*100:.1f}cm")
TOL=dict(reach=4,pen=1,tilt=2,lift=2,bal=1,interf=2)  # cm
ok=(g['reachR']*100<TOL['reach'] and g['reachL']*100<TOL['reach'] and g['penR']*100<TOL['pen'] and g['penL']*100<TOL['pen']
    and g['foot_tilt']*100<TOL['tilt'] and g['foot_lift']*100<TOL['lift'] and g['bal']*100<TOL['bal'] and g['interf']*100<TOL['interf'])
print(f"\n  판정: {'✅ 해 존재 (전 제약 동시 만족)' if ok else '❌ 해 없음 — 위 잔차가 큰 제약이 충돌'}")
json.dump({'pose':pose,'geo':{'edge':EDGE,'top':TOPb,'grip':[BCX,GY_LOW,0.0],'half':HALF},'resid':{k:float(v) for k,v in g.items()},'ok':bool(ok)}, open('/tmp/cmp_render/feas_pose.json','w'))
