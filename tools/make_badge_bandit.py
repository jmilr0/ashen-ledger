"""Blender: Badge-bandit enemy (Broken Seal) — game-ready GLB + previews.

Rough road brigand, Occitania 1208, wearing a borrowed (fake) northern/hospital-style
badge on the chest. Mail scraps / leather, spear or cudgel, mud-road dirt.
NO fantasy armor kits. Rebuild:
  /usr/bin/blender -b -P tools/make_badge_bandit.py

Scale (locked):
  - Height ~1.72 m, origin at feet
  - Max width under 0.60 m capsule (~0.56 party constraint)
  - Stylized low-poly readable at isometric distance
"""
from __future__ import annotations

import math
import os
import sys
import bmesh
import bpy
from mathutils import Matrix, Vector

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..'))
if not os.path.isdir(os.path.join(ROOT, 'public', 'models')):
    ROOT = '/workspace/ashen-ledger'
OUT_DIR = os.path.join(ROOT, 'public', 'models', 'characters')
PREV_DIR = os.path.join(OUT_DIR, 'previews')
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PREV_DIR, exist_ok=True)

TARGET_HEIGHT = 1.72
MAX_WIDTH = 0.56


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
    return {
        'min': (min(xs), min(ys), min(zs)),
        'max': (max(xs), max(ys), max(zs)),
        'size': (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)),
    }


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
        obj.scale = (obj.scale[0] * s, obj.scale[1] * s, obj.scale[2] * s)
        transform_apply(obj, location=False, rotation=False, scale=True)
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


# ---------- character parts ----------

def make_torso(leather, tunic):
    bm = bmesh.new()
    segs = 18
    # Broader brigand chest, shorter tunic
    profile = [
        (0.72, 0.165, 0.130, 0.010),
        (0.88, 0.175, 0.138, 0.012),
        (1.02, 0.185, 0.145, 0.014),
        (1.16, 0.195, 0.150, 0.012),
        (1.28, 0.200, 0.148, 0.008),
        (1.36, 0.155, 0.120, 0.004),
        (1.42, 0.072, 0.065, 0.000),
    ]
    rings = []
    for z, rx, ry, fold in profile:
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            wave = 1.0 + fold * math.sin(a * 4 + z * 5)
            x = rx * wave * math.cos(a)
            y = ry * wave * math.sin(a)
            # flatten front for badge readability
            if math.sin(a) > 0.3:
                y *= 0.88
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

    # short skirt / ragged hem
    skirt = [
        (0.58, 0.172, 0.138, 0.018),
        (0.42, 0.160, 0.128, 0.022),
        (0.30, 0.148, 0.118, 0.016),
    ]
    prev = rings[0]
    for z, rx, ry, fold in skirt:
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            wave = 1.0 + fold * math.sin(a * 5 + z * 7)
            # ragged: vary hem height
            zz = z - 0.02 * abs(math.sin(a * 3))
            row.append(bm.verts.new((rx * wave * math.cos(a), ry * wave * math.sin(a), zz)))
        for j in range(segs):
            j2 = (j + 1) % segs
            bm.faces.new((prev[j], prev[j2], row[j2], row[j]))
        prev = row
    lip = []
    for v in prev:
        lip.append(bm.verts.new((v.co.x * 1.04, v.co.y * 1.04, v.co.z - 0.015)))
    for j in range(segs):
        j2 = (j + 1) % segs
        bm.faces.new((prev[j], prev[j2], lip[j2], lip[j]))
    c2 = sum((v.co for v in lip), Vector()) / len(lip)
    c2.z -= 0.01
    center2 = bm.verts.new(c2)
    for j in range(segs):
        bm.faces.new((center2, lip[(j + 1) % segs], lip[j]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    subdivide_bm(bm, 1)
    for v in bm.verts:
        if 0.35 < v.co.z < 1.30:
            a = math.atan2(v.co.y, v.co.x)
            n = Vector((v.co.x, v.co.y, 0))
            if n.length > 1e-4:
                n.normalize()
                v.co += n * (0.004 * math.sin(a * 6 + v.co.z * 8))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object('Bandit_Torso', bm, leather)


def make_mail_scraps(mail):
    """Patchy mail scraps on shoulders / upper chest — not full hauberk."""
    parts = []
    # shoulder scrap L/R
    for sx, side in ((1, 'L'), (-1, 'R')):
        bm = bmesh.new()
        segs = 12
        rings = []
        for z, rx, ry in ((1.22, 0.08, 0.07), (1.30, 0.10, 0.08), (1.36, 0.09, 0.07)):
            row = []
            for j in range(segs):
                a = (j / segs) * math.tau * 0.55 + (0.15 if sx > 0 else math.pi * 0.7)
                rmod = 1.0 + 0.04 * math.sin(a * 8)
                row.append(bm.verts.new((
                    sx * 0.12 + rx * rmod * math.cos(a),
                    ry * rmod * math.sin(a) * 0.9,
                    z,
                )))
            rings.append(row)
        for i in range(len(rings) - 1):
            for j in range(segs - 1):
                try:
                    bm.faces.new((rings[i][j], rings[i][j + 1], rings[i + 1][j + 1], rings[i + 1][j]))
                except ValueError:
                    pass
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'_mail{side}', bm, mail))

    # chest mail strip under badge
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.10
        v.co.y *= 0.02
        v.co.z *= 0.08
        v.co += Vector((0.0, 0.135, 1.08))
    # ding the surface
    subdivide_bm(bm, 1)
    for v in bm.verts:
        v.co.y += 0.004 * math.sin(v.co.x * 40 + v.co.z * 30)
    parts.append(bm_to_object('_mailChest', bm, mail))
    return join_named('Bandit_Mail', parts)


def make_badge(badge_metal, badge_enamel, variant='a'):
    """Borrowed fake northern/hospital-style badge — large enough for iso distance."""
    parts = []
    # Disc body — oversized slightly for readability
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=20, radius1=0.075, radius2=0.075, depth=0.012,
        matrix=Matrix.Translation((0.02, 0.155, 1.12)) @ Matrix.Rotation(math.radians(90), 4, 'X'),
    )
    parts.append(bm_to_object('_badgeDisc', bm, badge_metal))

    # Raised rim
    bm = bmesh.new()
    segs = 20
    z_front = 0.162
    outer, inner = [], []
    for r in (0.078, 0.062):
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            row.append(bm.verts.new((0.02 + r * math.cos(a), z_front, 1.12 + r * math.sin(a))))
        if r > 0.07:
            outer = row
        else:
            inner = row
    # extrude rim thickness
    outer2, inner2 = [], []
    for v in outer:
        outer2.append(bm.verts.new((v.co.x, v.co.y + 0.008, v.co.z)))
    for v in inner:
        inner2.append(bm.verts.new((v.co.x, v.co.y + 0.008, v.co.z)))
    for j in range(segs):
        j2 = (j + 1) % segs
        bm.faces.new((outer[j], outer[j2], outer2[j2], outer2[j]))
        bm.faces.new((inner2[j], inner2[j2], inner[j2], inner[j]))
        bm.faces.new((outer2[j], outer2[j2], inner2[j2], inner2[j]))
        bm.faces.new((inner[j], inner[j2], outer[j2], outer[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('_badgeRim', bm, badge_metal))

    # Cross / hospital mark (fake northern hospitaliers look)
    enamel_col = badge_enamel
    # vertical bar
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.018
        v.co.y *= 0.006
        v.co.z *= 0.048
        v.co += Vector((0.02, 0.168, 1.12))
    parts.append(bm_to_object('_crossV', bm, enamel_col))
    # horizontal bar
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.048
        v.co.y *= 0.006
        v.co.z *= 0.016
        v.co += Vector((0.02, 0.168, 1.12))
    parts.append(bm_to_object('_crossH', bm, enamel_col))

    # Slightly crooked pin / strap — looks stolen / borrowed
    bm = bmesh.new()
    path = [Vector((-0.02, 0.148, 1.18)), Vector((0.02, 0.152, 1.195)), Vector((0.06, 0.148, 1.175))]
    tube(bm, path, [0.006, 0.005, 0.006], segs=5)
    strap_m = mat('Bandit_BadgeStrap', (0.18, 0.12, 0.08), 0.85)
    parts.append(bm_to_object('_badgeStrap', bm, strap_m))

    # Variant B: ding / off-color chip on badge
    if variant == 'b':
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=0.012,
                                  matrix=Matrix.Translation((0.055, 0.170, 1.095)))
        ding = mat('Bandit_BadgeDing', (0.35, 0.32, 0.28), 0.6, metallic=0.4)
        parts.append(bm_to_object('_ding', bm, ding))

    return join_named('Bandit_Badge', parts)


def make_head(skin, hair_m, brow_m):
    parts = []
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=14, radius=0.105)
    for v in bm.verts:
        x, y, z = v.co
        v.co.x = x * 0.92
        v.co.y = y * 0.95
        v.co.z = z * 1.12
        # harder jaw
        if z < -0.02:
            v.co.x *= 1.05
            v.co.y *= 0.95
        v.co += Vector((0, 0.01, 1.55))
    parts.append(bm_to_object('_skull', bm, skin))

    # nose
    bm = bmesh.new()
    path = [Vector((0, 0.070, 1.575)), Vector((0, 0.095, 1.555)),
            Vector((0, 0.108, 1.530)), Vector((0, 0.095, 1.515))]
    tube(bm, path, [0.011, 0.012, 0.013, 0.008], segs=7)
    parts.append(bm_to_object('_nose', bm, skin))

    # brows — meaner
    for sx in (-1, 1):
        bm = bmesh.new()
        path = []
        radii = []
        for i in range(6):
            t = i / 5
            path.append(Vector((sx * (0.012 + 0.045 * t), 0.085 - 0.006 * abs(t - 0.3),
                                1.590 + 0.008 * math.sin(t * math.pi) - 0.008 * t)))
            radii.append(0.007 - 0.002 * t)
        tube(bm, path, radii, segs=5)
        parts.append(bm_to_object(f'_brow{sx}', bm, brow_m))

    # ears
    for sx in (-1, 1):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.028)
        for v in bm.verts:
            v.co.x *= 0.4
            v.co.y *= 0.6
            v.co.z *= 1.15
            v.co += Vector((sx * 0.095, -0.01, 1.545))
        parts.append(bm_to_object(f'_ear{sx}', bm, skin))

    # eyes
    eye_w = mat('Bandit_EyeW', (0.88, 0.85, 0.80), 0.4)
    eye_d = mat('Bandit_EyeD', (0.12, 0.08, 0.05), 0.35)
    for sx in (-1, 1):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.014)
        for v in bm.verts:
            v.co.y *= 0.6
            v.co += Vector((sx * 0.032, 0.090, 1.555))
        parts.append(bm_to_object(f'_eye{sx}', bm, eye_w))
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=0.007)
        for v in bm.verts:
            v.co += Vector((sx * 0.032, 0.100, 1.555))
        parts.append(bm_to_object(f'_iris{sx}', bm, eye_d))

    # mouth — thin grim
    lip = mat('Bandit_Lip', (0.55, 0.35, 0.30), 0.55)
    bm = bmesh.new()
    path = [Vector((t * 0.022, 0.085 - 0.006 * abs(t), 1.505)) for t in [-1, -0.5, 0, 0.5, 1]]
    tube(bm, path, [0.004] * 5, segs=4)
    parts.append(bm_to_object('_mouth', bm, lip))

    # scruffy hair / short rough cut
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.115)
    kill = [v for v in bm.verts if v.co.z < -0.02]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    for v in bm.verts:
        v.co.x *= 1.05
        v.co.y *= 1.08
        v.co.z *= 0.88
        v.co += Vector((0, -0.015, 1.575))
    # messy clumps
    for x, y, z, r in (
        (-0.05, 0.07, 1.60, 0.028), (0.02, 0.08, 1.61, 0.026),
        (0.05, 0.06, 1.59, 0.024), (-0.08, 0.0, 1.55, 0.032),
        (0.08, 0.0, 1.55, 0.030), (0, -0.06, 1.52, 0.05),
    ):
        bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=r,
                                  matrix=Matrix.Translation((x, y, z)))
    parts.append(bm_to_object('_hair', bm, hair_m))

    # short beard stubble mass
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.055)
    for v in bm.verts:
        v.co.x *= 0.95
        v.co.y *= 0.7
        v.co.z *= 0.85
        v.co += Vector((0, 0.06, 1.48))
        if v.co.z > 1.52:
            v.co.z = 1.515
    parts.append(bm_to_object('_beard', bm, hair_m))

    return join_named('Bandit_Head', parts)


def make_belt(leather):
    bm = bmesh.new()
    segs = 20
    z0, z1 = 0.82, 0.87
    outer, inner = [], []
    for z in (z0, z1):
        o_row, i_row = [], []
        for j in range(segs):
            a = (j / segs) * math.tau
            o_row.append(bm.verts.new((0.175 * math.cos(a), 0.138 * math.sin(a), z)))
            i_row.append(bm.verts.new((0.155 * math.cos(a), 0.120 * math.sin(a), z)))
        outer.append(o_row)
        inner.append(i_row)
    for j in range(segs):
        j2 = (j + 1) % segs
        bm.faces.new((outer[0][j], outer[0][j2], outer[1][j2], outer[1][j]))
        bm.faces.new((inner[1][j], inner[1][j2], inner[0][j2], inner[0][j]))
        bm.faces.new((outer[1][j], outer[1][j2], inner[1][j2], inner[1][j]))
        bm.faces.new((inner[0][j], inner[0][j2], outer[0][j2], outer[0][j]))
    # crude buckle
    buckle = [
        (-0.025, 0.130, z0 - 0.005), (0.025, 0.130, z0 - 0.005),
        (0.025, 0.150, z0 - 0.005), (-0.025, 0.150, z0 - 0.005),
        (-0.025, 0.130, z1 + 0.005), (0.025, 0.130, z1 + 0.005),
        (0.025, 0.150, z1 + 0.005), (-0.025, 0.150, z1 + 0.005),
    ]
    bv = [bm.verts.new(p) for p in buckle]
    for f in [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]:
        bm.faces.new([bv[i] for i in f])
    iron = mat('Bandit_Buckle', (0.40, 0.38, 0.32), 0.45, metallic=0.5)
    belt_obj = bm_to_object('Bandit_Belt', bm, leather)
    # pouch
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.035)
    for v in bm.verts:
        v.co.x *= 0.7
        v.co.z *= 1.2
        v.co += Vector((-0.12, 0.14, 0.84))
    pouch = bm_to_object('_pouch', bm, leather)
    return join_named('Bandit_Belt', [belt_obj, pouch])


def make_limbs(leather, skin, hose, boots_m):
    parts = []
    # shoulders
    for sx, side in ((1, 'L'), (-1, 'R')):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.055)
        for v in bm.verts:
            v.co.x *= 1.1
            v.co += Vector((sx * 0.185, 0.0, 1.30))
        parts.append(bm_to_object(f'_sh{side}', bm, leather))

    # arms — left holds weapon readiness, right free/cudgel side
    # Upper arms
    bm = bmesh.new()
    tube(bm, [Vector((0.20, 0.02, 1.26)), Vector((0.24, 0.04, 1.08)), Vector((0.26, 0.06, 0.92))],
         [0.046, 0.042, 0.038], segs=9)
    parts.append(bm_to_object('_uaL', bm, leather))
    bm = bmesh.new()
    tube(bm, [Vector((-0.20, 0.02, 1.26)), Vector((-0.23, 0.05, 1.08)), Vector((-0.24, 0.08, 0.94))],
         [0.046, 0.042, 0.038], segs=9)
    parts.append(bm_to_object('_uaR', bm, leather))

    # forearms
    bm = bmesh.new()
    tube(bm, [Vector((0.26, 0.06, 0.92)), Vector((0.28, 0.08, 0.80)), Vector((0.30, 0.10, 0.70))],
         [0.036, 0.032, 0.028], segs=8)
    parts.append(bm_to_object('_faL', bm, skin))
    bm = bmesh.new()
    tube(bm, [Vector((-0.24, 0.08, 0.94)), Vector((-0.25, 0.10, 0.82)), Vector((-0.26, 0.12, 0.72))],
         [0.036, 0.032, 0.028], segs=8)
    parts.append(bm_to_object('_faR', bm, skin))

    # hands
    for side, center in (('L', Vector((0.30, 0.10, 0.68))), ('R', Vector((-0.26, 0.12, 0.70)))):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.034)
        for v in bm.verts:
            v.co.x *= 0.85
            v.co.z *= 1.05
            v.co += center
        parts.append(bm_to_object(f'_hand{side}', bm, skin))

    # legs
    for sx, side in ((0.09, 'L'), (-0.09, 'R')):
        bm = bmesh.new()
        tube(bm, [Vector((sx, 0.01, 0.70)), Vector((sx, 0.02, 0.50)), Vector((sx, 0.025, 0.32))],
             [0.062, 0.055, 0.048], segs=10)
        parts.append(bm_to_object(f'_th{side}', bm, leather))
        bm = bmesh.new()
        tube(bm, [Vector((sx, 0.025, 0.32)), Vector((sx, 0.03, 0.18)), Vector((sx, 0.035, 0.08))],
             [0.045, 0.040, 0.034], segs=9)
        parts.append(bm_to_object(f'_calf{side}', bm, hose))

    # muddy boots
    for sx, side in ((0.09, 'L'), (-0.09, 'R')):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.048)
        for v in bm.verts:
            v.co.y *= 1.1
            v.co.z *= 0.8
            v.co += Vector((sx, 0.02, 0.075))
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.040,
                                  matrix=Matrix.Translation((sx, 0.08, 0.028)))
        for v in bm.verts:
            local = v.co - Vector((sx, 0.08, 0.028))
            if (v.co - Vector((sx, 0.02, 0.075))).length > 0.05:
                v.co.y = 0.08 + local.y * 1.65
                v.co.z = 0.028 + local.z * 0.6
                v.co.x = sx + local.x * 0.9
            if v.co.z < 0.01:
                v.co.z = 0.006
        parts.append(bm_to_object(f'_boot{side}', bm, boots_m))

    return join_named('Bandit_Limbs', parts)


def make_weapon(wood, iron, variant='a'):
    """Spear (a) or cudgel (b)."""
    parts = []
    if variant == 'a':
        # Spear shaft in left hand, butt near ground, tip up
        bm = bmesh.new()
        path, radii = [], []
        for i in range(20):
            t = i / 19
            # from hand upward-forward
            x = 0.30 + 0.02 * t
            y = 0.10 + 0.05 * t
            z = 0.68 + t * 1.35
            path.append(Vector((x, y, z)))
            radii.append(0.016 - 0.004 * t)
        tube(bm, path, radii, segs=8)
        parts.append(bm_to_object('_shaft', bm, wood))
        # iron spearhead
        bm = bmesh.new()
        tip = Vector((0.32, 0.16, 2.05))
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=8, radius1=0.028, radius2=0.002, depth=0.14,
            matrix=Matrix.Translation(tip + Vector((0, 0, -0.02))) @ Matrix.Rotation(math.radians(8), 4, 'X'),
        )
        # small crossguard socket
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=8, radius1=0.022, radius2=0.022, depth=0.03,
            matrix=Matrix.Translation(tip + Vector((0, 0, -0.10))),
        )
        parts.append(bm_to_object('_spearhead', bm, iron))
    else:
        # Cudgel / club in right hand
        bm = bmesh.new()
        path = [Vector((-0.26, 0.12, 0.70)), Vector((-0.28, 0.14, 0.95)),
                Vector((-0.30, 0.16, 1.15)), Vector((-0.32, 0.18, 1.32))]
        tube(bm, path, [0.018, 0.022, 0.032, 0.042], segs=9)
        # knotty head
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.055,
                                  matrix=Matrix.Translation((-0.33, 0.19, 1.38)))
        parts.append(bm_to_object('_cudgel', bm, wood))
        # iron studs
        for i, (ox, oy, oz) in enumerate((
            (-0.30, 0.22, 1.40), (-0.36, 0.16, 1.36), (-0.33, 0.21, 1.32),
        )):
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=0.012,
                                      matrix=Matrix.Translation((ox, oy, oz)))
            parts.append(bm_to_object(f'_stud{i}', bm, iron))

    return join_named('Bandit_Weapon', parts)


def make_hood_cowl(cloth):
    """Short rough cowl / shoulder wrap — road brigand, not fantasy hood."""
    bm = bmesh.new()
    u_segs, v_segs = 24, 10
    theta0, theta1 = math.radians(50), math.radians(310)
    grid = []
    for i in range(v_segs + 1):
        v = i / v_segs
        z = 1.40 - v * 0.55
        row = []
        for j in range(u_segs + 1):
            t = j / u_segs
            ang = theta0 + (theta1 - theta0) * t
            r = 0.18 + 0.06 * v + 0.015 * math.sin(t * math.tau * 3 + v * 4)
            x = r * math.cos(ang)
            y = -0.04 + r * math.sin(ang) * 0.85
            z_adj = z + 0.02 * abs(math.sin(ang)) * (1 - v)
            row.append(bm.verts.new((x, y, z_adj)))
        grid.append(row)
    for i in range(v_segs):
        for j in range(u_segs):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object('Bandit_Cowl', bm, cloth)


def create_armature(name='Bandit_Armature'):
    arm_data = bpy.data.armatures.new(name)
    arm_obj = bpy.data.objects.new(name, arm_data)
    link_object(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bones = arm_data.edit_bones

    def add_bone(bname, head, tail, parent=None):
        b = bones.new(bname)
        b.head = Vector(head)
        b.tail = Vector(tail)
        if parent is not None:
            b.parent = bones[parent]
        return b

    add_bone('Root', (0, 0, 0), (0, 0, 0.1))
    add_bone('Hips', (0, 0, 0.82), (0, 0, 0.98), 'Root')
    add_bone('Spine', (0, 0, 0.98), (0, 0, 1.18), 'Hips')
    add_bone('Chest', (0, 0, 1.18), (0, 0, 1.36), 'Spine')
    add_bone('Neck', (0, 0, 1.36), (0, 0, 1.46), 'Chest')
    add_bone('Head', (0, 0, 1.46), (0, 0, 1.68), 'Neck')
    add_bone('Shoulder_L', (0.08, 0, 1.30), (0.18, 0, 1.28), 'Chest')
    add_bone('UpperArm_L', (0.18, 0, 1.28), (0.26, 0.06, 0.92), 'Shoulder_L')
    add_bone('ForeArm_L', (0.26, 0.06, 0.92), (0.30, 0.10, 0.68), 'UpperArm_L')
    add_bone('Hand_L', (0.30, 0.10, 0.68), (0.32, 0.12, 0.62), 'ForeArm_L')
    add_bone('Shoulder_R', (-0.08, 0, 1.30), (-0.18, 0, 1.28), 'Chest')
    add_bone('UpperArm_R', (-0.18, 0, 1.28), (-0.24, 0.08, 0.94), 'Shoulder_R')
    add_bone('ForeArm_R', (-0.24, 0.08, 0.94), (-0.26, 0.12, 0.70), 'UpperArm_R')
    add_bone('Hand_R', (-0.26, 0.12, 0.70), (-0.28, 0.14, 0.64), 'ForeArm_R')
    add_bone('Thigh_L', (0.09, 0, 0.82), (0.09, 0.02, 0.32), 'Hips')
    add_bone('Calf_L', (0.09, 0.02, 0.32), (0.09, 0.035, 0.06), 'Thigh_L')
    add_bone('Foot_L', (0.09, 0.035, 0.06), (0.09, 0.11, 0.02), 'Calf_L')
    add_bone('Thigh_R', (-0.09, 0, 0.82), (-0.09, 0.02, 0.32), 'Hips')
    add_bone('Calf_R', (-0.09, 0.02, 0.32), (-0.09, 0.035, 0.06), 'Thigh_R')
    add_bone('Foot_R', (-0.09, 0.035, 0.06), (-0.09, 0.11, 0.02), 'Calf_R')
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj


def build_bandit(variant='a'):
    clear_scene()
    skin = mat('Bandit_Skin', (0.72, 0.55, 0.42), 0.58, specular=0.35)
    leather = mat('Bandit_Leather', (0.28, 0.20, 0.12), 0.88, specular=0.18)
    cloth = mat('Bandit_Cloth', (0.35, 0.30, 0.24), 0.90, specular=0.12)
    hair_m = mat('Bandit_Hair', (0.18, 0.12, 0.08), 0.78)
    brow_m = mat('Bandit_Brow', (0.12, 0.08, 0.05), 0.8)
    hose = mat('Bandit_Hose', (0.25, 0.22, 0.18), 0.88)
    boots_m = mat('Bandit_Boots', (0.12, 0.09, 0.07), 0.92)
    mail = mat('Bandit_Mail', (0.48, 0.48, 0.44), 0.42, metallic=0.6, specular=0.5)
    wood = mat('Bandit_Wood', (0.38, 0.26, 0.14), 0.80, specular=0.25)
    iron = mat('Bandit_Iron', (0.35, 0.34, 0.32), 0.40, metallic=0.7, specular=0.5)

    if variant == 'a':
        badge_metal = mat('Bandit_BadgeMetal', (0.62, 0.58, 0.42), 0.35, metallic=0.75, specular=0.55)
        badge_enamel = mat('Bandit_BadgeEnamel', (0.55, 0.12, 0.10), 0.55, specular=0.3)  # dull red cross
    else:
        badge_metal = mat('Bandit_BadgeMetalB', (0.50, 0.52, 0.55), 0.40, metallic=0.7, specular=0.5)
        badge_enamel = mat('Bandit_BadgeEnamelB', (0.15, 0.28, 0.45), 0.55, specular=0.3)  # faded blue

    meshes = [
        make_torso(leather, cloth),
        make_mail_scraps(mail),
        make_badge(badge_metal, badge_enamel, variant=variant),
        make_head(skin, hair_m, brow_m),
        make_belt(leather),
        make_limbs(leather, skin, hose, boots_m),
        make_weapon(wood, iron, variant=variant),
        make_hood_cowl(cloth),
    ]
    meshes = [m for m in meshes if m is not None]

    # Measure height from BODY only (exclude spear/cudgel tip), then scale ALL meshes.
    body = [o for o in meshes if 'Weapon' not in o.name]
    bb0 = world_bounds(body if body else meshes)
    h0 = bb0['size'][2]
    if h0 > 1e-6:
        s = TARGET_HEIGHT / h0
        print(f"Body height {h0:.4f} -> scale {s:.4f} to {TARGET_HEIGHT}")
        for obj in meshes:
            obj.scale = (obj.scale[0] * s, obj.scale[1] * s, obj.scale[2] * s)
            transform_apply(obj, location=False, rotation=False, scale=True)
    plant_feet(meshes)
    b = world_bounds(meshes)
    bb = world_bounds(body) if body else b
    print(f"Pre-armature body size={tuple(round(x, 4) for x in bb['size'])} all={tuple(round(x, 4) for x in b['size'])}")

    body_w = bb['size'][0]
    if body_w > MAX_WIDTH:
        sx = MAX_WIDTH / body_w
        print(f"Body width {body_w:.3f} > {MAX_WIDTH}, scaling X by {sx:.4f}")
        for obj in meshes:
            for v in obj.data.vertices:
                v.co.x *= sx
            obj.data.update()
        plant_feet(meshes)

    arm = create_armature(f'Bandit_Armature_{variant.upper()}')
    for obj in meshes:
        obj.parent = arm

    b = world_bounds(meshes)
    tris = count_tris(meshes)
    print(f"Bandit {variant} final size={tuple(round(x, 4) for x in b['size'])} tris={tris}")
    return meshes, arm


def export_glb(path):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type in {'MESH', 'ARMATURE'} and not obj.name.startswith('Preview') and obj.name != 'CapsuleGuide':
            obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_animations=False,
        export_skins=True,
        export_morph=False,
    )


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
    key.name = 'PreviewKey'
    key.data.energy = 300
    key.data.size = 2.5
    key.rotation_euler = (math.radians(50), math.radians(15), math.radians(35))

    bpy.ops.object.light_add(type='AREA', location=(-2.0, 1.5, 2.4))
    fill = bpy.context.active_object
    fill.name = 'PreviewFill'
    fill.data.energy = 100
    fill.data.size = 3.0
    fill.data.color = (0.75, 0.82, 0.9)

    bpy.ops.object.light_add(type='SUN', location=(0, 0, 5))
    sun = bpy.context.active_object
    sun.name = 'PreviewSun'
    sun.data.energy = 1.4
    sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(-20))

    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = 'PreviewGround'
    ground.data.materials.append(mat('Ground', (0.42, 0.36, 0.28), 0.95))


def add_capsule_guide():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.72, vertices=24, location=(0, 0, 0.86))
    guide = bpy.context.active_object
    guide.name = 'CapsuleGuide'
    m = mat('CapsuleGuide', (0.2, 0.55, 0.85), 0.4)
    try:
        m.blend_method = 'BLEND'
    except Exception:
        pass
    try:
        bsdf = m.node_tree.nodes.get('Principled BSDF')
        if 'Alpha' in bsdf.inputs:
            bsdf.inputs['Alpha'].default_value = 0.18
    except Exception:
        pass
    guide.data.materials.append(m)
    return guide


def render_previews(prefix='badge_bandit'):
    setup_preview_world()
    guide = add_capsule_guide()
    bpy.ops.object.camera_add(location=(0, -3.2, 1.15))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam

    views = [
        ('front', (0, 3.5, 1.15), False),
        ('threequarter', (2.6, 2.8, 1.40), False),
    ]
    target = Vector((0, 0, 0.95))
    for name, loc, show_guide in views:
        guide.hide_render = not show_guide
        guide.hide_viewport = not show_guide
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        out = os.path.join(PREV_DIR, f'{prefix}_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)


def cleanup_preview_helpers():
    for name in ('PreviewGround', 'CapsuleGuide', 'PreviewCam',
                 'PreviewKey', 'PreviewFill', 'PreviewSun'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def export_one(variant, filename, preview_prefix):
    meshes, arm = build_bandit(variant=variant)
    glb_path = os.path.join(OUT_DIR, filename)
    export_glb(glb_path)
    print('Exported', glb_path)

    render_previews(prefix=preview_prefix)
    cleanup_preview_helpers()
    export_glb(glb_path)
    print('Re-exported clean', glb_path)

    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    body_objs = [o for o in mesh_objs if 'Weapon' not in o.name]
    b = world_bounds(mesh_objs)
    bb = world_bounds(body_objs) if body_objs else b
    tris = count_tris(mesh_objs)
    names = sorted(o.name for o in mesh_objs)
    meta = os.path.join(PREV_DIR, f'{preview_prefix}_scale.txt')
    with open(meta, 'w') as f:
        f.write(
            f"variant={variant}\n"
            f"body_height_m={bb['size'][2]:.4f}\n"
            f"body_width_x_m={bb['size'][0]:.4f}\n"
            f"overall_height_m={b['size'][2]:.4f}\n"
            f"overall_width_x_m={b['size'][0]:.4f}\n"
            f"depth_y_m={b['size'][1]:.4f}\n"
            f"tris={tris}\n"
            f"objects={','.join(names)}\n"
            f"capsule_diameter_m=0.60\n"
            f"target_height_m={TARGET_HEIGHT}\n"
            f"max_body_width_m={MAX_WIDTH}\n"
            f"origin=feet\n"
        )
    print('Wrote', meta)
    print(f'Done {variant}. height={b["size"][2]:.4f} width={b["size"][0]:.4f} tris={tris}')
    return glb_path, b, tris


def main():
    # Primary spear + red-cross badge
    export_one('a', 'badge_bandit.glb', 'badge_bandit')
    # Nice-to-have: cudgel + blue badge variant
    export_one('b', 'badge_bandit_b.glb', 'badge_bandit_b')


if __name__ == '__main__':
    main()
