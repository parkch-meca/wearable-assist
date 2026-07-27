import os; os.environ.setdefault('DISPLAY',':1')
import opensim as osim, numpy as np, pyvista as pv, json
import render_box_stoop_video as R
FIX="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim"
R.MODEL=FIX
m=osim.Model(FIX); s=m.initSystem(); cs=m.getCoordinateSet(); names=[cs.get(i).getName() for i in range(cs.getSize())]
for n in ['pro_sup_r','wrist_flex_r','wrist_dev_r']: cs.get(n).setLocked(s,False)
pose=json.load(open('/tmp/cmp_render/m1_pose.json'))
# drive LEFT arm from its own coords = mirror of right (fixed axes -> same coord value gives mirror pose)
mir={'shoulder_elv_l':'shoulder_elv_r','shoulder_rot_l':'shoulder_rot_r','elv_angle_l':'elv_angle_r',
     'elbow_flexion_l':'elbow_flexion_r','pro_sup_l':'pro_sup_r','wrist_flex_l':'wrist_flex_r','wrist_dev_l':'wrist_dev_r'}
for l,rr in mir.items(): pose[l]=pose.get(rr,0.0)
pose['clav_prot_l']=pose.get('clav_prot_r',0.0); pose['clav_elev_l']=pose.get('clav_elev_r',0.0)
for c,v in pose.items():
    if c in names: cc=cs.get(c); cc.setValue(s,(np.deg2rad(v) if cc.getMotionType()!=2 else v),False)
m.assemble(s); m.realizePosition(s)
def B(n): p=m.getBodySet().get(n).getPositionInGround(s); return np.array([p.get(0),p.get(1),p.get(2)])
hr=B('hand_R'); hl=B('hand_L')
print(f"양손 위치: R={np.round(hr,3)} L={np.round(hl,3)}  z-대칭오차={abs(hr[2]+hl[2])*100:.2f}cm (0=완벽대칭)")
# render front, NO viz-mirror: draw ACTUAL left arm meshes
meshes=R.collect_meshes(m); pv.global_theme.background='#141414'
pl=pv.Plotter(window_size=(760,820),off_screen=True,border=False); fc={}
for mi in meshes:
    if mi['frame'] not in fc:
        try: fc[mi['frame']]=m.getComponent(mi['frame'])
        except: pass
for mi in meshes:
    if mi['frame'] not in fc: continue
    try: surf=pv.read(mi['path'])
    except: continue
    sx,sy,sz=mi['scale']
    if (sx,sy,sz)!=(1,1,1): surf=surf.scale([sx,sy,sz],inplace=False)
    surf=surf.transform(R.transform_mat4(fc[mi['frame']].getTransformInGround(s)),inplace=False)
    pl.add_mesh(surf,color='#E8E0D0',opacity=0.96,smooth_shading=True)   # ALL meshes actual, NO mirror
box=[hr[0]+0.10,-0.455,0.0]
pl.add_mesh(pv.Cube(center=(box[0],box[1],0),x_length=0.3,y_length=0.3,z_length=0.3),color='#d98a20')
pl.add_mesh(pv.Box(bounds=(0.18,0.73,-0.905,-0.605,-0.45,0.45)),color='#20365a')
pl.add_light(pv.Light(position=(2,3,4),intensity=0.85)); pl.add_light(pv.Light(position=(-2,2,-1),intensity=0.35))
pl.camera_position=[(3.2,0.0,0.0),(0.1,-0.35,0),(0,1,0)]; pl.camera.parallel_projection=True; pl.camera.parallel_scale=0.95
pl.screenshot('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/armfix_no_vizmirror.png'); pl.close()
print("SAVED armfix_no_vizmirror.png (viz-mirror 없이 좌우 대칭 파지)")
