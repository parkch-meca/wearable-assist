"""Box-lift motion from the COMPLETED stoop grasp (M1 model). 5 s:
stand -> stoop reach -> grasp -> lift (partial straighten, box rises) -> hold -> return.
Arms (shoulder/elbow/clav protraction) stay at grasp config so hands keep the box;
only trunk/legs straighten on lift -> box rises with the shoulders. Foot-anchored + FK pelvis."""
import opensim as osim, numpy as np, json, pyvista as pv, os
from scipy.optimize import minimize
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap.osim"
GEO="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry"
OUT="/data/stoop_motion/box_stoop_lift_m1.mot"
grasp=json.load(open('/tmp/cmp_render/m1_pose.json'))
m=osim.Model(P); state=m.initSystem(); cs=m.getCoordinateSet(); coords=[cs.get(i).getName() for i in range(cs.getSize())]
for n in ['pro_sup_r','wrist_flex_r','wrist_dev_r']: cs.get(n).setLocked(state,False)
LUMB=['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE']
THOR=['T12_L1_FE','T11_T12_FE','T10_T11_FE','T9_T10_FE','T8_T9_FE','T7_T8_FE','T6_T7_FE','T5_T6_FE','T4_T5_FE','T3_T4_FE','T2_T3_FE','T1_T2_FE']
# joints that STRAIGHTEN on lift (trunk+legs); arms(shoulder/elbow/clav/wrist) stay fixed to hold box
STRAIGHTEN=['hip_flexion_r','hip_flexion_l','knee_angle_r','knee_angle_l','ankle_angle_r','ankle_angle_l','pelvis_tilt']+LUMB+THOR
FLOOR=-0.905
footloc=np.vstack([np.asarray(pv.read(os.path.join(GEO,f)).points) for f in ['foot.vtp','bofoot.vtp']])
def setc(d):
    for k,v in d.items():
        if k in coords: c=cs.get(k); c.setValue(state,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def lowest_foot():
    bd=m.getBodySet().get('calcn_r'); T=bd.getTransformInGround(state); R=T.R(); p=T.p()
    Rm=np.array([[R.get(i,j) for j in range(3)] for i in range(3)]); pv_=np.array([p.get(0),p.get(1),p.get(2)]); return ((Rm@footloc.T).T+pv_)[:,1].min()
def calcnx(): p=m.getBodySet().get('calcn_r').getPositionInGround(state); return p.get(0)
setc({c:0.0 for c in coords}); m.assemble(state); m.realizePosition(state); fstand_x=calcnx()
P_stand={c:0.0 for c in coords}
P_grasp={c:grasp.get(c,0.0) for c in coords}
# P_lift: box just OFF the table (still stooped, body straightens only ~15%)
P_lift=dict(P_grasp)
for k in STRAIGHTEN: P_lift[k]=P_grasp.get(k,0.0)*0.85
# P_carry: stand up + hold box in front at waist (re-solve arm so box comes IN to body, not forward)
comps={c.getName():c for c in (osim.PhysicalFrame.safeDownCast(x) for x in m.getComponentsList()) if c}
PFR={'thumb':comps['hand_R_geom_frame_9'],'pinky':comps['hand_R_geom_frame_13'],'midtip':comps['hand_R_geom_frame_21'],'midmc':comps['hand_R_geom_frame_11']}
def fpp(pf): q=pf.getPositionInGround(state); return np.array([q.get(0),q.get(1),q.get(2)])
def palmN():
    d=fpp(PFR['midtip'])-fpp(PFR['midmc']); d/=np.linalg.norm(d)+1e-9
    r=fpp(PFR['thumb'])-fpp(PFR['pinky']); r/=np.linalg.norm(r)+1e-9
    nn=-np.cross(d,r); return nn/(np.linalg.norm(nn)+1e-9)
P_carry=dict(P_grasp)
for k in STRAIGHTEN: P_carry[k]=P_grasp.get(k,0.0)*0.08   # clearly upright standing
setc(P_carry); m.assemble(state); m.realizePosition(state)
pelx=m.getBodySet().get('pelvis').getPositionInGround(state).get(0)
# carry: box in FRONT of body at waist; hand grips right side (z=+0.15)
carry_hand=np.array([pelx+0.24, FLOOR+0.78, 0.15])
RC=['clav_prot_r','clav_elev_r','shoulder_elv_r','elv_angle_r','shoulder_rot_r','elbow_flexion_r']
rlb=np.array([0,-25,0,-90,-90,20]); rub=np.array([30,25,120,120,45,140])
def carryobj(y):
    y=np.clip(y,rlb,rub); p=dict(P_carry)
    for k,v in zip(RC,y): p[k]=v
    setc(p); m.assemble(state); m.realizePosition(state)
    he=np.linalg.norm(fpp(PFR['midmc'])-carry_hand); pn=palmN()
    elb=m.getJointSet().get('elbow').getChildFrame().getPositionInGround(state); elb=np.array([elb.get(0),elb.get(1),elb.get(2)])
    sh=m.getBodySet().get('humerus_R').getPositionInGround(state); sh=np.array([sh.get(0),sh.get(1),sh.get(2)])
    elbow_out=max(0,elb[2]-(sh[2]+0.03))
    return he*2+1.0*(1+pn[2])+2.5*elbow_out
cb=None
for s_ in range(30):
    rr=minimize(carryobj,rlb+(rub-rlb)*np.random.RandomState(s_).rand(len(RC)),method='Nelder-Mead',options={'maxiter':1800})
    if cb is None or rr.fun<cb.fun: cb=rr
for k,v in zip(RC,np.clip(cb.x,rlb,rub)): P_carry[k]=float(v)
P_carry['clav_prot_l']=-P_carry.get('clav_prot_r',0.0); P_carry['clav_elev_l']=P_carry.get('clav_elev_r',0.0)
setc(P_carry); m.assemble(state); m.realizePosition(state)
print(f"CARRY hand_err={np.linalg.norm(fpp(PFR['midmc'])-carry_hand)*100:.1f}cm  box_front={pelx+0.24:.2f}")
FPS=30; T=7.5; n=int(T*FPS)+1; ts=np.linspace(0,T,n)
def sm(a): return a*a*(3-2*a)
def kp(t):
    # full cycle, GENTLE transitions (no fast-return acceleration artifact). Total 7.0s.
    if t<0.4: return P_stand
    if t<1.9: a=sm((t-0.4)/1.5); return {c:(1-a)*P_stand[c]+a*P_grasp[c] for c in coords}   # reach to box(on table)
    if t<2.3: return P_grasp                                                                  # grasp hold
    if t<3.6: a=sm((t-2.3)/1.3); return {c:(1-a)*P_grasp[c]+a*P_carry[c] for c in coords}      # stand up, box rises
    if t<4.5: return P_carry                                                                   # carry hold
    if t<6.0: a=sm((t-4.5)/1.5); return {c:(1-a)*P_carry[c]+a*P_grasp[c] for c in coords}       # lower box back (1.5s)
    if t<7.5: a=sm((t-6.0)/1.5); return {c:(1-a)*P_grasp[c]+a*P_stand[c] for c in coords}       # release + stand (1.5s, = descent, no spike)
    return P_stand
rows=[]
# wrist orientation gate: neutral during approach/departure, grasp orientation only while gripping
# (avoids the unnatural wrist roll when interpolating wrist_flex/dev from 0 on a swinging arm)
WRIST=[c for c in ['pro_sup_r','wrist_flex_r','wrist_dev_r','pro_sup_l','wrist_flex_l','wrist_dev_l'] if c in coords]
def wrist_alpha(t):
    if t<1.4: return 0.0
    if t<1.9: return sm((t-1.4)/0.5)     # orient wrist as hand nears box
    if t<6.0: return 1.0                  # gripping
    if t<6.5: return sm((6.5-t)/0.5)      # release -> neutral
    return 0.0
for t in ts:
    pose=dict(kp(t)); pose['pelvis_tx']=0; pose['pelvis_ty']=0
    wa=wrist_alpha(t)
    for w in WRIST: pose[w]=P_grasp.get(w,0.0)*wa   # gate wrist to grasp orientation only while gripping
    setc(pose); m.assemble(state); m.realizePosition(state)
    pose['pelvis_ty']=FLOOR-lowest_foot()
    setc(pose); m.assemble(state); m.realizePosition(state)
    pose['pelvis_tx']=fstand_x-calcnx()
    rows.append([t]+[pose[c] for c in coords])
rows=np.array(rows)
hdr=["box_stoop_lift_m1","version=1",f"nRows={n}",f"nColumns={len(coords)+1}","inDegrees=yes","","Units are S.I. units (second, meters, Newtons, ...)","endheader"]
with open(OUT,"w") as f:
    f.write("\n".join(hdr)+"\n"); f.write("time\t"+"\t".join(coords)+"\n")
    for r in rows: f.write("\t".join(f"{x:.6f}" for x in r)+"\n")
print("WROTE",OUT,"rows",n,"coords",len(coords))
# quick per-frame sanity: foot y min and pelvis over key frames
for tt in [0.0,1.5,2.3,3.0,3.5,4.0,4.5]:
    i=int(round(tt*FPS)); pose={coords[j]:rows[i,1+j] for j in range(len(coords))}
    setc(pose); m.assemble(state); m.realizePosition(state)
    fy=lowest_foot(); px=m.getBodySet().get('pelvis').getPositionInGround(state).get(0)
    hy=fpp(PFR['midmc'])[1]; hx=fpp(PFR['midmc'])[0]
    print(f"  t={tt:.1f} foot_y={fy:.3f} pelvis_x={px:+.3f} hand=({hx:+.3f},{hy:+.3f})  box_h_above_table={(hy-0.01)-(FLOOR+0.30):.2f}m")
