import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
def crop(p,pad=6):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>16; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
fig=plt.figure(figsize=(16,9.6)); gs=fig.add_gridspec(2,3,height_ratios=[1,1],width_ratios=[1,1,1.55],wspace=0.06,hspace=0.16)
fig.suptitle("M1 견갑 protraction 추가 — regression 통과(ΔES 0.03%p) + 자세 개선(등 55°→40°). 독립검증은 여전히 과굴곡 판독(수치-지각 괴리)",
             fontsize=13,fontweight='bold',y=0.995,color='#1a3a6a')
# progression side views
for i,(p,t) in enumerate([("/tmp/cmp_render/interf/dist3_side.png","분산 only 등55°"),
                          ("/tmp/cmp_render/interf/m1a_side.png","M1(prot미사용) 등46°"),
                          ("/tmp/cmp_render/interf/m1c_side.png","M1(prot48°) 등40°·최선")]):
    ax=fig.add_subplot(gs[0,i]) if i<2 else fig.add_subplot(gs[0,2])
    ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=9.5,fontweight='bold')
# bottom-left: m1c front, and side (repeat best)
ax=fig.add_subplot(gs[1,0]); ax.imshow(crop("/tmp/cmp_render/interf/m1c_front.png")); ax.axis('off'); ax.set_title("M1 최선 앞 — 대칭 파지",fontsize=9.5,fontweight='bold')
ax=fig.add_subplot(gs[1,1]); ax.imshow(crop("/tmp/cmp_render/interf/m1c_side.png")); ax.axis('off'); ax.set_title("M1 최선 옆 — 깊은 squat(무릎-81°)",fontsize=9.5,fontweight='bold')
ax=fig.add_subplot(gs[1,2]); ax.axis('off')
ax.text(0,1.02,"[regression 게이트] 통과 ✅",fontsize=12,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.95,"stoop SO ES 활성도 baseline vs M1 (76 ES근육, 5구간):\n"
               "Hold 8.18%→8.18%,  MAX ΔES = 0.029%p (solver 잡음).\n"
               "→ stoop/squat headline 정량 안 흔들림. 견갑=ES 무관 실증.",fontsize=8.8,va='top')
ax.text(0,0.80,"[자세 개선 실측]",fontsize=12,fontweight='bold',color='#225',va='top')
ax.text(0,0.735,"등 lean(골반→T1):  55° → 46° → 40° (protraction 강제)\n"
               "어깨 전방돌출:      30cm → 22cm\n"
               "clav_prot 48°로 어깨 독립 전방이동 → 체간 세움.\n"
               "무릎 squat -81°, 간섭0, 대칭, palm 3.0cm.",fontsize=8.8,va='top')
ax.text(0,0.585,"[한계] 독립검증 여전히 과굴곡",fontsize=12,fontweight='bold',color='#a00',va='top')
ax.text(0,0.52,"6회 독립검증 모두 등을 70~80°로 읽고 NOT-SOLVED.\n"
               "이번엔 '무릎 안 굽음'이라 했으나 실제 knee=-81°(깊은 squat).\n"
               "→ 렌더 json 다리메시 확인=굽은 무릎 정확히 배치(충실).\n"
               "즉 객관 40°/깊은squat vs 지각 70~80°/직선다리 괴리.",fontsize=8.8,va='top')
ax.text(0,0.36,"[원인 추정]",fontsize=12,fontweight='bold',color='#225',va='top')
ax.text(0,0.30,"골격만 있는 깊은 squat는 뼈 겹쳐 판독 난해 + 앞의 낮은\n"
               "박스를 잡는 동작은 본질적으로 상체가 박스 위로 쏠린 실루엣.\n"
               "객관 개선은 확실하나 '자연스러움' 지각은 미달.",fontsize=8.8,va='top')
ax.text(0,0.17,"[결정 요청]",fontsize=12,fontweight='bold',color='#7a0000',va='top')
ax.text(0,0.11,"M1+regression은 완료·안전. 자세는 객관 최선(등40°).\n"
               "① 이 자세 수용하고 SO/영상  ② 근육입힌 렌더로 재판단\n"
               "③ 더 깊은 squat 시도(hip 더 낮춤)  — 사용자 시각 판단 요청.",fontsize=8.8,va='top',color='#333')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/box_table30_M1_grid.png"
fig.savefig(OUT,dpi=110,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
