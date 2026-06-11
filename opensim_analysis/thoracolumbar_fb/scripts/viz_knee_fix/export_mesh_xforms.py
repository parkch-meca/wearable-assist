import opensim as osim, json, numpy as np, os
from xml.etree import ElementTree as ET
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"

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

model=osim.Model(P); state=model.initSystem()
fmap={}
for fr in model.getComponentsList():
    pf=osim.PhysicalFrame.safeDownCast(fr)
    if pf is None: continue
    T=pf.getTransformInGround(state); R=T.R(); p=T.p()
    fmap[pf.getName()]=dict(R=[R.get(r,c) for r in range(3) for c in range(3)],
                            p=[p.get(0),p.get(1),p.get(2)])
out={}
miss=[]
for base,fr in parse_mesh_frames(P):
    if fr in fmap: out[base]=fmap[fr]
    else: miss.append((base,fr))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"tlfb_mesh_xforms.json"),"w"))
print("meshes mapped:",len(out),"missing frame:",len(miss), miss[:5])
