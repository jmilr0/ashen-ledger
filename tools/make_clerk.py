"""Blender: The Clerk (Broken Seal) — game-ready hero companion GLB + previews.

Dirt-and-mail Occitan notary/chaplain (1208–10). Stylized low-poly hero mesh,
NOT greybox primitives. Rebuild:
  /usr/bin/blender -b -P tools/make_clerk.py

Scale (locked):
  - Height 1.75 m, origin at feet center on ground
  - Max width ~0.56–0.58 m (fit 0.6 m diameter capsule)
  - Poly target 12k–30k tris
"""
from __future__ import annotations

import math
import os
import bmesh
import bpy
from mathutils import Matrix, Vector, Euler

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Prefer repo-relative; fall back when copied to /tmp for runners
ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..'))
if not os.path.isdir(os.path.join(ROOT, 'public', 'models')):
    ROOT = '/workspace/ashen-ledger'

OUT_DIR = os.path.join(ROOT, 'public', 'models', 'characters')
PREV_DIR = os.path.join(OUT_DIR, 'previews')
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PREV_DIR, exist_ok=True)

TARGET_HEIGHT = 1.75
MAX_WIDTH = 0.58  # soft max across X (staff/satchel included)


# ---------------------------------------------------------------------------
# Scene / material helpers
# ---------------------------------------------------------------------------

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


def link_object(obj, collection=None):
    if collection is None:
        collection = bpy.context.scene.collection
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    return obj


def new_mesh_object(name, mesh):
    obj = bpy.data.objects.new(name, mesh)
    link_object(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def shade_smooth(obj, angle_deg=40.0):
    mesh = obj.data
    for poly in mesh.polygons:
        poly.use_smooth = True
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass


def apply_mat(obj, material):
    if material.name not in [m.name for m in obj.data.materials]:
        obj.data.materials.append(material)
    else:
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
    return obj



def join_named(name, objs, material=None):
    """Join mesh objects and force final name."""
    objs = [o for o in objs if o is not None and o.name in bpy.data.objects]
    if not objs:
        return None
    if len(objs) == 1:
        objs[0].name = name
        if material is not None:
            apply_mat(objs[0], material)
        return objs[0]
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = name
    # ensure datablock name too
    if joined.data:
        joined.data.name = name
    shade_smooth(joined)
    return joined


def subdivide_object(obj, cuts=1):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=cuts, use_grid_fill=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    shade_smooth(obj)
    return obj

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
            xs.append(c.x)
            ys.append(c.y)
            zs.append(c.z)
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


# ---------------------------------------------------------------------------
# Procedural mesh builders (bmesh)
# ---------------------------------------------------------------------------

def make_tapered_limb(name, z0, z1, r0, r1, segs=12, rings=6, material=None,
                      bend_y=0.0, lean_x=0.0, oval_y=1.0):
    """Vertical tapered tube from z0→z1 with optional lean/bend."""
    bm = bmesh.new()
    verts_rings = []
    for i in range(rings + 1):
        t = i / rings
        z = z0 + (z1 - z0) * t
        r = r0 + (r1 - r0) * t
        # slight S-curve bend in Y and lean in X
        cx = lean_x * t
        cy = bend_y * math.sin(t * math.pi)
        ring = []
        for j in range(segs):
            a = (j / segs) * math.tau
            x = cx + r * math.cos(a)
            y = cy + r * oval_y * math.sin(a)
            ring.append(bm.verts.new((x, y, z)))
        verts_rings.append(ring)
    bm.verts.ensure_lookup_table()

    for i in range(rings):
        for j in range(segs):
            j2 = (j + 1) % segs
            v00 = verts_rings[i][j]
            v01 = verts_rings[i][j2]
            v10 = verts_rings[i + 1][j]
            v11 = verts_rings[i + 1][j2]
            bm.faces.new((v00, v01, v11, v10))

    # Cap bottom & top
    for ring, flip in ((verts_rings[0], True), (verts_rings[-1], False)):
        f = bmesh.ops.edgeloop_fill(bm, edges=[
            e for e in bm.edges if e.is_boundary and all(v in ring for v in e.verts)
        ])
        # fallback triangulate fan if fill fails
        if not f.get('faces'):
            c = Vector((0, 0, 0))
            for v in ring:
                c += v.co
            c /= len(ring)
            center = bm.verts.new(c)
            for j in range(segs):
                j2 = (j + 1) % segs
                if flip:
                    bm.faces.new((center, ring[j2], ring[j]))
                else:
                    bm.faces.new((center, ring[j], ring[j2]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object(name, bm, material)


def make_body_torso(name, material):
    """Sculpted wool tunic torso — chest/waist taper, mild folds."""
    bm = bmesh.new()
    segs = 16
    # profile rings: (z, rx, ry, fold_amp)
    profile = [
        (0.78, 0.155, 0.120, 0.004),  # hips / tunic hem top of pelvis join
        (0.90, 0.150, 0.115, 0.006),  # waist belt line
        (1.02, 0.145, 0.112, 0.008),  # mid torso
        (1.14, 0.160, 0.118, 0.010),  # chest
        (1.26, 0.175, 0.125, 0.008),  # upper chest / shoulders
        (1.34, 0.155, 0.115, 0.004),  # neck base
        (1.40, 0.070, 0.065, 0.000),  # neck top
    ]
    rings = []
    for z, rx, ry, fold in profile:
        ring = []
        for j in range(segs):
            a = (j / segs) * math.tau
            # mild cloth undulation
            wave = 1.0 + fold * math.sin(a * 4) + fold * 0.5 * math.cos(a * 2 + z * 3)
            x = rx * wave * math.cos(a)
            y = ry * wave * math.sin(a)
            # slightly flatten front for readable chest
            if math.sin(a) > 0.2:
                y *= 0.92
            ring.append(bm.verts.new((x, y, z)))
        rings.append(ring)
    bm.verts.ensure_lookup_table()

    for i in range(len(rings) - 1):
        for j in range(segs):
            j2 = (j + 1) % segs
            bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))

    # neck cap
    top = rings[-1]
    c = sum((v.co for v in top), Vector()) / len(top)
    center = bm.verts.new(c)
    for j in range(segs):
        bm.faces.new((center, top[j], top[(j + 1) % segs]))

    # open bottom — will meet skirt/legs; add hem ring flare
    hem_z = 0.72
    hem = []
    for j in range(segs):
        a = (j / segs) * math.tau
        wave = 1.0 + 0.012 * math.sin(a * 5)
        x = 0.175 * wave * math.cos(a)
        y = 0.135 * wave * math.sin(a)
        hem.append(bm.verts.new((x, y, hem_z)))
    for j in range(segs):
        j2 = (j + 1) % segs
        bm.faces.new((hem[j], hem[j2], rings[0][j2], rings[0][j]))
    # hem underside cap (slightly inward)
    c2 = sum((v.co for v in hem), Vector()) / len(hem)
    c2.z -= 0.02
    center2 = bm.verts.new(c2)
    for j in range(segs):
        bm.faces.new((center2, hem[(j + 1) % segs], hem[j]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # light subdivide for fold readability
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
    # re-apply mild noise folds on mid-body verts
    for v in bm.verts:
        if 0.85 < v.co.z < 1.30:
            a = math.atan2(v.co.y, v.co.x)
            n = Vector((v.co.x, v.co.y, 0))
            if n.length > 1e-4:
                n.normalize()
                v.co += n * (0.004 * math.sin(a * 6 + v.co.z * 8))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object(name, bm, material)


def make_skirt(name, material):
    """Tunic skirt / lower hem draping over thighs."""
    bm = bmesh.new()
    segs = 18
    profile = [
        (0.72, 0.175, 0.135, 0.010),
        (0.58, 0.185, 0.145, 0.014),
        (0.45, 0.175, 0.140, 0.016),
        (0.34, 0.160, 0.130, 0.012),
    ]
    rings = []
    for z, rx, ry, fold in profile:
        ring = []
        for j in range(segs):
            a = (j / segs) * math.tau
            # split for legs: slight indent front/back mid
            indent = 0.0
            if abs(math.cos(a)) < 0.35:
                indent = -0.012 * (1.0 - abs(math.cos(a)) / 0.35)
            wave = 1.0 + fold * math.sin(a * 5 + z * 4)
            x = (rx * wave + indent) * math.cos(a)
            y = ry * wave * math.sin(a)
            ring.append(bm.verts.new((x, y, z)))
        rings.append(ring)

    for i in range(len(rings) - 1):
        for j in range(segs):
            j2 = (j + 1) % segs
            bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))

    # bottom hem thickened lip
    bot = rings[-1]
    lip = []
    for v in bot:
        lip.append(bm.verts.new((v.co.x * 1.02, v.co.y * 1.02, v.co.z - 0.015)))
    for j in range(segs):
        j2 = (j + 1) % segs
        bm.faces.new((bot[j], bot[j2], lip[j2], lip[j]))
    c = sum((v.co for v in lip), Vector()) / len(lip)
    c.z -= 0.01
    center = bm.verts.new(c)
    for j in range(segs):
        bm.faces.new((center, lip[(j + 1) % segs], lip[j]))

    # top open — no need to cap; overlaps torso
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
    return bm_to_object(name, bm, material)


def make_head(name, skin, hair_mat, brow_mat):
    """Readable lean male face: skull, nose, brows, ears, jaw, simple eyes."""
    parts = []

    # --- skull ---
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=14, radius=0.105)
    # elongate / lean scholar proportions
    for v in bm.verts:
        x, y, z = v.co
        # slightly longer face, narrower cheeks
        v.co.x = x * 0.92
        v.co.y = y * 0.95
        v.co.z = z * 1.12
        # jaw taper
        if z < -0.02:
            v.co.x *= 0.88 + 0.12 * ((z + 0.105) / 0.085)
            v.co.y *= 0.95
        # forehead flatten slightly forward
        if z > 0.04 and y > 0:
            v.co.y *= 0.92
        # cheek hollow
        if abs(x) > 0.04 and -0.02 < z < 0.04 and y > -0.02:
            v.co.x *= 0.94
    # move to world head position
    for v in bm.verts:
        v.co += Vector((0, 0.01, 1.575))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    skull = bm_to_object(f'{name}_Skull', bm, skin)
    parts.append(skull)

    # --- nose ---
    bm = bmesh.new()
    # bridge → tip prism
    nose_pts = [
        # back of bridge (wider)
        (-0.012, 0.078, 1.590), (0.012, 0.078, 1.590),
        (-0.010, 0.078, 1.555), (0.010, 0.078, 1.555),
        # tip
        (-0.009, 0.112, 1.548), (0.009, 0.112, 1.548),
        (-0.008, 0.105, 1.530), (0.008, 0.105, 1.530),
        # nostrils underside
        (-0.011, 0.095, 1.525), (0.011, 0.095, 1.525),
    ]
    vs = [bm.verts.new(p) for p in nose_pts]
    faces = [
        (0, 1, 3, 2),
        (0, 2, 4), (1, 5, 3), (2, 3, 5, 4),
        (4, 5, 7, 6),
        (6, 7, 9, 8),
        (4, 6, 8), (5, 9, 7),
        (8, 9, 3, 2),
    ]
    for f in faces:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # subdivide once for smoother nose
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
    nose = bm_to_object(f'{name}_Nose', bm, skin)
    parts.append(nose)

    # --- brows ---
    for side, sx in (('L', 1), ('R', -1)):
        bm = bmesh.new()
        # arched brow ridge
        for i in range(6):
            t = i / 5
            x = sx * (0.018 + 0.045 * t)
            y = 0.085 - 0.01 * abs(t - 0.4)
            z = 1.605 + 0.012 * math.sin(t * math.pi) - 0.004 * t
            r = 0.008 - 0.002 * t
            bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=r,
                                      matrix=Matrix.Translation((x, y, z)))
        brow = bm_to_object(f'{name}_Brow{side}', bm, brow_mat)
        parts.append(brow)

    # --- ears ---
    for side, sx in (('L', 1), ('R', -1)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.028)
        for v in bm.verts:
            v.co.x *= 0.45
            v.co.y *= 0.7
            v.co.z *= 1.15
            v.co += Vector((sx * 0.095, -0.01, 1.570))
        ear = bm_to_object(f'{name}_Ear{side}', bm, skin)
        parts.append(ear)

    # --- eyes (simple inset spheres + dark iris) ---
    eye_dark = mat('EyeDark', (0.08, 0.07, 0.06), 0.35)
    eye_white = mat('EyeWhite', (0.88, 0.86, 0.82), 0.45)
    for side, sx in (('L', 1), ('R', -1)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.016)
        for v in bm.verts:
            v.co.y *= 0.7
            v.co += Vector((sx * 0.032, 0.090, 1.575))
        eye = bm_to_object(f'{name}_Eye{side}', bm, eye_white)
        parts.append(eye)

        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.008)
        for v in bm.verts:
            v.co += Vector((sx * 0.032, 0.102, 1.575))
        iris = bm_to_object(f'{name}_Iris{side}', bm, eye_dark)
        parts.append(iris)

    # --- mouth slit (subtle) ---
    bm = bmesh.new()
    for i in range(7):
        t = (i / 6) * 2 - 1
        x = t * 0.022
        y = 0.088 - 0.006 * abs(t)
        z = 1.522
        bmesh.ops.create_uvsphere(bm, u_segments=5, v_segments=4, radius=0.004,
                                  matrix=Matrix.Translation((x, y, z)))
    # squash
    for v in bm.verts:
        v.co.z = 1.522 + (v.co.z - 1.522) * 0.4
    lip = bm_to_object(f'{name}_Mouth', bm, mat('Lip', (0.62, 0.40, 0.36), 0.6))
    parts.append(lip)

    # --- hair: bowl + fringe + nape ---
    bm = bmesh.new()
    # main cap
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.118)
    kill = []
    for v in bm.verts:
        # remove lower hemisphere more aggressively in front
        if v.co.z < -0.02:
            kill.append(v)
        else:
            v.co.x *= 1.05
            v.co.y *= 1.08
            v.co.z *= 0.95
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    for v in bm.verts:
        v.co += Vector((0, -0.01, 1.600))
    # fringe clumps
    for i, x in enumerate((-0.05, -0.02, 0.02, 0.05)):
        bmesh.ops.create_uvsphere(
            bm, u_segments=6, v_segments=5, radius=0.028,
            matrix=Matrix.Translation((x, 0.08, 1.62 - abs(x) * 0.15)),
        )
    # sideburns / temples
    for sx in (-1, 1):
        bmesh.ops.create_uvsphere(
            bm, u_segments=6, v_segments=5, radius=0.032,
            matrix=Matrix.Translation((sx * 0.085, 0.02, 1.575)),
        )
    # nape
    bmesh.ops.create_uvsphere(
        bm, u_segments=8, v_segments=6, radius=0.055,
        matrix=Matrix.Translation((0, -0.06, 1.55)),
    )
    for v in bm.verts:
        # flatten nape sphere a bit
        if v.co.y < -0.04 and v.co.z < 1.58:
            v.co.z = max(v.co.z, 1.48)
    hair = bm_to_object(f'{name}_Hair', bm, hair_mat)
    parts.append(hair)

    # Join all head parts into Clerk_Head
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    head = bpy.context.active_object
    head.name = name
    shade_smooth(head, 50)
    return head


def make_cloak(name, material):
    """Draped travel cloak — rear/side silhouette with folds, open at front."""
    bm = bmesh.new()
    # Parametric cloak: theta from ~40° to 320° (open front), height layers
    u_segs = 28
    v_segs = 12
    theta0 = math.radians(50)
    theta1 = math.radians(310)

    def radius_at(t, v):
        # t in [0,1] around, v in [0,1] height
        base = 0.20 + 0.06 * v  # flares downward
        fold = 0.018 * math.sin(t * math.tau * 3.5 + v * 4)
        # pull in at shoulders
        if v > 0.85:
            base *= 0.75 + 0.25 * (1 - (v - 0.85) / 0.15)
        return base + fold

    def center_y(v):
        # shift cloak mass rearward
        return -0.04 - 0.06 * (1 - v)

    grid = []
    for i in range(v_segs + 1):
        v = i / v_segs
        z = 1.38 - v * 0.95  # shoulders → mid-calf
        row = []
        for j in range(u_segs + 1):
            t = j / u_segs
            ang = theta0 + (theta1 - theta0) * t
            r = radius_at(t, v)
            x = r * math.cos(ang)
            y = center_y(v) + r * math.sin(ang) * 0.85
            # shoulder drape: higher at sides
            z_adj = z + 0.03 * math.sin(ang) * (1 - v) if abs(math.sin(ang)) > 0 else z
            # collar rise at top back
            if v < 0.08:
                z_adj += 0.04 * (1 - abs(t - 0.5) * 2) * (1 - v / 0.08)
            row.append(bm.verts.new((x, y, z_adj)))
        grid.append(row)

    for i in range(v_segs):
        for j in range(u_segs):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))

    # thickness: duplicate inward shell slightly
    # (single shell is fine for game; add hem tube)
    hem = grid[-1]
    hem_in = []
    for v in hem:
        # pull toward body slightly
        p = Vector((v.co.x, v.co.y, v.co.z))
        inward = Vector((-p.x, -p.y + 0.04, 0))
        if inward.length > 1e-5:
            inward.normalize()
        hem_in.append(bm.verts.new((p.x + inward.x * 0.02, p.y + inward.y * 0.02, p.z + 0.01)))
    for j in range(u_segs):
        bm.faces.new((hem[j], hem[j + 1], hem_in[j + 1], hem_in[j]))

    # hood / collar roll at top
    collar = grid[0]
    for j in range(0, u_segs, 2):
        p = collar[j].co
        bm.verts.new((p.x * 0.7, p.y * 0.7 - 0.02, p.z + 0.05))
    # simple collar band as tube along top edge
    for j in range(u_segs):
        p = collar[j].co
        q = Vector((p.x * 0.82, p.y * 0.7 - 0.01, p.z + 0.035))
        # create small bridging faces via extra verts stored
    # rebuild collar with second row
    collar2 = []
    for j in range(u_segs + 1):
        p = collar[j].co
        collar2.append(bm.verts.new((p.x * 0.78, p.y * 0.65 - 0.015, p.z + 0.04)))
    for j in range(u_segs):
        bm.faces.new((collar[j], collar[j + 1], collar2[j + 1], collar2[j]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # one subdivide for fold density
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
    # deepen folds post-subdivide
    for v in bm.verts:
        ang = math.atan2(v.co.y + 0.08, v.co.x)
        n = Vector((v.co.x, v.co.y + 0.08, 0))
        if n.length > 0.05:
            n.normalize()
            v.co += n * (0.006 * math.sin(ang * 5 + v.co.z * 6))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object(name, bm, material)


def make_mail_collar(name, material):
    """Subtle mail coif ring / collar at neck — dirt-and-mail, not plate."""
    bm = bmesh.new()
    segs = 20
    rings_z = [
        (1.355, 0.095, 0.085),
        (1.375, 0.100, 0.088),
        (1.395, 0.092, 0.082),
        (1.410, 0.078, 0.072),
    ]
    rings = []
    for z, rx, ry in rings_z:
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            # slight hexagonal mail suggestion via radius modulation
            rmod = 1.0 + 0.03 * math.sin(a * 8)
            row.append(bm.verts.new((rx * rmod * math.cos(a), ry * rmod * math.sin(a), z)))
        rings.append(row)
    for i in range(len(rings) - 1):
        for j in range(segs):
            j2 = (j + 1) % segs
            bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
    # top & bottom caps thin
    for ring, up in ((rings[0], False), (rings[-1], True)):
        c = sum((v.co for v in ring), Vector()) / len(ring)
        center = bm.verts.new(c)
        for j in range(segs):
            if up:
                bm.faces.new((center, ring[j], ring[(j + 1) % segs]))
            else:
                bm.faces.new((center, ring[(j + 1) % segs], ring[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object(name, bm, material)


def make_belt(name, material):
    bm = bmesh.new()
    segs = 20
    z0, z1 = 0.865, 0.905
    r0, r1 = 0.165, 0.168
    rings = []
    for z, r in ((z0, r0), (z1, r1)):
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            row.append(bm.verts.new((r * math.cos(a), 0.12 * math.sin(a) / 0.165 * r, z)))
        rings.append(row)
    # outer wall
    for j in range(segs):
        j2 = (j + 1) % segs
        bm.faces.new((rings[0][j], rings[0][j2], rings[1][j2], rings[1][j]))
    # inner wall (thinner)
    inner = []
    for zi, z in enumerate((z0, z1)):
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            r = 0.145
            row.append(bm.verts.new((r * math.cos(a), 0.105 * math.sin(a), z)))
        inner.append(row)
    for j in range(segs):
        j2 = (j + 1) % segs
        bm.faces.new((inner[1][j], inner[1][j2], inner[0][j2], inner[0][j]))
    # top/bottom rims
    for j in range(segs):
        j2 = (j + 1) % segs
        bm.faces.new((rings[1][j], rings[1][j2], inner[1][j2], inner[1][j]))
        bm.faces.new((inner[0][j], inner[0][j2], rings[0][j2], rings[0][j]))
    # buckle block at front
    buckle = [
        (-0.025, 0.115, z0 - 0.005), (0.025, 0.115, z0 - 0.005),
        (0.025, 0.135, z0 - 0.005), (-0.025, 0.135, z0 - 0.005),
        (-0.025, 0.115, z1 + 0.005), (0.025, 0.115, z1 + 0.005),
        (0.025, 0.135, z1 + 0.005), (-0.025, 0.135, z1 + 0.005),
    ]
    bv = [bm.verts.new(p) for p in buckle]
    for f in [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]:
        bm.faces.new([bv[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object(name, bm, material)


def make_satchel(name, leather, parchment):
    """Leather charter satchel on left hip + strap + parchment edge."""
    objs = []

    # bag body
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.07
        v.co.y *= 0.045
        v.co.z *= 0.11
        v.co += Vector((0.20, 0.08, 0.88))
    # round edges via subdivide + smooth
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=2, use_grid_fill=True)
    # inflate slightly non-uniform for soft leather look
    center = Vector((0.20, 0.08, 0.88))
    for v in bm.verts:
        d = v.co - center
        # less inflate on back face (toward body, -Y-ish wait +Y is front)
        v.co += d.normalized() * 0.008 * (0.5 + 0.5 * abs(d.x) / 0.07) if d.length > 1e-6 else Vector()
    bag = bm_to_object(f'{name}_Bag', bm, leather)
    objs.append(bag)

    # flap
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.075
        v.co.y *= 0.02
        v.co.z *= 0.06
        v.co += Vector((0.20, 0.11, 0.94))
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
    flap = bm_to_object(f'{name}_Flap', bm, leather)
    objs.append(flap)

    # parchment peeking out
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.045
        v.co.y *= 0.008
        v.co.z *= 0.07
        v.co += Vector((0.20, 0.12, 0.93))
    parch = bm_to_object(f'{name}_Charter', bm, parchment)
    objs.append(parch)

    # strap over shoulder
    bm = bmesh.new()
    segs = 14
    for i in range(segs + 1):
        t = i / segs
        # from satchel up over right-ish shoulder? left hip satchel → strap to opposite shoulder
        # satchel is on +X (character left when facing +Y)... wait: +X is character's left if facing +Y.
        # Strap goes to right shoulder (-X).
        x = 0.20 - 0.32 * t
        y = 0.08 - 0.04 * math.sin(t * math.pi)
        z = 0.92 + 0.42 * math.sin(t * math.pi * 0.9)
        if t > 0.85:
            z = 1.30 - (t - 0.85) * 0.5
        r = 0.012
        # cross-section quad
        for k, (dx, dy) in enumerate(((-r, 0), (r, 0), (r, 0), (-r, 0))):
            pass
        # simpler: small sphere chain then we'll skin as tube
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=6, radius1=0.011, radius2=0.011, depth=0.04,
            matrix=Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(90), 4, 'X'),
        )
    strap = bm_to_object(f'{name}_Strap', bm, leather)
    objs.append(strap)

    # Join satchel parts
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    sat = bpy.context.active_object
    sat.name = name
    shade_smooth(sat)
    return sat


def make_staff(name, wood):
    """Wooden walking staff with grip wrap + knob — NOT a sword."""
    bm = bmesh.new()
    segs = 10
    # main shaft profile (slight taper, mild crook)
    n = 18
    rings = []
    for i in range(n + 1):
        t = i / n
        z = 0.02 + t * 1.48
        r = 0.016 - 0.003 * t
        # gentle crook near top
        x = -0.22 + (-0.02 if t > 0.7 else 0.0) * ((t - 0.7) / 0.3 if t > 0.7 else 0)
        y = 0.06 + 0.02 * math.sin(t * math.pi)
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            row.append(bm.verts.new((x + r * math.cos(a), y + r * math.sin(a), z)))
        rings.append(row)
    for i in range(n):
        for j in range(segs):
            j2 = (j + 1) % segs
            bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
    # caps
    for ring, up in ((rings[0], False), (rings[-1], True)):
        c = sum((v.co for v in ring), Vector()) / len(ring)
        center = bm.verts.new(c)
        for j in range(segs):
            if up:
                bm.faces.new((center, ring[j], ring[(j + 1) % segs]))
            else:
                bm.faces.new((center, ring[(j + 1) % segs], ring[j]))

    # knob
    knob_c = Vector((-0.24, 0.07, 1.52))
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.028,
                              matrix=Matrix.Translation(knob_c))
    # grip wrap ridges near hand height
    for gz in (0.78, 0.82, 0.86):
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=8, radius1=0.019, radius2=0.019, depth=0.025,
            matrix=Matrix.Translation((-0.22, 0.06, gz)),
        )

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object(name, bm, wood)


def make_hands(skin, leather):
    objs = []
    # Left hand (open, near hip)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.038)
    for v in bm.verts:
        v.co.x *= 0.85
        v.co.z *= 1.15
        v.co += Vector((0.24, 0.05, 0.78))
    # fingers as small capsules
    for i, fx in enumerate((-0.015, 0.0, 0.015, 0.028)):
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=5, radius1=0.007, radius2=0.005, depth=0.035,
            matrix=Matrix.Translation((0.24 + fx, 0.07, 0.75)) @ Matrix.Rotation(math.radians(70), 4, 'X'),
        )
    hand_l = bm_to_object('Clerk_HandL', bm, skin)
    objs.append(hand_l)

    # Right hand gripping staff
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.038)
    for v in bm.verts:
        v.co.x *= 0.9
        v.co.z *= 1.1
        v.co += Vector((-0.22, 0.07, 0.80))
    for i, offset in enumerate((-0.01, 0.0, 0.01, 0.02)):
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=5, radius1=0.007, radius2=0.005, depth=0.03,
            matrix=Matrix.Translation((-0.22 + offset * 0.3, 0.09, 0.78))
            @ Matrix.Rotation(math.radians(90), 4, 'X'),
        )
    hand_r = bm_to_object('Clerk_HandR', bm, skin)
    objs.append(hand_r)
    return objs


def make_boots(material):
    objs = []
    for side, sx in (('L', 0.09), ('R', -0.09)):
        bm = bmesh.new()
        # ankle
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.048)
        for v in bm.verts:
            v.co.x *= 0.95
            v.co.y *= 1.1
            v.co.z *= 0.9
            v.co += Vector((sx, 0.02, 0.08))
        # foot
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.045)
        for v in list(bm.verts)[-10 * 8:]:  # approximate last sphere verts — better mark
            pass
        # remake foot carefully
        foot_verts = [v for v in bm.verts if (v.co - Vector((sx, 0.02, 0.08))).length < 0.06]
        # separate foot sphere
        bm2_start = len(bm.verts)
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.042,
                                  matrix=Matrix.Translation((sx, 0.07, 0.035)))
        for v in bm.verts:
            # elongate foot forward
            local = v.co - Vector((sx, 0.07, 0.035))
            if abs(local.z) < 0.05 and (v.co - Vector((sx, 0.02, 0.08))).length > 0.05:
                v.co.y = sx * 0 + 0.07 + local.y * 1.6
                v.co.z = 0.035 + local.z * 0.7
                v.co.x = sx + local.x * 0.9
        # sole flatten
        for v in bm.verts:
            if v.co.z < 0.015:
                v.co.z = 0.01 + v.co.z * 0.2
        boot = bm_to_object(f'Clerk_Boot{side}', bm, material)
        objs.append(boot)
    return objs


def make_ink_pouch_and_quill(leather, hair_mat, wood):
    objs = []
    # ink pouch on belt front-right of buckle
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.028)
    for v in bm.verts:
        v.co.x *= 0.7
        v.co.z *= 1.2
        v.co += Vector((-0.08, 0.14, 0.88))
    pouch = bm_to_object('Clerk_InkPouch', bm, leather)
    objs.append(pouch)

    # quill
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=6, radius1=0.006, radius2=0.002, depth=0.14,
        matrix=Matrix.Translation((0.06, 0.14, 0.95))
        @ Matrix.Rotation(math.radians(55), 4, 'X')
        @ Matrix.Rotation(math.radians(15), 4, 'Z'),
    )
    # feather tip fluff
    bmesh.ops.create_uvsphere(
        bm, u_segments=6, v_segments=4, radius=0.012,
        matrix=Matrix.Translation((0.07, 0.20, 1.02)),
    )
    quill = bm_to_object('Clerk_Quill', bm, hair_mat)
    objs.append(quill)
    return objs


def make_shoulders_arms(tunic, skin):
    objs = []
    # shoulders
    for side, sx in (('L', 1), ('R', -1)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.055)
        for v in bm.verts:
            v.co.x *= 1.1
            v.co += Vector((sx * 0.17, 0.0, 1.28))
        sh = bm_to_object(f'Clerk_Shoulder{side}', bm, tunic)
        objs.append(sh)

    # upper arms (A-pose slight)
    for side, sx in (('L', 1), ('R', -1)):
        arm = make_tapered_limb(
            f'Clerk_UpperArm{side}',
            z0=1.22, z1=0.95,
            r0=0.048, r1=0.040,
            segs=10, rings=5,
            material=tunic,
            lean_x=sx * 0.05,
            bend_y=0.02,
            oval_y=0.95,
        )
        # shift outward
        for v in arm.data.vertices:
            v.co.x += sx * 0.17
        arm.data.update()
        objs.append(arm)

        forearm = make_tapered_limb(
            f'Clerk_ForeArm{side}',
            z0=0.95, z1=0.78,
            r0=0.038, r1=0.032,
            segs=10, rings=4,
            material=skin,
            lean_x=sx * 0.02,
            bend_y=0.03,
            oval_y=0.9,
        )
        for v in forearm.data.vertices:
            v.co.x += sx * (0.20 if side == 'L' else 0.20)
        # right arm closer to staff
        if side == 'R':
            for v in forearm.data.vertices:
                v.co.x = -0.20 + (v.co.x + 0.20) * 0.3 - 0.02
                v.co.y += 0.03
        else:
            for v in forearm.data.vertices:
                v.co.y += 0.02
        forearm.data.update()
        objs.append(forearm)

    return objs


def make_legs(tunic, hose):
    objs = []
    for side, sx in (('L', 0.09), ('R', -0.09)):
        thigh = make_tapered_limb(
            f'Clerk_Thigh{side}',
            z0=0.72, z1=0.40,
            r0=0.065, r1=0.052,
            segs=12, rings=5,
            material=tunic,
            oval_y=0.92,
        )
        for v in thigh.data.vertices:
            v.co.x += sx
        thigh.data.update()
        objs.append(thigh)

        calf = make_tapered_limb(
            f'Clerk_Calf{side}',
            z0=0.40, z1=0.10,
            r0=0.048, r1=0.038,
            segs=10, rings=5,
            material=hose,
            bend_y=0.015,
            oval_y=0.9,
        )
        for v in calf.data.vertices:
            v.co.x += sx
            v.co.y += 0.01
        calf.data.update()
        objs.append(calf)
    return objs


# ---------------------------------------------------------------------------
# Armature (simple A-pose hooks)
# ---------------------------------------------------------------------------

def create_armature(name='Clerk_Armature'):
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
            b.use_connect = False
        return b

    add_bone('Root', (0, 0, 0), (0, 0, 0.1))
    add_bone('Hips', (0, 0, 0.85), (0, 0, 1.0), 'Root')
    add_bone('Spine', (0, 0, 1.0), (0, 0, 1.2), 'Hips')
    add_bone('Chest', (0, 0, 1.2), (0, 0, 1.38), 'Spine')
    add_bone('Neck', (0, 0, 1.38), (0, 0, 1.48), 'Chest')
    add_bone('Head', (0, 0, 1.48), (0, 0, 1.70), 'Neck')
    add_bone('Shoulder_L', (0.08, 0, 1.30), (0.18, 0, 1.28), 'Chest')
    add_bone('UpperArm_L', (0.18, 0, 1.28), (0.22, 0.02, 0.98), 'Shoulder_L')
    add_bone('ForeArm_L', (0.22, 0.02, 0.98), (0.24, 0.05, 0.78), 'UpperArm_L')
    add_bone('Hand_L', (0.24, 0.05, 0.78), (0.24, 0.08, 0.72), 'ForeArm_L')
    add_bone('Shoulder_R', (-0.08, 0, 1.30), (-0.18, 0, 1.28), 'Chest')
    add_bone('UpperArm_R', (-0.18, 0, 1.28), (-0.22, 0.04, 0.98), 'Shoulder_R')
    add_bone('ForeArm_R', (-0.22, 0.04, 0.98), (-0.22, 0.07, 0.80), 'UpperArm_R')
    add_bone('Hand_R', (-0.22, 0.07, 0.80), (-0.22, 0.09, 0.74), 'ForeArm_R')
    add_bone('Thigh_L', (0.09, 0, 0.85), (0.09, 0.01, 0.42), 'Hips')
    add_bone('Calf_L', (0.09, 0.01, 0.42), (0.09, 0.03, 0.08), 'Thigh_L')
    add_bone('Foot_L', (0.09, 0.03, 0.08), (0.09, 0.10, 0.02), 'Calf_L')
    add_bone('Thigh_R', (-0.09, 0, 0.85), (-0.09, 0.01, 0.42), 'Hips')
    add_bone('Calf_R', (-0.09, 0.01, 0.42), (-0.09, 0.03, 0.08), 'Thigh_R')
    add_bone('Foot_R', (-0.09, 0.03, 0.08), (-0.09, 0.10, 0.02), 'Calf_R')

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj


def parent_meshes_to_armature(arm_obj, mesh_objs):
    for obj in mesh_objs:
        obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    # Keep transform parent without auto weights (cleaner for multi-material hero);
    # still provides anim hooks hierarchy.
    bpy.ops.object.parent_set(type='ARMATURE_NAME')
    bpy.ops.object.select_all(action='DESELECT')


# ---------------------------------------------------------------------------
# Build / export / preview
# ---------------------------------------------------------------------------

def build_clerk():
    clear_scene()

    # Muted earth PBR palette (Occitan winter road)
    skin = mat('Clerk_Skin', (0.78, 0.60, 0.48), 0.55, specular=0.4)
    tunic = mat('Clerk_Wool', (0.42, 0.34, 0.26), 0.88, specular=0.2)
    cloak = mat('Clerk_Cloak', (0.26, 0.23, 0.20), 0.92, specular=0.15)
    leather = mat('Clerk_Leather', (0.20, 0.13, 0.08), 0.82, specular=0.25)
    hair_m = mat('Clerk_Hair', (0.14, 0.10, 0.08), 0.75)
    brow_m = mat('Clerk_Brow', (0.12, 0.09, 0.07), 0.8)
    wood = mat('Clerk_Oak', (0.40, 0.27, 0.14), 0.78, specular=0.3)
    mail = mat('Clerk_Mail', (0.50, 0.50, 0.46), 0.40, metallic=0.65, specular=0.5)
    hose = mat('Clerk_Hose', (0.30, 0.26, 0.22), 0.85)
    boots = mat('Clerk_Boots', (0.10, 0.08, 0.07), 0.9)
    parchment = mat('Clerk_Parchment', (0.74, 0.66, 0.48), 0.88)

    meshes = []

    # Core body
    body = make_body_torso('Clerk_Body', tunic)
    meshes.append(body)
    skirt = make_skirt('Clerk_TunicSkirt', tunic)
    meshes.append(skirt)
    meshes.append(make_mail_collar('Clerk_MailCollar', mail))
    meshes.append(make_belt('Clerk_Belt', leather))
    meshes.append(make_head('Clerk_Head', skin, hair_m, brow_m))
    meshes.append(make_cloak('Clerk_Cloak', cloak))
    meshes.append(make_satchel('Clerk_Satchel', leather, parchment))
    meshes.append(make_staff('Clerk_Staff', wood))
    meshes.extend(make_shoulders_arms(tunic, skin))
    meshes.extend(make_legs(tunic, hose))
    meshes.extend(make_hands(skin, leather))
    meshes.extend(make_boots(boots))
    meshes.extend(make_ink_pouch_and_quill(leather, hair_m, wood))

    # Filter to mesh objects still in scene
    meshes = [o for o in meshes if o.name in bpy.data.objects]

    # Normalize height & plant feet
    scale_group_to_height(meshes, TARGET_HEIGHT)
    b = world_bounds(meshes)
    print(f"Pre-armature bounds size={tuple(round(x, 4) for x in b['size'])}")

    # Soft clamp width if over MAX_WIDTH (scale X only carefully — avoid if close)
    width = b['size'][0]
    if width > MAX_WIDTH:
        sx = MAX_WIDTH / width
        print(f"Width {width:.3f} > {MAX_WIDTH}, scaling X by {sx:.4f}")
        for obj in meshes:
            for v in obj.data.vertices:
                v.co.x *= sx
            obj.data.update()
        plant_feet(meshes)

    arm = create_armature('Clerk_Armature')
    # Parent with armature deform names (no weight paint — bone hooks for later)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:
        obj.parent = arm

    b = world_bounds(meshes)
    tris = count_tris(meshes)
    print(f"Clerk final size={tuple(round(x, 4) for x in b['size'])} tris={tris}")
    return meshes, arm


def export_glb(path):
    # Select character meshes + armature only
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
    key.data.energy = 280
    key.data.size = 2.5
    key.rotation_euler = (math.radians(50), math.radians(15), math.radians(35))

    bpy.ops.object.light_add(type='AREA', location=(-2.0, 1.5, 2.4))
    fill = bpy.context.active_object
    fill.name = 'PreviewFill'
    fill.data.energy = 90
    fill.data.size = 3.0
    fill.data.color = (0.75, 0.82, 0.9)

    bpy.ops.object.light_add(type='SUN', location=(0, 0, 5))
    sun = bpy.context.active_object
    sun.name = 'PreviewSun'
    sun.data.energy = 1.3
    sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(-20))

    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = 'PreviewGround'
    ground.data.materials.append(mat('Ground', (0.45, 0.40, 0.34), 0.95))


def add_capsule_guide():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.75, vertices=24, location=(0, 0, 0.875))
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


def render_previews():
    setup_preview_world()
    guide = add_capsule_guide()

    bpy.ops.object.camera_add(location=(0, -3.2, 1.15))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam

    views = [
        ('front', (0, 3.4, 1.15), True and False),
        ('threequarter', (2.5, 2.7, 1.35), False),
        ('side', (3.4, 0.15, 1.15), False),
        ('front_with_capsule', (0, 3.4, 1.15), True),
    ]
    # fix: front should not show guide
    views = [
        ('front', (0, 3.4, 1.15), False),
        ('threequarter', (2.5, 2.7, 1.35), False),
        ('side', (3.4, 0.15, 1.15), False),
        ('front_with_capsule', (0, 3.4, 1.15), True),
    ]
    target = Vector((0, 0, 0.95))

    for name, loc, show_guide in views:
        guide.hide_render = not show_guide
        guide.hide_viewport = not show_guide
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        out = os.path.join(PREV_DIR, f'clerk_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)


def cleanup_preview_helpers():
    for name in ('PreviewGround', 'CapsuleGuide', 'PreviewCam',
                 'PreviewKey', 'PreviewFill', 'PreviewSun'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
    for obj in list(bpy.data.objects):
        if obj.type in {'LIGHT', 'CAMERA'} and obj.name.startswith('Preview'):
            bpy.data.objects.remove(obj, do_unlink=True)


def main():
    meshes, arm = build_clerk()
    glb_path = os.path.join(OUT_DIR, 'clerk.glb')
    export_glb(glb_path)
    print('Exported', glb_path)

    render_previews()
    cleanup_preview_helpers()
    export_glb(glb_path)
    print('Re-exported clean', glb_path)

    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    b = world_bounds(mesh_objs)
    tris = count_tris(mesh_objs)
    meta = os.path.join(PREV_DIR, 'clerk_scale.txt')
    with open(meta, 'w') as f:
        f.write(
            f"height_m={b['size'][2]:.4f}\n"
            f"width_x_m={b['size'][0]:.4f}\n"
            f"depth_y_m={b['size'][1]:.4f}\n"
            f"tris={tris}\n"
            f"capsule_diameter_m=0.60\n"
            f"formation_spacing_m=0.90 (context only)\n"
            f"target_height_m={TARGET_HEIGHT}\n"
        )
    print('Wrote', meta)
    print(f'Done. height={b["size"][2]:.4f} width={b["size"][0]:.4f} tris={tris}')


if __name__ == '__main__':
    main()
