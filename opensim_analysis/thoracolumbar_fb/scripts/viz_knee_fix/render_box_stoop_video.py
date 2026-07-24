"""Box-lift stoop suit comparison video (public / 일반인용).
Left 슈트없음 (B_off) | Right 슈트착용 (B_on), ES color on spine + table/box + Korean overlay.
ES peak(max muscle, EMG-aligned) drives per-frame %. Headline: 허리 근육 부담 23% 감소.
PyVista (OpenSim direct, no MuSkeMo knee issue). Modes: preview | video."""
import os, sys, shutil, subprocess, time
os.environ.setdefault('DISPLAY', ':1')
from pathlib import Path
import numpy as np, opensim as osim, pyvista as pv
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib import font_manager as fm
from PIL import Image, ImageDraw, ImageFont
KF="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(KF); plt.rcParams['font.family']=fm.FontProperties(fname=KF).get_name(); plt.rcParams['axes.unicode_minus']=False
def pilfont(sz): return ImageFont.truetype(KF, sz)
MODEL='/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap.osim'
GEOM=Path('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry')
MOT='/data/stoop_motion/box_stoop_lift_m1.mot'
SO_OFF='/data/stoop_results/box_stoop_so/B_off/so_B_off_StaticOptimization_activation.sto'
SO_ON ='/data/stoop_results/box_stoop_so/B_on/so_B_on_StaticOptimization_activation.sto'
IMG_DIR=Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box'); IMG_DIR.mkdir(parents=True,exist_ok=True)
VIDEO_DIR=Path('/data/opensim_results'); FRAME_DIR=Path('/tmp/box_stoop_vid'); FRAME_DIR.mkdir(parents=True,exist_ok=True)
OUT_MP4=VIDEO_DIR/'box_stoop_suit_video.mp4'
FPS=30; T_TOTAL=7.5; RES_W,RES_H=1600,1000; TITLE_H=64; TOP_H=676; BOT_H=RES_H-TITLE_H-TOP_H  # 260
FLOOR=-0.905; EDGE=0.18; TABLE_H=0.30; TOPb=FLOOR+TABLE_H; BOX=0.30; HALF=BOX/2
GRIP_START,GRIP_END=1.9,6.0
ES_CMAP=LinearSegmentedColormap.from_list('es',[(0,'#909090'),(0.25,'#FFB300'),(0.5,'#FF6600'),(0.75,'#CC2200'),(1,'#8B0000')],N=256)
ES_CLIM=0.45   # color ceiling (ES peak ~37% at load -> good spread)
CAM=[(2.2,0.0,3.0),(0.12,-0.02,0.0),(0.0,1.0,0.0)]   # default 3-quarter; front view = [(3.2,0.0,0.0),(0.12,-0.02,0),(0,1,0)]
def is_es(n): return n.startswith(('IL_','LTpT_','LTpL_'))
# ---- model / motion / SO ----
def transform_mat4(T):
    R,p=T.R(),T.p(); M=np.eye(4)
    for i in range(3):
        for j in range(3): M[i,j]=R.get(i,j)
        M[i,3]=p.get(i)
    return M
def collect_meshes(model):
    out=[]
    for c in list(model.getComponentsList()):
        if c.getConcreteClassName()!='Mesh': continue
        mesh=osim.Mesh.safeDownCast(c); mf=mesh.get_mesh_file()
        if not mf: continue
        p=GEOM/mf
        if not p.exists(): p=GEOM/Path(mf).name
        if not p.exists(): continue
        sf=mesh.get_scale_factors()
        out.append({'path':str(p),'frame':mesh.getFrame().getAbsolutePathString(),'scale':(sf.get(0),sf.get(1),sf.get(2))})
    return out
def load_so(path):
    tbl=osim.TimeSeriesTable(path); labs=list(tbl.getColumnLabels()); t=np.array(list(tbl.getIndependentColumn()))
    dat=np.array([[tbl.getRowAtIndex(i)[j] for j in range(len(labs))] for i in range(tbl.getNumRows())])
    return t,labs,dat
def acts_at(t_arr,dat,labs,tq):
    i=int(np.argmin(np.abs(t_arr-tq))); return {labs[j]:float(dat[i,j]) for j in range(len(labs))}
def es_peak_pct(a):
    v=[a[k] for k in a if is_es(k)]; return 100.0*max(v) if v else 0.0
def apply_motion(model,state,mot,t):
    times=list(mot.getIndependentColumn()); idx=int(np.argmin([abs(ti-t) for ti in times])); row=mot.getRowAtIndex(idx)
    labs=list(mot.getColumnLabels()); cs=model.getCoordinateSet()
    for ci,nm in enumerate(labs):
        if not cs.contains(nm): continue
        c=cs.get(nm); v=row[ci]
        if c.getMotionType()==1: v=np.radians(v)
        c.setValue(state,v,False)
    model.assemble(state); model.realizePosition(state)
def hand_pos(model,state):
    comps={c.getName():c for c in (osim.PhysicalFrame.safeDownCast(x) for x in model.getComponentsList()) if c}
    q=comps['hand_R_geom_frame_11'].getPositionInGround(state); return np.array([q.get(0),q.get(1),q.get(2)])
def box_center(hand,tq,box_table):
    if GRIP_START<=tq<=GRIP_END:
        bc=[hand[0]+HALF-0.05,hand[1]-0.01,0.0]
        if bc[1]-HALF<TOPb-0.005: bc[1]=TOPb+HALF
        return bc
    return list(box_table)
def muscle_pd(model,state,acts):
    pts=[]; cells=[]; sc=[]; M=model.getMuscles()
    for i in range(M.getSize()):
        m=M.get(i); nm=m.getName()
        if not is_es(nm): continue
        a=acts.get(nm,0.0); pp=m.getGeometryPath().getCurrentPath(state)
        pl=[[pp.get(k).getLocationInGround(state).get(j) for j in range(3)] for k in range(pp.getSize())]
        if len(pl)<2: continue
        s=len(pts); pts.extend(pl)
        for ii in range(len(pl)-1): cells+= [2,s+ii,s+ii+1]; sc.append(a)
    if not pts: return None
    pd=pv.PolyData(); pd.points=np.array(pts,float); pd.lines=np.array(cells,np.int64); pd.cell_data['a']=np.array(sc,float); return pd
# ---- 3D side-by-side (skeleton+ES+table+box), returns RES_W x TOP_H image ----
def render_3d(model,state,meshes,acts_off,acts_on,box_c,out_png):
    pv.global_theme.background='#141414'
    pl=pv.Plotter(shape=(1,2),window_size=(RES_W,TOP_H),off_screen=True,border=False)
    fc={}
    for mi in meshes:
        if mi['frame'] not in fc:
            try: fc[mi['frame']]=model.getComponent(mi['frame'])
            except Exception: pass
    cam=CAM   # 3-quarter (default) or front (verification), module-level so it can be overridden
    def arm_side(fp):   # full shoulder girdle + arm, so left is a perfect z-mirror of right
        if any(k in fp for k in ('clavicle_R','scapula_R','humerus_R','ulna_R','radius_R','hand_R')): return 'R'
        if any(k in fp for k in ('clavicle_L','scapula_L','humerus_L','ulna_L','radius_L','hand_L')): return 'L'
        return None
    for col,(acts,lab) in enumerate([(acts_off,'OFF'),(acts_on,'ON')]):
        pl.subplot(0,col)
        for mi in meshes:
            if mi['frame'] not in fc: continue
            sd=arm_side(mi['frame'])
            if sd=='L': continue   # VIZ-MIRROR: model left arm is a defective right-copy -> skip, draw z-mirror of right instead
            try: surf=pv.read(mi['path'])
            except Exception: continue
            sx,sy,sz=mi['scale']
            if (sx,sy,sz)!=(1,1,1): surf=surf.scale([sx,sy,sz],inplace=False)
            surf=surf.transform(transform_mat4(fc[mi['frame']].getTransformInGround(state)),inplace=False)
            pl.add_mesh(surf,color='#E8E0D0',opacity=0.96,smooth_shading=True,specular=0.3,specular_power=15)
            if sd=='R':   # draw z=0 mirror of right arm as the left arm (correct bilateral grip)
                mir=surf.reflect((0,0,1),point=(0,0,0))
                pl.add_mesh(mir,color='#E8E0D0',opacity=0.96,smooth_shading=True,specular=0.3,specular_power=15,culling=False)
        pd=muscle_pd(model,state,acts)
        if pd is not None: pl.add_mesh(pd,scalars='a',cmap=ES_CMAP,clim=[0,ES_CLIM],line_width=5.0,show_scalar_bar=False)
        # floor + table (blue) + box (orange)
        pl.add_mesh(pv.Plane(center=(0.25,FLOOR-0.003,0),direction=(0,1,0),i_size=2.4,j_size=1.6),color='#2a2a2a',opacity=0.6)
        pl.add_mesh(pv.Box(bounds=(EDGE,EDGE+0.55,FLOOR,TOPb,-0.45,0.45)),color='#20365a',opacity=1.0,specular=0.1)
        pl.add_mesh(pv.Cube(center=(box_c[0],box_c[1],box_c[2]),x_length=BOX,y_length=BOX,z_length=BOX),color='#d98a20',opacity=1.0,specular=0.2)
        pl.add_light(pv.Light(position=(2,3,4),focal_point=(0.1,-0.3,0),intensity=0.85))
        pl.add_light(pv.Light(position=(-2,2,-1),focal_point=(0.1,-0.3,0),intensity=0.35))
        pl.camera_position=cam; pl.camera.parallel_projection=True; pl.camera.parallel_scale=1.12
    pl.screenshot(str(out_png)); pl.close()
# ---- bottom overlay (matplotlib, Korean) ----
def phase_ko(t):
    if t<0.4: return '준비','#888888'
    if t<2.3: return '허리 굽혀 잡기','#E67E00'
    if t<3.6: return '들어올리기','#CC2200'
    if t<4.5: return '들고 있기','#CC2200'
    if t<6.0: return '내려놓기','#E67E00'
    return '일어서기','#2E7D32'
def bottom(t,es_off,es_on,out_png):
    DPI=150; fig=plt.figure(figsize=(RES_W/DPI,BOT_H/DPI),dpi=DPI); fig.patch.set_facecolor('#0D0D0D')
    axb=fig.add_axes([0.03,0.16,0.60,0.72]); axt=fig.add_axes([0.68,0.12,0.30,0.80])
    for ax in (axb,axt): ax.set_facecolor('#0D0D0D'); ax.set_xticks([]); ax.set_yticks([])
    for ax in (axb,axt):
        for s in ax.spines.values(): s.set_visible(False)
    pn,pc=phase_ko(t)
    red=(es_off-es_on)/es_off*100 if es_off>3 else 0
    axb.axis('off'); axb.set_xlim(0,1); axb.set_ylim(0,1)
    # headline (fixed) + live
    axb.text(0.0,0.98,'허리 근육 부담  —  슈트 없음 vs 착용',fontsize=11,fontweight='bold',color='white',va='top',transform=axb.transAxes)
    axb.text(0.0,0.80,f'동작: {pn}    t={t:.1f}s',fontsize=9,fontweight='bold',color=pc,va='top',transform=axb.transAxes)
    def bar(y,val,lab,cap=45.0):
        frac=min(max(val/cap,0),1)
        axb.add_patch(mpatches.FancyBboxPatch((0.16,y),0.66,0.14,boxstyle='round,pad=0.006',facecolor='#2a2a2a',edgecolor='#444',lw=1,transform=axb.transAxes))
        axb.add_patch(mpatches.FancyBboxPatch((0.16,y),0.66*frac,0.14,boxstyle='round,pad=0.004',facecolor=ES_CMAP(min(val/(ES_CLIM*100),1)),edgecolor='none',transform=axb.transAxes))
        axb.text(0.14,y+0.07,lab,ha='right',va='center',fontsize=9,color='white',fontweight='bold',transform=axb.transAxes)
        axb.text(0.83,y+0.07,f'{val:.0f}%',ha='left',va='center',fontsize=9,color='white',fontweight='bold',transform=axb.transAxes)
    bar(0.52,es_off,'슈트 없음'); bar(0.30,es_on,'슈트 착용')
    if red>0.5:
        axb.text(0.49,0.13,f'허리 근육 부담  ↓ {red:.0f}%',ha='center',va='bottom',fontsize=13,fontweight='bold',color='#5bc8ff',transform=axb.transAxes)
    else:
        msg='박스를 잡기 전' if t<GRIP_START else '박스를 내려놓음'
        axb.text(0.49,0.13,msg,ha='center',va='bottom',fontsize=10,color='#888',transform=axb.transAxes)
    # timeline
    axt.axis('off'); axt.set_xlim(0,1); axt.set_ylim(0,1)
    axt.text(0.5,0.98,'진행',ha='center',va='top',fontsize=9,color='white',transform=axt.transAxes)
    axt.add_patch(mpatches.Rectangle((0.15,0.12),0.7,0.78,facecolor='#222',edgecolor='#444',transform=axt.transAxes))
    fr=0.12+0.78*(t/T_TOTAL)
    axt.add_patch(mpatches.Rectangle((0.15,0.12),0.7,0.78*(t/T_TOTAL),facecolor='#2471a3',alpha=0.5,transform=axt.transAxes))
    axt.plot([0.15,0.85],[fr,fr],color='#FFFF00',lw=2,transform=axt.transAxes)
    axt.text(0.5,0.05,'슈트: SMA 직물 허리보조 24N·m | KIMM',ha='center',va='top',fontsize=6.5,color='#777',transform=axt.transAxes)
    fig.savefig(str(out_png),dpi=100,facecolor='#0D0D0D',bbox_inches='tight',pad_inches=0); plt.close(fig)
# ---- composite: title + 3D(panel labels) + bottom ----
def composite(img3d,imgbot,t,es_off,es_on,out_png):
    c=Image.new('RGB',(RES_W,RES_H),(13,13,13)); d=ImageDraw.Draw(c)
    d.rectangle([0,0,RES_W,TITLE_H],fill=(18,20,26))
    d.text((RES_W//2,TITLE_H//2),'낮은 테이블의 박스를 들 때, 허리 근육이 받는 부담',font=pilfont(30),fill=(255,255,255),anchor='mm')
    t3=Image.open(img3d).convert('RGB').resize((RES_W,TOP_H),Image.LANCZOS); c.paste(t3,(0,TITLE_H))
    d.line([(RES_W//2,TITLE_H),(RES_W//2,TITLE_H+TOP_H)],fill=(70,70,70),width=2)
    # panel labels
    d.text((RES_W//4,TITLE_H+14),'슈트 없음',font=pilfont(26),fill=(230,150,150),anchor='mm')
    d.text((3*RES_W//4,TITLE_H+14),'슈트 착용',font=pilfont(26),fill=(150,200,255),anchor='mm')
    tb=Image.open(imgbot).convert('RGB').resize((RES_W,BOT_H),Image.LANCZOS); c.paste(tb,(0,TITLE_H+TOP_H))
    c.save(str(out_png))
def render_frame(t,out_png,ctx,pfx='f'):
    model,state,meshes,mot,(to,lo,do),(tn,ln,dn),box_table=ctx
    apply_motion(model,state,mot,t); hand=hand_pos(model,state); bc=box_center(hand,t,box_table)
    ao=acts_at(to,do,lo,t); an=acts_at(tn,dn,ln,t)
    eo=es_peak_pct(ao); en=es_peak_pct(an)
    p3=FRAME_DIR/f'{pfx}_3d.png'; pb=FRAME_DIR/f'{pfx}_bot.png'
    render_3d(model,state,meshes,ao,an,bc,p3); bottom(t,eo,en,pb); composite(p3,pb,t,eo,en,out_png)
    for p in (p3,pb):
        try: os.remove(p)
        except OSError: pass
    return eo,en
def setup():
    model=osim.Model(MODEL); state=model.initSystem()
    for n in ('pro_sup_r','wrist_flex_r','wrist_dev_r'):   # unlock right wrist so .mot palm orientation applies (mirrored to left)
        if model.getCoordinateSet().contains(n): model.getCoordinateSet().get(n).setLocked(state,False)
    model.assemble(state); meshes=collect_meshes(model)
    mot=osim.TimeSeriesTable(MOT); to,lo,do=load_so(SO_OFF); tn,ln,dn=load_so(SO_ON)
    # box table position = box at grasp moment
    apply_motion(model,state,mot,GRIP_START); box_table=box_center(hand_pos(model,state),GRIP_START,[EDGE+0.16,TOPb+HALF,0])
    return model,state,meshes,mot,(to,lo,do),(tn,ln,dn),box_table
if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'preview'
    ctx=setup()
    if mode=='preview':
        for t,lab in [(1.5,'reach'),(2.8,'liftpeak'),(4.0,'carry')]:
            out=IMG_DIR/f'boxvid_preview_{lab}.png'; eo,en=render_frame(t,out,ctx,f'prev_{lab}')
            print(f'preview t={t} {lab}: ES peak OFF={eo:.0f}% ON={en:.0f}% -> {out}')
    elif mode=='video':
        if FRAME_DIR.exists(): shutil.rmtree(FRAME_DIR)
        FRAME_DIR.mkdir(parents=True)
        N=int(FPS*T_TOTAL)+1; t0=time.time()
        for fi in range(N):
            t=fi/FPS; render_frame(t,FRAME_DIR/f'frame_{fi:04d}.png',ctx,f'f{fi:04d}')
            if fi%30==0: print(f'  frame {fi}/{N} t={t:.1f}s elapsed={time.time()-t0:.0f}s',flush=True)
        subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',str(FRAME_DIR/'frame_%04d.png'),
                        '-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium','-movflags','+faststart',str(OUT_MP4)],check=True)
        print('VIDEO',OUT_MP4,f'{OUT_MP4.stat().st_size/1e6:.1f}MB')
