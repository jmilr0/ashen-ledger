"""Blender: Ferry rope hitch prop (Broken Seal) — game-ready GLB + previews.

Dirt-and-mail wooden post + thick hemp rope (cuttable ferry rope). Wet oak, mud.
NO fantasy glow. Rebuild:
  /usr/bin/blender -b -P tools/make_ferry_rope.py

Scale notes:
  - Origin at base of post on ground
  - Post ~1.4 m; rope hitch at y≈1.1, readable length ~1.8–2.0 m
  - Mesh may be ~1.2× vs game collider (ferry radius ~0.55) for forgiving RMB
"""
from __future__ import annotations

import math
import os
import bmesh
import bpy
from mathutils import Matrix, Vector

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


def make_post(oak, mud):
    parts = []
    # Main weathered oak post — slightly tapered, wet look
    bm = bmesh.new()
    segs = 16
    profile = [
        (0.00, 0.115),
        (0.08, 0.110),
        (0.35, 0.100),
        (0.70, 0.095),
        (1.05, 0.090),
        (1.28, 0.088),
        (1.40, 0.095),  # slightly flared top
        (1.46, 0.078),
    ]
    rings = []
    for z, r in profile:
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            # bark irregularity
            rr = r * (1.0 + 0.04 * math.sin(a * 3 + z * 8) + 0.025 * math.cos(a * 5 + z * 4))
            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        rings.append(row)
    for i in range(len(rings) - 1):
        for j in range(segs):
            j2 = (j + 1) % segs
            bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
    # top cap
    top = rings[-1]
    c = sum((v.co for v in top), Vector()) / len(top)
    center = bm.verts.new((c.x, c.y, c.z + 0.01))
    for j in range(segs):
        bm.faces.new((center, top[j], top[(j + 1) % segs]))
    # bottom face
    bot = rings[0]
    c0 = sum((v.co for v in bot), Vector()) / len(bot)
    center0 = bm.verts.new((c0.x, c0.y, 0.0))
    for j in range(segs):
        bm.faces.new((center0, bot[(j + 1) % segs], bot[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Ferry_Post', bm, oak))

    # Iron ring / cleat band around hitch height
    bm = bmesh.new()
    segs = 20
    z0, z1 = 1.02, 1.12
    outer, inner = [], []
    for z in (z0, z1):
        o_row, i_row = [], []
        for j in range(segs):
            a = (j / segs) * math.tau
            o_row.append(bm.verts.new((0.108 * math.cos(a), 0.108 * math.sin(a), z)))
            i_row.append(bm.verts.new((0.086 * math.cos(a), 0.086 * math.sin(a), z)))
        outer.append(o_row)
        inner.append(i_row)
    for j in range(segs):
        j2 = (j + 1) % segs
        bm.faces.new((outer[0][j], outer[0][j2], outer[1][j2], outer[1][j]))
        bm.faces.new((inner[1][j], inner[1][j2], inner[0][j2], inner[0][j]))
        bm.faces.new((outer[1][j], outer[1][j2], inner[1][j2], inner[1][j]))
        bm.faces.new((inner[0][j], inner[0][j2], outer[0][j2], outer[0][j]))
    iron = mat('Ferry_Iron', (0.28, 0.26, 0.22), 0.55, metallic=0.55, specular=0.4)
    parts.append(bm_to_object('Ferry_Band', bm, iron))

    # Mud caked at base
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=8, radius=0.18)
    kill = [v for v in bm.verts if v.co.z < -0.02]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    for v in bm.verts:
        v.co.x *= 1.35
        v.co.y *= 1.15
        v.co.z *= 0.55
        v.co.z = max(v.co.z, 0.0)
        # irregular mud lumps
        a = math.atan2(v.co.y, v.co.x)
        v.co.x += 0.02 * math.sin(a * 4)
        v.co.y += 0.015 * math.cos(a * 3)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Ferry_MudBase', bm, mud))

    # Extra mud clods
    for i, (mx, my, mz, mr) in enumerate((
        (0.14, 0.08, 0.04, 0.06),
        (-0.12, -0.06, 0.03, 0.05),
        (0.06, -0.14, 0.035, 0.055),
        (-0.08, 0.12, 0.03, 0.045),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=mr)
        for v in bm.verts:
            v.co.z *= 0.7
            v.co += Vector((mx, my, mz))
            if v.co.z < 0:
                v.co.z = 0.005
        parts.append(bm_to_object(f'_mud{i}', bm, mud))

    return join_named('Ferry_PostAssembly', parts)


def make_hitch_wrap(hemp):
    """Rope wraps around the post at hitch height (readable cuttable hitch)."""
    bm = bmesh.new()
    # helical wraps around post
    turns = 3.2
    pts = 48
    path, radii = [], []
    for i in range(pts):
        t = i / (pts - 1)
        ang = t * turns * math.tau
        z = 1.05 + t * 0.12 + 0.015 * math.sin(t * math.pi * 4)
        r = 0.105 + 0.012 * math.sin(t * math.pi * 6)
        path.append(Vector((r * math.cos(ang), r * math.sin(ang), z)))
        radii.append(0.028 + 0.004 * math.sin(t * math.pi * 8))
    tube(bm, path, radii, segs=8)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object('Ferry_HitchWrap', bm, hemp)


def make_main_rope(hemp):
    """Thick hemp ferry rope extending from hitch along +X (~1.8–2.0 m readable)."""
    bm = bmesh.new()
    # Start at hitch, slight sag, extend to ~1.9m
    path, radii = [], []
    n = 28
    length = 1.95
    for i in range(n):
        t = i / (n - 1)
        x = 0.10 + t * length
        # slight natural sag + twist offset
        y = 0.02 * math.sin(t * math.pi * 2) + 0.04 * math.sin(t * math.pi)
        z = 1.10 - 0.08 * math.sin(t * math.pi) + 0.015 * math.sin(t * math.pi * 3)
        # near hitch: rise slightly into wrap
        if t < 0.08:
            z = 1.08 + t / 0.08 * 0.03
            x = 0.08 + t / 0.08 * 0.08
        path.append(Vector((x, y, z)))
        # thick cuttable rope — ~1.2× forgiving vs thin collider rope
        radii.append(0.038 - 0.004 * t + 0.003 * math.sin(t * math.pi * 10))
    tube(bm, path, radii, segs=12)

    # stranded twist suggestion: surface bumps along rope
    for v in list(bm.verts):
        # approximate along-rope param by x
        t = max(0.0, min(1.0, (v.co.x - 0.1) / length))
        a = math.atan2(v.co.z - 1.05, v.co.y)
        nvec = Vector((0, v.co.y, v.co.z - (1.10 - 0.08 * math.sin(t * math.pi))))
        # skip if near origin of post
        if v.co.x > 0.15 and nvec.length > 1e-4:
            # strand ridges
            pass  # keep tube clean; twist via separate strands below

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    main = bm_to_object('Ferry_RopeMain', bm, hemp)

    # Secondary twisted strand overlay for readable hemp texture at iso distance
    bm2 = bmesh.new()
    path2, radii2 = [], []
    for i in range(n):
        t = i / (n - 1)
        x = 0.12 + t * (length - 0.05)
        y = 0.02 * math.sin(t * math.pi * 2) + 0.04 * math.sin(t * math.pi)
        z = 1.10 - 0.08 * math.sin(t * math.pi)
        # offset for strand
        ang = t * math.tau * 6
        oy = 0.022 * math.cos(ang)
        oz = 0.022 * math.sin(ang)
        path2.append(Vector((x, y + oy, z + oz)))
        radii2.append(0.016)
    tube(bm2, path2, radii2, segs=6)
    hemp_dark = mat('Ferry_HempDark', (0.42, 0.34, 0.22), 0.92, specular=0.12)
    strand = bm_to_object('Ferry_RopeStrand', bm2, hemp_dark)

    # Frayed cuttable end (readable for "Cut rope")
    bm3 = bmesh.new()
    tip = Vector((0.10 + length, 0.04, 1.10))
    for k in range(7):
        a = k / 7 * math.tau
        end = tip + Vector((0.08 + 0.04 * math.sin(k), 0.04 * math.cos(a), 0.035 * math.sin(a * 2)))
        path3 = [tip + Vector((-0.05, 0, 0)), tip, end]
        tube(bm3, path3, [0.018, 0.014, 0.006], segs=5)
    fray = bm_to_object('Ferry_RopeFray', bm3, hemp_dark)

    # Knot bulb at hitch junction
    bm4 = bmesh.new()
    bmesh.ops.create_uvsphere(bm4, u_segments=12, v_segments=8, radius=0.055)
    for v in bm4.verts:
        v.co.x *= 1.3
        v.co.y *= 0.9
        v.co.z *= 0.85
        v.co += Vector((0.12, 0.02, 1.09))
    knot = bm_to_object('Ferry_Knot', bm4, hemp)

    return join_named('Ferry_Rope', [main, strand, fray, knot])


def make_stake_and_ring(oak, iron):
    """Far-side hint: short stake stub with iron ring (rope goes toward far latch)."""
    parts = []
    # Small wooden cleat / horn on post top for hitch authenticity
    bm = bmesh.new()
    path = [Vector((-0.02, 0.0, 1.38)), Vector((0.0, 0.0, 1.42)),
            Vector((0.08, 0.0, 1.44)), Vector((0.14, 0.0, 1.40))]
    tube(bm, path, [0.028, 0.032, 0.030, 0.022], segs=8)
    parts.append(bm_to_object('Ferry_Cleat', bm, oak))

    # Iron ring hanging at hitch (period ferry hardware)
    bm = bmesh.new()
    segs = 16
    major_r, tube_r = 0.055, 0.012
    rings = []
    for i in range(segs):
        a = (i / segs) * math.tau
        cx = 0.095 + major_r * math.cos(a)
        cz = 1.08 + major_r * math.sin(a)
        cy = 0.0
        # torus cross-section
        row = []
        for j in range(8):
            b = (j / 8) * math.tau
            # local frame
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
    parts.append(bm_to_object('Ferry_IronRing', bm, iron))
    return join_named('Ferry_Hardware', parts)


def build_ferry_rope():
    clear_scene()
    oak = mat('Ferry_WetOak', (0.32, 0.22, 0.12), 0.78, specular=0.28)
    mud = mat('Ferry_Mud', (0.28, 0.22, 0.14), 0.95, specular=0.08)
    hemp = mat('Ferry_Hemp', (0.55, 0.45, 0.28), 0.88, specular=0.15)
    iron = mat('Ferry_IronRingMat', (0.30, 0.28, 0.24), 0.50, metallic=0.6, specular=0.45)

    meshes = [
        make_post(oak, mud),
        make_hitch_wrap(hemp),
        make_main_rope(hemp),
        make_stake_and_ring(oak, iron),
    ]
    meshes = [m for m in meshes if m is not None]
    plant_base(meshes)

    # Center origin under post base (post is near x=0)
    b = world_bounds(meshes)
    # Shift so post center XY is at origin (rope extends +X)
    # Post is already near origin; just plant Z
    dx = -((b['min'][0] + b['max'][0]) * 0.5 - 0.55)  # keep post near 0, rope +X
    # Actually: origin at base of post — post is at ~0, don't recenter to full AABB
    # Leave XY as built (post at 0, rope +X)
    plant_base(meshes)

    b = world_bounds(meshes)
    tris = count_tris(meshes)
    print(f"Ferry rope size={tuple(round(x, 4) for x in b['size'])} "
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

    bpy.ops.mesh.primitive_plane_add(size=8, location=(0.6, 0, 0))
    ground = bpy.context.active_object
    ground.name = 'PreviewGround'
    ground.data.materials.append(mat('Ground', (0.38, 0.34, 0.26), 0.95))


def render_previews():
    setup_preview_world()
    bpy.ops.object.camera_add(location=(0.9, -3.4, 1.2))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam
    target = Vector((0.7, 0, 0.85))

    views = [
        ('front', (0.8, -3.5, 1.15)),
        ('threequarter', (3.2, -2.4, 1.55)),
    ]
    for name, loc in views:
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        out = os.path.join(PREV_DIR, f'ferry_rope_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)


def cleanup_preview_helpers():
    for name in ('PreviewGround', 'PreviewCam', 'PreviewKey', 'PreviewFill', 'PreviewSun'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def main():
    meshes = build_ferry_rope()
    glb_path = os.path.join(OUT_DIR, 'ferry_rope.glb')
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
    meta = os.path.join(PREV_DIR, 'ferry_rope_scale.txt')
    with open(meta, 'w') as f:
        f.write(
            f"height_m={b['size'][2]:.4f}\n"
            f"width_x_m={b['size'][0]:.4f}\n"
            f"depth_y_m={b['size'][1]:.4f}\n"
            f"tris={tris}\n"
            f"objects={','.join(names)}\n"
            f"collider_radius_m=0.55\n"
            f"mesh_vs_collider_note=~1.2x forgiving RMB\n"
            f"rope_hitch_z_m~=1.10\n"
        )
    print('Wrote', meta)
    print(f'Done. height={b["size"][2]:.4f} width={b["size"][0]:.4f} tris={tris}')
    print('Objects:', names)


if __name__ == '__main__':
    main()
