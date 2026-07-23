import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
def crop(p,pad=4):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>16; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
frames=[("mf2_2.3_side","1) 파지 (박스 테이블 위)","박스 h=+0.12m"),
        ("mf2_3.2_side","2) 들어올림 (박스 뜸)","박스 h=+0.27m"),
        ("mf2_3.6_side","3) 들어올림 (더 높이)","박스 h=+0.44m"),
        ("mf2_4.3_side","4) 일어서 carry","박스 h=+0.50m")]
fig=plt.figure(figsize=(16,6.6)); gs=fig.add_gridspec(1,4,wspace=0.04)
fig.suptitle("박스 들기 모션 — 박스가 손 따라 테이블에서 떨어져 단조 상승 (옆면 시퀀스)",fontsize=15,fontweight='bold',y=1.02,color='#0a6')
for i,(f,t,h) in enumerate(frames):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(f"/tmp/cmp_render/interf/{f}.png")); ax.axis('off')
    ax.set_title(t,fontsize=11,fontweight='bold'); ax.text(0.5,-0.04,h,transform=ax.transAxes,ha='center',fontsize=10.5,color='#a00',fontweight='bold')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/box_lift_motion_seq.png"
fig.savefig(OUT,dpi=115,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
