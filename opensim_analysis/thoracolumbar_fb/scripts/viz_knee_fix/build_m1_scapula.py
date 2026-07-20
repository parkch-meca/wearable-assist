"""M1: sternoclavicular WeldJoint -> 2-DOF CustomJoint (clav_prot + clav_elev).
scapula stays welded to clavicle (clavR_scapR_jnt unchanged) so the whole shoulder
girdle protracts with the clavicle. default_value=0 => identical to welded model at rest.
Writes ..._M1.osim. Then verifies load + tests protraction direction."""
import re, os, numpy as np
SRC="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
DST="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap.osim"
xml=open(SRC).read()

def coord_block(name, rng):
    return f'''<Coordinate name="{name}">
							<default_value>0</default_value>
							<default_speed_value>0</default_speed_value>
							<range>{rng}</range>
							<clamped>true</clamped>
							<locked>false</locked>
							<prescribed_function />
							<is_free_to_satisfy_constraints>false</is_free_to_satisfy_constraints>
						</Coordinate>'''

def rot_axis(name, coord, axis):
    return f'''<TransformAxis name="{name}">
							<coordinates>{coord}</coordinates>
							<axis>{axis}</axis>
							<LinearFunction name="function">
								<coefficients> 1 0</coefficients>
							</LinearFunction>
						</TransformAxis>'''

def const_axis(name, axis):
    return f'''<TransformAxis name="{name}">
							<axis>{axis}</axis>
							<MultiplierFunction name="function">
								<function>
									<Constant>
										<value>0</value>
									</Constant>
								</function>
								<scale>1</scale>
							</MultiplierFunction>
						</TransformAxis>'''

def build_custom(side):
    S=side.upper(); s=side.lower()
    jn=f'ster{S}_clav{S}_jnt'
    # grab the original WeldJoint block
    m=re.search(rf'<WeldJoint name="{jn}">.*?</WeldJoint>', xml, re.S)
    assert m, f'{jn} not found'
    block=m.group(0)
    # extract sockets + frames verbatim
    pf=re.search(r'<socket_parent_frame>(.*?)</socket_parent_frame>', block).group(1)
    cf=re.search(r'<socket_child_frame>(.*?)</socket_child_frame>', block).group(1)
    frames=re.search(r'<frames>.*?</frames>', block, re.S).group(0)
    # protraction about +Y (vertical): swings distal clavicle anterior/posterior
    # elevation about +X (anterior): swings distal clavicle up/down
    prot=f'clav_prot_{s}'; elev=f'clav_elev_{s}'
    coords=f'''<coordinates>
						{coord_block(prot,'-0.34906585 0.61086524')}
						{coord_block(elev,'-0.34906585 0.43633231')}
					</coordinates>'''
    st=f'''<SpatialTransform>
						{rot_axis('rotation1',prot,'0 1 0')}
						{rot_axis('rotation2',elev,'1 0 0')}
						{const_axis('rotation3','0 0 1')}
						{const_axis('translation1','1 0 0')}
						{const_axis('translation2','0 1 0')}
						{const_axis('translation3','0 0 1')}
					</SpatialTransform>'''
    cj=f'''<CustomJoint name="{jn}">
					<socket_parent_frame>{pf}</socket_parent_frame>
					<socket_child_frame>{cf}</socket_child_frame>
					{coords}
					{st}
					{frames}
				</CustomJoint>'''
    return block, cj

new=xml
for side in ['R','L']:
    old,cj=build_custom(side); new=new.replace(old,cj)
open(DST,'w').write(new)
print("WROTE",DST)

# ---- verify load + coordinate presence ----
import opensim as osim
m=osim.Model(DST); st=m.initSystem(); cs=m.getCoordinateSet()
names=[cs.get(i).getName() for i in range(cs.getSize())]
newc=[c for c in names if c.startswith('clav_')]
print("new coords:",newc,"total coords:",len(names))
# test protraction direction: humerus_R x at prot=0 vs +30 deg
def setc(d):
    for k,v in d.items():
        c=cs.get(k); c.setValue(st,(v if c.getMotionType()==2 else np.deg2rad(v)),False)
def hx(): m.assemble(st); m.realizePosition(st); p=m.getBodySet().get('humerus_R').getPositionInGround(st); return np.array([p.get(0),p.get(1),p.get(2)])
setc({c:0.0 for c in names}); h0=hx()
setc({'clav_prot_r':30.0}); h1=hx()
setc({'clav_prot_r':0.0,'clav_elev_r':20.0}); h2=hx()
print(f"prot=0  humerusR x={h0[0]:.3f} y={h0[1]:.3f} z={h0[2]:.3f}")
print(f"prot=+30 dx={(h1[0]-h0[0])*100:+.1f}cm dy={(h1[1]-h0[1])*100:+.1f}cm dz={(h1[2]-h0[2])*100:+.1f}cm  (want +x forward)")
print(f"elev=+20 dx={(h2[0]-h0[0])*100:+.1f}cm dy={(h2[1]-h0[1])*100:+.1f}cm dz={(h2[2]-h0[2])*100:+.1f}cm")
