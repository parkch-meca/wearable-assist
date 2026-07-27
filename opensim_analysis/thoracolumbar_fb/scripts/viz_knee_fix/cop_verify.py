import os; os.environ.setdefault('DISPLAY',':1')
import opensim as osim, numpy as np, pyvista as pv
import render_box_stoop_video as R
GD='/home/sysop/opensim-build/opensim-gui/opensim-models/Pipelines/Gait2354_Simbody'
MODEL="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim"
m=osim.Model(MODEL); s=m.initSystem(); cs=m.getCoordinateSet()
names=[cs.get(i).getName() for i in range(cs.getSize())]; mt={cs.get(i).getName():cs.get(i).getMotionType() for i in range(cs.getSize())}
mot=osim.TimeSeriesTable('/data/gait_motion/gait_retarget_so.mot'); T=np.array(list(mot.getIndependentColumn()))
grf=osim.TimeSeriesTable('/data/gait_motion/gait_grf_scaled.mot'); tg=np.array(list(grf.getIndependentColumn()))
def gi(c,ti): return grf.getDependentColumn(c)[int(np.argmin(np.abs(tg-ti)))]
def pose(i):
    for c in names: cs.get(c).setValue(s,(np.deg2rad(mot.getDependentColumn(c)[i]) if mt[c]==1 else mot.getDependentColumn(c)[i]),False)
    m.realizePosition(s)
meshes=R.collect_meshes(m)
# warmup
_w=pv.Plotter(off_screen=True,window_size=(100,100)); _w.add_mesh(pv.Sphere()); _w.screenshot('/tmp/_w.png'); _w.close()
def render(ti,lbl):
    i=int(np.argmin(np.abs(T-ti))); pose(i); px=cs.get('pelvis_tx').getValue(s)
    pl=pv.Plotter(window_size=(520,720),off_screen=True,border=False); pl.set_background('#141414')
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
        pl.add_mesh(surf,color='#E0D8C8',opacity=0.97,smooth_shading=True)
    gp=pv.Plane(center=(px,0.0,0),direction=(0,1,0),i_size=3.0,j_size=1.2); pl.add_mesh(gp,color='#242424')
    # COP markers + force vectors (scaled) for both plates if in stance
    for pfx,fcol,scol in [('','#ffd11a','#ff3333'),('1_','#1affd1','#33aaff')]:
        vy=gi(pfx+'ground_force_vy',ti)
        if vy>20:
            cop=np.array([gi(pfx+'ground_force_px',ti),gi(pfx+'ground_force_py',ti),gi(pfx+'ground_force_pz',ti)])
            fv=np.array([gi(pfx+'ground_force_vx',ti),vy,gi(pfx+'ground_force_vz',ti)])/900.0
            pl.add_mesh(pv.Sphere(radius=0.03,center=cop),color=scol)
            pl.add_mesh(pv.Arrow(start=cop,direction=fv,scale=np.linalg.norm(fv)),color=fcol)
    pl.add_light(pv.Light(position=(px,3,4),intensity=0.6)); pl.add_light(pv.Light(light_type='headlight',intensity=0.5))
    pl.camera_position=[(px,0.8,4.0),(px,0.8,0),(0,1,0)]; pl.camera.parallel_projection=True; pl.camera.parallel_scale=1.0
    out=f'/tmp/cop_{int(ti*100)}.png'; pl.screenshot(out); pl.close(); return out
frames=[(0.73,'R heel strike'),(1.05,'R mid-stance'),(1.38,'R toe-off / L heel strike')]
imgs=[(render(ti,l),l) for ti,l in frames]
# trajectory plot: calcn-x vs COP-px (both feet)
def footx(b):
    xs=[]
    for i in range(len(T)):
        pose(i); xs.append(m.getBodySet().get(b).getPositionInGround(s).get(0))
    return np.array(xs)
fxr=footx('calcn_r'); fxl=footx('calcn_l')
copr=np.array([gi('ground_force_px',t) for t in T]); copl=np.array([gi('1_ground_force_px',t) for t in T])
vyr=np.array([gi('ground_force_vy',t) for t in T]); vyl=np.array([gi('1_ground_force_vy',t) for t in T])
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.image as mpimg
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'); plt.rcParams['font.family']='Noto Sans CJK JP'; plt.rcParams['axes.unicode_minus']=False
fig=plt.figure(figsize=(15,8.5)); gs=fig.add_gridspec(2,3)
for k,(p,l) in enumerate(imgs):
    a=fig.add_subplot(gs[0,k]); a.imshow(mpimg.imread(p)); a.axis('off'); a.set_title(l,fontsize=11)
axL=fig.add_subplot(gs[1,0:2])
axL.plot(T,fxr,'b-',label='calcn_R x (발)'); axL.plot(T,copr,'b--',label='COP_R px (GRF)')
axL.plot(T,fxl,'r-',label='calcn_L x (발)'); axL.plot(T,copl,'r--',label='COP_L px (GRF)')
axL.fill_between(T,0,1,where=vyr>20,color='b',alpha=0.06); axL.fill_between(T,0,1,where=vyl>20,color='r',alpha=0.06)
axL.set_ylim(0.1,0.95); axL.set_xlabel('t (s)'); axL.set_ylabel('전후 위치 x (m)'); axL.grid(alpha=0.3); axL.legend(fontsize=8,ncol=2)
axL.set_title('COP px vs 발(calcn) x — 스탠스(음영) 중 COP가 발밑/heel→toe 추종해야')
axR=fig.add_subplot(gs[1,2])
axR.plot(T,vyr,'b-',label='GRF_R vy'); axR.plot(T,vyl,'r-',label='GRF_L vy'); axR.axhline(765,color='k',ls=':',lw=1,label='체중 765N')
axR.set_xlabel('t (s)'); axR.set_ylabel('수직력 (N)'); axR.grid(alpha=0.3); axR.legend(fontsize=8); axR.set_title('좌/우 GRF 수직력 (스탠스 타이밍)')
fig.suptitle('걷기 [2]+[3] GRF COP 정렬 검증 (스케일 GRF x1.069, de-slip 없는 SO 모션)',fontsize=13,weight='bold')
fig.tight_layout(rect=[0,0,1,0.96])
fig.savefig('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/gait_cop_verify.png',dpi=105)
print('SAVED gait_cop_verify.png')
