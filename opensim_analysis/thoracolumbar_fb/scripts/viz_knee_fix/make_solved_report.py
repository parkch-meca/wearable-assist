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
fig=plt.figure(figsize=(16,9.5)); gs=fig.add_gridspec(1,3,width_ratios=[1,1,1.55],wspace=0.07)
fig.suptitle("박스 양손 파지 — 모델 frame 비대칭 진단·수정 → 독립 검증 PASS ✅",fontsize=16.5,fontweight='bold',y=0.99,color='#0a6')
for i,(p,t) in enumerate([("/tmp/cmp_render/interf/headup2_front.png","앞 — 양손 대칭 파지, 머리 들림"),
                          ("/tmp/cmp_render/interf/headup2_side.png","옆 — 박스 보며 듦(머리 안 처박힘)")]):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=11,fontweight='bold')
ax=fig.add_subplot(gs[0,2]); ax.axis('off')
ax.text(0,1.0,"[1] 모델 결함 진단 (사실)",fontsize=13,fontweight='bold',color='#a00',va='top')
ax.text(0,0.92,"좌우 팔 관절 축(CustomJoint axis) 대조:\n"
               "• elbow·radioulnar = 제대로 미러됨(x,y 부호 반전)\n"
               "• ⚠️ shoulder_L·radius_hand_l(손목) = 오른쪽과 축이 '동일'(미러 아님)\n"
               "  → 같은 관절값이 위치는 대칭이나 한 손바닥 방향 틀어짐(splay).",fontsize=10.5,va='top')
ax.text(0,0.69,"[2] 우리 수정 탓? → 아님",fontsize=13,fontweight='bold',color='#225',va='top')
ax.text(0,0.62,"original 모델도 shoulder_L/손목_l 축이 오른쪽 복사본. = original 정의 결함\n(forearm_v1·손목해제 등 우리 수정과 무관).",fontsize=10.5,va='top')
ax.text(0,0.50,"[3] 수정 (viz 전용, 정량 0)",fontsize=13,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.42,"• 올바른 오른팔을 z=0 평면으로 반사해 왼팔로 렌더(오른팔 mesh 미러=정확한 왼팔).\n"
               "• 관절 축 자체보다 확실: 좌우 완벽 거울 보장. .osim 파일 불변 → SO/ES 정량 0.\n"
               "• + 곧은척추 hip-hinge 체간 + 목 신전으로 머리 들기.",fontsize=10.5,va='top')
ax.text(0,0.25,"[4] 독립 검증 PASS (양손 각각+대칭+머리)",fontsize=13,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.17,"✅ 오른손/왼손 각각 박스 잡음(splay·손등 아님) ✅ 좌우 대칭 ✅ 관통 없음\n"
               "✅ 발 접지 ✅ 박스 테이블 위(50cm) ✅ 머리 안 처박힘(박스 보며 듦) ✅ 아킴보 과하지 않음",fontsize=10.5,va='top',color='#225')
ax.text(0,0.02,"생성/검증 분리 ~15라운드 끝 첫 완전 PASS. 모델 진단이 돌파구(우회 아님). 다음=모션/SO/동영상(승인 후).",fontsize=10.5,fontweight='bold',color='#7a0000',va='top')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/box_grasp_SOLVED_grid.png"
fig.savefig(OUT,dpi=110,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
