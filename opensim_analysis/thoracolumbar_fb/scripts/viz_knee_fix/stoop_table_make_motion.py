import opensim as osim, numpy as np, json
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
OUT="/data/stoop_motion/stoop_table_box_v1.mot"
D=json.load(open('/tmp/cmp_render/table_stoop_pose.json')); grasp=D['pose']
model=osim.Model(P); model.initSystem(); cs=model.getCoordinateSet()
coords=[cs.get(i).getName() for i in range(cs.getSize())]
state=model.initSystem()
def setc(d):
    for k,v in d.items():
        if k in coords: c=cs.get(k); c.setValue(state,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def calcn(): p=model.getBodySet().get('calcn_r').getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
setc({c:0.0 for c in coords}); model.assemble(state); model.realizePosition(state); fstand=calcn()
# target = grasp pose joint angles (exclude pelvis_tx/ty: solved per-frame for grounding)
TARGET={k:grasp[k] for k in grasp if k not in ('pelvis_tx','pelvis_ty')}
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
    for k,v in TARGET.items():
        if k in coords: pose[k]=v*a  # deg for rot; for trans (rad units conv) handled below
    # per-frame ground feet
    pose['pelvis_tx']=0.0; pose['pelvis_ty']=0.0
    setc(pose); model.assemble(state); model.realizePosition(state); f=calcn()
    pose['pelvis_tx']=fstand[0]-f[0]; pose['pelvis_ty']=fstand[1]-f[1]
    setc(pose); model.assemble(state); model.realizePosition(state)
    rows.append([t]+[pose[c] for c in coords])
rows=np.array(rows)
hdr=["stoop_table_box_v1","version=1",f"nRows={n}",f"nColumns={len(coords)+1}","inDegrees=yes","","Units are S.I. units (second, meters, Newtons, ...)","endheader"]
with open(OUT,"w") as f:
    f.write("\n".join(hdr)+"\n"); f.write("time\t"+"\t".join(coords)+"\n")
    for r in rows: f.write("\t".join(f"{x:.6f}" for x in r)+"\n")
ti=int(np.argmax([amp(t) for t in ts]))
print("WROTE",OUT,"deepest t=",round(ts[ti],2))
# verify deepest frame foot + hand
setc({c:rows[ti,1+j] for j,c in enumerate(coords)}); model.assemble(state); model.realizePosition(state)
def Bd(n): p=model.getBodySet().get(n).getPositionInGround(state); return np.round([p.get(0),p.get(1),p.get(2)],3)
print("deepest calcn",Bd('calcn_r'),"hand_R",Bd('hand_R'),"tibia_R x",Bd('tibia_R')[0])
