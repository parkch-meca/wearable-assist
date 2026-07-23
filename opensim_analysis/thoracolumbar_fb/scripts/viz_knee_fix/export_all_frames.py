"""One OpenSim session: export ALL motion frames' mesh ground transforms + box center
into a single combined json for fast batch Blender rendering (skeleton + table + box)."""
import opensim as osim, numpy as np, json, os
from xml.etree import ElementTree as ET
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap.osim"
MOT="/data/stoop_motion/box_stoop_lift_m1.mot"
OUT="/tmp/cmp_render/motion_all.json"
FLOOR=-0.905; EDGE=0.18; TABLE_H=0.30; TOPb=FLOOR+TABLE_H; BOX=0.30; HALF=BOX/2
m=osim.Model(P); state=m.initSystem(); cs=m.getCoordinateSet(); coords=[cs.get(i).getName() for i in range(cs.getSize())]
for n in ['pro_sup_r','wrist_flex_r','wrist_dev_r']: cs.get(n).setLocked(state,False)
comps={c.getName():c for c in (osim.PhysicalFrame.safeDownCast(x) for x in m.getComponentsList()) if c}
midmc=comps['hand_R_geom_frame_11']
def fp(pf): q=pf.getPositionInGround(state); return np.array([q.get(0),q.get(1),q.get(2)])
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
def side_of(fr):
    f=(fr or '').lower()
    if any(x in f for x in ('humerus_r','ulna_r','radius_r','hand_r')): return 'R'
    if any(x in f for x in ('humerus_l','ulna_l','radius_l','hand_l')): return 'L'
    return 'other'
tbl=osim.TimeSeriesTable(MOT); times=list(tbl.getIndependentColumn()); labels=list(tbl.getColumnLabels())
GRIP_START,GRIP_END=1.9,6.0   # box attached to hands only while gripped (matches motion kp)
def set_pose(row):
    for j,lab in enumerate(labels):
        if lab in coords: c=cs.get(lab); c.setValue(state,(np.deg2rad(row[j]) if c.getMotionType()!=2 else row[j]),False)
    m.assemble(state); m.realizePosition(state)
def box_from_hand():
    hand=fp(midmc); bc=[float(hand[0]+HALF-0.05),float(hand[1]-0.01),0.0]
    if bc[1]-HALF < TOPb-0.005: bc[1]=TOPb+HALF   # cannot go below table top
    return bc
# fixed table box position = box at the grasp moment (continuity before/after grip)
gi=int(np.argmin([abs(t-GRIP_START) for t in times])); set_pose(tbl.getRowAtIndex(gi)); BOX_TABLE=box_from_hand()
frames=[]; sides={}
for i in range(len(times)):
    set_pose(tbl.getRowAtIndex(i))
    fmt={}
    for fr in m.getComponentsList():
        pf=osim.PhysicalFrame.safeDownCast(fr)
        if pf is None: continue
        T=pf.getTransformInGround(state); R=T.R(); p=T.p()
        fmt[pf.getName()]=([round(R.get(rr,cc),5) for rr in range(3) for cc in range(3)],[round(p.get(0),5),round(p.get(1),5),round(p.get(2),5)])
    mx={}
    for b,fr in MF:
        if fr in fmt:
            mx[b]={'R':fmt[fr][0],'p':fmt[fr][1]}
            if b not in sides: sides[b]=side_of(fr)
    if GRIP_START<=times[i]<=GRIP_END:
        bc=box_from_hand()
    else:
        bc=list(BOX_TABLE)   # box rests on table before grasp / after release
    frames.append({'mx':mx,'box':[round(bc[0],4),round(bc[1],4),round(bc[2],4)]})
json.dump({'sides':sides,'geo':{'edge':EDGE,'top':TOPb,'half':HALF},'floor':FLOOR,'n':len(frames),'frames':frames}, open(OUT,'w'))
print("SAVED",OUT,"frames",len(frames))
