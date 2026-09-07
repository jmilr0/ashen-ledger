"""Blender: Mile / league marker prop (Broken Seal) — game-ready GLB + previews.

Worn limestone roadside pillar / league stone on the Fontfroide–Narbonne pilgrim
road. Dirt-and-mail Occitania 1208 — NO fantasy glow.
Rebuild:
  /usr/bin/blender -b -P tools/make_mile_marker.py

Scale notes:
  - Origin at ground center of pillar footprint
  - Pillar ~1.15–1.25 m high; base ~0.45 m; shaft ~0.28–0.32 m
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


def make_base(limestone, mud):
    parts = []
    # Squared rubble footing, slightly sunk into mud
    bm = bmesh.new()
    box_bm(bm, -0.28, 0.28, -0.26, 0.26, 0.0, 0.18)
    wear_stone(bm, amp=0.018, seed=3.2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Mile_Base', bm, limestone, smooth=False))

    # Secondary step / plinth ring
    bm = bmesh.new()
    box_bm(bm, -0.22, 0.22, -0.20, 0.20, 0.16, 0.28)
    wear_stone(bm, amp=0.012, seed=4.1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Mile_Plinth', bm, limestone, smooth=False))

    # Mud skirts at corners
    for i, (mx, my) in enumerate((
        (-0.22, 0.18), (0.20, -0.16), (-0.18, -0.20), (0.24, 0.14),
        (0.05, 0.22), (-0.08, -0.24),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=0.07)
        for v in bm.verts:
            v.co.z *= 0.35
            v.co.x *= 1.4
            v.co += Vector((mx, my, 0.02))
            if v.co.z < 0:
                v.co.z = 0.002
        parts.append(bm_to_object(f'_mud{i}', bm, mud, smooth=True))

    return join_named('Mile_Footing', parts)


def make_shaft(limestone, lichen):
    parts = []
    # Slightly tapered square shaft with worn edges
    bm = bmesh.new()
    # Build as stacked boxes with taper for readable silhouette
    heights = [
        (0.28, 0.55, 0.175, 0.160),
        (0.55, 0.85, 0.160, 0.145),
        (0.85, 1.05, 0.145, 0.135),
        (1.05, 1.18, 0.135, 0.120),
    ]
    for i, (z0, z1, r0, r1) in enumerate(heights):
        segs = 4
        # octagonal-ish by using worn box
        box_bm(bm, -r0, r0, -r0 * 0.92, r0 * 0.92, z0, z1)
        # taper top of each segment toward r1
        bm.verts.ensure_lookup_table()
        for v in bm.verts:
            if abs(v.co.z - z1) < 0.002:
                sx = r1 / max(r0, 1e-6)
                v.co.x *= sx
                v.co.y *= sx * 0.92 / 0.92
    wear_stone(bm, amp=0.014, seed=7.5)
    # Soften corners slightly
    for v in bm.verts:
        ax, ay = abs(v.co.x), abs(v.co.y)
        if ax > 0.08 and ay > 0.08:
            v.co.x *= 0.96
            v.co.y *= 0.96
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Mile_Shaft', bm, limestone, smooth=False))

    # Shallow carved league numeral / cross notch on +Y face (pilgrim road mark)
    bm = bmesh.new()
    # Vertical stem of a crude cross / I mark
    box_bm(bm, -0.018, 0.018, 0.138, 0.148, 0.62, 0.92)
    # Crossbar
    box_bm(bm, -0.055, 0.055, 0.138, 0.148, 0.78, 0.82)
    # Small wedge nick (damage)
    box_bm(bm, 0.04, 0.08, 0.130, 0.145, 0.70, 0.74)
    parts.append(bm_to_object('Mile_Carve', bm, lichen, smooth=False))

    # Lichen patches
    for i, (x, y, z, s) in enumerate((
        (-0.12, 0.10, 0.95, 0.04),
        (0.10, -0.08, 0.70, 0.035),
        (-0.08, -0.12, 0.48, 0.03),
        (0.05, 0.12, 1.08, 0.028),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=s)
        for v in bm.verts:
            v.co.z *= 0.4
            v.co += Vector((x, y, z))
        parts.append(bm_to_object(f'_lich{i}', bm, lichen, smooth=True))

    return join_named('Mile_Pillar', parts)


def make_cap(limestone):
    parts = []
    # Simple weathered cap / coping — not a fancy finial
    bm = bmesh.new()
    box_bm(bm, -0.15, 0.15, -0.14, 0.14, 1.15, 1.22)
    wear_stone(bm, amp=0.01, seed=9.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Mile_Cap', bm, limestone, smooth=False))

    # Slight pyramid / pitched top (worn)
    bm = bmesh.new()
    verts = [
        bm.verts.new((-0.14, -0.13, 1.22)),
        bm.verts.new((0.14, -0.13, 1.22)),
        bm.verts.new((0.14, 0.13, 1.22)),
        bm.verts.new((-0.14, 0.13, 1.22)),
        bm.verts.new((0.02, 0.0, 1.32)),
    ]
    bm.faces.new([verts[0], verts[1], verts[4]])
    bm.faces.new([verts[1], verts[2], verts[4]])
    bm.faces.new([verts[2], verts[3], verts[4]])
    bm.faces.new([verts[3], verts[0], verts[4]])
    bm.faces.new([verts[0], verts[3], verts[2], verts[1]])
    wear_stone(bm, amp=0.008, seed=11.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Mile_Peak', bm, limestone, smooth=False))

    # Iron staple remnant (old notice board / rope tie)
    iron = mat('Mile_Iron', (0.30, 0.28, 0.24), 0.55, metallic=0.55, specular=0.4)
    bm = bmesh.new()
    path = [
        Vector((-0.02, 0.145, 0.95)),
        Vector((-0.02, 0.175, 0.97)),
        Vector((0.02, 0.175, 0.97)),
        Vector((0.02, 0.145, 0.95)),
    ]
    tube(bm, path, [0.012, 0.011, 0.011, 0.012], segs=6)
    parts.append(bm_to_object('Mile_Staple', bm, iron, smooth=True))

    return join_named('Mile_Top', parts)


def make_roadside_rubble(limestone, mud):
    parts = []
    for i, (x, y, sx, sy, sz) in enumerate((
        (-0.38, 0.10, 0.08, 0.06, 0.05),
        (0.36, -0.08, 0.07, 0.05, 0.04),
        (-0.30, -0.22, 0.06, 0.05, 0.035),
        (0.28, 0.20, 0.05, 0.06, 0.03),
    )):
        bm = bmesh.new()
        box_bm(bm, x - sx, x + sx, y - sy, y + sy, 0.0, sz)
        wear_stone(bm, amp=0.008, seed=20 + i)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'_rubble{i}', bm, limestone if i % 2 == 0 else mud, smooth=False))
    return join_named('Mile_Rubble', parts)


def build_mile_marker():
    clear_scene()
    limestone = mat('Mile_Limestone', (0.62, 0.56, 0.44), 0.92, specular=0.12)
    lichen = mat('Mile_Lichen', (0.48, 0.50, 0.36), 0.95, specular=0.08)
    mud = mat('Mile_Mud', (0.30, 0.24, 0.16), 0.97, specular=0.06)

    meshes = [
        make_base(limestone, mud),
        make_shaft(limestone, lichen),
        make_cap(limestone),
        make_roadside_rubble(limestone, mud),
    ]
    meshes = [m for m in meshes if m is not None]
    plant_and_center(meshes)

    b = world_bounds(meshes)
    tris = count_tris(meshes)
    print(f"Mile marker size={tuple(round(x, 4) for x in b['size'])} "
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

    bpy.ops.object.light_add(type='AREA', location=(2.5, -3.0, 3.0))
    key = bpy.context.active_object
    key.name = 'PreviewKey'
    key.data.energy = 280
    key.data.size = 2.5
    key.rotation_euler = (math.radians(50), math.radians(8), math.radians(28))

    bpy.ops.object.light_add(type='AREA', location=(-2.0, 1.8, 2.2))
    fill = bpy.context.active_object
    fill.name = 'PreviewFill'
    fill.data.energy = 90
    fill.data.size = 3.0
    fill.data.color = (0.72, 0.78, 0.88)

    bpy.ops.object.light_add(type='SUN', location=(0, 0, 5))
    sun = bpy.context.active_object
    sun.name = 'PreviewSun'
    sun.data.energy = 1.2
    sun.rotation_euler = (math.radians(38), math.radians(6), math.radians(-25))

    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = 'PreviewGround'
    ground.data.materials.append(mat('Ground', (0.34, 0.30, 0.22), 0.96))


def render_previews():
    setup_preview_world()
    bpy.ops.object.camera_add(location=(0, -3.2, 1.0))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam
    target = Vector((0, 0, 0.65))

    views = [
        ('front', (0.0, -3.4, 0.95)),
        ('threequarter', (2.6, -2.5, 1.4)),
    ]
    for name, loc in views:
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        out = os.path.join(PREV_DIR, f'mile_marker_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)


def cleanup_preview_helpers():
    for name in ('PreviewGround', 'PreviewCam', 'PreviewKey', 'PreviewFill', 'PreviewSun'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def main():
    meshes = build_mile_marker()
    glb_path = os.path.join(OUT_DIR, 'mile_marker.glb')
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
    meta = os.path.join(PREV_DIR, 'mile_marker_scale.txt')
    with open(meta, 'w') as f:
        f.write(
            f"height_m={b['size'][2]:.4f}\n"
            f"width_x_m={b['size'][0]:.4f}\n"
            f"depth_y_m={b['size'][1]:.4f}\n"
            f"tris={tris}\n"
            f"objects={','.join(names)}\n"
            f"origin=ground_center_pillar_footprint\n"
            f"collision=tight_to_mesh\n"
            f"interact_latch_note=~1.2x generous RMB latch only (not collider shell)\n"
            f"reads=worn_limestone_league_stone_roadside\n"
            f"style=fontfroide_narbonne_mile_marker_occitan_1208\n"
        )
    print('Wrote', meta)
    print(f'Done. height={b["size"][2]:.4f} width={b["size"][0]:.4f} depth={b["size"][1]:.4f} tris={tris}')
    print('Objects:', names)


if __name__ == '__main__':
    main()
