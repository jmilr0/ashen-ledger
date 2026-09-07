"""Blender: Priory yard rope hitch (Broken Seal) — game-ready GLB + previews.

Courtyard post + iron ring + thick hemp brace/cuttable rope for hold_door /
yard fight readability. Same spirit as ferry_rope, dirt-and-mail Occitania 1208.
NO fantasy glow. Rebuild:
  /usr/bin/blender -b -P tools/make_yard_rope.py

Scale notes:
  - Origin at base of post on ground
  - Post ~1.35 m; hitch at z≈1.05; rope readable length ~1.6–1.8 m
  - Mesh may be ~1.2× vs game collider for forgiving RMB (like ferry)
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


def plant_base(objects):
    b = world_bounds(objects)
    dz = -b['min'][2]
    for obj in objects:
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


def make_yard_post(oak, limestone, mud):
    """Squared oak courtyard post set in limestone socket — not ferry river post."""
    parts = []
    # Squared timber post
    bm = bmesh.new()
    segs_profile = [
        (0.00, 0.09),
        (0.15, 0.085),
        (0.50, 0.080),
        (0.90, 0.078),
        (1.20, 0.075),
        (1.32, 0.082),
        (1.38, 0.070),
    ]
    # Build as octagonal-ish square with chamfer via cylinder irregularity
    segs = 12
    rings = []
    for z, r in segs_profile:
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            # squarish: push toward axes
            sq = 1.0 + 0.18 * math.cos(a * 4)
            rr = r * sq * (1.0 + 0.03 * math.sin(a * 3 + z * 6))
            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        rings.append(row)
    for i in range(len(rings) - 1):
        for j in range(segs):
            j2 = (j + 1) % segs
            bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
    top = rings[-1]
    c = sum((v.co for v in top), Vector()) / len(top)
    center = bm.verts.new((c.x, c.y, c.z + 0.008))
    for j in range(segs):
        bm.faces.new((center, top[j], top[(j + 1) % segs]))
    bot = rings[0]
    c0 = sum((v.co for v in bot), Vector()) / len(bot)
    center0 = bm.verts.new((c0.x, c0.y, 0.0))
    for j in range(segs):
        bm.faces.new((center0, bot[(j + 1) % segs], bot[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Yard_Post', bm, oak, smooth=True))

    # Limestone socket / curb at base (courtyard)
    bm = bmesh.new()
    box_bm(bm, -0.22, 0.22, -0.22, 0.22, 0.0, 0.14)
    for v in bm.verts:
        if v.co.z > 0.1:
            v.co.x *= 0.92
            v.co.y *= 0.92
        n = math.sin(v.co.x * 8) * math.cos(v.co.y * 7)
        v.co.x += 0.008 * n
        v.co.y += 0.006 * math.sin(v.co.z * 5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Yard_Socket', bm, limestone, smooth=False))

    # Iron band at hitch height
    bm = bmesh.new()
    segs = 18
    z0, z1 = 0.98, 1.08
    outer, inner = [], []
    for z in (z0, z1):
        o_row, i_row = [], []
        for j in range(segs):
            a = (j / segs) * math.tau
            o_row.append(bm.verts.new((0.100 * math.cos(a), 0.100 * math.sin(a), z)))
            i_row.append(bm.verts.new((0.078 * math.cos(a), 0.078 * math.sin(a), z)))
        outer.append(o_row)
        inner.append(i_row)
    for j in range(segs):
        j2 = (j + 1) % segs
        bm.faces.new((outer[0][j], outer[0][j2], outer[1][j2], outer[1][j]))
        bm.faces.new((inner[1][j], inner[1][j2], inner[0][j2], inner[0][j]))
        bm.faces.new((outer[1][j], outer[1][j2], inner[1][j2], inner[1][j]))
        bm.faces.new((inner[0][j], inner[0][j2], outer[0][j2], outer[0][j]))
    iron = mat('Yard_BandIron', (0.28, 0.26, 0.22), 0.55, metallic=0.55, specular=0.4)
    parts.append(bm_to_object('Yard_Band', bm, iron, smooth=True))

    # Dirt clods
    for i, (mx, my, mr) in enumerate((
        (0.18, 0.10, 0.055), (-0.15, -0.08, 0.05), (0.08, -0.16, 0.048),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=mr)
        for v in bm.verts:
            v.co.z *= 0.5
            v.co += Vector((mx, my, 0.03))
            if v.co.z < 0:
                v.co.z = 0.003
        parts.append(bm_to_object(f'_ymud{i}', bm, mud, smooth=True))

    return join_named('Yard_PostAssembly', parts)


def make_iron_ring(iron):
    """Large courtyard hitch ring bolted to post — reads as yard hardware."""
    parts = []
    # Torus ring hanging on +X side
    bm = bmesh.new()
    segs = 18
    major_r, tube_r = 0.07, 0.014
    rings = []
    for i in range(segs):
        a = (i / segs) * math.tau
        cx = 0.095 + major_r * math.cos(a)
        cz = 1.03 + major_r * math.sin(a)
        cy = 0.0
        row = []
        for j in range(8):
            b = (j / 8) * math.tau
            nx, nz = math.cos(a), math.sin(a)
            ox = cx + tube_r * math.cos(b) * nx
            oz = cz + tube_r * math.cos(b) * nz
            oy = cy + tube_r * math.sin(b)
            row.append(bm.verts.new((ox, oy, oz)))
        rings.append(row)
    for i in range(segs):
        i2 = (i + 1) % segs
        for j in range(8):
            j2 = (j + 1) % 8
            bm.faces.new((rings[i][j], rings[i][j2], rings[i2][j2], rings[i2][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Yard_Ring', bm, iron, smooth=True))

    # Staple / eye bolt into post
    bm = bmesh.new()
    path = [Vector((0.06, 0, 1.03)), Vector((0.10, 0, 1.03)), Vector((0.12, 0, 1.03))]
    tube(bm, path, [0.016, 0.014, 0.012], segs=8)
    parts.append(bm_to_object('Yard_EyeBolt', bm, iron, smooth=True))

    return join_named('Yard_Hardware', parts)


def make_hitch_wrap(hemp):
    bm = bmesh.new()
    turns = 2.8
    pts = 40
    path, radii = [], []
    for i in range(pts):
        t = i / (pts - 1)
        ang = t * turns * math.tau
        z = 1.00 + t * 0.10 + 0.012 * math.sin(t * math.pi * 4)
        r = 0.098 + 0.010 * math.sin(t * math.pi * 6)
        path.append(Vector((r * math.cos(ang), r * math.sin(ang), z)))
        radii.append(0.026 + 0.003 * math.sin(t * math.pi * 8))
    tube(bm, path, radii, segs=8)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object('Yard_HitchWrap', bm, hemp, smooth=True)


def make_main_rope(hemp):
    """Brace / cuttable yard rope extending +X — readable at iso for hold_door."""
    bm = bmesh.new()
    path, radii = [], []
    n = 26
    length = 1.70
    for i in range(n):
        t = i / (n - 1)
        x = 0.12 + t * length
        y = 0.03 * math.sin(t * math.pi * 2) + 0.02 * math.sin(t * math.pi)
        z = 1.05 - 0.10 * math.sin(t * math.pi) + 0.012 * math.sin(t * math.pi * 3)
        if t < 0.08:
            z = 1.03 + t / 0.08 * 0.03
            x = 0.10 + t / 0.08 * 0.08
        path.append(Vector((x, y, z)))
        radii.append(0.036 - 0.004 * t + 0.003 * math.sin(t * math.pi * 10))
    tube(bm, path, radii, segs=12)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    main = bm_to_object('Yard_RopeMain', bm, hemp, smooth=True)

    # Strand overlay
    bm2 = bmesh.new()
    path2, radii2 = [], []
    for i in range(n):
        t = i / (n - 1)
        x = 0.14 + t * (length - 0.06)
        y = 0.03 * math.sin(t * math.pi * 2) + 0.02 * math.sin(t * math.pi)
        z = 1.05 - 0.10 * math.sin(t * math.pi)
        ang = t * math.tau * 5.5
        path2.append(Vector((x, y + 0.020 * math.cos(ang), z + 0.020 * math.sin(ang))))
        radii2.append(0.014)
    tube(bm2, path2, radii2, segs=6)
    hemp_dark = mat('Yard_HempDark', (0.40, 0.32, 0.20), 0.92, specular=0.12)
    strand = bm_to_object('Yard_RopeStrand', bm2, hemp_dark, smooth=True)

    # Frayed end (cuttable read)
    bm3 = bmesh.new()
    tip = Vector((0.12 + length, 0.03, 1.05))
    for k in range(6):
        a = k / 6 * math.tau
        end = tip + Vector((0.07 + 0.03 * math.sin(k), 0.035 * math.cos(a), 0.03 * math.sin(a * 2)))
        tube(bm3, [tip + Vector((-0.04, 0, 0)), tip, end], [0.016, 0.012, 0.005], segs=5)
    fray = bm_to_object('Yard_RopeFray', bm3, hemp_dark, smooth=True)

    # Knot at hitch
    bm4 = bmesh.new()
    bmesh.ops.create_uvsphere(bm4, u_segments=12, v_segments=8, radius=0.05)
    for v in bm4.verts:
        v.co.x *= 1.25
        v.co.y *= 0.9
        v.co.z *= 0.85
        v.co += Vector((0.14, 0.02, 1.04))
    knot = bm_to_object('Yard_Knot', bm4, hemp, smooth=True)

    return join_named('Yard_Rope', [main, strand, fray, knot])


def make_far_stake(oak, iron):
    """Far stake stub the brace rope aims toward (door / brace latch hint)."""
    parts = []
    # Short stake at end of rope
    x = 1.85
    bm = bmesh.new()
    box_bm(bm, x - 0.04, x + 0.04, -0.04, 0.04, 0.0, 0.55)
    for v in bm.verts:
        if v.co.z > 0.45:
            v.co.x = x + (v.co.x - x) * 0.5
            v.co.y *= 0.5
    parts.append(bm_to_object('Yard_FarStake', bm, oak, smooth=False))

    # Small iron ring on stake
    bm = bmesh.new()
    segs = 12
    major_r, tube_r = 0.04, 0.009
    rings = []
    for i in range(segs):
        a = (i / segs) * math.tau
        cx = x - 0.02 + major_r * math.cos(a) * 0.3
        cz = 0.48 + major_r * math.sin(a)
        cy = 0.0
        row = []
        for j in range(6):
            b = (j / 6) * math.tau
            row.append(bm.verts.new((
                cx + tube_r * math.cos(b) * math.cos(a),
                cy + tube_r * math.sin(b),
                cz + tube_r * math.cos(b) * math.sin(a),
            )))
        rings.append(row)
    for i in range(segs):
        i2 = (i + 1) % segs
        for j in range(6):
            j2 = (j + 1) % 6
            try:
                bm.faces.new((rings[i][j], rings[i][j2], rings[i2][j2], rings[i2][j]))
            except ValueError:
                pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Yard_FarRing', bm, iron, smooth=True))
    return join_named('Yard_FarHardware', parts)


def build_yard_rope():
    clear_scene()
    oak = mat('Yard_Oak', (0.34, 0.24, 0.13), 0.82, specular=0.22)
    limestone = mat('Yard_Limestone', (0.58, 0.53, 0.42), 0.90, specular=0.15)
    mud = mat('Yard_Mud', (0.28, 0.22, 0.14), 0.95, specular=0.08)
    hemp = mat('Yard_Hemp', (0.52, 0.43, 0.27), 0.88, specular=0.15)
    iron = mat('Yard_Iron', (0.30, 0.28, 0.24), 0.50, metallic=0.6, specular=0.45)

    meshes = [
        make_yard_post(oak, limestone, mud),
        make_iron_ring(iron),
        make_hitch_wrap(hemp),
        make_main_rope(hemp),
        make_far_stake(oak, iron),
    ]
    meshes = [m for m in meshes if m is not None]
    plant_base(meshes)

    b = world_bounds(meshes)
    tris = count_tris(meshes)
    print(f"Yard rope size={tuple(round(x, 4) for x in b['size'])} "
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

    bpy.ops.mesh.primitive_plane_add(size=8, location=(0.7, 0, 0))
    ground = bpy.context.active_object
    ground.name = 'PreviewGround'
    ground.data.materials.append(mat('Ground', (0.38, 0.34, 0.26), 0.95))


def render_previews():
    setup_preview_world()
    bpy.ops.object.camera_add(location=(0.9, -3.4, 1.2))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam
    target = Vector((0.7, 0, 0.8))

    views = [
        ('front', (0.8, -3.5, 1.15)),
        ('threequarter', (3.0, -2.3, 1.5)),
    ]
    for name, loc in views:
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        out = os.path.join(PREV_DIR, f'yard_rope_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)


def cleanup_preview_helpers():
    for name in ('PreviewGround', 'PreviewCam', 'PreviewKey', 'PreviewFill', 'PreviewSun'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def main():
    meshes = build_yard_rope()
    glb_path = os.path.join(OUT_DIR, 'yard_rope.glb')
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
    meta = os.path.join(PREV_DIR, 'yard_rope_scale.txt')
    with open(meta, 'w') as f:
        f.write(
            f"height_m={b['size'][2]:.4f}\n"
            f"width_x_m={b['size'][0]:.4f}\n"
            f"depth_y_m={b['size'][1]:.4f}\n"
            f"tris={tris}\n"
            f"objects={','.join(names)}\n"
            f"origin=post_base_ground\n"
            f"collision=tight_to_mesh\n"
            f"interact_latch_note=~1.2x forgiving RMB (ferry pattern)\n"
            f"rope_hitch_z_m~=1.05\n"
            f"style=priory_yard_brace_rope_occitan_1208\n"
        )
    print('Wrote', meta)
    print(f'Done. height={b["size"][2]:.4f} width={b["size"][0]:.4f} tris={tris}')
    print('Objects:', names)


if __name__ == '__main__':
    main()
