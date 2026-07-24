"""Re-solve ONLY the grasp arm with a NEUTRAL-WRIST preference (palm direction via pro_sup,
wrist_flex/dev minimized). Body pose is loaded fixed from m1_pose.json (spine unchanged ->
SO/ES stay valid). Keeps palm on the box side face + palm facing -z + fingers down + elbow down.
Writes updated m1_pose.json (arm only). Prints before/after wrist angles + palm check."""
import opensim as osim, numpy as np, json, os
from scipy.optimize import minimize
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap.osim"
POSE='/tmp/cmp_render/m1_pose.json'
m=osim.Model(P); state=m.initSystem(); cs=m.getCoordinateSet(); names=[cs.get(i).getName() for i in range(cs.getSize())]
for n in ['pro_sup_r','wrist_flex_r','wrist_dev_r']: cs.get(n).setLocked(state,False)
comps={c.getName():c for c in (osim.PhysicalFrame.safeDownCast(x) for x in m.getComponentsList()) if c}
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
def Jt(j): p=m.getJointSet().get(j).getChildFrame().getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def Bd(n): p=m.getBodySet().get(n).getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def realize(): m.assemble(state); m.realizePosition(state)
FLOOR=-0.905; EDGE=0.18; TOPb=FLOOR+0.30; BOX=0.30; BCX=EDGE+0.16; HALF=BOX/2; GRIP_H=0.16
palmT=np.array([BCX-HALF+0.05,TOPb+GRIP_H,HALF]); tipT=np.array([BCX-HALF+0.05,TOPb+GRIP_H-0.14,HALF])
pose=json.load(open(POSE)); setc(pose); realize()
print("BEFORE  wrist_flex=%.0f wrist_dev=%.0f pro_sup=%.0f  palm_err=%.1fcm palmN=%s"%(
    np.degrees(cs.get('wrist_flex_r').getValue(state)),np.degrees(cs.get('wrist_dev_r').getValue(state)),
    np.degrees(cs.get('pro_sup_r').getValue(state)),np.linalg.norm(fp(PFR['midmc'])-palmT)*100,np.round(palmR(),2)))
# re-solve arm: same reach/palm/elbow constraints + NEUTRAL WRIST penalty (flex,dev->0; pro_sup free for palm dir)
RC=['clav_prot_r','clav_elev_r','shoulder_elv_r','elv_angle_r','shoulder_rot_r','elbow_flexion_r','pro_sup_r','wrist_flex_r','wrist_dev_r']
lb=np.array([0,-25,0,-90,-90,0,-90,-30,-20]); ub=np.array([48,25,155,155,45,150,90,30,20])  # wrist_flex/dev tight -30..30
x0=np.array([pose.get(k,0.0) for k in RC])
def aobj(y):
    y=np.clip(y,lb,ub); p=dict(pose)
    for k,v in zip(RC,y): p[k]=v
    setc(p); realize()
    pe=np.linalg.norm(fp(PFR['midmc'])-palmT); te=np.linalg.norm(fp(PFR['midtip'])-tipT); pn=palmR()
    hh=np.array([fp(pf) for pf in hfR]); pen=((hh[:,0]>BCX-HALF)&(hh[:,0]<BCX+HALF)&(np.abs(hh[:,2])<HALF-0.005)&(hh[:,1]>TOPb)&(hh[:,1]<TOPb+BOX)).sum()
    elb=Jt('elbow'); sh=Bd('humerus_R')
    elbow_high=max(0,elb[1]-(sh[1]-0.16)); elbow_out=max(0,elb[2]-(sh[2]+0.03))
    wrist_neutral=(y[7]**2+y[8]**2)/500.0   # minimize wrist_flex^2+wrist_dev^2 (deg) -> near-straight wrist
    return pe*2+te*2+1.0*(1+pn[2])+0.03*pen+3.5*elbow_high+3.5*elbow_out+wrist_neutral
best=None
for s_ in range(60):
    x=x0 if s_==0 else lb+(ub-lb)*np.random.RandomState(s_).rand(len(RC))
    rr=minimize(aobj,x,method='Nelder-Mead',options={'maxiter':3000})
    if best is None or rr.fun<best.fun: best=rr
y=np.clip(best.x,lb,ub)
for k,v in zip(RC,y): pose[k]=float(v)
pose['clav_prot_l']=-pose.get('clav_prot_r',0.0); pose['clav_elev_l']=pose.get('clav_elev_r',0.0)
setc(pose); realize()
pe=np.linalg.norm(fp(PFR['midmc'])-palmT)*100; te=np.linalg.norm(fp(PFR['midtip'])-tipT)*100
print("AFTER   wrist_flex=%.0f wrist_dev=%.0f pro_sup=%.0f  palm_err=%.1fcm tip=%.1fcm palmN=%s"%(
    y[7],y[8],y[6],pe,te,np.round(palmR(),2)))
json.dump(pose, open(POSE,'w'))
print("SAVED updated m1_pose.json (body/spine unchanged, arm wrist neutralized)")
