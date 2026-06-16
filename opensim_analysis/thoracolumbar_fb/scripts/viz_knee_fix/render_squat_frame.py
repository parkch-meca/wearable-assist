"""Public-friendly render: opaque bones + green(편함)->red(힘듦) ES color. OFF/ON, side/back.
SAME structure (knee fix bones + ES path-point curves). Only color/alpha changed."""
import bpy, os, json, mathutils
FRAME="/tmp/cmp_render/squat_frames/frame_1.992.json"
OSIM="/tmp/cmp_render/tlfb/TLFB.osim"
OUT="/tmp/cmp_render/squat_pub"; os.makedirs(OUT,exist_ok=True)
RAD=0.006
D=json.load(open(FRAME))
VMAX=0.43  # squat working ES range (OFF peak)
# green -> yellow -> orange -> red (편함 -> 힘듦)
GYR=[(0.00,0.10,0.66,0.18),(0.40,0.55,0.80,0.10),(0.58,0.96,0.86,0.10),(0.78,0.97,0.45,0.05),(1.00,0.88,0.04,0.04)]
def gyr(x):
    x=max(0.,min(1.,x))
    for i in range(len(GYR)-1):
        t0,r0,g0,b0=GYR[i]; t1,r1,g1,b1=GYR[i+1]
        if x<=t1:
            f=(x-t0)/(t1-t0) if t1>t0 else 0
            return (r0+(r1-r0)*f,g0+(g1-g0)*f,b0+(b1-b0)*f)
    return GYR[-1][1:]
AMIN=0.13  # 대비 강화: 작동 ES 범위로 정규화 (수치 왜곡 아님)
def actcolor(a):
    n=max(0.,min(1.,(a-AMIN)/(VMAX-AMIN))); return gyr(n), n
def mat_from(R,p):
    return mathutils.Matrix(((R[0],R[1],R[2],p[0]),(R[3],R[4],R[5],p[1]),(R[6],R[7],R[8],p[2]),(0,0,0,1)))
def look_at(cl,t):
    cl=mathutils.Vector(cl); t=mathutils.Vector(t); f=(t-cl).normalized(); up=mathutils.Vector((0,1,0))
    r=f.cross(up); r=r if r.length>1e-6 else mathutils.Vector((1,0,0)); r.normalize(); u=r.cross(f).normalized()
    return mathutils.Matrix(((r.x,u.x,-f.x),(r.y,u.y,-f.y),(r.z,u.z,-f.z))).to_euler()
def white_mat():
    m=bpy.data.materials.get("BoneWhite")
    if m: return m
    m=bpy.data.materials.new("BoneWhite"); m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(0.92,0.91,0.86,1)
    if "Roughness" in b.inputs: b.inputs["Roughness"].default_value=0.55
    if "Alpha" in b.inputs: b.inputs["Alpha"].default_value=0.88
    for en in ("Emission Color","Emission"):
        if en in b.inputs:
            try: b.inputs[en].default_value=(0.85,0.84,0.78,1)
            except: pass
    if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=0.4
    m.blend_method='BLEND'
    return m

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
imp=getattr(bpy.ops,'import'); imp.import_opensim_model(filepath=OSIM)
bpy.context.view_layer.update()
wm=white_mat()
for o in list(bpy.data.objects):
    t=o.get('MuSkeMo_type')
    if o.type=='MESH' and t=='GEOMETRY':
        if o.name in D['mesh']:
            o.parent=None; o.matrix_world=mat_from(D['mesh'][o.name]['R'],D['mesh'][o.name]['p'])
        o.data.materials.clear(); o.data.materials.append(wm); o.hide_render=False
    elif o.type=='CURVE' or t in ('WRAP','LANDMARK','JOINT'):
        bpy.data.objects.remove(o, do_unlink=True)
for coll in bpy.data.collections:
    if any(k in coll.name.lower() for k in ['wrap','joint cent','landmark','frame','muscle']):
        coll.hide_render=True
mcoll=bpy.data.collections.new("ES"); bpy.context.scene.collection.children.link(mcoll)
muscle_objs={}
for nm,md in D['muscles'].items():
    pts=md['pts']
    if len(pts)<2: continue
    cu=bpy.data.curves.new(nm,'CURVE'); cu.dimensions='3D'
    sp=cu.splines.new('POLY'); sp.points.add(len(pts)-1)
    for i,(x,y,z) in enumerate(pts): sp.points[i].co=(x,y,z,1)
    cu.bevel_depth=RAD; cu.use_fill_caps=True
    ob=bpy.data.objects.new(nm,cu); mcoll.objects.link(ob)
    mat=bpy.data.materials.new("m_"+nm); mat.use_nodes=True
    ob.data.materials.append(mat); muscle_objs[nm]=(ob,mat)
def recolor(cond):
    for nm,(ob,mat) in muscle_objs.items():
        col,n=actcolor(D['muscles'][nm][cond])
        b=mat.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value=(col[0],col[1],col[2],1)
        for en in ("Emission Color","Emission"):
            if en in b.inputs:
                try: b.inputs[en].default_value=(col[0],col[1],col[2],1)
                except: pass
        if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=0.2+1.3*n
mn=[1e9]*3; mx=[-1e9]*3
for o in bpy.data.objects:
    if o.type in ('MESH','CURVE') and not o.hide_render:
        for v in o.bound_box:
            wv=o.matrix_world@mathutils.Vector(v)
            for i in range(3): mn[i]=min(mn[i],wv[i]); mx[i]=max(mx[i],wv[i])
cx=(mn[0]+mx[0])/2; cy=(mn[1]+mx[1])/2; cz=(mn[2]+mx[2])/2
xext=mx[0]-mn[0]; yext=mx[1]-mn[1]; zext=mx[2]-mn[2]
RESX,RESY=820,1020
ortho=max(yext, xext*RESY/RESX, zext*RESY/RESX)*1.10
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=RESX; sc.render.resolution_y=RESY
sc.render.image_settings.file_format='PNG'; sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background')
if bg: bg.inputs[0].default_value=(0.05,0.055,0.07,1); bg.inputs[1].default_value=1.0
for loc,en in [((cx+2,cy+2,cz+3),5.0),((cx-2,cy+1,cz+3),4.0),((cx,cy-1,cz-3),2.8)]:
    bpy.ops.object.light_add(type='SUN',location=loc); bpy.context.object.data.energy=en
bpy.ops.object.camera_add(location=(0,0,0)); cam=bpy.context.object; sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=ortho; cam.data.sensor_fit='VERTICAL'
cam.data.clip_start=0.01; cam.data.clip_end=60
VIEWS={"side":(cx,cy,cz+5)}
for cond in ['off','on']:
    recolor(cond)
    for vn,loc in VIEWS.items():
        cam.location=mathutils.Vector(loc); cam.rotation_euler=look_at(loc,(cx,cy,cz))
        sc.render.filepath=os.path.join(OUT,f"pub_{cond}_{vn}.png"); bpy.ops.render.render(write_still=True); print("[render]",cond,vn)
print("PUBLIC_DONE")
