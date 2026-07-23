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
D="/tmp/cmp_render/motion_png"
cols=[(9,"0.3s 서기"),(45,"1.5s 숙임"),(69,"2.3s 파지"),(96,"3.2s 들어올림"),(129,"4.3s carry"),(165,"5.5s 복귀")]
fig=plt.figure(figsize=(17,6.4)); gs=fig.add_gridspec(2,6,wspace=0.03,hspace=0.08)
fig.suptitle("박스 들기 모션 전체 미리보기 — 6.03초, 30fps (SO 전 육안 확인용) · 위=옆 / 아래=앞",fontsize=14.5,fontweight='bold',y=1.02,color='#1a3a6a')
for j,(fi,lab) in enumerate(cols):
    ax=fig.add_subplot(gs[0,j]); ax.imshow(crop(f"{D}/side_{fi:04d}.png")); ax.axis('off'); ax.set_title(lab,fontsize=10.5,fontweight='bold')
    ax=fig.add_subplot(gs[1,j]); ax.imshow(crop(f"{D}/front_{fi:04d}.png")); ax.axis('off')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/box_lift_motion_keyframes.png"
fig.savefig(OUT,dpi=112,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
