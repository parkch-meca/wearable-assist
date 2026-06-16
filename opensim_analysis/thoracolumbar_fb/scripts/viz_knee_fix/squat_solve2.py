import opensim as osim, numpy as np
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
model=osim.Model(P); state=model.initSystem(); cs=model.getCoordinateSet()
names=[cs.get(i).getName() for i in range(cs.getSize())]
def setc(d):
    for k,v in d.items():
        if k in names:
            c=cs.get(k); c.setValue(state, (v if c.getMotionType()==2 else np.deg2rad(v)), False)
def bX(n): b=model.getBodySet().get(n); p=b.getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def jX(j): J=model.getJointSet().get(j); p=J.getChildFrame().getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def comX(): return model.calcMassCenterPosition(state).get(0)
def realize(): model.assemble(state); model.realizePosition(state)

setc({}); realize()
foot_std=-0.907; foot_cx=(bX('calcn_r')[0]+jX('mtp_r')[0])/2
print("standing foot_cx",round(foot_cx,3),"comX",round(comX(),3))

def pose(knee,hip,ankle,ptilt,pty,ptx,arm):
    setc({'knee_angle_r':knee,'knee_angle_l':knee,'hip_flexion_r':hip,'hip_flexion_l':hip,
          'ankle_angle_r':ankle,'ankle_angle_l':ankle,'pelvis_tilt':ptilt,'pelvis_ty':pty,'pelvis_tx':ptx,
          'shoulder_elv_r':arm,'shoulder_elv_l':arm,'elv_angle_r':0,'elv_angle_l':0,'elbow_flexion_r':5,'elbow_flexion_l':5})
    realize()

KNEE,HIP,PTILT,ARM=-100,95,-28,85
# 1) ankle for flat foot
best=None
for ank in np.arange(20,50,1.0):
    pose(KNEE,HIP,ank,PTILT,0,0,ARM)
    dh=bX('calcn_r')[1]-jX('mtp_r')[1]
    if best is None or abs(dh)<abs(best[1]): best=(ank,dh)
ANK=float(best[0]); print("flat ankle=",ANK,"calcnY-mtpY=",round(best[1],3))
# 2) pelvis_ty to ground foot bottom = -0.907
pose(KNEE,HIP,ANK,PTILT,0,0,ARM)
fb=min(bX('calcn_r')[1], jX('mtp_r')[1])
PTY=foot_std - fb  # vertical shift
pose(KNEE,HIP,ANK,PTILT,PTY,0,ARM)
fb2=min(bX('calcn_r')[1], jX('mtp_r')[1]); print("pelvis_ty=",round(PTY,3),"foot_bottom now",round(fb2,3))
# 3) pelvis_tx so COM over foot center
ptx=0.0
for _ in range(8):
    pose(KNEE,HIP,ANK,PTILT,PTY,ptx,ARM)
    err=comX()-((bX('calcn_r')[0]+jX('mtp_r')[0])/2)
    ptx-=err  # shift pelvis to move COM toward foot center
PTX=ptx; pose(KNEE,HIP,ANK,PTILT,PTY,PTX,ARM)
fc=(bX('calcn_r')[0]+jX('mtp_r')[0])/2
print("pelvis_tx=",round(PTX,3),"comX",round(comX(),3),"footCx",round(fc,3),"balance err",round(comX()-fc,3))
# report descent + key heights
print("pelvis descent (pelvis_ty)=",round(PTY,3))
print("hip Y",round(jX('hip_r')[1],3),"knee Y",round(jX('knee_r')[1],3),"ankle Y",round(jX('ankle_r')[1],3))
print("DEEPEST_POSE", dict(knee=KNEE,hip=HIP,ankle=ANK,ptilt=PTILT,pty=round(PTY,3),ptx=round(PTX,3),arm=ARM))
