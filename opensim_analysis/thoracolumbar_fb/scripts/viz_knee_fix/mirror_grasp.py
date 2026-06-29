import opensim as osim, numpy as np, json, itertools
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
model=osim.Model(P); state=model.initSystem(); cs=model.getCoordinateSet(); names=[cs.get(i).getName() for i in range(cs.getSize())]
for n in ['pro_sup_r','wrist_flex_r','wrist_dev_r','pro_sup_l','wrist_flex_l','wrist_dev_l']: cs.get(n).setLocked(state,False)
model.assemble(state); model.realizePosition(state)
def setc(d):
    for k,v in d.items():
        if k in names: c=cs.get(k); c.setValue(state,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def realize(): model.assemble(state); model.realizePosition(state)
def hand(b): p=model.getBodySet().get(b).getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
# load the pose where RIGHT arm was natural (palm50)
D=json.load(open('/tmp/cmp_render/palm50_pose.json')); pose=dict(D['pose']); geo=D['geo']
# enforce sagittal symmetry of trunk/legs (zero asymmetric pelvis dofs)
for k in ['pelvis_rotation','pelvis_list','pelvis_tz']:
    if k in pose: pose[k]=0.0
setc(pose); realize()
hR=hand('hand_R');
print("RIGHT hand (natural):",np.round(hR,3))
RC=['shoulder_elv_r','elv_angle_r','shoulder_rot_r','elbow_flexion_r','pro_sup_r','wrist_flex_r','wrist_dev_r']
LC=['shoulder_elv_l','elv_angle_l','shoulder_rot_l','elbow_flexion_l','pro_sup_l','wrist_flex_l','wrist_dev_l']
rvals=[np.rad2deg(cs.get(c).getValue(state)) for c in RC]
print("RIGHT arm deg:",[round(v,1) for v in rvals])
target_L=np.array([hR[0],hR[1],-hR[2]])  # mirror of right hand across sagittal (z->-z)
# brute force mirror signs (each coord +1/-1), pick combo giving left hand closest to target_L within joint ranges
best=None
for signs in itertools.product([1,-1],repeat=7):
    p=dict(pose)
    ok=True
    for c,s,rv in zip(LC,signs,rvals):
        v=s*rv; cc=cs.get(c)
        lo,hi=np.rad2deg([cc.getRangeMin(),cc.getRangeMax()])
        if v<lo-1 or v>hi+1: ok=False; break
        p[c]=np.deg2rad(v) if cc.getMotionType()!=2 else v
    if not ok: continue
    for k,v in p.items():
        if k in names: cs.get(k).setValue(state,(v if cs.get(k).getMotionType()==2 else (v)),False) if False else cs.get(k).setValue(state, v if cs.get(k).getMotionType()==2 else v, False)
    # simpler: set via setc with deg conversion
    setc({**pose, **{c:s*rv for c,s,rv in zip(LC,signs,rvals)}}); realize()
    hL=hand('hand_L'); err=np.linalg.norm(hL-target_L)
    if best is None or err<best[0]: best=(err,signs,hL.copy())
err,signs,hL=best
print("best mirror signs:",signs,"-> left hand",np.round(hL,3),"target",np.round(target_L,3),"err",round(err*100,1),"cm")
# apply
final=dict(pose)
for c,s,rv in zip(LC,signs,rvals): final[c]=s*rv
setc(final); realize()
print("최종: handR",np.round(hand('hand_R'),3),"handL",np.round(hand('hand_L'),3))
json.dump({'pose':final,'geo':geo,'mirror_signs':list(signs)}, open('/tmp/cmp_render/mirror_pose.json','w'))
print("SAVED mirror_pose.json")
