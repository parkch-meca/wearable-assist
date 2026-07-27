import os; os.environ.setdefault('DISPLAY',':1')
import opensim as osim, numpy as np, pyvista as pv
import render_box_stoop_video as R
MODEL="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim"
m=osim.Model(MODEL); s=m.initSystem(); cs=m.getCoordinateSet()
names=[cs.get(i).getName() for i in range(cs.getSize())]; mt={cs.get(i).getName():cs.get(i).getMotionType() for i in range(cs.getSize())}
t=osim.TimeSeriesTable('/data/gait_motion/gait_retarget_v2.mot')
def pose(i):
    for nm in names: cs.get(nm).setValue(s,(np.deg2rad(t.getDependentColumn(nm)[i]) if mt[nm]==1 else t.getDependentColumn(nm)[i]),False)
    m.realizePosition(s)
meshes=R.collect_meshes(m)
RARM={'humerus_R','ulna_R','radius_R','hand_R'}; LARM={'humerus_L','ulna_L','radius_L','hand_L'}
def render(fi):
    pose(fi); px=cs.get('pelvis_tx').getValue(s)
    pl=pv.Plotter(window_size=(560,720),off_screen=True,border=False); pv.global_theme.background='#141414'
    fc={}
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
        fr=mi['frame']; col='#E0D8C8'
        if any(b in fr for b in RARM): col='#3a9bff'
        elif any(b in fr for b in LARM): col='#ff5555'
        pl.add_mesh(surf,color=col,opacity=0.99,smooth_shading=True)
    gp=pv.Plane(center=(px,0.135,0),direction=(0,1,0),i_size=3.5,j_size=1.2); pl.add_mesh(gp,color='#2a2a2a')
    for gx in np.arange(round(px-1.6,1),px+1.6,0.2): pl.add_mesh(pv.Line((gx,0.137,-0.6),(gx,0.137,0.6)),color='#555555',line_width=1)
    pl.add_light(pv.Light(position=(px+2,3,4),intensity=0.55)); pl.add_light(pv.Light(position=(px-2,2,-2),intensity=0.35)); pl.add_light(pv.Light(light_type='headlight',intensity=0.45))
    pl.camera_position=[(px,0.9,3.8),(px,0.9,0),(0,1,0)]; pl.camera.parallel_projection=True; pl.camera.parallel_scale=1.0
    out=f'/tmp/gsc_{fi}.png'; pl.screenshot(out); pl.close(); return out
render(0)  # warmup discard (first-frame underexposure)
frames=[(0,'t0.40'),(15,'t0.65'),(27,'t0.85'),(39,'t1.05'),(51,'t1.25'),(63,'t1.45')]
imgs=[(render(fi),lbl) for fi,lbl in frames]
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.image as mpimg
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'); plt.rcParams['font.family']='Noto Sans CJK JP'
fig,ax=plt.subplots(2,3,figsize=(15,9.5))
for k,(p,lbl) in enumerate(imgs):
    a=ax[k//3,k%3]; a.imshow(mpimg.imread(p)); a.axis('off'); a.set_title(lbl,fontsize=11)
fig.suptitle('[3] 걷기 retarget v2 — 측면뷰 (파랑=오른팔, 빨강=왼팔)\n전후 팔 스윙 = 수평 변위 / 바닥격자 0.2m = stance 발 미끄러짐 점검',fontsize=12,weight='bold')
fig.tight_layout(rect=[0,0,1,0.95])
fig.savefig('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/gait_v2_side_color_grid.png',dpi=100)
print('SAVED gait_v2_side_color_grid.png')
