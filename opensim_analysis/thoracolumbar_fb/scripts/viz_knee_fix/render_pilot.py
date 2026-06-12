"""Stoop pilot: per-frame bone placement (knee fix) + ES muscle path-point curves
colored by activation. Renders OFF and ON, side+back. Visualization only."""
import bpy, os, json, mathutils

FRAME="/tmp/cmp_render/frames/frame_2.500.json"
OSIM="/tmp/cmp_render/tlfb/TLFB.osim"
OUT="/tmp/cmp_render/pilot"; os.makedirs(OUT,exist_ok=True)
RAD=0.006
D=json.load(open(FRAME))
# color scale: shared vmax across both conditions
acts=[v['off'] for v in D['muscles'].values()]+[v['on'] for v in D['muscles'].values()]
VMAX=max(0.05, max(acts))
print("[scale] VMAX=",round(VMAX,3))

def mat_from(R,p):
    return mathutils.Matrix(((R[0],R[1],R[2],p[0]),(R[3],R[4],R[5],p[1]),(R[6],R[7],R[8],p[2]),(0,0,0,1)))
def look_at(cl,t):
    cl=mathutils.Vector(cl); t=mathutils.Vector(t); f=(t-cl).normalized(); up=mathutils.Vector((0,1,0))
    r=f.cross(up); r=r if r.length>1e-6 else mathutils.Vector((1,0,0)); r.normalize(); u=r.cross(f).normalized()
    return mathutils.Matrix(((r.x,u.x,-f.x),(r.y,u.y,-f.y),(r.z,u.z,-f.z))).to_euler()
def actcolor(a):
    n=max(0.0,min(1.0,a/VMAX))
    # gray -> red
    base=(0.40+0.50*n, 0.40-0.33*n, 0.42-0.35*n)
    return base, n  # color, emission norm

def white_mat():
    m=bpy.data.materials.get("BoneWhite")
    if m: return m
    m=bpy.data.materials.new("BoneWhite"); m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(0.93,0.93,0.91,1)
    if "Roughness" in b.inputs: b.inputs["Roughness"].default_value=0.55
    for en in ("Emission Color","Emission"):
        if en in b.inputs:
            try: b.inputs[en].default_value=(0.8,0.8,0.78,1)
            except: pass
    if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=0.25
    return m

# import bones via MuSkeMo
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
imp=getattr(bpy.ops,'import'); imp.import_opensim_model(filepath=OSIM)
bpy.context.view_layer.update()
wm=white_mat()
# place bones, delete muskemo muscles + markers
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

# create ES muscle curves
mcoll=bpy.data.collections.new("ES_muscles"); bpy.context.scene.collection.children.link(mcoll)
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
    ob.data.materials.append(mat)
    muscle_objs[nm]=(ob,mat)

def recolor(cond):
    for nm,(ob,mat) in muscle_objs.items():
        a=D['muscles'][nm][cond]; col,n=actcolor(a)
        b=mat.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value=(col[0],col[1],col[2],1)
        for en in ("Emission Color","Emission"):
            if en in b.inputs:
                try: b.inputs[en].default_value=(col[0],col[1],col[2],1)
                except: pass
        if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=0.3+1.6*n

# scene bbox/camera
mn=[1e9]*3; mx=[-1e9]*3
for o in bpy.data.objects:
    if o.type in ('MESH','CURVE') and not o.hide_render:
        for v in o.bound_box:
            wv=o.matrix_world@mathutils.Vector(v)
            for i in range(3): mn[i]=min(mn[i],wv[i]); mx[i]=max(mx[i],wv[i])
cx=(mn[0]+mx[0])/2; cy=(mn[1]+mx[1])/2; cz=(mn[2]+mx[2])/2; ortho=(mx[1]-mn[1])*1.12
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=760; sc.render.resolution_y=1050
sc.render.image_settings.file_format='PNG'; sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background')
if bg: bg.inputs[0].default_value=(0.09,0.10,0.12,1); bg.inputs[1].default_value=1.0
for loc,en in [((cx+2,cy+2,cz+3),5.0),((cx-2,cy+1,cz+3),3.5),((cx,cy-1,cz-3),2.5)]:
    bpy.ops.object.light_add(type='SUN',location=loc); bpy.context.object.data.energy=en
bpy.ops.object.camera_add(location=(0,0,0)); cam=bpy.context.object; sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=ortho; cam.data.sensor_fit='VERTICAL'
cam.data.clip_start=0.01; cam.data.clip_end=60
VIEWS={"side":(cx,cy,cz+5),"back":(cx-5,cy,cz)}
for cond in ['off','on']:
    recolor(cond)
    for vn,loc in VIEWS.items():
        cam.location=mathutils.Vector(loc); cam.rotation_euler=look_at(loc,(cx,cy,cz))
        fp=os.path.join(OUT,f"pilot_{cond}_{vn}.png"); sc.render.filepath=fp
        bpy.ops.render.render(write_still=True); print("[render]",cond,vn)
print("PILOT_DONE")
