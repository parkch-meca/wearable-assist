import opensim as osim, numpy as np
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
OUT="/data/stoop_motion/squat_synthetic_v1.mot"
model=osim.Model(P); state=model.initSystem(); cs=model.getCoordinateSet()
coords=[cs.get(i).getName() for i in range(cs.getSize())]
def setc(d):
    for k,v in d.items():
        if k in coords:
            c=cs.get(k); c.setValue(state,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def calcn():  # right foot heel pos (ground)
    p=model.getBodySet().get('calcn_r').getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])

TARGET={'knee_angle_r':-100,'knee_angle_l':-100,'hip_flexion_r':95,'hip_flexion_l':95,
        'ankle_angle_r':34,'ankle_angle_l':34,'pelvis_tilt':-28,
        'shoulder_elv_r':85,'shoulder_elv_l':85,'elv_angle_r':90,'elv_angle_l':90,
        'elbow_flexion_r':5,'elbow_flexion_l':5}
# standing foot reference
setc({c:0.0 for c in coords}); model.assemble(state); model.realizePosition(state)
fstand=calcn(); print("standing calcn",np.round(fstand,3))

FPS=30; T=5.0; n=int(T*FPS)+1; ts=np.linspace(0,T,n)
def amp(t):
    if t<0.5: return 0.0
    if t<2.0: x=(t-0.5)/1.5; return x*x*(3-2*x)
    if t<3.0: return 1.0
    if t<4.5: x=(t-3.0)/1.5; return 1-(x*x*(3-2*x))
    return 0.0

rows=[]
for t in ts:
    a=amp(t)
    pose={c:0.0 for c in coords}
    for k,v in TARGET.items(): pose[k]=v*a
    # foot-planting: solve pelvis_tx/ty so calcn stays at standing pos (rigid shift)
    pose['pelvis_tx']=0.0; pose['pelvis_ty']=0.0
    setc(pose); model.assemble(state); model.realizePosition(state)
    f=calcn()
    pose['pelvis_tx']=fstand[0]-f[0]
    pose['pelvis_ty']=fstand[1]-f[1]
    setc(pose); model.assemble(state); model.realizePosition(state)
    # build row in deg/m
    row=[t]
    for c in coords:
        v=pose[c]
        row.append(v)
    rows.append(row)
rows=np.array(rows)
hdr=["squat_synthetic_v1","version=1",f"nRows={n}",f"nColumns={len(coords)+1}","inDegrees=yes",
     "","Units are S.I. units (second, meters, Newtons, ...)","endheader"]
with open(OUT,"w") as f:
    f.write("\n".join(hdr)+"\n"); f.write("time\t"+"\t".join(coords)+"\n")
    for r in rows: f.write("\t".join(f"{x:.6f}" for x in r)+"\n")
ti=int(np.argmin(rows[:,1+coords.index('knee_angle_r')]))
print("WROTE",OUT,"deepest t",round(ts[ti],2),"pelvis_tx",round(rows[ti,1+coords.index('pelvis_tx')],3),"pelvis_ty",round(rows[ti,1+coords.index('pelvis_ty')],3))
# verify foot planted at deepest
setc({c:rows[ti,1+j] for j,c in enumerate(coords)}); model.assemble(state); model.realizePosition(state)
print("deepest calcn",np.round(calcn(),3),"(should match standing x,y)")
