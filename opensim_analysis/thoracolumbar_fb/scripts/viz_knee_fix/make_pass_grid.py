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
fig=plt.figure(figsize=(16,9.5)); gs=fig.add_gridspec(1,3,width_ratios=[1,1,1.45],wspace=0.07)
fig.suptitle("박스 양손 손바닥 파지 — 독립 검증 PASS (테이블 50cm, 손목 시각화해제)",fontsize=17,fontweight='bold',y=0.99,color='#0a6')
for i,(p,t) in enumerate([("/tmp/cmp_render/interf/palm50_front.png","앞(FRONT) — 양손 손바닥 박스 향함"),
                          ("/tmp/cmp_render/interf/palm50_side.png","옆(SIDE) — stoop, 테이블 50cm")]):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=12,fontweight='bold')
ax=fig.add_subplot(gs[0,2]); ax.axis('off')
ax.text(0,1.0,"독립 검증 PASS ✅ (생성/검증 분리)",fontsize=14,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.91,"검증자(수치·의도 차단, 그림만)가 보강 체크리스트로 판정:\n"
               "✅ 손바닥면 박스 향함(손등 아님)  ✅ 양손 접촉  ✅ 관통 없음\n"
               "✅ 발 전체 접지  ✅ 박스 테이블 위  ✅ 테이블 낮음(허벅지)  ✅ 자세 자연",fontsize=11,va='top',color='#225')
ax.text(0,0.68,"[핵심 수정 — 손등→손바닥]",fontsize=13,fontweight='bold',color='#a00',va='top')
ax.text(0,0.60,"이전 FAIL 원인: palm normal 부호를 거꾸로 잡아 **손등**을 박스로 향하게 함.\n"
               "수정: 엄지/새끼/중지 frame 외적으로 진짜 손바닥 방향 실측(sign=−1).\n"
               "→ 손바닥 normal R(−Z)/L(+Z) 박스 중심 향함, 도달 R/L 0.0cm.",fontsize=11,va='top')
ax.text(0,0.40,"[테이블 50cm 고정] 75cm로 안 올림. 어깨를 테이블 위로 가져오는\n체간 자세로 도달 해결(테이블 높이로 회피 X).",fontsize=11,va='top',color='#225')
ax.text(0,0.27,"[정량 영향 0] pro_sup/wrist 메모리 해제만, .osim 디스크 locked=true 불변. SO/ES 무관.",fontsize=11,va='top',color='#225')
ax.text(0,0.16,"[검증자 caveat — 투명 공개]",fontsize=12,fontweight='bold',color='#7a0000',va='top')
ax.text(0,0.09,"• 손바닥/손등 구분은 해상도상 100% 단정은 아니나 손등 징후 없음.\n"
               "• 손가락이 옆면 깊게 감싸기보다 윗모서리에 걸치는 편(그립 깊이 여지).\n"
               "→ 최종 육안 확인은 사용자께. 더 깊은 그립 원하면 1회 더 조정 가능.",fontsize=10.5,va='top',color='#333')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/box_grasp_PASS_grid.png"
fig.savefig(OUT,dpi=110,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
