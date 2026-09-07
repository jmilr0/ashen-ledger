"""Blender: Parish porch prop (Broken Seal) — game-ready GLB + previews.

Rural Occitan Romanesque/early-Gothic parish porch: stone steps, arched
doorway surround, shut wooden door, worn limestone. Dirt-and-mail — NO fantasy.
Rebuild:
  /usr/bin/blender -b -P tools/make_parish_porch.py

Scale notes:
  - Origin at ground center of porch footprint
  - Door ~1.15 m wide × ~2.15 m tall; porch footprint ~3.2 × 1.9 m
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


def shade_smooth(obj, angle=None):
    for poly in obj.data.polygons:
        poly.use_smooth = True
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass
    if angle is not None:
        try:
            mod = obj.modifiers.new('EdgeSplit', 'EDGE_SPLIT')
            mod.split_angle = math.radians(angle)
            bpy.ops.object.modifier_apply(modifier='EdgeSplit')
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
    """Origin at ground center of footprint."""
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
    """Add an axis-aligned box to bm; return 8 verts (bottom 4, top 4)."""
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
        (0, 1, 2, 3),  # bottom
        (4, 7, 6, 5),  # top
        (0, 4, 5, 1),  # -Y
        (1, 5, 6, 2),  # +X
        (2, 6, 7, 3),  # +Y
        (3, 7, 4, 0),  # -X
    ]
    for f in faces:
        bm.faces.new([verts[i] for i in f])
    return verts


def wear_stone(bm, amp=0.012, seed=1.7):
    """Slight irregularity on limestone faces for worn look."""
    for v in bm.verts:
        n = (math.sin(v.co.x * 7.1 + seed) * math.cos(v.co.y * 5.3 + seed * 1.3)
             + 0.5 * math.sin(v.co.z * 9.2 + v.co.x * 3.1))
        # mostly push along XY so steps stay plantable
        v.co.x += amp * 0.6 * n
        v.co.y += amp * 0.5 * math.sin(v.co.x * 4.2 + seed)
        if v.co.z > 0.02:
            v.co.z += amp * 0.35 * math.cos(v.co.x * 6.1 + v.co.y * 4.8)


def make_steps(limestone, mud):
    """Three worn limestone steps rising toward the door (+Y into nave)."""
    parts = []
    # Step treads: deeper/wider at bottom. Facing -Y (street side).
    # Platform/landing under door at z≈0.36
    steps = [
        # (y_front, y_back, z_top, x_half, name)
        (-0.95, -0.55, 0.12, 1.55, 'Step1'),
        (-0.55, -0.20, 0.24, 1.45, 'Step2'),
        (-0.20, 0.35, 0.36, 1.35, 'Landing'),
    ]
    for y0, y1, zt, xh, name in steps:
        bm = bmesh.new()
        box_bm(bm, -xh, xh, y0, y1, 0.0, zt)
        wear_stone(bm, amp=0.01, seed=hash(name) % 97)
        # slight front edge wear (rounded by pushing verts)
        for v in bm.verts:
            if abs(v.co.y - y0) < 0.02 and v.co.z > zt * 0.5:
                v.co.z -= 0.008
                v.co.y += 0.006
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Porch_{name}', bm, limestone, smooth=False))

    # Side cheek walls along steps
    for side, sx in (('L', -1), ('R', 1)):
        bm = bmesh.new()
        x0 = sx * 1.55
        x1 = sx * 1.72
        box_bm(bm, min(x0, x1), max(x0, x1), -0.95, 0.35, 0.0, 0.42)
        wear_stone(bm, amp=0.008, seed=3.1 if sx < 0 else 5.2)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Porch_Cheek{side}', bm, limestone, smooth=False))

    # Mud / dirt at street edge of bottom step
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=7, radius=0.22)
    kill = [v for v in bm.verts if v.co.z < -0.02]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    for v in bm.verts:
        v.co.x *= 2.4
        v.co.y *= 0.9
        v.co.z *= 0.4
        v.co += Vector((0.15, -1.05, 0.02))
        if v.co.z < 0:
            v.co.z = 0.002
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Porch_Mud', bm, mud, smooth=True))

    for i, (mx, my) in enumerate(((-0.9, -1.0), (0.7, -1.08), (-0.3, -0.85))):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=0.07)
        for v in bm.verts:
            v.co.z *= 0.55
            v.co += Vector((mx, my, 0.03))
            if v.co.z < 0:
                v.co.z = 0.004
        parts.append(bm_to_object(f'_pmud{i}', bm, mud, smooth=True))

    return join_named('Porch_Steps', parts)


def make_arch_surround(limestone):
    """Romanesque round-arch doorway surround / pier jambs + archivolt."""
    parts = []
    # Door opening: x in [-0.58, 0.58], z up to ~2.15 (springing ~1.55 + radius 0.58)
    jamb_inner = 0.58
    jamb_outer = 1.05
    depth_front = -0.05   # slightly proud of landing front? door sits on landing
    depth_back = 0.55
    spring_z = 1.55
    pier_base_z = 0.36

    # Left and right piers (jambs)
    for side, sx in (('L', -1), ('R', 1)):
        bm = bmesh.new()
        x_in = sx * jamb_inner
        x_out = sx * jamb_outer
        box_bm(bm, min(x_in, x_out), max(x_in, x_out),
               depth_front, depth_back, pier_base_z, spring_z + 0.08)
        # inner reveal step (Romanesque recess)
        x_mid = sx * 0.78
        box_bm(bm, min(x_in, x_mid), max(x_in, x_mid),
               depth_front - 0.04, depth_front + 0.12, pier_base_z, spring_z)
        wear_stone(bm, amp=0.009, seed=8.0 + sx)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Porch_Jamb{side}', bm, limestone, smooth=False))

    # Impost / capital bands at springing
    for side, sx in (('L', -1), ('R', 1)):
        bm = bmesh.new()
        x0 = sx * 0.52
        x1 = sx * 1.12
        box_bm(bm, min(x0, x1), max(x0, x1),
               depth_front - 0.06, depth_back + 0.04,
               spring_z - 0.06, spring_z + 0.10)
        wear_stone(bm, amp=0.006, seed=11 + sx)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Porch_Impost{side}', bm, limestone, smooth=False))

    # Round archivolt (extruded arch ring) — readable at iso distance
    bm = bmesh.new()
    segs = 20
    r_inner = jamb_inner
    r_outer = 1.02
    z_c = spring_z
    y0, y1 = depth_front - 0.05, depth_back
    # Build arch as stacked quads in the XZ plane, extruded in Y
    # Outer and inner arcs at two Y depths
    for yi, y in enumerate((y0, y1)):
        pass
    # Create ring faces between inner/outer at front and back, then sides
    front_outer, front_inner, back_outer, back_inner = [], [], [], []
    for i in range(segs + 1):
        a = math.pi * (1.0 - i / segs)  # π → 0 (left to right over top)
        co = math.cos(a)
        si = math.sin(a)
        front_outer.append(bm.verts.new((r_outer * co, y0, z_c + r_outer * si)))
        front_inner.append(bm.verts.new((r_inner * co, y0, z_c + r_inner * si)))
        back_outer.append(bm.verts.new((r_outer * co, y1, z_c + r_outer * si)))
        back_inner.append(bm.verts.new((r_inner * co, y1, z_c + r_inner * si)))
    bm.verts.ensure_lookup_table()
    for i in range(segs):
        # front face of archivolt
        bm.faces.new((front_inner[i], front_inner[i + 1], front_outer[i + 1], front_outer[i]))
        # back
        bm.faces.new((back_outer[i], back_outer[i + 1], back_inner[i + 1], back_inner[i]))
        # outer barrel
        bm.faces.new((front_outer[i], front_outer[i + 1], back_outer[i + 1], back_outer[i]))
        # inner soffit
        bm.faces.new((back_inner[i], back_inner[i + 1], front_inner[i + 1], front_inner[i]))
    # end caps at springing (left and right)
    for idx in (0, segs):
        bm.faces.new((front_inner[idx], front_outer[idx], back_outer[idx], back_inner[idx]))
    wear_stone(bm, amp=0.007, seed=14.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Porch_Archivolt', bm, limestone, smooth=True))

    # Outer gable / wall mass above and beside arch (reads as church facade stub)
    bm = bmesh.new()
    # rectangular mass with arched hole approximated by solid sides + top
    # Top lintel / wall above crown
    crown_z = spring_z + r_outer
    box_bm(bm, -1.25, 1.25, depth_front + 0.02, depth_back + 0.08,
           crown_z - 0.05, crown_z + 0.55)
    # Side wall masses beyond jambs
    box_bm(bm, -1.55, -jamb_outer + 0.02, depth_front + 0.02, depth_back + 0.08,
           pier_base_z, crown_z + 0.55)
    box_bm(bm, jamb_outer - 0.02, 1.55, depth_front + 0.02, depth_back + 0.08,
           pier_base_z, crown_z + 0.55)
    # Simple pitched coping suggestion (two sloped boxes via vert push)
    wear_stone(bm, amp=0.01, seed=17.0)
    # pitch the top verts
    for v in bm.verts:
        if v.co.z > crown_z + 0.35:
            v.co.z += 0.18 * (1.0 - abs(v.co.x) / 1.55)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Porch_Facade', bm, limestone, smooth=False))

    # Threshold sill under door
    bm = bmesh.new()
    box_bm(bm, -jamb_inner - 0.04, jamb_inner + 0.04,
           depth_front - 0.02, depth_front + 0.18,
           pier_base_z - 0.04, pier_base_z + 0.04)
    wear_stone(bm, amp=0.005, seed=19.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Porch_Sill', bm, limestone, smooth=False))

    return join_named('Porch_Stone', parts)


def make_door(oak, iron, wax):
    """Shut heavy wooden door with iron strap hinges and wax-seal scrap."""
    parts = []
    # Door leaf — slightly recessed in opening
    dw, dh, dd = 1.12, 2.10, 0.07
    z0 = 0.40
    y = 0.08
    bm = bmesh.new()
    box_bm(bm, -dw / 2, dw / 2, y, y + dd, z0, z0 + dh)
    # plank grooves: push vertical lines
    for v in bm.verts:
        # front face detail via thin inset boards suggested by X offset
        if abs(v.co.y - y) < 0.01:
            # board seams every ~0.22 m
            seam = abs((v.co.x + 0.56) % 0.22 - 0.11)
            if seam < 0.015:
                v.co.y -= 0.008
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Porch_DoorLeaf', bm, oak, smooth=False))

    # Vertical stile / rail suggestion boards as thin overlays
    for i, x in enumerate((-0.38, -0.14, 0.14, 0.38)):
        bm = bmesh.new()
        box_bm(bm, x - 0.04, x + 0.04, y - 0.012, y + 0.002, z0 + 0.05, z0 + dh - 0.05)
        parts.append(bm_to_object(f'_plank{i}', bm, oak, smooth=False))

    # Horizontal ledges
    for i, z in enumerate((z0 + 0.35, z0 + 1.05, z0 + 1.75)):
        bm = bmesh.new()
        box_bm(bm, -dw / 2 + 0.04, dw / 2 - 0.04, y - 0.014, y + 0.004, z - 0.04, z + 0.04)
        parts.append(bm_to_object(f'_ledge{i}', bm, oak, smooth=False))

    # Iron strap hinges (left side, street-readable)
    for i, z in enumerate((z0 + 0.45, z0 + 1.10, z0 + 1.75)):
        bm = bmesh.new()
        # strap across door
        box_bm(bm, -dw / 2 - 0.02, -dw / 2 + 0.42, y - 0.02, y + 0.01, z - 0.035, z + 0.035)
        # hinge knuckle
        bmesh.ops.create_cone(bm, cap_ends=True, segments=10,
                              radius1=0.028, radius2=0.028, depth=0.09)
        for v in list(bm.verts)[-22:]:
            # cone created at origin; move knuckle
            pass
        # Reposition last cone verts roughly — simpler: separate knuckle
        parts.append(bm_to_object(f'_strap{i}', bm, iron, smooth=False))

        bm2 = bmesh.new()
        bmesh.ops.create_uvsphere(bm2, u_segments=8, v_segments=6, radius=0.03)
        for v in bm2.verts:
            v.co.x *= 0.7
            v.co.y *= 0.7
            v.co.z *= 1.1
            v.co += Vector((-dw / 2 - 0.01, y - 0.01, z))
        parts.append(bm_to_object(f'_knuckle{i}', bm2, iron, smooth=True))

    # Ring handle + backplate
    bm = bmesh.new()
    box_bm(bm, 0.28, 0.48, y - 0.018, y + 0.004, z0 + 1.00, z0 + 1.22)
    parts.append(bm_to_object('Porch_HandlePlate', bm, iron, smooth=False))

    bm = bmesh.new()
    segs = 14
    major_r, tube_r = 0.07, 0.014
    rings = []
    cx, cy, cz = 0.38, y - 0.03, z0 + 1.05
    for i in range(segs):
        a = (i / segs) * math.tau
        px = cx + major_r * math.cos(a)
        pz = cz + major_r * math.sin(a)
        row = []
        for j in range(8):
            b = (j / 8) * math.tau
            nx, nz = math.cos(a), math.sin(a)
            row.append(bm.verts.new((
                px + tube_r * math.cos(b) * nx,
                cy + tube_r * math.sin(b),
                pz + tube_r * math.cos(b) * nz,
            )))
        rings.append(row)
    for i in range(segs):
        i2 = (i + 1) % segs
        for j in range(8):
            j2 = (j + 1) % 8
            bm.faces.new((rings[i][j], rings[i][j2], rings[i2][j2], rings[i2][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Porch_Ring', bm, iron, smooth=True))

    # Small wax blob near handle (letter/seal scrap — parish dirt-and-mail)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.035)
    for v in bm.verts:
        v.co.x *= 1.2
        v.co.y *= 0.5
        v.co.z *= 0.9
        v.co += Vector((0.22, y - 0.02, z0 + 1.35))
    parts.append(bm_to_object('Porch_Wax', bm, wax, smooth=True))

    # Nail heads
    for i, (nx, nz) in enumerate((
        (-0.45, z0 + 0.55), (-0.45, z0 + 1.2), (-0.45, z0 + 1.85),
        (0.45, z0 + 0.55), (0.45, z0 + 1.2), (0.45, z0 + 1.85),
        (0.0, z0 + 0.7), (0.0, z0 + 1.5),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=0.018)
        for v in bm.verts:
            v.co.y *= 0.4
            v.co += Vector((nx, y - 0.01, nz))
        parts.append(bm_to_object(f'_nail{i}', bm, iron, smooth=True))

    return join_named('Porch_Door', parts)


def build_parish_porch():
    clear_scene()
    limestone = mat('Porch_Limestone', (0.62, 0.56, 0.44), 0.88, specular=0.18)
    limestone_dark = mat('Porch_LimestoneDark', (0.48, 0.44, 0.36), 0.92, specular=0.14)
    # use same limestone for most; dark unused alias ok — keep one primary
    oak = mat('Porch_Oak', (0.28, 0.18, 0.10), 0.82, specular=0.22)
    mud = mat('Porch_Mud', (0.30, 0.24, 0.15), 0.96, specular=0.08)
    iron = mat('Porch_Iron', (0.26, 0.24, 0.22), 0.48, metallic=0.55, specular=0.4)
    wax = mat('Porch_Wax', (0.55, 0.22, 0.14), 0.55, specular=0.35)

    meshes = [
        make_steps(limestone, mud),
        make_arch_surround(limestone),
        make_door(oak, iron, wax),
    ]
    meshes = [m for m in meshes if m is not None]
    plant_and_center(meshes)

    b = world_bounds(meshes)
    tris = count_tris(meshes)
    print(f"Parish porch size={tuple(round(x, 4) for x in b['size'])} "
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

    bpy.ops.object.light_add(type='AREA', location=(3.5, -4.0, 4.5))
    key = bpy.context.active_object
    key.name = 'PreviewKey'
    key.data.energy = 350
    key.data.size = 3.5
    key.rotation_euler = (math.radians(55), math.radians(8), math.radians(35))

    bpy.ops.object.light_add(type='AREA', location=(-3.0, 2.5, 3.0))
    fill = bpy.context.active_object
    fill.name = 'PreviewFill'
    fill.data.energy = 110
    fill.data.size = 4.0
    fill.data.color = (0.75, 0.80, 0.90)

    bpy.ops.object.light_add(type='SUN', location=(0, 0, 8))
    sun = bpy.context.active_object
    sun.name = 'PreviewSun'
    sun.data.energy = 1.4
    sun.rotation_euler = (math.radians(42), math.radians(10), math.radians(-30))

    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = 'PreviewGround'
    ground.data.materials.append(mat('Ground', (0.36, 0.32, 0.24), 0.95))


def render_previews():
    setup_preview_world()
    bpy.ops.object.camera_add(location=(0, -6.5, 2.2))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam
    target = Vector((0, 0.1, 1.5))

    views = [
        ('front', (0.0, -7.2, 2.0)),
        ('threequarter', (5.5, -5.2, 3.0)),
    ]
    for name, loc in views:
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        out = os.path.join(PREV_DIR, f'parish_porch_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)


def cleanup_preview_helpers():
    for name in ('PreviewGround', 'PreviewCam', 'PreviewKey', 'PreviewFill', 'PreviewSun'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def main():
    meshes = build_parish_porch()
    glb_path = os.path.join(OUT_DIR, 'parish_porch.glb')
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
    meta = os.path.join(PREV_DIR, 'parish_porch_scale.txt')
    with open(meta, 'w') as f:
        f.write(
            f"height_m={b['size'][2]:.4f}\n"
            f"width_x_m={b['size'][0]:.4f}\n"
            f"depth_y_m={b['size'][1]:.4f}\n"
            f"tris={tris}\n"
            f"objects={','.join(names)}\n"
            f"origin=ground_center_porch_footprint\n"
            f"collision=tight_to_mesh\n"
            f"interact_latch_note=~1.2x generous RMB latch only (not collider shell)\n"
            f"door_w_m~=1.12 door_h_m~=2.10\n"
            f"style=romanesque_rural_occitan_1208\n"
        )
    print('Wrote', meta)
    print(f'Done. height={b["size"][2]:.4f} width={b["size"][0]:.4f} depth={b["size"][1]:.4f} tris={tris}')
    print('Objects:', names)


if __name__ == '__main__':
    main()
