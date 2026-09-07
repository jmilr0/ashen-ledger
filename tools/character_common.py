
"""Shared Blender helpers for Broken Seal party companion GLBs."""
from __future__ import annotations
import math, os, bmesh, bpy
from mathutils import Matrix, Vector

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..'))
if not os.path.isdir(os.path.join(ROOT, 'public', 'models')):
    ROOT = '/workspace/ashen-ledger'
OUT_DIR = os.path.join(ROOT, 'public', 'models', 'characters')
PREV_DIR = os.path.join(OUT_DIR, 'previews')
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PREV_DIR, exist_ok=True)
MAX_WIDTH_DEFAULT = 0.58

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                       bpy.data.lights, bpy.data.armatures, bpy.data.curves):
        for block in list(collection):
            if block.users == 0:
                collection.remove(block)

def mat(name, color, roughness=0.7, metallic=0.0, specular=0.35):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    if 'Metallic' in bsdf.inputs:
        bsdf.inputs['Metallic'].default_value = metallic
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = specular
    elif 'Specular' in bsdf.inputs:
        bsdf.inputs['Specular'].default_value = specular
    return m

def link_object(obj):
    col = bpy.context.scene.collection
    if obj.name not in col.objects:
        col.objects.link(obj)
    return obj

def new_mesh_object(name, mesh):
    obj = bpy.data.objects.new(name, mesh)
    link_object(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj

def shade_smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass

def apply_mat(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)

def bm_to_object(name, bm, material=None):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = new_mesh_object(name, mesh)
    if material is not None:
        apply_mat(obj, material)
    shade_smooth(obj)
    return obj

def join_named(name, objs):
    objs = [o for o in objs if o is not None and o.name in bpy.data.objects]
    if not objs:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = name
    if joined.data:
        joined.data.name = name
    shade_smooth(joined)
    return joined

def transform_apply(obj, location=True, rotation=True, scale=True):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)

def world_bounds(objects):
    xs, ys, zs = [], [], []
    for obj in objects:
        for corner in obj.bound_box:
            c = obj.matrix_world @ Vector(corner)
            xs.append(c.x); ys.append(c.y); zs.append(c.z)
    return {'min': (min(xs), min(ys), min(zs)), 'max': (max(xs), max(ys), max(zs)),
            'size': (max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))}

def plant_feet(objects):
    b = world_bounds(objects)
    dz = -b['min'][2]
    for obj in objects:
        obj.location.z += dz
        transform_apply(obj, location=True, rotation=False, scale=False)

def scale_group_to_height(objects, target_h):
    b = world_bounds(objects)
    h = b['size'][2]
    if h <= 1e-6:
        return
    s = target_h / h
    for obj in objects:
        obj.scale = (obj.scale[0]*s, obj.scale[1]*s, obj.scale[2]*s)
        transform_apply(obj, location=False, rotation=False, scale=True)
    plant_feet(objects)

def clamp_width(objects, max_width=MAX_WIDTH_DEFAULT):
    b = world_bounds(objects)
    width = b['size'][0]
    if width > max_width:
        sx = max_width / width
        print(f"Width {width:.3f} > {max_width}, scaling X by {sx:.4f}")
        for obj in objects:
            for v in obj.data.vertices:
                v.co.x *= sx
            obj.data.update()
        plant_feet(objects)

def count_tris(objects):
    total = 0
    for obj in objects:
        mesh = obj.data
        mesh.calc_loop_triangles()
        total += len(mesh.loop_triangles)
    return total

def subdivide_bm(bm, cuts=1):
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=cuts, use_grid_fill=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

def tube(bm, path, radii, segs=10, close_caps=True):
    rings = []
    for i, (p, r) in enumerate(zip(path, radii)):
        if i < len(path) - 1:
            tang = (path[i + 1] - p).normalized()
        else:
            tang = (p - path[i - 1]).normalized()
        up = Vector((0, 0, 1))
        if abs(tang.dot(up)) > 0.9:
            up = Vector((1, 0, 0))
        binormal = tang.cross(up).normalized()
        normal = binormal.cross(tang).normalized()
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            offset = (binormal * math.cos(a) + normal * math.sin(a)) * r
            row.append(bm.verts.new(p + offset))
        rings.append(row)
    bm.verts.ensure_lookup_table()
    for i in range(len(rings) - 1):
        for j in range(segs):
            j2 = (j + 1) % segs
            bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
    if close_caps:
        for ring, up in ((rings[0], False), (rings[-1], True)):
            c = sum((v.co for v in ring), Vector()) / len(ring)
            center = bm.verts.new(c)
            for j in range(segs):
                if up:
                    bm.faces.new((center, ring[j], ring[(j + 1) % segs]))
                else:
                    bm.faces.new((center, ring[(j + 1) % segs], ring[j]))
    return rings

def make_lathe_body(name, material, profile, segs=20, fold_amp=0.012, fold_freq=5,
                    skirt=None, hem_scale=1.03, subdiv=1, deepen_folds=True):
    bm = bmesh.new()
    rings = []
    for z, rx, ry, fold in profile:
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            wave = 1.0 + fold * math.sin(a * fold_freq + z * 6) + 0.4 * fold * math.cos(a * 3)
            x = rx * wave * math.cos(a)
            y = ry * wave * math.sin(a)
            if math.sin(a) > 0.25:
                y *= 0.90
            row.append(bm.verts.new((x, y, z)))
        rings.append(row)
    for i in range(len(rings) - 1):
        for j in range(segs):
            j2 = (j + 1) % segs
            bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
    top = rings[-1]
    c = sum((v.co for v in top), Vector()) / len(top)
    center = bm.verts.new(c)
    for j in range(segs):
        bm.faces.new((center, top[j], top[(j + 1) % segs]))
    prev = rings[0]
    if skirt:
        for z, rx, ry, fold in skirt:
            row = []
            for j in range(segs):
                a = (j / segs) * math.tau
                indent = 0.0
                if abs(math.cos(a)) < 0.4:
                    indent = -0.014 * (1.0 - abs(math.cos(a)) / 0.4)
                wave = 1.0 + fold * math.sin(a * 6 + z * 5)
                x = (rx * wave + indent) * math.cos(a)
                y = ry * wave * math.sin(a)
                row.append(bm.verts.new((x, y, z)))
            for j in range(segs):
                j2 = (j + 1) % segs
                bm.faces.new((prev[j], prev[j2], row[j2], row[j]))
            prev = row
    lip = [bm.verts.new((v.co.x * hem_scale, v.co.y * hem_scale, v.co.z - 0.018)) for v in prev]
    for j in range(segs):
        j2 = (j + 1) % segs
        bm.faces.new((prev[j], prev[j2], lip[j2], lip[j]))
    c2 = sum((v.co for v in lip), Vector()) / len(lip)
    c2.z -= 0.012
    center2 = bm.verts.new(c2)
    for j in range(segs):
        bm.faces.new((center2, lip[(j + 1) % segs], lip[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if subdiv:
        subdivide_bm(bm, subdiv)
    if deepen_folds:
        z0 = profile[0][0] - 0.35 if skirt else profile[0][0]
        z1 = profile[-2][0] if len(profile) > 1 else profile[-1][0]
        for v in bm.verts:
            if z0 < v.co.z < z1:
                a = math.atan2(v.co.y, v.co.x)
                n = Vector((v.co.x, v.co.y, 0))
                if n.length > 1e-4:
                    n.normalize()
                    v.co += n * (fold_amp * 0.4 * math.sin(a * 7 + v.co.z * 9))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object(name, bm, material)

def make_head(prefix, skin, hair_m, brow_m, hair_style='short'):
    parts = []
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=0.108)
    for v in bm.verts:
        x, y, z = v.co
        v.co.x = x * (0.86 if hair_style == 'lean' else 0.90)
        v.co.y = y * 0.94
        v.co.z = z * (1.16 if hair_style == 'lean' else 1.14)
        if z < -0.015:
            t = (z + 0.108) / 0.093
            v.co.x *= 0.86 + 0.14 * t
        if z > 0.045 and y > 0:
            v.co.y *= 0.90
        v.co += Vector((0, 0.012, 1.575))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object(f'_{prefix}_skull', bm, skin))

    bm = bmesh.new()
    path = [Vector((0, 0.072, 1.598)), Vector((0, 0.095, 1.575)),
            Vector((0, 0.112, 1.545)), Vector((0, 0.100, 1.528))]
    tube(bm, path, [0.012, 0.011, 0.013, 0.009], segs=8)
    for sx in (-1, 1):
        bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=0.006,
                                  matrix=Matrix.Translation((sx * 0.008, 0.098, 1.528)))
    parts.append(bm_to_object(f'_{prefix}_nose', bm, skin))

    for sx in (-1, 1):
        bm = bmesh.new()
        path, radii = [], []
        for i in range(7):
            t = i / 6
            path.append(Vector((sx * (0.015 + 0.048 * t), 0.088 - 0.008 * abs(t - 0.35),
                                1.608 + 0.012 * math.sin(t * math.pi) - 0.003 * t)))
            radii.append(0.007 - 0.002 * t)
        tube(bm, path, radii, segs=6)
        parts.append(bm_to_object(f'_{prefix}_brow{sx}', bm, brow_m))

    for sx in (-1, 1):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.030)
        for v in bm.verts:
            v.co.x *= 0.42; v.co.y *= 0.65; v.co.z *= 1.2
            v.co += Vector((sx * 0.098, -0.008, 1.568))
        parts.append(bm_to_object(f'_{prefix}_ear{sx}', bm, skin))

    eye_w = mat(f'{prefix}_EyeWhite', (0.90, 0.88, 0.84), 0.4)
    eye_d = mat(f'{prefix}_EyeDark', (0.07, 0.06, 0.05), 0.3)
    for sx in (-1, 1):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.015)
        for v in bm.verts:
            v.co.y *= 0.65
            v.co += Vector((sx * 0.034, 0.092, 1.575))
        parts.append(bm_to_object(f'_{prefix}_eye{sx}', bm, eye_w))
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.0075)
        for v in bm.verts:
            v.co += Vector((sx * 0.034, 0.103, 1.575))
        parts.append(bm_to_object(f'_{prefix}_iris{sx}', bm, eye_d))

    lip_m = mat(f'{prefix}_Lip', (0.60, 0.38, 0.34), 0.55)
    bm = bmesh.new()
    path = [Vector((t * 0.024, 0.090 - 0.008 * abs(t), 1.520)) for t in [-1,-0.6,-0.3,0,0.3,0.6,1]]
    tube(bm, path, [0.004]*7, segs=5)
    parts.append(bm_to_object(f'_{prefix}_mouth', bm, lip_m))

    bm = bmesh.new()
    if hair_style == 'tonsure':
        bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=0.118)
        kill = [v for v in bm.verts if v.co.z > 0.04 or v.co.z < -0.02]
        bmesh.ops.delete(bm, geom=kill, context='VERTS')
        for v in bm.verts:
            v.co.x *= 1.08; v.co.y *= 1.08
            v.co += Vector((0, -0.005, 1.585))
        for sx in (-1, 1):
            bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.028,
                                      matrix=Matrix.Translation((sx*0.085, 0.01, 1.555)))
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.050,
                                  matrix=Matrix.Translation((0, -0.070, 1.540)))
    elif hair_style == 'lean':
        bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=0.118)
        kill = [v for v in bm.verts if v.co.z < -0.02]
        bmesh.ops.delete(bm, geom=kill, context='VERTS')
        for v in bm.verts:
            v.co.x *= 1.02; v.co.y *= 1.15; v.co.z *= 0.95
            v.co += Vector((0, -0.02, 1.600))
        for x in (-0.04, 0.0, 0.04):
            bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.022,
                                      matrix=Matrix.Translation((x, 0.09, 1.600)))
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.055,
                                  matrix=Matrix.Translation((0, -0.08, 1.520)))
    elif hair_style == 'cropped':
        bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=10, radius=0.112)
        kill = [v for v in bm.verts if v.co.z < -0.01]
        bmesh.ops.delete(bm, geom=kill, context='VERTS')
        for v in bm.verts:
            v.co.x *= 1.04; v.co.y *= 1.05; v.co.z *= 0.88
            v.co += Vector((0, -0.008, 1.600))
    elif hair_style == 'coif_ready':
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.110)
        kill = [v for v in bm.verts if v.co.z < 0.02]
        bmesh.ops.delete(bm, geom=kill, context='VERTS')
        for v in bm.verts:
            v.co *= 0.95
            v.co += Vector((0, -0.01, 1.610))
    else:
        bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=0.120)
        kill = [v for v in bm.verts if v.co.z < -0.015]
        bmesh.ops.delete(bm, geom=kill, context='VERTS')
        for v in bm.verts:
            v.co.x *= 1.06; v.co.y *= 1.10; v.co.z *= 0.92
            v.co += Vector((0, -0.012, 1.605))
        for x in (-0.055, -0.025, 0.005, 0.035, 0.055):
            bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.026,
                                      matrix=Matrix.Translation((x, 0.085, 1.615 - abs(x)*0.2)))
        for sx in (-1, 1):
            bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.034,
                                      matrix=Matrix.Translation((sx*0.090, 0.015, 1.570)))
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.060,
                                  matrix=Matrix.Translation((0, -0.065, 1.545)))
    parts.append(bm_to_object(f'_{prefix}_hair', bm, hair_m))
    return join_named(f'{prefix}_Head', parts)

def make_belt(prefix, leather, z0=0.862, z1=0.908, rx=0.168, ry=0.125):
    bm = bmesh.new()
    segs = 24
    outer, inner = [], []
    for z in (z0, z1):
        o_row, i_row = [], []
        for j in range(segs):
            a = (j / segs) * math.tau
            o_row.append(bm.verts.new((rx * math.cos(a), ry * math.sin(a), z)))
            i_row.append(bm.verts.new(((rx-0.02)*math.cos(a), (ry-0.017)*math.sin(a), z)))
        outer.append(o_row); inner.append(i_row)
    for j in range(segs):
        j2 = (j + 1) % segs
        bm.faces.new((outer[0][j], outer[0][j2], outer[1][j2], outer[1][j]))
        bm.faces.new((inner[1][j], inner[1][j2], inner[0][j2], inner[0][j]))
        bm.faces.new((outer[1][j], outer[1][j2], inner[1][j2], inner[1][j]))
        bm.faces.new((inner[0][j], inner[0][j2], outer[0][j2], outer[0][j]))
    buckle = [
        (-0.028, ry-0.007, z0-0.006), (0.028, ry-0.007, z0-0.006),
        (0.028, ry+0.015, z0-0.006), (-0.028, ry+0.015, z0-0.006),
        (-0.028, ry-0.007, z1+0.006), (0.028, ry-0.007, z1+0.006),
        (0.028, ry+0.015, z1+0.006), (-0.028, ry+0.015, z1+0.006),
    ]
    bv = [bm.verts.new(p) for p in buckle]
    for f in [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]:
        bm.faces.new([bv[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object(f'{prefix}_Belt', bm, leather)

def make_limbs(prefix, sleeve_mat, skin, hose, boots_m, build='average', bare_forearms=True):
    parts = []
    specs = {
        'stocky': (0.062, 0.052, 0.040, 0.072, 0.050, 0.190),
        'lean':   (0.050, 0.040, 0.030, 0.055, 0.038, 0.160),
        'broad':  (0.060, 0.050, 0.038, 0.068, 0.048, 0.185),
        'average':(0.058, 0.048, 0.034, 0.066, 0.042, 0.175),
    }
    sh_r, ua, fa, th, calf, shoulder_x = specs.get(build, specs['average'])

    for sx, side in ((1, 'L'), (-1, 'R')):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=sh_r)
        for v in bm.verts:
            v.co.x *= 1.15
            v.co += Vector((sx * shoulder_x, 0.0, 1.285))
        parts.append(bm_to_object(f'_{prefix}_sh{side}', bm, sleeve_mat))

    for sx, side in ((1, 'L'), (-1, 'R')):
        bm = bmesh.new()
        path = [Vector((sx*(shoulder_x+0.02), 0.01, 1.24)),
                Vector((sx*(shoulder_x+0.045), 0.03, 1.10)),
                Vector((sx*(shoulder_x+0.06), 0.05, 0.96))]
        tube(bm, path, [ua, ua*0.92, ua*0.85], segs=10)
        parts.append(bm_to_object(f'_{prefix}_ua{side}', bm, sleeve_mat))

    for sx, side in ((1, 'L'), (-1, 'R')):
        bm = bmesh.new()
        path = [Vector((sx*(shoulder_x+0.06), 0.05, 0.96)),
                Vector((sx*(shoulder_x+0.07), 0.06, 0.86)),
                Vector((sx*(shoulder_x+0.075), 0.07, 0.78))]
        tube(bm, path, [fa, fa*0.9, fa*0.8], segs=10)
        parts.append(bm_to_object(f'_{prefix}_fa{side}', bm, skin if bare_forearms else sleeve_mat))

    for side, center in (('L', Vector((shoulder_x+0.075, 0.07, 0.76))),
                         ('R', Vector((-(shoulder_x+0.075), 0.07, 0.76)))):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.036)
        for v in bm.verts:
            v.co.x *= 0.85; v.co.z *= 1.1; v.co += center
        for fx in (-0.012, 0.0, 0.012, 0.022):
            tip = center + Vector((fx * (1 if side == 'L' else -0.3), 0.035, -0.025))
            bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.007, radius2=0.0045, depth=0.032,
                matrix=Matrix.Translation(tip) @ Matrix.Rotation(math.radians(75), 4, 'X'))
        parts.append(bm_to_object(f'_{prefix}_hand{side}', bm, skin))

    thigh_mat = hose if build == 'lean' else sleeve_mat
    for sx, side in ((0.092, 'L'), (-0.092, 'R')):
        bm = bmesh.new()
        tube(bm, [Vector((sx,0,0.70)), Vector((sx,0.01,0.55)), Vector((sx,0.015,0.40))],
             [th, th*0.88, th*0.76], segs=12)
        parts.append(bm_to_object(f'_{prefix}_th{side}', bm, thigh_mat))
        bm = bmesh.new()
        tube(bm, [Vector((sx,0.015,0.40)), Vector((sx,0.025,0.25)), Vector((sx,0.03,0.10))],
             [calf, calf*0.88, calf*0.75], segs=10)
        parts.append(bm_to_object(f'_{prefix}_calf{side}', bm, hose))

    for sx, side in ((0.092, 'L'), (-0.092, 'R')):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.050)
        for v in bm.verts:
            v.co.y *= 1.05; v.co.z *= 0.85
            v.co += Vector((sx, 0.02, 0.085))
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.044,
                                  matrix=Matrix.Translation((sx, 0.075, 0.032)))
        for v in bm.verts:
            local = v.co - Vector((sx, 0.075, 0.032))
            if abs(local.z) < 0.05 and (v.co - Vector((sx, 0.02, 0.085))).length > 0.055:
                v.co.y = 0.075 + local.y * 1.7
                v.co.z = 0.032 + local.z * 0.65
                v.co.x = sx + local.x * 0.88
            if v.co.z < 0.012:
                v.co.z = 0.008
        parts.append(bm_to_object(f'_{prefix}_boot{side}', bm, boots_m))
    return join_named(f'{prefix}_Limbs', parts)

def create_armature(name='Armature'):
    arm_data = bpy.data.armatures.new(name)
    arm_obj = bpy.data.objects.new(name, arm_data)
    link_object(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bones = arm_data.edit_bones
    def add_bone(bname, head, tail, parent=None):
        b = bones.new(bname)
        b.head = Vector(head); b.tail = Vector(tail)
        if parent is not None:
            b.parent = bones[parent]
        return b
    add_bone('Root', (0,0,0), (0,0,0.1))
    add_bone('Hips', (0,0,0.85), (0,0,1.0), 'Root')
    add_bone('Spine', (0,0,1.0), (0,0,1.2), 'Hips')
    add_bone('Chest', (0,0,1.2), (0,0,1.38), 'Spine')
    add_bone('Neck', (0,0,1.38), (0,0,1.48), 'Chest')
    add_bone('Head', (0,0,1.48), (0,0,1.70), 'Neck')
    add_bone('Shoulder_L', (0.08,0,1.30), (0.18,0,1.28), 'Chest')
    add_bone('UpperArm_L', (0.18,0,1.28), (0.24,0.04,0.96), 'Shoulder_L')
    add_bone('ForeArm_L', (0.24,0.04,0.96), (0.25,0.06,0.76), 'UpperArm_L')
    add_bone('Hand_L', (0.25,0.06,0.76), (0.25,0.09,0.70), 'ForeArm_L')
    add_bone('Shoulder_R', (-0.08,0,1.30), (-0.18,0,1.28), 'Chest')
    add_bone('UpperArm_R', (-0.18,0,1.28), (-0.22,0.05,0.96), 'Shoulder_R')
    add_bone('ForeArm_R', (-0.22,0.05,0.96), (-0.22,0.07,0.79), 'UpperArm_R')
    add_bone('Hand_R', (-0.22,0.07,0.79), (-0.22,0.09,0.73), 'ForeArm_R')
    add_bone('Thigh_L', (0.09,0,0.85), (0.09,0.01,0.42), 'Hips')
    add_bone('Calf_L', (0.09,0.01,0.42), (0.09,0.03,0.08), 'Thigh_L')
    add_bone('Foot_L', (0.09,0.03,0.08), (0.09,0.11,0.02), 'Calf_L')
    add_bone('Thigh_R', (-0.09,0,0.85), (-0.09,0.01,0.42), 'Hips')
    add_bone('Calf_R', (-0.09,0.01,0.42), (-0.09,0.03,0.08), 'Thigh_R')
    add_bone('Foot_R', (-0.09,0.03,0.08), (-0.09,0.11,0.02), 'Calf_R')
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

def finalize_scale(meshes, target_height, max_width=MAX_WIDTH_DEFAULT):
    scale_group_to_height(meshes, target_height)
    b = world_bounds(meshes)
    print(f"Pre-armature bounds size={tuple(round(x, 4) for x in b['size'])}")
    clamp_width(meshes, max_width)
    return meshes

def export_glb(path):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type in {'MESH', 'ARMATURE'} and not obj.name.startswith('Preview') and obj.name != 'CapsuleGuide':
            obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True,
        export_apply=True, export_yup=True, export_animations=False, export_skins=True, export_morph=False)

def setup_preview_world():
    scene = bpy.context.scene
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 768
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    bpy.ops.object.light_add(type='AREA', location=(2.2, -2.5, 3.2))
    key = bpy.context.active_object
    key.name = 'PreviewKey'; key.data.energy = 300; key.data.size = 2.5
    key.rotation_euler = (math.radians(50), math.radians(15), math.radians(35))
    bpy.ops.object.light_add(type='AREA', location=(-2.0, 1.5, 2.4))
    fill = bpy.context.active_object
    fill.name = 'PreviewFill'; fill.data.energy = 100; fill.data.size = 3.0
    fill.data.color = (0.75, 0.82, 0.9)
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 5))
    sun = bpy.context.active_object
    sun.name = 'PreviewSun'; sun.data.energy = 1.4
    sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(-20))
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = 'PreviewGround'
    ground.data.materials.append(mat('Ground', (0.45, 0.40, 0.34), 0.95))

def add_capsule_guide(height=1.75):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=height, vertices=24, location=(0, 0, height*0.5))
    guide = bpy.context.active_object
    guide.name = 'CapsuleGuide'
    m = mat('CapsuleGuide', (0.2, 0.55, 0.85), 0.4)
    try: m.blend_method = 'BLEND'
    except Exception: pass
    try:
        bsdf = m.node_tree.nodes.get('Principled BSDF')
        if 'Alpha' in bsdf.inputs: bsdf.inputs['Alpha'].default_value = 0.18
    except Exception: pass
    guide.data.materials.append(m)
    return guide

def render_previews(slug, height=1.75):
    setup_preview_world()
    guide = add_capsule_guide(height)
    bpy.ops.object.camera_add(location=(0, -3.2, 1.15))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam
    views = [('front', (0, 3.4, 1.15)), ('threequarter', (2.5, 2.7, 1.35))]
    target = Vector((0, 0, 0.95))
    guide.hide_render = True; guide.hide_viewport = True
    for name, loc in views:
        cam.location = loc
        cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        out = os.path.join(PREV_DIR, f'{slug}_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)

def cleanup_preview_helpers():
    for name in ('PreviewGround', 'CapsuleGuide', 'PreviewCam', 'PreviewKey', 'PreviewFill', 'PreviewSun'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

def write_scale_meta(slug, meshes, target_height, look_note=''):
    b = world_bounds(meshes)
    tris = count_tris(meshes)
    names = sorted(o.name for o in meshes)
    meta = os.path.join(PREV_DIR, f'{slug}_scale.txt')
    with open(meta, 'w') as f:
        f.write(f"height_m={b['size'][2]:.4f}\nwidth_x_m={b['size'][0]:.4f}\n"
                f"depth_y_m={b['size'][1]:.4f}\ntris={tris}\nobjects={','.join(names)}\n"
                f"capsule_diameter_m=0.60\nformation_spacing_m=0.90 (context only)\n"
                f"target_height_m={target_height}\nlook={look_note}\n")
    print('Wrote', meta)
    print(f'Done. height={b["size"][2]:.4f} width={b["size"][0]:.4f} tris={tris}')
    print('Objects:', names)
    return b, tris

def finish_character(slug, meshes, arm_name, target_height, max_width=MAX_WIDTH_DEFAULT, look_note=''):
    meshes = [m for m in meshes if m is not None]
    finalize_scale(meshes, target_height, max_width)
    arm = create_armature(arm_name)
    for obj in meshes:
        obj.parent = arm
    b = world_bounds(meshes)
    tris = count_tris(meshes)
    print(f"{slug} final size={tuple(round(x, 4) for x in b['size'])} tris={tris}")
    if tris < 10000: print('WARN: tris under 10k target')
    if tris > 28000: print('WARN: tris over 28k target')
    glb_path = os.path.join(OUT_DIR, f'{slug}.glb')
    export_glb(glb_path)
    print('Exported', glb_path)
    render_previews(slug, target_height)
    cleanup_preview_helpers()
    export_glb(glb_path)
    print('Re-exported clean', glb_path)
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    write_scale_meta(slug, mesh_objs, target_height, look_note=look_note)
    return glb_path
