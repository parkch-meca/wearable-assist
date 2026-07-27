"""Walking OFF|ON suit non-interference video. armfix model, gait_retarget_v2 (de-slip forward walk),
tight SO activations (OFF/ON). NO viz-mirror (armfix -> both arms drawn from own coords, independent swing).
ES color same clim both panels -> OFF/ON look near-identical (HONEST = suit does not interfere).
Message: lifting suit does not disturb normal walking. Modes: preview | video."""
import os, sys, subprocess
os.environ.setdefault('DISPLAY', ':1')
from pathlib import Path
import numpy as np, opensim as osim, pyvista as pv
from PIL import Image, ImageDraw, ImageFont
import render_box_stoop_video as R   # reuse: transform_mat4, collect_meshes, muscle_pd, load_so, acts_at, is_es, ES_CMAP, ES_CLIM
KF="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
def pilfont(sz): return ImageFont.truetype(KF, sz)
MODEL='/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim'
MOT='/data/gait_motion/gait_retarget_v2.mot'
SO_OFF='/data/gait_results/gait_off_tight/so_StaticOptimization_activation.sto'
SO_ON ='/data/gait_results/gait_on_tight/so_StaticOptimization_activation.sto'
IMG=Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box')
FRAME=Path('/tmp/gait_vid'); FRAME.mkdir(parents=True,exist_ok=True)
OUT_MP4=Path('/data/opensim_results/gait_suit_video.mp4'); Path('/data/opensim_results').mkdir(exist_ok=True)
RES_W,RES_H=1600,980; TITLE_H=70; TOP_H=690; BOT_H=RES_H-TITLE_H-TOP_H
ES_CLIM=0.45; GROUND=0.135
FPS=20
def pose(model,state,mot,i,names,mt):
    row=mot.getRowAtIndex(i)
    for ci,nm in enumerate(names):
        c=model.getCoordinateSet().get(nm); v=row[ci]
        c.setValue(state,(np.radians(v) if mt[nm]==1 else v),False)
    model.realizePosition(state)

def render_3d(model,state,meshes,fc,acts_off,acts_on,px,out_png):
    pv.global_theme.background='#141414'
    pl=pv.Plotter(shape=(1,2),window_size=(RES_W,TOP_H),off_screen=True,border=False)
    for col,acts in enumerate([acts_off,acts_on]):
        pl.subplot(0,col)
        for mi in meshes:
            if mi['frame'] not in fc: continue
            try: surf=pv.read(mi['path'])
            except Exception: continue
            sx,sy,sz=mi['scale']
            if (sx,sy,sz)!=(1,1,1): surf=surf.scale([sx,sy,sz],inplace=False)
            surf=surf.transform(R.transform_mat4(fc[mi['frame']].getTransformInGround(state)),inplace=False)
            pl.add_mesh(surf,color='#E8E0D0',opacity=0.96,smooth_shading=True,specular=0.3,specular_power=15)  # ALL actual, no viz-mirror
        pd=R.muscle_pd(model,state,acts)
        if pd is not None: pl.add_mesh(pd,scalars='a',cmap=R.ES_CMAP,clim=[0,ES_CLIM],line_width=8.5,show_scalar_bar=False)
        pl.add_mesh(pv.Plane(center=(px,GROUND-0.003,0),direction=(0,1,0),i_size=3.2,j_size=1.4),color='#2a2a2a',opacity=0.7)
        for gx in np.arange(round(px-1.6,1),px+1.6,0.3): pl.add_mesh(pv.Line((gx,GROUND,-0.65),(gx,GROUND,0.65)),color='#3c3c3c',line_width=1)
        pl.add_light(pv.Light(position=(px+2,3,4),intensity=0.7)); pl.add_light(pv.Light(position=(px-2,2,-2),intensity=0.35)); pl.add_light(pv.Light(light_type='headlight',intensity=0.4))
        pl.camera_position=[(px,0.95,3.9),(px,0.95,0),(0,1,0)]; pl.camera.parallel_projection=True; pl.camera.parallel_scale=0.96
    pl.screenshot(str(out_png)); pl.close()

def gait_phase(i,n):
    f=i/(n-1)
    # right foot stance ~0.18-0.85 of window (from GRF); simplified narrative
    if f<0.20: return '왼발 디딤'
    if f<0.42: return '양발 지지'
    if f<0.72: return '오른발 디딤'
    return '왼발 디딤 전환'

def es_peak(acts):
    v=[acts[k] for k in acts if R.is_es(k)]; return 100.0*max(v) if v else 0.0

def composite(img3d_png, i, n, eoff, eon, out_png):
    top=Image.open(img3d_png).convert('RGB')
    canvas=Image.new('RGB',(RES_W,RES_H),'#141414'); d=ImageDraw.Draw(canvas)
    # title
    t="슈트를 입고 걸을 때, 허리 근육은?"
    d.text((RES_W//2,TITLE_H//2),t,font=pilfont(34),fill='#f2f2f2',anchor='mm')
    canvas.paste(top,(0,TITLE_H))
    # panel labels
    d.text((RES_W//4,TITLE_H+14),'슈트 없음',font=pilfont(30),fill='#cfe3ff',anchor='mm')
    d.text((3*RES_W//4,TITLE_H+14),'슈트 착용',font=pilfont(30),fill='#ffd9c0',anchor='mm')
    d.line((RES_W//2,TITLE_H,RES_W//2,TITLE_H+TOP_H),fill='#333',width=2)
    # bottom band
    by=TITLE_H+TOP_H
    d.rectangle((0,by,RES_W,RES_H),fill='#101010')
    # ES peak bars (small values, honest)
    d.text((RES_W//4,by+30),f'허리 근육 부담(ES peak): {eoff:.0f}%',font=pilfont(26),fill='#cfe3ff',anchor='mm')
    d.text((3*RES_W//4,by+30),f'허리 근육 부담(ES peak): {eon:.0f}%',font=pilfont(26),fill='#ffd9c0',anchor='mm')
    dd=eon-eoff
    msg=f'걸을 때는 거의 변화 없음 (Δ{dd:+.0f}%p) — 슈트가 보행을 방해하지 않습니다'
    d.text((RES_W//2,by+78),msg,font=pilfont(28),fill='#eaffea',anchor='mm')
    d.text((RES_W//2,by+120),'무거운 것을 들 때는 최대 47%↓, 그냥 걸을 때는 거의 그대로 — 필요할 때만 돕고 일상은 안 거스릅니다',
           font=pilfont(21),fill='#bdbdbd',anchor='mm')
    d.text((RES_W-14,by+BOT_H-16),gait_phase(i,n),font=pilfont(20),fill='#888',anchor='rm')
    canvas.save(out_png)

def main():
    mode=sys.argv[1] if len(sys.argv)>1 else 'preview'
    model=osim.Model(MODEL); state=model.initSystem(); cs=model.getCoordinateSet()
    names=[cs.get(i).getName() for i in range(cs.getSize())]; mt={n:cs.get(n).getMotionType() for n in names}
    mot=osim.TimeSeriesTable(MOT); T=np.array(list(mot.getIndependentColumn())); n=mot.getNumRows()
    to,lo,do=R.load_so(SO_OFF); tn,ln,dn=R.load_so(SO_ON)
    meshes=R.collect_meshes(model); fc={}
    for mi in meshes:
        if mi['frame'] not in fc:
            try: fc[mi['frame']]=model.getComponent(mi['frame'])
            except Exception: pass
    # warmup
    _w=pv.Plotter(off_screen=True,window_size=(80,80)); _w.add_mesh(pv.Sphere()); _w.screenshot('/tmp/_w.png'); _w.close()
    idxs=range(n) if mode=='video' else [0,18,36,54,72]
    outs=[]
    for i in idxs:
        pose(model,state,mot,i,names,mt); px=cs.get('pelvis_tx').getValue(state)
        ao=R.acts_at(to,do,lo,T[i]); an=R.acts_at(tn,dn,ln,T[i])
        eo=es_peak(ao); en=es_peak(an)
        r3=f'/tmp/gait_vid/r{i:04d}.png'; render_3d(model,state,meshes,fc,ao,an,px,r3)
        outp=(FRAME/f'frame_{i:04d}.png'); composite(r3,i,n,eo,en,str(outp)); outs.append((str(outp),i,eo,en))
        if mode!='video': print(f'frame {i} t={T[i]:.2f} ES OFF={eo:.0f}% ON={en:.0f}%')
    if mode=='video':
        subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-pattern_type','glob','-i',str(FRAME/'frame_*.png'),
                        '-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-c:v','libx264','-pix_fmt','yuv420p','-crf','20',str(OUT_MP4)])
        print('WROTE',OUT_MP4)
    else:
        # preview keyframe grid
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.image as mpimg
        fig,ax=plt.subplots(1,len(outs),figsize=(4*len(outs),5.2))
        for k,(p,i,eo,en) in enumerate(outs):
            ax[k].imshow(mpimg.imread(p)); ax[k].axis('off'); ax[k].set_title(f't={T[i]:.2f}\nOFF {eo:.0f}% ON {en:.0f}%',fontsize=9)
        fig.tight_layout(); fig.savefig(str(IMG/'gait_video_grid.png'),dpi=90); print('SAVED gait_video_grid.png')
main()
