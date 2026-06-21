import opensim as osim, numpy as np
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
model=osim.Model(P); state=model.initSystem(); cs=model.getCoordinateSet(); names=[cs.get(i).getName() for i in range(cs.getSize())]
def setc(d):
    for k,v in d.items():
        if k in names: c=cs.get(k); c.setValue(state,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def B(n): p=model.getBodySet().get(n).getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def Jt(j): p=model.getJointSet().get(j).getChildFrame().getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def comX(): return model.calcMassCenterPosition(state).get(0)
def realize(): model.assemble(state); model.realizePosition(state)
setc({c:0.0 for c in names}); realize(); fstand=B('calcn_r')
FLOOR=-0.905; BOX=0.30; BOX_CX=0.40

def solve(table_h):
    box_top=FLOOR+table_h+BOX        # box sits on table
    box_grip_y=FLOOR+table_h+BOX*0.5 # grasp box mid-height
    target=np.array([BOX_CX-0.03, box_grip_y, 0.13])
    best=None
    for hip in np.arange(20,95,5.0):
      for elv in np.arange(15,75,5.0):
        tilt=-hip*0.45
        pose={c:0.0 for c in names}
        pose.update({'hip_flexion_r':hip,'hip_flexion_l':hip,'knee_angle_r':-30,'knee_angle_l':-30,
                     'ankle_angle_r':14,'ankle_angle_l':14,'pelvis_tilt':tilt,
                     'shoulder_elv_r':elv,'shoulder_elv_l':elv,'elv_angle_r':90,'elv_angle_l':90,'elbow_flexion_r':40,'elbow_flexion_l':40})
        pose['pelvis_tx']=0;pose['pelvis_ty']=0; setc(pose); realize()
        f=B('calcn_r'); pose['pelvis_tx']=fstand[0]-f[0]; pose['pelvis_ty']=fstand[1]-f[1]; setc(pose); realize()
        h=B('hand_R'); err=np.linalg.norm(h[:2]-target[:2])
        if best is None or err<best[0]: best=(err,hip,elv,tilt,h.copy(),target.copy(),pose)
    err,hip,elv,tilt,h,target,pose=best
    setc(pose); realize()
    foot=min(B('calcn_r')[1],Jt('mtp_r')[1]); heel=B('calcn_r')[0]; toe=Jt('mtp_r')[0]; cmx=comX()
    inbase=min(heel,toe)<cmx<max(heel,toe)
    print(f"table {table_h*100:.0f}cm: hip{hip:.0f} elv{elv:.0f} tilt{tilt:.0f} | hand-box err={err*100:.0f}cm (dy={h[1]-target[1]:+.2f} dx={h[0]-target[0]:+.2f}) | foot {foot:.3f}(접지{abs(foot-FLOOR)*100:.0f}cm오차) | COM in_base={inbase}")
    return best
for th in [0.50,0.65,0.75]:
    solve(th)
