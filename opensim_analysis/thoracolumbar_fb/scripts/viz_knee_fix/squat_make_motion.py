import opensim as osim, numpy as np
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
OUT="/data/stoop_motion/squat_synthetic_v1.mot"
model=osim.Model(P); model.initSystem(); cs=model.getCoordinateSet()
coords=[cs.get(i).getName() for i in range(cs.getSize())]
isrot={cs.get(i).getName(): (cs.get(i).getMotionType()!=2) for i in range(cs.getSize())}  # True=rotational(deg)

# deepest targets (solved): bodyweight squat, neutral spine, feet flat, balanced
TARGET={'knee_angle_r':-100,'knee_angle_l':-100,'hip_flexion_r':95,'hip_flexion_l':95,
        'ankle_angle_r':34,'ankle_angle_l':34,'pelvis_tilt':-28,'pelvis_ty':-0.319,'pelvis_tx':0.0,
        'shoulder_elv_r':85,'shoulder_elv_l':85,'elv_angle_r':90,'elv_angle_l':90,
        'elbow_flexion_r':5,'elbow_flexion_l':5}
# spine FE explicitly 0 (neutral) -> default 0, fine.

FPS=30; T=5.0; n=int(T*FPS)+1
ts=np.linspace(0,T,n)
def amp(t):
    # 0-0.5 stand, 0.5-2.0 descend, 2.0-3.0 hold, 3.0-4.5 ascend, 4.5-5 stand
    if t<0.5: return 0.0
    if t<2.0:
        x=(t-0.5)/1.5; return x*x*(3-2*x)
    if t<3.0: return 1.0
    if t<4.5:
        x=(t-3.0)/1.5; return 1-(x*x*(3-2*x))
    return 0.0

rows=[]
for t in ts:
    a=amp(t); row=[t]
    for c in coords:
        v=TARGET.get(c,0.0)*a
        row.append(v)  # rotational in deg, translational in m
    rows.append(row)
rows=np.array(rows)

hdr=["squat_synthetic_v1","version=1",f"nRows={n}",f"nColumns={len(coords)+1}","inDegrees=yes",
     "","Units are S.I. units (second, meters, Newtons, ...)","endheader"]
with open(OUT,"w") as f:
    f.write("\n".join(hdr)+"\n")
    f.write("time\t"+"\t".join(coords)+"\n")
    for r in rows:
        f.write("\t".join(f"{x:.6f}" for x in r)+"\n")
print("WROTE",OUT,"rows",n,"cols",len(coords)+1)
# sanity: print deepest row key coords
ti=int(np.argmin(rows[:,1+coords.index('knee_angle_r')]))
print("deepest t=",round(ts[ti],2),"knee",round(rows[ti,1+coords.index('knee_angle_r')],1),
      "hip",round(rows[ti,1+coords.index('hip_flexion_r')],1),"pty",round(rows[ti,1+coords.index('pelvis_ty')],3))
