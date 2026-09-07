"""Blender: Ruined priory false altar (Broken Seal) — game-ready GLB + previews.

Real limestone table + cheap wood false face / hollow front (fake shrine for the
splinter), wax stubs. Dirt-and-mail Occitania 1208 — NO holy FX / fantasy glow.
Rebuild:
  /usr/bin/blender -b -P tools/make_false_altar.py

Scale notes:
  - Origin at ground center of altar footprint
  - Table ~1.5 m wide × ~0.9 m deep × ~1.05 m high (top slab)
  - Collision shell tight to mesh; interact latch may run ~1.2× for RMB
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
        (0, 1, 2, 3), (4, 7, 6, 5),
        (0, 4, 5, 1), (1, 5, 6, 2),
        (2, 6, 7, 3), (3, 7, 4, 0),
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


def make_stone_table(limestone, mud):
    """Real ruined limestone mensa on twin supports — the honest stone."""
    parts = []
    # Twin stone supports (real)
    for i, x in enumerate((-0.45, 0.45)):
        bm = bmesh.new()
        box_bm(bm, x - 0.18, x + 0.18, -0.28, 0.28, 0.0, 0.78)
        wear_stone(bm, amp=0.014, seed=3.0 + i)
        # slight batter
        for v in bm.verts:
            if v.co.z > 0.4:
                v.co.x += (0.02 if x > 0 else -0.02) * (v.co.z - 0.4)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Altar_Support{i}', bm, limestone, smooth=False))

    # Thick stone slab (real table)
    bm = bmesh.new()
    box_bm(bm, -0.78, 0.78, -0.42, 0.42, 0.78, 0.98)
    # chipped front edge
    for v in bm.verts:
        if v.co.y < -0.35 and v.co.z > 0.9:
            v.co.z -= 0.02 * abs(math.sin(v.co.x * 9))
            v.co.y += 0.015 * math.sin(v.co.x * 7)
        if abs(v.co.x) > 0.7 and v.co.z > 0.9:
            v.co.z -= 0.018 * abs(math.sin(v.co.y * 11 + 1))
    wear_stone(bm, amp=0.01, seed=7.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Altar_Slab', bm, limestone, smooth=False))

    # Mud / rubble at base
    for i, (mx, my, mr) in enumerate((
        (-0.5, 0.2, 0.09), (0.48, -0.18, 0.08), (0.1, 0.32, 0.07), (-0.2, -0.3, 0.075),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=mr)
        for v in bm.verts:
            v.co.z *= 0.4
            v.co.x *= 1.4
            v.co += Vector((mx, my, 0.025))
            if v.co.z < 0:
                v.co.z = 0.002
        parts.append(bm_to_object(f'_amud{i}', bm, mud, smooth=True))

    return join_named('Altar_Stone', parts)


def make_false_front(cheap_oak, dark_oak):
    """Cheap wood false altar face / hollow front — reads as FAKE shrine."""
    parts = []
    # Front panel (thin cheap boards, slightly proud of stone)
    # Hollow cavity behind: open underside / back gap so it reads fake
    y_face = -0.48
    # Main false face panel
    bm = bmesh.new()
    box_bm(bm, -0.72, 0.72, y_face - 0.04, y_face + 0.02, 0.08, 0.82)
    for v in bm.verts:
        v.co.z += 0.006 * math.sin(v.co.x * 10)
    parts.append(bm_to_object('Altar_FalseFace', bm, cheap_oak, smooth=False))

    # Vertical board seams (thin darker strips)
    for i, x in enumerate((-0.36, 0.0, 0.36)):
        bm = bmesh.new()
        box_bm(bm, x - 0.012, x + 0.012, y_face - 0.045, y_face + 0.025, 0.1, 0.80)
        parts.append(bm_to_object(f'_seam{i}', bm, dark_oak, smooth=False))

    # Crude painted cross suggestion (dark wood inlay — NO glow)
    bm = bmesh.new()
    # vertical bar
    box_bm(bm, -0.04, 0.04, y_face - 0.05, y_face - 0.035, 0.28, 0.68)
    # horizontal bar
    box_bm(bm, -0.16, 0.16, y_face - 0.05, y_face - 0.035, 0.50, 0.58)
    parts.append(bm_to_object('Altar_FakeCross', bm, dark_oak, smooth=False))

    # Side cheeks of false box (hollow interior readable from sides)
    for sx in (-1, 1):
        bm = bmesh.new()
        x0 = sx * 0.70
        box_bm(bm, x0 - 0.03 * sx, x0 + 0.02 * sx if sx > 0 else x0 - 0.02,
               y_face, -0.15, 0.08, 0.78)
        # Fix box coords properly
        bm.free()
        bm = bmesh.new()
        if sx < 0:
            box_bm(bm, -0.74, -0.68, y_face, -0.12, 0.08, 0.78)
        else:
            box_bm(bm, 0.68, 0.74, y_face, -0.12, 0.08, 0.78)
        parts.append(bm_to_object(f'Altar_Cheek{"L" if sx < 0 else "R"}', bm, cheap_oak, smooth=False))

    # Back of false box open / thin lip only (hollow)
    bm = bmesh.new()
    box_bm(bm, -0.68, 0.68, -0.16, -0.12, 0.08, 0.14)  # bottom lip
    box_bm(bm, -0.68, 0.68, -0.16, -0.12, 0.72, 0.78)  # top lip
    parts.append(bm_to_object('Altar_HollowLip', bm, dark_oak, smooth=False))

    # Pegs / nails (iron dots) holding cheap face
    iron = mat('Altar_Nail', (0.30, 0.28, 0.24), 0.5, metallic=0.55, specular=0.4)
    for i, (x, z) in enumerate(((-0.6, 0.2), (0.6, 0.2), (-0.6, 0.7), (0.6, 0.7), (0.0, 0.75))):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=0.012)
        for v in bm.verts:
            v.co += Vector((x, y_face - 0.03, z))
        parts.append(bm_to_object(f'_nail{i}', bm, iron, smooth=True))

    return join_named('Altar_False', parts)


def make_wax_stubs(wax, wick_mat):
    """Burned-down wax stubs — no flame, no holy FX."""
    parts = []
    # Positions on stone slab
    stubs = [
        (-0.35, -0.15, 0.98, 0.028, 0.09),
        (-0.18, 0.12, 0.98, 0.032, 0.055),
        (0.22, -0.08, 0.98, 0.025, 0.07),
        (0.48, 0.18, 0.98, 0.030, 0.045),
        (0.05, 0.05, 0.98, 0.022, 0.035),  # nearly spent
    ]
    for i, (x, y, z0, r, h) in enumerate(stubs):
        bm = bmesh.new()
        segs = 10
        # tapered stub with drips
        rings = []
        for k, (t, rr, zz) in enumerate((
            (0.0, r * 1.15, 0.0),
            (0.25, r * 1.05, h * 0.25),
            (0.55, r * 0.95, h * 0.55),
            (0.85, r * 0.75, h * 0.85),
            (1.0, r * 0.55, h),
        )):
            row = []
            for j in range(segs):
                a = (j / segs) * math.tau
                irr = rr * (1.0 + 0.08 * math.sin(a * 3 + i) + 0.05 * math.cos(a * 5))
                # drip bulge mid
                if 0.2 < t < 0.5 and j % 3 == 0:
                    irr *= 1.25
                row.append(bm.verts.new((
                    x + irr * math.cos(a),
                    y + irr * math.sin(a),
                    z0 + zz,
                )))
            rings.append(row)
        for ri in range(len(rings) - 1):
            for j in range(segs):
                j2 = (j + 1) % segs
                bm.faces.new((rings[ri][j], rings[ri][j2], rings[ri + 1][j2], rings[ri + 1][j]))
        # top crater
        top = rings[-1]
        c = sum((v.co for v in top), Vector()) / len(top)
        crater = bm.verts.new((c.x, c.y, c.z - 0.008))
        for j in range(segs):
            bm.faces.new((crater, top[(j + 1) % segs], top[j]))
        # bottom
        bot = rings[0]
        c0 = sum((v.co for v in bot), Vector()) / len(bot)
        center0 = bm.verts.new((c0.x, c0.y, z0))
        for j in range(segs):
            bm.faces.new((center0, bot[j], bot[(j + 1) % segs]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Altar_Wax{i}', bm, wax, smooth=True))

        # Blackened wick stub
        bm = bmesh.new()
        path = [
            Vector((x, y, z0 + h - 0.005)),
            Vector((x + 0.003, y, z0 + h + 0.012)),
        ]
        tube(bm, path, [0.004, 0.003], segs=5)
        parts.append(bm_to_object(f'_wick{i}', bm, wick_mat, smooth=True))

    # Pooled wax puddles on slab
    for i, (x, y, s) in enumerate(((-0.32, -0.12, 0.05), (0.25, -0.05, 0.04), (0.45, 0.15, 0.035))):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=4, radius=s)
        for v in bm.verts:
            v.co.z *= 0.15
            v.co.x *= 1.5
            v.co += Vector((x, y, 0.985))
            if v.co.z < 0.98:
                v.co.z = 0.982
        parts.append(bm_to_object(f'_puddle{i}', bm, wax, smooth=True))

    return join_named('Altar_Wax', parts)


def make_splinter_plinth(oak, limestone):
    """Small cheap stand on slab where splinter sits — empty / ready."""
    parts = []
    bm = bmesh.new()
    box_bm(bm, -0.08, 0.08, -0.06, 0.06, 0.98, 1.05)
    parts.append(bm_to_object('Altar_Plinth', bm, oak, smooth=False))
    # Cloth scrap under (dull linen, not holy glow)
    cloth = mat('Altar_Cloth', (0.55, 0.50, 0.40), 0.92, specular=0.1)
    bm = bmesh.new()
    box_bm(bm, -0.22, 0.22, -0.14, 0.14, 0.975, 0.985)
    for v in bm.verts:
        v.co.z += 0.004 * math.sin(v.co.x * 12) * math.cos(v.co.y * 10)
    parts.append(bm_to_object('Altar_Cloth', bm, cloth, smooth=True))
    return join_named('Altar_RelicStand', parts)


def build_false_altar():
    clear_scene()
    limestone = mat('Altar_Limestone', (0.58, 0.53, 0.42), 0.90, specular=0.15)
    cheap_oak = mat('Altar_CheapOak', (0.42, 0.32, 0.18), 0.88, specular=0.18)
    dark_oak = mat('Altar_DarkOak', (0.22, 0.15, 0.09), 0.90, specular=0.14)
    mud = mat('Altar_Mud', (0.27, 0.21, 0.14), 0.96, specular=0.08)
    wax = mat('Altar_Wax', (0.78, 0.72, 0.55), 0.55, specular=0.35)
    wick = mat('Altar_Wick', (0.12, 0.10, 0.08), 0.95, specular=0.05)
    oak = mat('Altar_Oak', (0.30, 0.20, 0.11), 0.85, specular=0.20)

    meshes = [
        make_stone_table(limestone, mud),
        make_false_front(cheap_oak, dark_oak),
        make_wax_stubs(wax, wick),
        make_splinter_plinth(oak, limestone),
    ]
    meshes = [m for m in meshes if m is not None]
    plant_and_center(meshes)

    b = world_bounds(meshes)
    tris = count_tris(meshes)
    print(f"False altar size={tuple(round(x, 4) for x in b['size'])} "
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

    bpy.ops.object.light_add(type='AREA', location=(2.5, -2.8, 3.0))
    key = bpy.context.active_object
    key.name = 'PreviewKey'
    key.data.energy = 280
    key.data.size = 2.8
    key.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))

    bpy.ops.object.light_add(type='AREA', location=(-2.2, 1.8, 2.2))
    fill = bpy.context.active_object
    fill.name = 'PreviewFill'
    fill.data.energy = 90
    fill.data.size = 3.2
    fill.data.color = (0.72, 0.78, 0.88)

    bpy.ops.object.light_add(type='SUN', location=(0, 0, 5))
    sun = bpy.context.active_object
    sun.name = 'PreviewSun'
    sun.data.energy = 1.2
    sun.rotation_euler = (math.radians(38), math.radians(8), math.radians(-25))

    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = 'PreviewGround'
    ground.data.materials.append(mat('Ground', (0.36, 0.32, 0.24), 0.95))


def render_previews():
    setup_preview_world()
    bpy.ops.object.camera_add(location=(0, -3.2, 1.3))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam
    target = Vector((0, 0, 0.7))

    views = [
        ('front', (0.0, -3.4, 1.2)),
        ('threequarter', (2.8, -2.4, 1.6)),
    ]
    for name, loc in views:
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        out = os.path.join(PREV_DIR, f'false_altar_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)


def cleanup_preview_helpers():
    for name in ('PreviewGround', 'PreviewCam', 'PreviewKey', 'PreviewFill', 'PreviewSun'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def main():
    meshes = build_false_altar()
    glb_path = os.path.join(OUT_DIR, 'false_altar.glb')
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
    meta = os.path.join(PREV_DIR, 'false_altar_scale.txt')
    with open(meta, 'w') as f:
        f.write(
            f"height_m={b['size'][2]:.4f}\n"
            f"width_x_m={b['size'][0]:.4f}\n"
            f"depth_y_m={b['size'][1]:.4f}\n"
            f"tris={tris}\n"
            f"objects={','.join(names)}\n"
            f"origin=ground_center_altar_footprint\n"
            f"collision=tight_to_mesh\n"
            f"interact_latch_note=~1.2x generous RMB latch only (not collider shell)\n"
            f"reads=real_stone_table+cheap_false_wood_face+wax_stubs\n"
            f"style=ruined_priory_false_shrine_occitan_1208\n"
        )
    print('Wrote', meta)
    print(f'Done. height={b["size"][2]:.4f} width={b["size"][0]:.4f} depth={b["size"][1]:.4f} tris={tris}')
    print('Objects:', names)


if __name__ == '__main__':
    main()
