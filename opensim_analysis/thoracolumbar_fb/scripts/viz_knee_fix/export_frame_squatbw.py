import opensim as osim, numpy as np, json, os, sys
from xml.etree import ElementTree as ET

P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
MOT="/data/stoop_motion/squat_synthetic_v1.mot"
ACT_OFF="/data/squat_results/suit_sweep/F0/squat_F0_StaticOptimization_activation.sto"
ACT_ON ="/data/squat_results/suit_sweep/F200/squat_F200_StaticOptimization_activation.sto"

TIMES=[float(x) for x in sys.argv[1:]] or [2.5]
OUTDIR=os.environ.get("VFRAMES_OUT","/tmp/cmp_render/frames"); os.makedirs(OUTDIR,exist_ok=True)

SPINE=['il_','iliocost','longissi','ltpl','ltpt','long_col','mf_','multifidus','deepmult','supmult','ql_','ps_','semi','splen']
def is_spine(n):
    n=n.lower(); return any(n.startswith(t) or ('_'+t) in n for t in SPINE)

def read_sto(path):
    L=open(path).read().splitlines()
    hi=[i for i,l in enumerate(L) if l.strip().lower()=='endheader'][0]
    cols=L[hi+1].split('\t')
    data=np.array([[float(x) for x in l.split('\t')] for l in L[hi+2:] if l.strip()])
    return cols,data
def act_at(cols,data,t):
    ti=int(np.argmin(np.abs(data[:,0]-t)))
    return {cols[j]:float(data[ti,j]) for j in range(1,len(cols))}

oc,od=read_sto(ACT_OFF); nc,nd=read_sto(ACT_ON)

# mesh frames
def parse_mesh_frames(p):
    root=ET.parse(p).getroot(); pm={c:par for par in root.iter() for c in par}; out=[]
    for mesh in root.iter('Mesh'):
        mf=mesh.find('mesh_file')
        if mf is None or not mf.text: continue
        base=os.path.basename(mf.text.strip())
        node=mesh; fr=None
        while node in pm:
            node=pm[node]
            if node.tag in ('Body','PhysicalOffsetFrame'): fr=node.get('name'); break
        out.append((base,fr))
    return out
MF=parse_mesh_frames(P)

model=osim.Model(P); state=model.initSystem()
st=osim.Storage(MOT); model.getSimbodyEngine().convertDegreesToRadians(st)
times=osim.ArrayDouble(); st.getTimeColumn(times); n=st.getSize()
ts=[times.getitem(i) for i in range(n)]
cs=model.getCoordinateSet()
muscles=model.getMuscles()
es_names=[muscles.get(i).getName() for i in range(muscles.getSize()) if is_spine(muscles.get(i).getName())]

def set_pose(t):
    idx=min(range(n), key=lambda i: abs(ts[i]-t))
    row=st.getStateVector(idx).getData()
    for i in range(cs.getSize()):
        c=cs.get(i); ci=st.getStateIndex(c.getName())
        if ci>=0: c.setValue(state,row.getitem(ci),False)
    model.assemble(state); model.realizePosition(state)

def frame_map():
    m={}
    for fr in model.getComponentsList():
        pf=osim.PhysicalFrame.safeDownCast(fr)
        if pf is None: continue
        T=pf.getTransformInGround(state); R=T.R(); p=T.p()
        m[pf.getName()]=([R.get(r,c) for r in range(3) for c in range(3)],[p.get(0),p.get(1),p.get(2)])
    return m

for t in TIMES:
    set_pose(t)
    fm=frame_map()
    mesh_x={}
    for base,fr in MF:
        if fr in fm: mesh_x[base]={'R':fm[fr][0],'p':fm[fr][1]}
    ao=act_at(oc,od,t); an=act_at(nc,nd,t)
    mus={}
    for nm in es_names:
        gp=model.getMuscles().get(nm).getGeometryPath()
        pts=gp.getCurrentPath(state)
        P3=[]
        for k in range(pts.getSize()):
            loc=pts.get(k).getLocationInGround(state); P3.append([loc.get(0),loc.get(1),loc.get(2)])
        mus[nm]={'pts':P3,'off':ao.get(nm,0.0),'on':an.get(nm,0.0)}
    out={'t':t,'mesh':mesh_x,'muscles':mus}
    fn=os.path.join(OUTDIR,f"frame_{t:.3f}.json")
    json.dump(out, open(fn,'w'))
    # summary
    offv=np.mean([v['off'] for v in mus.values()]); onv=np.mean([v['on'] for v in mus.values()])
    print(f"t={t:.3f} meshes={len(mesh_x)} ES_muscles={len(mus)} meanES off={offv:.3f} on={onv:.3f} -> {fn}")
print("EXPORT_FRAME_DONE")
