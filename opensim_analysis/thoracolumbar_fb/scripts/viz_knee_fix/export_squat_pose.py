import opensim as osim, numpy as np, json, os, sys
from xml.etree import ElementTree as ET
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
MOT="/data/stoop_motion/squat_synthetic_v1.mot"
TIMES=[float(x) for x in sys.argv[1:]] or [2.0]
OUTDIR="/tmp/cmp_render/squat_motion_frames"; os.makedirs(OUTDIR,exist_ok=True)
SPINE=['il_','iliocost','longissi','ltpl','ltpt','long_col','mf_','multifidus','deepmult','supmult','ql_','ps_','semi','splen']
def is_spine(n): n=n.lower(); return any(n.startswith(t) or ('_'+t) in n for t in SPINE)
def parse_mesh_frames(p):
    root=ET.parse(p).getroot(); pm={c:par for par in root.iter() for c in par}; out=[]
    for mesh in root.iter('Mesh'):
        mf=mesh.find('mesh_file')
        if mf is None or not mf.text: continue
        base=os.path.basename(mf.text.strip()); node=mesh; fr=None
        while node in pm:
            node=pm[node]
            if node.tag in ('Body','PhysicalOffsetFrame'): fr=node.get('name'); break
        out.append((base,fr))
    return out
MF=parse_mesh_frames(P)
model=osim.Model(P); state=model.initSystem()
st=osim.Storage(MOT); model.getSimbodyEngine().convertDegreesToRadians(st)
times=osim.ArrayDouble(); st.getTimeColumn(times); N=st.getSize(); ts=[times.getitem(i) for i in range(N)]
cs=model.getCoordinateSet()
muscles=model.getMuscles(); es=[muscles.get(i).getName() for i in range(muscles.getSize()) if is_spine(muscles.get(i).getName())]
def set_pose(t):
    idx=min(range(N),key=lambda i:abs(ts[i]-t)); row=st.getStateVector(idx).getData()
    for i in range(cs.getSize()):
        c=cs.get(i); ci=st.getStateIndex(c.getName())
        if ci>=0: c.setValue(state,row.getitem(ci),False)
    model.assemble(state); model.realizePosition(state)
def fmap():
    m={}
    for fr in model.getComponentsList():
        pf=osim.PhysicalFrame.safeDownCast(fr)
        if pf is None: continue
        T=pf.getTransformInGround(state); R=T.R(); p=T.p()
        m[pf.getName()]=([R.get(r,c) for r in range(3) for c in range(3)],[p.get(0),p.get(1),p.get(2)])
    return m
for t in TIMES:
    set_pose(t); fm=fmap()
    mesh_x={b:{'R':fm[fr][0],'p':fm[fr][1]} for b,fr in MF if fr in fm}
    mus={}
    for nm in es:
        gp=model.getMuscles().get(nm).getGeometryPath(); pts=gp.getCurrentPath(state)
        mus[nm]={'pts':[[pts.get(k).getLocationInGround(state).get(j) for j in range(3)] for k in range(pts.getSize())],'off':0.0,'on':0.0}
    json.dump({'t':t,'mesh':mesh_x,'muscles':mus}, open(os.path.join(OUTDIR,f"frame_{t:.3f}.json"),'w'))
    print(f"t={t} meshes={len(mesh_x)} muscles={len(mus)}")
print("DONE")
