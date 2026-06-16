import bpy, os, json, mathutils
FRAME="/tmp/cmp_render/squat_motion_frames/frame_2.000.json"
OSIM="/tmp/cmp_render/tlfb/TLFB.osim"
OUT="/tmp/cmp_render/squat_pose"; os.makedirs(OUT,exist_ok=True)
RAD=0.006
D=json.load(open(FRAME))
def mat_from(R,p):
    return mathutils.Matrix(((R[0],R[1],R[2],p[0]),(R[3],R[4],R[5],p[1]),(R[6],R[7],R[8],p[2]),(0,0,0,1)))
def look_at(cl,t):
    cl=mathutils.Vector(cl); t=mathutils.Vector(t); f=(t-cl).normalized(); up=mathutils.Vector((0,1,0))
    r=f.cross(up); r=r if r.length>1e-6 else mathutils.Vector((1,0,0)); r.normalize(); u=r.cross(f).normalized()
    return mathutils.Matrix(((r.x,u.x,-f.x),(r.y,u.y,-f.y),(r.z,u.z,-f.z))).to_euler()
def white_mat():
    m=bpy.data.materials.new("BoneWhite"); m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(0.92,0.91,0.86,1)
    if "Alpha" in b.inputs: b.inputs["Alpha"].default_value=0.88
    for en in ("Emission Color","Emission"):
        if en in b.inputs:
            try: b.inputs[en].default_value=(0.85,0.84,0.78,1)
            except: pass
    if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=0.4
    m.blend_method='BLEND'; return m
def musc_mat():
    m=bpy.data.materials.new("Musc"); m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(0.80,0.30,0.32,1)
    for en in ("Emission Color","Emission"):
        if en in b.inputs:
            try: b.inputs[en].default_value=(0.7,0.25,0.27,1)
            except: pass
    if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=0.5
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
    if any(k in coll.name.lower() for k in ['wrap','joint cent','landmark','frame','muscle']): coll.hide_render=True
mm=musc_mat(); mcoll=bpy.data.collections.new("ES"); bpy.context.scene.collection.children.link(mcoll)
for nm,md in D['muscles'].items():
    pts=md['pts']
    if len(pts)<2: continue
    cu=bpy.data.curves.new(nm,'CURVE'); cu.dimensions='3D'
    sp=cu.splines.new('POLY'); sp.points.add(len(pts)-1)
    for i,(x,y,z) in enumerate(pts): sp.points[i].co=(x,y,z,1)
    cu.bevel_depth=RAD; cu.use_fill_caps=True
    ob=bpy.data.objects.new(nm,cu); mcoll.objects.link(ob); ob.data.materials.append(mm)
mn=[1e9]*3; mx=[-1e9]*3
for o in bpy.data.objects:
    if o.type in ('MESH','CURVE') and not o.hide_render:
        for v in o.bound_box:
            wv=o.matrix_world@mathutils.Vector(v)
            for i in range(3): mn[i]=min(mn[i],wv[i]); mx[i]=max(mx[i],wv[i])
cx=(mn[0]+mx[0])/2; cy=(mn[1]+mx[1])/2; cz=(mn[2]+mx[2])/2
RESX,RESY=820,1020
ortho=max(mx[1]-mn[1], (mx[0]-mn[0])*RESY/RESX, (mx[2]-mn[2])*RESY/RESX)*1.08
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=RESX; sc.render.resolution_y=RESY
sc.render.image_settings.file_format='PNG'; sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background')
if bg: bg.inputs[0].default_value=(0.07,0.075,0.09,1); bg.inputs[1].default_value=1.0
for loc,en in [((cx+2,cy+2,cz+3),5.0),((cx-2,cy+1,cz+3),4.0),((cx,cy-1,cz-3),2.8)]:
    bpy.ops.object.light_add(type='SUN',location=loc); bpy.context.object.data.energy=en
bpy.ops.object.camera_add(location=(0,0,0)); cam=bpy.context.object; sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=ortho; cam.data.sensor_fit='VERTICAL'; cam.data.clip_start=0.01; cam.data.clip_end=60
# ground line: add a faint plane at foot level for reference
VIEWS={"side":(cx,cy,cz+6),"front":(cx+6,cy,cz)}
for vn,loc in VIEWS.items():
    cam.location=mathutils.Vector(loc); cam.rotation_euler=look_at(loc,(cx,cy,cz))
    sc.render.filepath=os.path.join(OUT,f"squat_{vn}.png"); bpy.ops.render.render(write_still=True); print("[render]",vn)
print("SQUAT_POSE_DONE")
