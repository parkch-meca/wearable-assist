"""Fix the left-arm joint axis defect: shoulder_L (3 coord axes) + radius_hand_l wrist (2 coord axes)
were bit-identical copies of the right (not mirrored). Apply the sagittal mirror rule (-ax,-ay,az)
validated against the already-correct elbow_l/radioulnar_l. Only <axis> vectors change — mesh, muscle
attachments, mass all already mirrored. Writes _M1scap_armfix.osim, verifies symmetry + invariants."""
import re, numpy as np, opensim as osim
SRC="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap.osim"
DST="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim"
xml=open(SRC).read()
# 5 defective coordinate axes (bit-identical to right) -> mirror (-ax,-ay,az)
FIX={
 '-0.99826000000000004 0.0023 0.058897999999999999':'0.99826000000000004 -0.0023 0.058897999999999999',  # shoulder_elv_l
 '0.0047999999999999996 0.99909000000000003 0.0424':'-0.0047999999999999996 -0.99909000000000003 0.0424', # shoulder_rot_l
 '0.0047999999999999996 0.0424 0.99909000000000003':'-0.0047999999999999996 -0.0424 0.99909000000000003', # elv_angle_l
 '-0.81906000000000001 -0.13561000000000001 -0.55744000000000005':'0.81906000000000001 0.13561000000000001 -0.55744000000000005', # wrist_dev_l
 '0.95643 -0.25220999999999999 0.14710000000000001':'-0.95643 0.25220999999999999 0.14710000000000001',   # wrist_flex_l
}
new=xml
for jn in ['shoulder_L','radius_hand_l']:
    mblk=re.search(rf'(<CustomJoint name="{jn}">.*?</CustomJoint>)', new, re.S); blk=mblk.group(1); nb=blk
    for k,v in FIX.items(): nb=nb.replace(k,v)
    assert nb!=blk, f"no change in {jn}"; new=new.replace(blk,nb)
# sterL_clavL_jnt (M1-added left clavicle): axes bit-identical to right -> mirror clav_prot [0 1 0]->[0 -1 0], clav_elev [1 0 0]->[-1 0 0]
mclav=re.search(r'(<CustomJoint name="sterL_clavL_jnt">.*?</CustomJoint>)', new, re.S); cblk=mclav.group(1)
ncb=cblk.replace('<axis>0 1 0</axis>','<axis>0 -1 0</axis>',1).replace('<axis>1 0 0</axis>','<axis>-1 0 0</axis>',1)
assert ncb!=cblk, "no change in sterL_clavL_jnt"; new=new.replace(cblk,ncb)
# note: right-arm blocks legitimately keep the original axis strings (that's correct) -> no global count assert
open(DST,'w').write(new); print("WROTE",DST)

def load(p): m=osim.Model(p); s=m.initSystem(); return m,s
def setpose(m,s,pose):
    cs=m.getCoordinateSet()
    for c,v in pose.items():
        if cs.contains(c): cc=cs.get(c); cc.setValue(s,(np.deg2rad(v) if cc.getMotionType()!=2 else v),False)
    m.assemble(s); m.realizePosition(s)
def bpos(m,s,b): p=m.getBodySet().get(b).getPositionInGround(s); return np.array([p.get(0),p.get(1),p.get(2)])
mf,sf=load(DST); md,sd=load(SRC)
# ---- symmetry check: left arm at pose X should = z-mirror of right arm at same pose ----
print("\n=== 좌우 대칭 검증 (수정 모델: 왼손 vs 오른손 z-미러) ===")
tests=[{'shoulder_elv_l':73,'elv_angle_l':90},{'shoulder_elv_l':45,'shoulder_rot_l':30,'elv_angle_l':60,'elbow_flexion_l':40,'wrist_flex_l':20,'wrist_dev_l':15},
       {'shoulder_elv_l':85,'elv_angle_l':90,'pro_sup_l':-30},
       {'clav_prot_l':20,'clav_elev_l':10,'shoulder_elv_l':60,'elv_angle_l':70}]  # clavicle driven (walking prereq)
maxerr=0
for t in tests:
    setpose(mf,sf,t); hl=bpos(mf,sf,'hand_L')
    tr={c.replace('_l','_r'):v for c,v in t.items()}; setpose(mf,sf,tr); hr=bpos(mf,sf,'hand_R')
    err=np.linalg.norm(hl-np.array([hr[0],hr[1],-hr[2]]))*100; maxerr=max(maxerr,err)
    print(f"  pose {list(t.items())[:2]}...: hand_L vs 오른손 z-미러 오차={err:.2f}cm")
    # reset
    setpose(mf,sf,{c:0 for c in list(t)+list(tr)})
print(f"  >>> MAX 대칭 오차 = {maxerr:.2f}cm  ({'PASS <0.1cm' if maxerr<0.1 else 'CHECK'})")
# ---- invariants: mass, COM (neutral), muscle count unchanged ----
def totmass(m): return sum(m.getBodySet().get(i).getMass() for i in range(m.getBodySet().getSize()))
setpose(md,sd,{}); setpose(mf,sf,{})
comd=md.calcMassCenterPosition(sd); comf=mf.calcMassCenterPosition(sf)
print("\n=== 불변 확인 (수정 전 vs 후) ===")
print(f"  총질량: {totmass(md):.3f} vs {totmass(mf):.3f} kg  ({'동일' if abs(totmass(md)-totmass(mf))<1e-6 else 'DIFF'})")
print(f"  중립 COM: [{comd.get(0):.4f},{comd.get(1):.4f},{comd.get(2):.4f}] vs [{comf.get(0):.4f},{comf.get(1):.4f},{comf.get(2):.4f}]")
print(f"  근육수: {md.getMuscles().getSize()} vs {mf.getMuscles().getSize()}  좌표수: {md.getCoordinateSet().getSize()} vs {mf.getCoordinateSet().getSize()}")
# neutral-pose left hand identical (coord 0 -> axis irrelevant -> same)
setpose(md,sd,{}); setpose(mf,sf,{})
print(f"  중립 왼손 위치 동일?: 오차={np.linalg.norm(bpos(md,sd,'hand_L')-bpos(mf,sf,'hand_L'))*100:.3f}cm (0이어야=정지분석 무영향)")
