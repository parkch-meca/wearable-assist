import opensim as osim, numpy as np, json, os
from xml.etree import ElementTree as ET
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
OUT="/tmp/cmp_render/table_pose_frame.json"
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
model=osim.Model(P); state=model.initSystem(); cs=model.getCoordinateSet(); names=[cs.get(i).getName() for i in range(cs.getSize())]
def setc(d):
    for k,v in d.items():
        if k in names: c=cs.get(k); c.setValue(state,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def B(n): p=model.getBodySet().get(n).getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
def realize(): model.assemble(state); model.realizePosition(state)
setc({c:0.0 for c in names}); realize(); fstand=B('calcn_r')
pose={c:0.0 for c in names}
pose.update({'hip_flexion_r':55,'hip_flexion_l':55,'knee_angle_r':-40,'knee_angle_l':-40,
             'ankle_angle_r':16,'ankle_angle_l':16,'pelvis_tilt':-28,
             'shoulder_elv_r':22,'shoulder_elv_l':22,'elv_angle_r':90,'elv_angle_l':90,'elbow_flexion_r':35,'elbow_flexion_l':35})
pose['pelvis_tx']=0;pose['pelvis_ty']=0; setc(pose); realize()
f=B('calcn_r'); pose['pelvis_tx']=fstand[0]-f[0]; pose['pelvis_ty']=fstand[1]-f[1]; setc(pose); realize()
hand=B('hand_R'); handL=B('hand_L')
print("hand_R",np.round(hand,3),"hand_L",np.round(handL,3))
fm={}
for fr in model.getComponentsList():
    pf=osim.PhysicalFrame.safeDownCast(fr)
    if pf is None: continue
    T=pf.getTransformInGround(state); R=T.R(); p=T.p()
    fm[pf.getName()]=([R.get(r,c) for r in range(3) for c in range(3)],[p.get(0),p.get(1),p.get(2)])
mesh_x={b:{'R':fm[fr][0],'p':fm[fr][1]} for b,fr in MF if fr in fm}
mus={}
for i in range(model.getMuscles().getSize()):
    nm=model.getMuscles().get(i).getName()
    if not is_spine(nm): continue
    gp=model.getMuscles().get(i).getGeometryPath(); pts=gp.getCurrentPath(state)
    mus[nm]={'pts':[[pts.get(k).getLocationInGround(state).get(j) for j in range(3)] for k in range(pts.getSize())],'off':0.0,'on':0.0}
json.dump({'t':0,'mesh':mesh_x,'muscles':mus,'hand_R':hand.tolist(),'hand_L':handL.tolist()}, open(OUT,'w'))
print("SAVED",OUT,"meshes",len(mesh_x),"muscles",len(mus))
