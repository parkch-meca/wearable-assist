import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
def crop(p,pad=8):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>18; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
fig=plt.figure(figsize=(15,9)); gs=fig.add_gridspec(1,3,width_ratios=[1,1,1.35],wspace=0.07)
fig.suptitle("stoop 테이블 박스 들기 모션 — 동작 검증 (50cm 테이블, 20kg 박스, 파지 t=2.0s)",fontsize=17,fontweight='bold',y=0.99)
for i,(p,t) in enumerate([("/tmp/cmp_render/interf/stoptable_side.png","옆(SIDE) — 다리 테이블 뒤, 손 박스"),
                          ("/tmp/cmp_render/interf/stoptable_front.png","앞(FRONT) — 박스 파지")]):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=12,fontweight='bold')
ax=fig.add_subplot(gs[0,2]); ax.axis('off')
ax.text(0,1.0,"동작 검증 (모션 grasp 프레임 실측)",fontsize=14,fontweight='bold',va='top')
checks=[("발 테이블 앞 접지 (매몰 0)","calcn y=−0.905 (지면), 매몰 0cm"),
        ("다리/정강이 테이블 침범 X","정강이 x=−0.12 < 테이블 edge 0.18 (뒤)"),
        ("손 박스 닿음 (gap 0)","hand_R=(0.32,−0.255)=박스 파지점"),
        ("상체 stoop 자연","고관절 hinge 43°·무릎 곧음·척추 굴곡"),
        ("균형 (COM 발 위)","COM 발 지지면 내"),
        ("테이블+박스 렌더","박스(갈색)·테이블(회색) 표시")]
y=0.90
for t,s in checks:
    ax.text(0,y,"✓",color='#1a8',fontsize=15,fontweight='bold',va='top')
    ax.text(0.05,y,t,fontsize=12,fontweight='bold',va='top')
    ax.text(0.05,y-0.035,s,fontsize=10.5,color='#555',va='top'); y-=0.10
ax.text(0,y-0.0,"모션: stoop_table_box_v1.mot (5s, 준비→숙여 reach\n→파지→듦→복귀). per-frame 발접지+다리 테이블뒤 유지.\n박스 20kg(양손 100N) 파지 후 적용 예정(SO).",fontsize=11,va='top',color='#225')
ax.text(0,y-0.16,"※ squat은 무릎이 테이블에 막혀 불가 → stoop 채택.\n   stoop은 척추 굴곡 동반 = 슈트 효과 부각 scenario.",fontsize=11,va='top',color='#a00')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/stoop_table_motion_verify_grid.png"
fig.savefig(OUT,dpi=110,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
