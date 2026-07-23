"""Export a render frame json at a given time of the box-lift .mot (M1 model).
Box follows the hands (box_center = hand + fixed grip offset). Table fixed at 30 cm."""
import opensim as osim, numpy as np, json, sys, os
from xml.etree import ElementTree as ET
P="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap.osim"
MOT="/data/stoop_motion/box_stoop_lift_m1.mot"
T=float(sys.argv[1]); OUTJ=sys.argv[2]
FLOOR=-0.905; EDGE=0.18; TABLE_H=0.30; TOPb=FLOOR+TABLE_H; BOX=0.30; HALF=BOX/2
m=osim.Model(P); state=m.initSystem(); cs=m.getCoordinateSet(); coords=[cs.get(i).getName() for i in range(cs.getSize())]
for n in ['pro_sup_r','wrist_flex_r','wrist_dev_r']: cs.get(n).setLocked(state,False)
comps={c.getName():c for c in (osim.PhysicalFrame.safeDownCast(x) for x in m.getComponentsList()) if c}
PFR_midmc=comps['hand_R_geom_frame_11']
def fp(pf): q=pf.getPositionInGround(state); return np.array([q.get(0),q.get(1),q.get(2)])
# load motion, pick nearest row to T
import csv
tbl=osim.TimeSeriesTable(MOT); times=list(tbl.getIndependentColumn()); labels=list(tbl.getColumnLabels())
i=int(np.argmin([abs(t-T) for t in times])); row=tbl.getRowAtIndex(i)
pose={labels[j]:row[j] for j in range(len(labels))}
for k,v in pose.items():
    if k in coords: c=cs.get(k); c.setValue(state,(np.deg2rad(v) if c.getMotionType()!=2 else v),False)
m.assemble(state); m.realizePosition(state)
def Bd(n): p=m.getBodySet().get(n).getPositionInGround(state); return np.array([p.get(0),p.get(1),p.get(2)])
hand=fp(PFR_midmc)
# box follows hand with the grasp offset (box_center = hand + (HALF-0.05, -0.01, -HAND_z))
box_center=[float(hand[0]+ (HALF-0.05)), float(hand[1]-0.01), 0.0]
# during early grasp the box sits on the table; clamp box bottom not below table top
box_bottom=box_center[1]-HALF
if box_bottom < TOPb-0.005:   # box resting on table
    box_center[1]=TOPb+HALF
print(f"t={times[i]:.2f} hand=({hand[0]:.3f},{hand[1]:.3f},{hand[2]:.3f}) box_center=({box_center[0]:.3f},{box_center[1]:.3f})")
# ---- mesh transforms + ES muscles + sides (same as grasp export) ----
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
SPINE=['il_','iliocost','longissi','ltpl','ltpt','long_col','mf_','multifidus','deepmult','supmult','ql_','ps_','semi','splen']
isS=lambda n: any(n.lower().startswith(t) or ('_'+t) in n.lower() for t in SPINE)
fm={}
for fr in m.getComponentsList():
    pf=osim.PhysicalFrame.safeDownCast(fr)
    if pf is None: continue
    Tf=pf.getTransformInGround(state); R=Tf.R(); p=Tf.p(); fm[pf.getName()]=([R.get(rr,cc) for rr in range(3) for cc in range(3)],[p.get(0),p.get(1),p.get(2)])
mesh_x={}; sides={}
for b,fr in MF:
    if fr in fm: mesh_x[b]={'R':fm[fr][0],'p':fm[fr][1]}; sides[b]=side_of(fr)
mus={}
for k in range(m.getMuscles().getSize()):
    nm=m.getMuscles().get(k).getName()
    if isS(nm):
        pts=m.getMuscles().get(k).getGeometryPath().getCurrentPath(state)
        mus[nm]={'pts':[[pts.get(q).getLocationInGround(state).get(j) for j in range(3)] for q in range(pts.getSize())]}
json.dump({'mesh':mesh_x,'sides':sides,'muscles':mus,
           'geo':{'edge':EDGE,'top':TOPb,'grip':[box_center[0],box_center[1],0.0],'half':HALF,'box_center':box_center}},
          open(OUTJ,'w'))
print("SAVED",OUTJ)
