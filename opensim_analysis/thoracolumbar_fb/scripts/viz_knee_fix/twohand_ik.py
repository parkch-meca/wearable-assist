import opensim as osim, numpy as np, json
from scipy.optimize import minimize
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
model=osim.Model(P); state=model.initSystem(); cs=model.getCoordinateSet(); names=[cs.get(i).getName() for i in range(cs.getSize())]
def setc(d):
    for k,v in d.items():
        if k in names: c=cs.get(k); c.setValue(state,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def Bd(n): p=model.getBodySet().get(n).getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def Jt(j): p=model.getJointSet().get(j).getChildFrame().getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def comX(): return model.calcMassCenterPosition(state).get(0)
def realize(): model.assemble(state); model.realizePosition(state)
setc({c:0.0 for c in names}); realize(); fstand=Bd('calcn_r'); FLOOR=-0.905
# TABLE/BOX
TABLE_H=0.50; EDGE=0.18; TOP=FLOOR+TABLE_H; BOX=0.30
BOX_CX=EDGE+0.16   # box center x (slightly onto table)
GY=TOP+BOX*0.5     # grip height (box mid) = -0.255
HALF=BOX/2         # box half-width 0.15
# right hand target = right face (z=+0.15), left hand = left face (z=-0.15), same x,y
TR=np.array([BOX_CX, GY, +HALF])
TL=np.array([BOX_CX, GY, -HALF])
print(f"box center x={BOX_CX:.2f} grip y={GY:.3f}  R-face z=+{HALF}  L-face z=-{HALF}")
# DOF: hip,knee,ankle,tilt,lumbar, R(elv,ang,rot,elb), L(elv,ang,rot,elb)  -- arms independent
lb=np.array([0,-125,-20,-65,-40, 0,-90,-90,0, -155,-90,-45,0])
ub=np.array([120,0,45,0,0, 155,155,45,150, 0,155,91,150])
LUMB=['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE']
def apply(x):
    x=np.clip(x,lb,ub); pose={c:0.0 for c in names}
    pose.update({'hip_flexion_r':x[0],'hip_flexion_l':x[0],'knee_angle_r':x[1],'knee_angle_l':x[1],'ankle_angle_r':x[2],'ankle_angle_l':x[2],'pelvis_tilt':x[3],
                 'shoulder_elv_r':x[5],'elv_angle_r':x[6],'shoulder_rot_r':x[7],'elbow_flexion_r':x[8],
                 'shoulder_elv_l':x[9],'elv_angle_l':x[10],'shoulder_rot_l':x[11],'elbow_flexion_l':x[12]})
    for L in LUMB: pose[L]=x[4]/5.0
    pose['pelvis_tx']=0;pose['pelvis_ty']=0; setc(pose); realize()
    f=Bd('calcn_r'); pose['pelvis_tx']=fstand[0]-f[0]; pose['pelvis_ty']=fstand[1]-f[1]; setc(pose); realize(); return x,pose
def metrics():
    hR=Bd('hand_R'); hL=Bd('hand_L'); foot=min(Bd('calcn_r')[1],Jt('mtp_r')[1]); heel=Bd('calcn_r')[0]; toe=Jt('mtp_r')[0]; cmx=comX()
    emb=max(0,FLOOR-foot); bal=max(0,cmx-max(heel,toe))+max(0,min(heel,toe)-cmx)
    legx=max(Jt('knee_r')[0],Jt('ankle_r')[0]); interf=max(0,legx-EDGE)
    return hR,hL,emb,bal,interf
def solve():
    def obj(x):
        apply(x); hR,hL,emb,bal,interf=metrics()
        reach=np.linalg.norm(hR-TR)+np.linalg.norm(hL-TL)
        return reach+5*emb+4*bal+6*interf
    best=None
    for s in range(20):
        x0=lb+(ub-lb)*np.random.RandomState(s).rand(len(lb))
        r=minimize(obj,x0,method='Nelder-Mead',options={'maxiter':2500,'xatol':1e-2,'fatol':1e-3})
        if best is None or r.fun<best.fun: best=r
    x,pose=apply(best.x); hR,hL,emb,bal,interf=metrics()
    gR=np.linalg.norm(hR-TR); gL=np.linalg.norm(hL-TL)
    print(f"손R gap={gR*100:.1f}cm (목표{np.round(TR,2)} 실제{np.round(hR,3)})")
    print(f"손L gap={gL*100:.1f}cm (목표{np.round(TL,2)} 실제{np.round(hL,3)})")
    print(f"발매몰{emb*100:.0f}cm 균형{'OK' if bal<0.02 else 'X'} 다리침범{interf*100:.0f}cm")
    print(f"자세 hip{x[0]:.0f} knee{x[1]:.0f} tilt{x[3]:.0f} lumbar{x[4]:.0f} | R elv{x[5]:.0f}ang{x[6]:.0f}rot{x[7]:.0f}elb{x[8]:.0f} | L elv{x[9]:.0f}ang{x[10]:.0f}rot{x[11]:.0f}elb{x[12]:.0f}")
    ok = gR<0.05 and gL<0.05 and emb<0.03 and bal<0.02 and interf<0.02
    print("=>", "✅ 양손 파지 가능" if ok else "❌ 불가")
    json.dump({'pose':pose,'geo':{'edge':EDGE,'top':TOP,'grip':[BOX_CX,GY,0.0],'half':HALF},'gR':gR,'gL':gL,'hR':hR.tolist(),'hL':hL.tolist()}, open('/tmp/cmp_render/twohand_pose.json','w'))
    return ok
solve()
