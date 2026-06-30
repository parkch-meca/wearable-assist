import opensim as osim, numpy as np, json, pyvista as pv, os
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
OUT="/data/stoop_motion/table_box_lift_v2.mot"
grasp=json.load(open('headup_pose.json'))  # PASS pose (right arm correct; left will be viz-mirrored)
m=osim.Model(P); state=m.initSystem(); cs=m.getCoordinateSet(); coords=[cs.get(i).getName() for i in range(cs.getSize())]
for n in ['pro_sup_r','wrist_flex_r','wrist_dev_r']: cs.get(n).setLocked(state,False)
LUMB=['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE']
TRUNK=['hip_flexion_r','hip_flexion_l','knee_angle_r','knee_angle_l','ankle_angle_r','ankle_angle_l','pelvis_tilt','T1_head_neck_FE']+LUMB
FLOOR=-0.905
footloc=np.vstack([np.asarray(pv.read(os.path.join('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry',f)).points) for f in ['foot.vtp','bofoot.vtp']])
def setc(d):
    for k,v in d.items():
        if k in coords: c=cs.get(k); c.setValue(state,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def lowest_foot():
    bd=m.getBodySet().get('calcn_r'); T=bd.getTransformInGround(state); R=T.R(); p=T.p()
    Rm=np.array([[R.get(i,j) for j in range(3)] for i in range(3)]); pv_=np.array([p.get(0),p.get(1),p.get(2)]); return ((Rm@footloc.T).T+pv_)[:,1].min()
def calcnx():
    p=m.getBodySet().get('calcn_r').getPositionInGround(state); return p.get(0)
setc({c:0.0 for c in coords}); m.assemble(state); m.realizePosition(state); fstand_x=calcnx()
P_stand={c:0.0 for c in coords}
P_grasp={c:grasp.get(c,0.0) for c in coords}
P_lift=dict(P_grasp)
for k in ['hip_flexion_r','hip_flexion_l','knee_angle_r','knee_angle_l','ankle_angle_r','ankle_angle_l','pelvis_tilt']+LUMB: P_lift[k]=P_grasp.get(k,0.0)*0.85  # partial straighten -> box rises
FPS=30; T=5.0; n=int(T*FPS)+1; ts=np.linspace(0,T,n)
def sm(a): return a*a*(3-2*a)
def kp(t):
    if t<0.5: return P_stand
    if t<2.0: a=sm((t-0.5)/1.5); return {c:(1-a)*P_stand[c]+a*P_grasp[c] for c in coords}
    if t<2.4: return P_grasp
    if t<3.0: a=sm((t-2.4)/0.6); return {c:(1-a)*P_grasp[c]+a*P_lift[c] for c in coords}
    if t<3.6: return P_lift
    if t<5.0: a=sm((t-3.6)/1.4); return {c:(1-a)*P_lift[c]+a*P_stand[c] for c in coords}
    return P_stand
rows=[]
for t in ts:
    pose=dict(kp(t)); pose['pelvis_tx']=0; pose['pelvis_ty']=0
    setc(pose); m.assemble(state); m.realizePosition(state)
    pose['pelvis_ty']=FLOOR-lowest_foot()
    setc(pose); m.assemble(state); m.realizePosition(state)
    pose['pelvis_tx']=fstand_x-calcnx()
    rows.append([t]+[pose[c] for c in coords])
rows=np.array(rows)
hdr=["table_box_lift_v2","version=1",f"nRows={n}",f"nColumns={len(coords)+1}","inDegrees=yes","","Units are S.I. units (second, meters, Newtons, ...)","endheader"]
with open(OUT,"w") as f:
    f.write("\n".join(hdr)+"\n"); f.write("time\t"+"\t".join(coords)+"\n")
    for r in rows: f.write("\t".join(f"{x:.6f}" for x in r)+"\n")
print("WROTE",OUT,"rows",n)
