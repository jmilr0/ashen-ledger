"""Blender: Locked burial-ground gate (Broken Seal) — game-ready GLB + previews.

Iron/wood churchyard gate that reads LOCKED (chain + padlock + bar), stone posts.
For the unburied-child parish beat. Dirt-and-mail Occitania 1208 — NO fantasy glow.
Rebuild:
  /usr/bin/blender -b -P tools/make_burial_gate.py

Scale notes:
  - Origin at ground center between posts
  - Clear opening ~1.7 m; posts ~1.7 m tall; gate leaf ~1.5 m high
  - Collision shell tight to mesh; only interact latch may run ~1.2× for RMB
"""
from __future__ import annotations

import math
import os
import bmesh
import bpy
from mathutils import Vector

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..'))
if not os.path.isdir(os.path.join(ROOT, 'public', 'models')):
    ROOT = '/workspace/ashen-ledger'
OUT_DIR = os.path.join(ROOT, 'public', 'models', 'props')
PREV_DIR = os.path.join(OUT_DIR, 'previews')
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PREV_DIR, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                       bpy.data.lights, bpy.data.curves):
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


def shade_flat(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = False
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.shade_flat()
    except Exception:
        pass


def apply_mat(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)


def bm_to_object(name, bm, material=None, smooth=True):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = new_mesh_object(name, mesh)
    if material is not None:
        apply_mat(obj, material)
    if smooth:
        shade_smooth(obj)
    else:
        shade_flat(obj)
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
    return {
        'min': (min(xs), min(ys), min(zs)),
        'max': (max(xs), max(ys), max(zs)),
        'size': (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)),
    }


def plant_and_center(objects):
    """Origin at ground center between posts."""
    b = world_bounds(objects)
    cx = (b['min'][0] + b['max'][0]) * 0.5
    cy = (b['min'][1] + b['max'][1]) * 0.5
    dz = -b['min'][2]
    for obj in objects:
        obj.location.x -= cx
        obj.location.y -= cy
        obj.location.z += dz
        transform_apply(obj, location=True, rotation=False, scale=False)


def count_tris(objects):
    total = 0
    for obj in objects:
        mesh = obj.data
        mesh.calc_loop_triangles()
        total += len(mesh.loop_triangles)
    return total


def box_bm(bm, xmin, xmax, ymin, ymax, zmin, zmax):
    verts = [
        bm.verts.new((xmin, ymin, zmin)),
        bm.verts.new((xmax, ymin, zmin)),
        bm.verts.new((xmax, ymax, zmin)),
        bm.verts.new((xmin, ymax, zmin)),
        bm.verts.new((xmin, ymin, zmax)),
        bm.verts.new((xmax, ymin, zmax)),
        bm.verts.new((xmax, ymax, zmax)),
        bm.verts.new((xmin, ymax, zmax)),
    ]
    bm.verts.ensure_lookup_table()
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    for f in faces:
        bm.faces.new([verts[i] for i in f])
    return verts


def wear_stone(bm, amp=0.01, seed=2.0):
    for v in bm.verts:
        n = math.sin(v.co.x * 6.3 + seed) * math.cos(v.co.z * 5.1 + seed)
        v.co.x += amp * 0.5 * n
        v.co.y += amp * 0.4 * math.sin(v.co.z * 4.2 + seed)
        if v.co.z > 0.05:
            v.co.z += amp * 0.25 * math.cos(v.co.x * 7.0)


def tube(bm, path, radii, segs=8, close_caps=True):
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


def make_posts(limestone, mud):
    """Pair of worn limestone gate posts with simple caps."""
    parts = []
    # Opening half-width (inner face of posts)
    half = 0.95
    post_w = 0.32
    post_d = 0.36
    post_h = 1.72

    for side, sx in (('L', -1), ('R', 1)):
        bm = bmesh.new()
        x0 = sx * half
        x1 = sx * (half + post_w)
        box_bm(bm, min(x0, x1), max(x0, x1), -post_d / 2, post_d / 2, 0.0, post_h)
        wear_stone(bm, amp=0.012, seed=4.0 + sx)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Gate_Post{side}', bm, limestone, smooth=False))

        # Cap / coping
        bm = bmesh.new()
        cx0 = min(x0, x1) - 0.04
        cx1 = max(x0, x1) + 0.04
        box_bm(bm, cx0, cx1, -post_d / 2 - 0.04, post_d / 2 + 0.04,
               post_h - 0.02, post_h + 0.14)
        # slight pyramid by lifting center-ish top verts
        for v in bm.verts:
            if v.co.z > post_h + 0.08:
                v.co.z += 0.06 * (1.0 - abs(v.co.y) / (post_d / 2 + 0.05))
        wear_stone(bm, amp=0.006, seed=9 + sx)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Gate_Cap{side}', bm, limestone, smooth=False))

        # Iron pintle / hinge stub on left post (gate hangs from L)
        if sx < 0:
            for i, z in enumerate((0.35, 1.25)):
                bm = bmesh.new()
                path = [
                    Vector((x0 + 0.02, 0.0, z)),
                    Vector((x0 - 0.04, 0.05, z)),
                    Vector((x0 - 0.08, 0.08, z)),
                ]
                tube(bm, path, [0.022, 0.020, 0.018], segs=8)
                iron = mat(f'_pintle_mat_{i}', (0.28, 0.26, 0.22), 0.5, metallic=0.55, specular=0.4)
                parts.append(bm_to_object(f'Gate_Pintle{i}', bm, iron, smooth=True))

    # Low mud / earth at bases
    for i, (mx, my) in enumerate((
        (-half - post_w * 0.5, 0.12),
        (half + post_w * 0.5, -0.08),
        (-half - 0.1, -0.18),
        (half + 0.05, 0.15),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=0.11)
        for v in bm.verts:
            v.co.z *= 0.45
            v.co.x *= 1.3
            v.co += Vector((mx, my, 0.03))
            if v.co.z < 0:
                v.co.z = 0.003
        parts.append(bm_to_object(f'_gmud{i}', bm, mud, smooth=True))

    return join_named('Gate_Posts', parts)


def make_gate_leaf(oak, iron):
    """Wooden framed gate with iron bars / rails — shut between posts."""
    parts = []
    # Gate fills opening with small gap; hangs slightly toward -Y (street)
    x0, x1 = -0.88, 0.88
    y0, y1 = -0.06, 0.06
    z0, z1 = 0.12, 1.48

    # Outer frame
    frame = [
        (x0, x0 + 0.09, z0, z1),       # left stile
        (x1 - 0.09, x1, z0, z1),       # right stile
        (x0, x1, z0, z0 + 0.09),       # bottom rail
        (x0, x1, z1 - 0.09, z1),       # top rail
        (x0, x1, 0.72, 0.82),          # mid rail
    ]
    for i, (xa, xb, za, zb) in enumerate(frame):
        bm = bmesh.new()
        box_bm(bm, xa, xb, y0, y1, za, zb)
        parts.append(bm_to_object(f'_frame{i}', bm, oak, smooth=False))

    # Vertical wooden pickets / boards
    n_pickets = 7
    for i in range(n_pickets):
        t = (i + 0.5) / n_pickets
        x = x0 + 0.12 + t * (x1 - x0 - 0.24)
        bm = bmesh.new()
        box_bm(bm, x - 0.035, x + 0.035, y0 + 0.01, y1 - 0.01, z0 + 0.1, z1 - 0.1)
        # pointed top suggestion
        for v in bm.verts:
            if v.co.z > z1 - 0.18:
                v.co.z += 0.04 * (1.0 - abs(v.co.x - x) / 0.04)
        parts.append(bm_to_object(f'_picket{i}', bm, oak, smooth=False))

    # Iron cross-bars (reads as churchyard iron)
    for i, z in enumerate((0.40, 1.05)):
        bm = bmesh.new()
        path = [Vector((x0 + 0.05, 0.0, z)), Vector((x1 - 0.05, 0.0, z))]
        tube(bm, path, [0.018, 0.018], segs=8)
        parts.append(bm_to_object(f'Gate_IronBar{i}', bm, iron, smooth=True))

    # Diagonal brace (wood)
    bm = bmesh.new()
    # approximate diagonal as thin box by placing verts
    # from lower-left to mid-right
    path = [
        Vector((x0 + 0.12, 0.0, z0 + 0.15)),
        Vector((0.2, 0.0, 0.75)),
        Vector((x1 - 0.15, 0.0, z1 - 0.2)),
    ]
    tube(bm, path, [0.028, 0.030, 0.028], segs=6)
    parts.append(bm_to_object('Gate_Brace', bm, oak, smooth=True))

    # Hinge straps on left
    for i, z in enumerate((0.38, 1.20)):
        bm = bmesh.new()
        box_bm(bm, x0 - 0.02, x0 + 0.28, y0 - 0.02, y1 + 0.01, z - 0.03, z + 0.03)
        parts.append(bm_to_object(f'Gate_HingeStrap{i}', bm, iron, smooth=False))

    return join_named('Gate_Leaf', parts)


def make_lock_hardware(iron, oak):
    """Horizontal bar + chain + padlock — must read LOCKED at iso distance."""
    parts = []
    # Heavy timber bar across gate (street side)
    bm = bmesh.new()
    box_bm(bm, -1.05, 1.05, -0.12, -0.04, 0.88, 1.02)
    # slightly irregular hewn look
    for v in bm.verts:
        v.co.z += 0.008 * math.sin(v.co.x * 8)
    parts.append(bm_to_object('Gate_Bar', bm, oak, smooth=False))

    # Iron keepers / brackets on both posts holding the bar
    for sx in (-1, 1):
        bm = bmesh.new()
        x = sx * 0.95
        box_bm(bm, x - 0.06 * sx - 0.05, x - 0.06 * sx + 0.05,
               -0.14, 0.08, 0.82, 1.08)
        # U-slot lips
        box_bm(bm, x - 0.08, x + 0.08, -0.16, -0.12, 0.84, 0.90)
        box_bm(bm, x - 0.08, x + 0.08, -0.16, -0.12, 1.00, 1.06)
        parts.append(bm_to_object(f'Gate_Keeper{"L" if sx < 0 else "R"}', bm, iron, smooth=False))

    # Chain loops over bar center → padlock (readable lock)
    bm = bmesh.new()
    # hanging chain path
    path, radii = [], []
    n = 18
    for i in range(n):
        t = i / (n - 1)
        # from bar top, drape down and toward latch
        x = 0.15 + 0.35 * t
        y = -0.10 - 0.04 * math.sin(t * math.pi)
        z = 1.02 - 0.35 * math.sin(t * math.pi) - 0.05 * t
        if t < 0.15:
            z = 1.02 - t / 0.15 * 0.05
        path.append(Vector((x, y, z)))
        radii.append(0.022 + 0.003 * math.sin(t * math.pi * 6))
    tube(bm, path, radii, segs=8)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Gate_Chain', bm, iron, smooth=True))

    # Extra chain wrap around bar
    bm = bmesh.new()
    path2, radii2 = [], []
    for i in range(16):
        t = i / 15
        ang = t * math.tau * 2.2
        r = 0.09
        x = 0.12 + r * math.cos(ang) * 0.3
        y = -0.08 + r * math.sin(ang)
        z = 0.95 + r * math.cos(ang)
        path2.append(Vector((x, y, z)))
        radii2.append(0.018)
    tube(bm, path2, radii2, segs=6)
    parts.append(bm_to_object('Gate_ChainWrap', bm, iron, smooth=True))

    # Padlock body (chunky, readable)
    bm = bmesh.new()
    box_bm(bm, 0.42, 0.62, -0.16, -0.04, 0.55, 0.78)
    # rounded bottom by pushing
    for v in bm.verts:
        if v.co.z < 0.60:
            v.co.x = 0.52 + (v.co.x - 0.52) * 0.85
    parts.append(bm_to_object('Gate_PadlockBody', bm, iron, smooth=False))

    # Shackle
    bm = bmesh.new()
    segs = 12
    path3, radii3 = [], []
    for i in range(segs):
        t = i / (segs - 1)
        # U shackle
        if t < 0.2:
            x = 0.46
            z = 0.78 + t / 0.2 * 0.08
        elif t < 0.8:
            a = (t - 0.2) / 0.6 * math.pi
            x = 0.52 + 0.08 * math.cos(math.pi - a)
            z = 0.86 + 0.08 * math.sin(a)
        else:
            x = 0.58
            z = 0.86 - (t - 0.8) / 0.2 * 0.08
        path3.append(Vector((x, -0.10, z)))
        radii3.append(0.016)
    tube(bm, path3, radii3, segs=6)
    parts.append(bm_to_object('Gate_Shackle', bm, iron, smooth=True))

    # Keyhole suggestion (dark indent as tiny box)
    bm = bmesh.new()
    box_bm(bm, 0.50, 0.54, -0.165, -0.155, 0.64, 0.72)
    dark = mat('Gate_Keyhole', (0.08, 0.07, 0.06), 0.9, metallic=0.2, specular=0.2)
    parts.append(bm_to_object('Gate_Keyhole', bm, dark, smooth=False))

    # Hasps / staples on gate leaf where chain attaches
    bm = bmesh.new()
    box_bm(bm, 0.35, 0.48, -0.08, 0.02, 0.70, 0.78)
    parts.append(bm_to_object('Gate_Hasp', bm, iron, smooth=False))

    return join_named('Gate_Lock', parts)


def make_low_wall_stubs(limestone):
    """Short wall stubs outward from posts (churchyard continuity)."""
    parts = []
    half = 0.95
    post_w = 0.32
    for side, sx in (('L', -1), ('R', 1)):
        bm = bmesh.new()
        x_start = sx * (half + post_w)
        x_end = sx * (half + post_w + 0.55)
        box_bm(bm, min(x_start, x_end), max(x_start, x_end),
               -0.14, 0.14, 0.0, 0.95)
        # coping
        box_bm(bm, min(x_start, x_end) - 0.02 * sx, max(x_start, x_end) + 0.02 * sx,
               -0.16, 0.16, 0.92, 1.05)
        wear_stone(bm, amp=0.01, seed=12 + sx)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Gate_Wall{side}', bm, limestone, smooth=False))
    return join_named('Gate_Walls', parts)


def build_burial_gate():
    clear_scene()
    limestone = mat('Gate_Limestone', (0.60, 0.55, 0.43), 0.90, specular=0.16)
    oak = mat('Gate_Oak', (0.30, 0.20, 0.11), 0.85, specular=0.20)
    mud = mat('Gate_Mud', (0.28, 0.22, 0.14), 0.96, specular=0.08)
    iron = mat('Gate_Iron', (0.27, 0.25, 0.22), 0.52, metallic=0.58, specular=0.42)

    meshes = [
        make_posts(limestone, mud),
        make_gate_leaf(oak, iron),
        make_lock_hardware(iron, oak),
        make_low_wall_stubs(limestone),
    ]
    meshes = [m for m in meshes if m is not None]
    plant_and_center(meshes)

    b = world_bounds(meshes)
    tris = count_tris(meshes)
    print(f"Burial gate size={tuple(round(x, 4) for x in b['size'])} "
          f"min={tuple(round(x, 4) for x in b['min'])} tris={tris}")
    return meshes


def export_glb(path):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and not obj.name.startswith('Preview'):
            obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_animations=False,
        export_skins=False,
        export_morph=False,
    )


def setup_preview_world():
    scene = bpy.context.scene
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

    bpy.ops.object.light_add(type='AREA', location=(3.0, -3.5, 3.5))
    key = bpy.context.active_object
    key.name = 'PreviewKey'
    key.data.energy = 320
    key.data.size = 3.0
    key.rotation_euler = (math.radians(52), math.radians(8), math.radians(30))

    bpy.ops.object.light_add(type='AREA', location=(-2.5, 2.0, 2.5))
    fill = bpy.context.active_object
    fill.name = 'PreviewFill'
    fill.data.energy = 100
    fill.data.size = 3.5
    fill.data.color = (0.72, 0.78, 0.88)

    bpy.ops.object.light_add(type='SUN', location=(0, 0, 6))
    sun = bpy.context.active_object
    sun.name = 'PreviewSun'
    sun.data.energy = 1.3
    sun.rotation_euler = (math.radians(40), math.radians(8), math.radians(-28))

    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = 'PreviewGround'
    ground.data.materials.append(mat('Ground', (0.35, 0.31, 0.23), 0.95))


def render_previews():
    setup_preview_world()
    bpy.ops.object.camera_add(location=(0, -5.0, 1.5))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam
    target = Vector((0, 0, 0.95))

    views = [
        ('front', (0.0, -5.2, 1.4)),
        ('threequarter', (4.0, -3.8, 2.2)),
    ]
    for name, loc in views:
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        out = os.path.join(PREV_DIR, f'burial_gate_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)


def cleanup_preview_helpers():
    for name in ('PreviewGround', 'PreviewCam', 'PreviewKey', 'PreviewFill', 'PreviewSun'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def main():
    meshes = build_burial_gate()
    glb_path = os.path.join(OUT_DIR, 'burial_gate.glb')
    export_glb(glb_path)
    print('Exported', glb_path)

    render_previews()
    cleanup_preview_helpers()
    export_glb(glb_path)
    print('Re-exported clean', glb_path)

    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    b = world_bounds(mesh_objs)
    tris = count_tris(mesh_objs)
    names = sorted(o.name for o in mesh_objs)
    meta = os.path.join(PREV_DIR, 'burial_gate_scale.txt')
    with open(meta, 'w') as f:
        f.write(
            f"height_m={b['size'][2]:.4f}\n"
            f"width_x_m={b['size'][0]:.4f}\n"
            f"depth_y_m={b['size'][1]:.4f}\n"
            f"tris={tris}\n"
            f"objects={','.join(names)}\n"
            f"origin=ground_center_between_posts\n"
            f"collision=tight_to_mesh\n"
            f"interact_latch_note=~1.2x generous RMB latch only (not collider shell)\n"
            f"opening_m~=1.90 locked=bar+chain+padlock\n"
            f"style=churchyard_iron_wood_occitan_1208\n"
        )
    print('Wrote', meta)
    print(f'Done. height={b["size"][2]:.4f} width={b["size"][0]:.4f} depth={b["size"][1]:.4f} tris={tris}')
    print('Objects:', names)


if __name__ == '__main__':
    main()
