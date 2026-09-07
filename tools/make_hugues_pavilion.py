"""Blender: Captain Hugues field pavilion (Broken Seal) — game-ready GLB + previews.

Northern captain campaign tent / awning: poles, guy ropes, dull canvas banner —
dirt and canvas, NO fantasy heraldry glow. Occitania 1208 dirt-and-mail.
Rebuild:
  /usr/bin/blender -b -P tools/make_hugues_pavilion.py

Scale notes:
  - Origin at ground center of tent footprint
  - Footprint ~3.2 × 2.6 m; ridge ~2.4 m; open front toward +Y
  - Collision shell tight to mesh (awning volume)
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


# Tent layout: ridge along X, open front +Y, closed back -Y
HALF_W = 1.45   # X half-width at eaves
HALF_D = 1.15   # Y half-depth
RIDGE_Z = 2.35
EAVE_Z = 1.55
POLE_R = 0.045


def make_poles(oak):
    """Corner poles + ridge pole / king posts."""
    parts = []
    # Four corner poles (front slightly shorter visually open)
    corners = [
        (-HALF_W, -HALF_D, EAVE_Z + 0.05),
        (HALF_W, -HALF_D, EAVE_Z + 0.05),
        (-HALF_W, HALF_D, EAVE_Z - 0.05),
        (HALF_W, HALF_D, EAVE_Z - 0.05),
    ]
    for i, (x, y, zh) in enumerate(corners):
        bm = bmesh.new()
        segs = 10
        rings = []
        for z, r in ((0.0, POLE_R * 1.1), (zh * 0.5, POLE_R), (zh, POLE_R * 0.9)):
            row = []
            for j in range(segs):
                a = (j / segs) * math.tau
                row.append(bm.verts.new((x + r * math.cos(a), y + r * math.sin(a), z)))
            rings.append(row)
        for ri in range(len(rings) - 1):
            for j in range(segs):
                j2 = (j + 1) % segs
                bm.faces.new((rings[ri][j], rings[ri][j2], rings[ri + 1][j2], rings[ri + 1][j]))
        top = rings[-1]
        c = sum((v.co for v in top), Vector()) / len(top)
        ctr = bm.verts.new((c.x, c.y, c.z + 0.01))
        for j in range(segs):
            bm.faces.new((ctr, top[j], top[(j + 1) % segs]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Pav_Pole{i}', bm, oak, smooth=True))

    # Center ridge posts (two)
    for i, x in enumerate((-0.5, 0.5)):
        bm = bmesh.new()
        path = [Vector((x, 0.0, 0.0)), Vector((x, 0.0, RIDGE_Z))]
        tube(bm, path, [POLE_R * 1.05, POLE_R * 0.85], segs=10)
        parts.append(bm_to_object(f'Pav_King{i}', bm, oak, smooth=True))

    # Ridge beam
    bm = bmesh.new()
    path = [Vector((-HALF_W - 0.05, 0.0, RIDGE_Z - 0.02)),
            Vector((HALF_W + 0.05, 0.0, RIDGE_Z - 0.02))]
    tube(bm, path, [0.04, 0.04], segs=8)
    parts.append(bm_to_object('Pav_Ridge', bm, oak, smooth=True))

    # Eave beams front/back
    for yi, y in enumerate((-HALF_D, HALF_D)):
        bm = bmesh.new()
        z = EAVE_Z if yi == 0 else EAVE_Z - 0.05
        path = [Vector((-HALF_W, y, z)), Vector((HALF_W, y, z))]
        tube(bm, path, [0.032, 0.032], segs=8)
        parts.append(bm_to_object(f'Pav_Eave{yi}', bm, oak, smooth=True))

    return join_named('Pav_Poles', parts)


def make_canvas(canvas, canvas_dark):
    """A-frame / ridge tent canvas with sag — open front flaps tied back."""
    parts = []
    # Left roof panel (-X side of ridge → left eave)
    # Sampled grid with sag
    def roof_panel(name, x_sign, material):
        bm = bmesh.new()
        nu, nv = 8, 6
        grid = []
        for i in range(nu + 1):
            row = []
            u = i / nu  # 0 at back (-Y) → 1 at front (+Y)
            for j in range(nv + 1):
                v = j / nv  # 0 at ridge → 1 at eave
                y = -HALF_D + u * (2 * HALF_D)
                # ridge to eave
                x_r = 0.0
                x_e = x_sign * HALF_W
                x = x_r + (x_e - x_r) * v
                z_r = RIDGE_Z
                z_e = EAVE_Z - (0.05 if y > 0 else 0.0)
                z = z_r + (z_e - z_r) * v
                # fabric sag
                sag = 0.08 * math.sin(u * math.pi) * math.sin(v * math.pi)
                z -= sag
                # slight wind billow on front
                if u > 0.7:
                    x += x_sign * 0.04 * (u - 0.7) * v
                row.append(bm.verts.new((x, y, z)))
            grid.append(row)
        bm.verts.ensure_lookup_table()
        for i in range(nu):
            for j in range(nv):
                bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        # duplicate thin underside? skip — single sided ok for game
        return bm_to_object(name, bm, material, smooth=True)

    parts.append(roof_panel('Pav_RoofL', -1, canvas))
    parts.append(roof_panel('Pav_RoofR', 1, canvas_dark))

    # Back wall canvas (closed)
    bm = bmesh.new()
    nu, nv = 7, 5
    grid = []
    for i in range(nu + 1):
        row = []
        u = i / nu  # -1 → 1 in X
        for j in range(nv + 1):
            v = j / nv  # ground → eave/ridge mid
            x = -HALF_W + u * (2 * HALF_W)
            y = -HALF_D - 0.02
            # height follows A-frame
            z_eave = EAVE_Z
            z_ridge = RIDGE_Z
            # interpolate height at this x
            t = abs(x) / HALF_W
            z_top = z_ridge + (z_eave - z_ridge) * t
            z = 0.05 + v * (z_top - 0.05)
            # slight belly
            y -= 0.04 * math.sin(u * math.pi) * math.sin(v * math.pi)
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Pav_BackWall', bm, canvas_dark, smooth=True))

    # Front flaps tied open (readable entrance)
    for sx, name in ((-1, 'L'), (1, 'R')):
        bm = bmesh.new()
        # flap hanging/tied to front corner pole outward
        pts = [
            Vector((sx * 0.15, HALF_D - 0.05, EAVE_Z - 0.1)),
            Vector((sx * 0.55, HALF_D + 0.15, EAVE_Z - 0.25)),
            Vector((sx * HALF_W * 0.85, HALF_D + 0.35, 0.9)),
            Vector((sx * HALF_W * 0.7, HALF_D + 0.25, 0.35)),
        ]
        # Build as flat-ish ribbon via tube-like strip
        # Use a thin box strip approximated with faces along path
        nu = 5
        nv = 3
        grid = []
        for i in range(nu + 1):
            t = i / nu
            # bezier-ish along pts
            if t < 0.33:
                tt = t / 0.33
                p = pts[0].lerp(pts[1], tt)
            elif t < 0.66:
                tt = (t - 0.33) / 0.33
                p = pts[1].lerp(pts[2], tt)
            else:
                tt = (t - 0.66) / 0.34
                p = pts[2].lerp(pts[3], tt)
            row = []
            for j in range(nv + 1):
                w = j / nv
                # width across flap
                across = Vector((-sx * 0.35, 0.08, 0)) * (w - 0.5) * 2
                # taper toward bottom
                across *= (1.0 - 0.3 * t)
                row.append(bm.verts.new(p + across + Vector((0, 0, 0.05 * math.sin(w * math.pi)))))
            grid.append(row)
        for i in range(nu):
            for j in range(nv):
                bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Pav_Flap{name}', bm, canvas if sx < 0 else canvas_dark, smooth=True))

    return join_named('Pav_Canvas', parts)


def make_guy_ropes(hemp, oak):
    """Guy ropes from eaves to ground stakes."""
    parts = []
    stakes = [
        (-HALF_W - 0.55, -HALF_D - 0.35, -HALF_W, -HALF_D, EAVE_Z),
        (HALF_W + 0.55, -HALF_D - 0.35, HALF_W, -HALF_D, EAVE_Z),
        (-HALF_W - 0.65, HALF_D + 0.45, -HALF_W, HALF_D, EAVE_Z - 0.05),
        (HALF_W + 0.65, HALF_D + 0.45, HALF_W, HALF_D, EAVE_Z - 0.05),
        (-0.2, -HALF_D - 0.7, -0.5, 0.0, RIDGE_Z),
        (0.2, HALF_D + 0.75, 0.5, 0.0, RIDGE_Z),
    ]
    for i, (sx, sy, ex, ey, ez) in enumerate(stakes):
        # stake
        bm = bmesh.new()
        box_bm(bm, sx - 0.025, sx + 0.025, sy - 0.025, sy + 0.025, 0.0, 0.28)
        for v in bm.verts:
            if v.co.z > 0.2:
                v.co.x = sx + (v.co.x - sx) * 0.4
                v.co.y = sy + (v.co.y - sy) * 0.4
        parts.append(bm_to_object(f'_stake{i}', bm, oak, smooth=False))

        # rope with sag
        bm = bmesh.new()
        path, radii = [], []
        n = 12
        for k in range(n):
            t = k / (n - 1)
            x = sx + (ex - sx) * t
            y = sy + (ey - sy) * t
            z = 0.25 + (ez - 0.25) * t - 0.12 * math.sin(t * math.pi)
            path.append(Vector((x, y, z)))
            radii.append(0.014)
        tube(bm, path, radii, segs=6)
        parts.append(bm_to_object(f'_guy{i}', bm, hemp, smooth=True))

    return join_named('Pav_Guys', parts)


def make_banner(canvas, canvas_dark, oak):
    """Dull northern campaign banner — faded stripe, NO glow / fantasy heraldry."""
    parts = []
    # Banner pole at front-left
    bx, by = -HALF_W - 0.15, HALF_D + 0.1
    bm = bmesh.new()
    path = [Vector((bx, by, 0.0)), Vector((bx, by, 2.55))]
    tube(bm, path, [0.028, 0.022], segs=8)
    parts.append(bm_to_object('Pav_BannerPole', bm, oak, smooth=True))

    # Cross-arm
    bm = bmesh.new()
    path = [Vector((bx - 0.05, by, 2.45)), Vector((bx + 0.55, by, 2.45))]
    tube(bm, path, [0.016, 0.016], segs=6)
    parts.append(bm_to_object('Pav_BannerArm', bm, oak, smooth=True))

    # Cloth hanging (dull faded ochre / ash stripe — northern host, not glowing)
    bm = bmesh.new()
    nu, nv = 5, 8
    grid = []
    for i in range(nu + 1):
        row = []
        u = i / nu
        for j in range(nv + 1):
            v = j / nv
            x = bx + 0.05 + u * 0.45
            y = by + 0.02 + 0.06 * math.sin(v * math.pi * 2) * (0.3 + 0.7 * u)
            z = 2.42 - v * 1.15
            # wind curl at bottom
            y += 0.08 * v * v * math.sin(u * math.pi)
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Pav_BannerCloth', bm, canvas_dark, smooth=True))

    # Faded horizontal stripe (separate darker band — readable but dull)
    stripe = mat('Pav_Stripe', (0.28, 0.22, 0.16), 0.92, specular=0.08)
    bm = bmesh.new()
    box_bm(bm, bx + 0.08, bx + 0.45, by + 0.03, by + 0.05, 1.85, 2.05)
    # bend approx by pushing verts
    for v in bm.verts:
        t = (v.co.z - 1.85) / 0.2
        v.co.y += 0.04 * math.sin(t * math.pi)
    parts.append(bm_to_object('Pav_BannerStripe', bm, stripe, smooth=True))

    return join_named('Pav_Banner', parts)


def make_ground_kit(oak, mud, canvas):
    """Bedroll / crate hint + mud — dirt campaign camp."""
    parts = []
    # Small crate
    bm = bmesh.new()
    box_bm(bm, -0.35, 0.05, -0.4, -0.05, 0.0, 0.32)
    parts.append(bm_to_object('Pav_Crate', bm, oak, smooth=False))

    # Bedroll
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.18)
    for v in bm.verts:
        v.co.x *= 1.8
        v.co.z *= 0.45
        v.co += Vector((0.5, -0.3, 0.08))
        if v.co.z < 0.01:
            v.co.z = 0.01
    parts.append(bm_to_object('Pav_Bedroll', bm, canvas, smooth=True))

    # Mud / trampled earth
    for i, (mx, my, mr) in enumerate((
        (0.0, 0.5, 0.2), (-0.8, -0.6, 0.15), (1.0, 0.3, 0.14), (0.3, -0.9, 0.12),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=mr)
        for v in bm.verts:
            v.co.z *= 0.25
            v.co.x *= 1.5
            v.co += Vector((mx, my, 0.015))
            if v.co.z < 0:
                v.co.z = 0.002
        parts.append(bm_to_object(f'_pmud{i}', bm, mud, smooth=True))

    return join_named('Pav_Camp', parts)


def build_hugues_pavilion():
    clear_scene()
    oak = mat('Pav_Oak', (0.34, 0.24, 0.13), 0.84, specular=0.20)
    canvas = mat('Pav_Canvas', (0.55, 0.48, 0.34), 0.88, specular=0.12)
    canvas_dark = mat('Pav_CanvasDark', (0.42, 0.36, 0.26), 0.90, specular=0.10)
    hemp = mat('Pav_Hemp', (0.48, 0.40, 0.26), 0.90, specular=0.12)
    mud = mat('Pav_Mud', (0.30, 0.24, 0.16), 0.96, specular=0.06)

    meshes = [
        make_poles(oak),
        make_canvas(canvas, canvas_dark),
        make_guy_ropes(hemp, oak),
        make_banner(canvas, canvas_dark, oak),
        make_ground_kit(oak, mud, canvas),
    ]
    meshes = [m for m in meshes if m is not None]
    plant_and_center(meshes)

    b = world_bounds(meshes)
    tris = count_tris(meshes)
    print(f"Hugues pavilion size={tuple(round(x, 4) for x in b['size'])} "
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

    bpy.ops.object.light_add(type='AREA', location=(4.0, -4.0, 4.5))
    key = bpy.context.active_object
    key.name = 'PreviewKey'
    key.data.energy = 360
    key.data.size = 4.0
    key.rotation_euler = (math.radians(52), math.radians(8), math.radians(30))

    bpy.ops.object.light_add(type='AREA', location=(-3.5, 2.5, 3.0))
    fill = bpy.context.active_object
    fill.name = 'PreviewFill'
    fill.data.energy = 120
    fill.data.size = 4.0
    fill.data.color = (0.75, 0.78, 0.85)

    bpy.ops.object.light_add(type='SUN', location=(0, 0, 8))
    sun = bpy.context.active_object
    sun.name = 'PreviewSun'
    sun.data.energy = 1.4
    sun.rotation_euler = (math.radians(42), math.radians(8), math.radians(-25))

    bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = 'PreviewGround'
    ground.data.materials.append(mat('Ground', (0.37, 0.33, 0.24), 0.95))


def render_previews():
    setup_preview_world()
    bpy.ops.object.camera_add(location=(0, -7.0, 2.5))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam
    target = Vector((0, 0, 1.2))

    views = [
        ('front', (0.0, -7.2, 2.3)),
        ('threequarter', (5.5, -5.0, 3.2)),
    ]
    for name, loc in views:
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        out = os.path.join(PREV_DIR, f'hugues_pavilion_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)


def cleanup_preview_helpers():
    for name in ('PreviewGround', 'PreviewCam', 'PreviewKey', 'PreviewFill', 'PreviewSun'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def main():
    meshes = build_hugues_pavilion()
    glb_path = os.path.join(OUT_DIR, 'hugues_pavilion.glb')
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
    meta = os.path.join(PREV_DIR, 'hugues_pavilion_scale.txt')
    with open(meta, 'w') as f:
        f.write(
            f"height_m={b['size'][2]:.4f}\n"
            f"width_x_m={b['size'][0]:.4f}\n"
            f"depth_y_m={b['size'][1]:.4f}\n"
            f"tris={tris}\n"
            f"objects={','.join(names)}\n"
            f"origin=ground_center_tent_footprint\n"
            f"collision=tight_to_mesh\n"
            f"open_front=+Y flaps_tied_back\n"
            f"banner=dull_faded_stripe_no_glow\n"
            f"style=northern_captain_field_pavilion_occitan_1208\n"
        )
    print('Wrote', meta)
    print(f'Done. height={b["size"][2]:.4f} width={b["size"][0]:.4f} depth={b["size"][1]:.4f} tris={tris}')
    print('Objects:', names)


if __name__ == '__main__':
    main()
