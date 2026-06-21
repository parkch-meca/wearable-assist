import opensim as osim, numpy as np
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
model=osim.Model(P); state=model.initSystem(); cs=model.getCoordinateSet()
names=[cs.get(i).getName() for i in range(cs.getSize())]
def setc(d):
    for k,v in d.items():
        if k in names: c=cs.get(k); c.setValue(state,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def B(n): p=model.getBodySet().get(n).getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def J(j): p=model.getJointSet().get(j).getChildFrame().getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def comX(): return model.calcMassCenterPosition(state).get(0)
def realize(): model.assemble(state); model.realizePosition(state)

# TABLE/BOX geometry
FLOOR=-0.905; TABLE_H=0.50; BOX=0.30
table_top=FLOOR+TABLE_H            # -0.405
box_cy=table_top+BOX/2             # -0.255 (box center height)
BOX_CX=0.42                        # box center in front
hand_target=np.array([BOX_CX-0.02, box_cy, 0.13])  # grasp side, near box
print(f"table_top={table_top:.3f} box_center_y={box_cy:.3f} box_cx={BOX_CX} hand_target={hand_target}")

setc({c:0.0 for c in names}); realize()
fstand=B('calcn_r'); hand_std=B('hand_R')
print("standing calcn",np.round(fstand,3)," hand_R",np.round(hand_std,3))

# shallow posture for table-height lift
LOW={'knee_angle_r':-35,'knee_angle_l':-35,'hip_flexion_r':50,'hip_flexion_l':50,
     'ankle_angle_r':12,'ankle_angle_l':12,'pelvis_tilt':-18}
def base_pose(arm_elv,elbow,extra=None):
    pose={c:0.0 for c in names}; pose.update(LOW)
    pose['shoulder_elv_r']=arm_elv; pose['shoulder_elv_l']=arm_elv
    pose['elv_angle_r']=90; pose['elv_angle_l']=90
    pose['elbow_flexion_r']=elbow; pose['elbow_flexion_l']=elbow
    if extra: pose.update(extra)
    return pose
def ground_and_set(pose):
    pose['pelvis_tx']=0; pose['pelvis_ty']=0; setc(pose); realize()
    f=B('calcn_r'); pose['pelvis_tx']=fstand[0]-f[0]; pose['pelvis_ty']=fstand[1]-f[1]
    setc(pose); realize(); return pose

# search shoulder_elv + elbow to reach hand_target (y,x)
best=None
for elv in np.arange(40,95,3.0):
    for elb in np.arange(10,80,5.0):
        pose=ground_and_set(base_pose(elv,elb))
        h=B('hand_R'); err=np.linalg.norm(h[:2]-hand_target[:2])  # match x,y
        if best is None or err<best[0]: best=(err,elv,elb,h.copy(),pose)
err,elv,elb,h,pose=best
print(f"best arm: shoulder_elv={elv:.0f} elbow={elb:.0f}  hand_R={np.round(h,3)}  target={np.round(hand_target,3)}  err={err:.3f}")
# final pose metrics
setc(pose); realize()
foot=min(B('calcn_r')[1], J('mtp_r')[1]); heel=B('calcn_r')[0]; toe=J('mtp_r')[0]
print(f"foot_bottom={foot:.3f} (지면 {FLOOR})  COMx={comX():.3f}  foot[{heel:.3f},{toe:.3f}] in_base={min(heel,toe)<comX()<max(heel,toe)}")
print(f"hand-box vertical gap={h[1]-box_cy:+.3f} m  hand-box horiz gap={h[0]-BOX_CX:+.3f} m")
print("DEEPEST", {k:round(v,3) for k,v in pose.items() if abs(v)>1e-6})
