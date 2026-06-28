import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np, json
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
D=json.load(open('/tmp/cmp_render/twohand_pose.json'))
gR=D['gR']*100; gL=D['gL']*100
def crop(p,pad=8):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>18; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
fig=plt.figure(figsize=(15,9)); gs=fig.add_gridspec(1,3,width_ratios=[1,1,1.3],wspace=0.06)
fig.suptitle("양손 박스 파지 검증 — 양손 동시 표면 접촉 (50cm 테이블, 30cm 박스)",fontsize=17,fontweight='bold',y=0.99)
for i,(p,t) in enumerate([("/tmp/cmp_render/interf/twohand_front.png","앞(FRONT) — 양손 박스 좌우 잡음"),
                          ("/tmp/cmp_render/interf/twohand_side.png","옆(SIDE) — 다리 테이블 뒤")]):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=12,fontweight='bold')
ax=fig.add_subplot(gs[0,2]); ax.axis('off')
ax.text(0,1.0,"[판단] 양손 박스 파지 = 가능 ✅",fontsize=15,fontweight='bold',color='#1a7',va='top')
ax.text(0,0.90,"양손 동시 표면 접촉 IK (한 점 아님):",fontsize=12,va='top')
rows=[["","목표(박스 면)","실제 손","gap"],
 ["손 R","z=+0.15(오른면)","z=+0.15","%.1fcm"%gR],
 ["손 L","z=-0.15(왼면)","z=-0.15","%.1fcm"%gL]]
tb=ax.table(cellText=rows,bbox=[0,0.62,1.0,0.22]); tb.auto_set_font_size(False); tb.set_fontsize(11)
for (r,c),cell in tb.get_celld().items():
    if r==0: cell.set_facecolor('#e8e8e8'); cell.set_text_props(fontweight='bold')
    else: cell.set_facecolor('#dff0df')
    cell.set_edgecolor('#aaa')
ax.text(0,0.56,"• 손 R gap %.1fcm, 손 L gap %.1fcm — 둘 다 ~0\n  (관통 음수 X, 떨어짐 X). 좌우 대칭."%(gR,gL),fontsize=11.5,va='top',color='#225')
ax.text(0,0.45,"[2] 어깨 가동 허용:\n  R: elv155°ang36°elb101° / L: elv-65°ang50°elb101°\n  양손이 박스 좌우면(폭30cm) 동시 도달. 어깨가 막지 않음.",fontsize=11,va='top')
ax.text(0,0.30,"[동시 제약 모두 충족]\n  ✅ 양손 표면 접촉  ✅ 발 접지(매몰0)\n  ✅ 다리 테이블 뒤(정강이 x0.06<edge0.18)\n  ✅ 균형(COM 발 위)  ✅ 척추 stoop",fontsize=11,va='top',color='#225')
ax.text(0,0.13,"[정정] 이전 '6/6'은 hand_R 한 점만 맞춰\n  R관통+L비접촉이었음(CHEOL HOON 지적).\n  양손 동시 제약 넣으니 둘 다 gap0 — 해결.",fontsize=11,va='top',color='#a00')
ax.text(0,0.02,"자세: hip83 knee-42 tilt-53 lumbar-35 (stoop+약간 무릎)",fontsize=10.5,va='top',color='#555')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/twohand_grasp_grid.png"
fig.savefig(OUT,dpi=110,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
