"""Blender: Goldsmith mold cavity prop (Broken Seal) — game-ready GLB + previews.

Floorboard section lifted / cavity with lead seal-die mold impression under the
boards — goldsmith beat hidey-hole. Dirt-and-mail Occitania 1208 — NO magic glow.
Rebuild:
  /usr/bin/blender -b -P tools/make_mold_cavity.py

Scale notes:
  - Origin at ground / floor plane center of the board section
  - Board footprint ~1.1 × 0.75 m; cavity depth ~0.12–0.18 m under boards
  - Collision shell tight to mesh; interact latch may run ~1.2× for RMB
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
    """Keep floor plane near z=0; center X/Y; allow cavity below floor."""
    b = world_bounds(objects)
    cx = (b['min'][0] + b['max'][0]) * 0.5
    cy = (b['min'][1] + b['max'][1]) * 0.5
    # Floor boards sit with top ~0.03; plant so lowest is not floating
    # but keep cavity readable below floor — shift so floor top ≈ 0.03
    for obj in objects:
        obj.location.x -= cx
        obj.location.y -= cy
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


def make_floor_frame(oak, dark):
    """Surrounding floorboards that stay put — hole in the middle."""
    parts = []
    # Outer frame boards (floor plane z≈0..0.03)
    # Layout: boards run along X; cavity opening ~0.55×0.40 centered
    boards = [
        # left strip
        (-0.55, -0.22, -0.38, 0.38, 0.0, 0.028),
        # right strip
        (0.22, 0.55, -0.38, 0.38, 0.0, 0.028),
        # front strip (between left/right, closing Y-)
        (-0.22, 0.22, -0.38, -0.20, 0.0, 0.028),
        # back strip
        (-0.22, 0.22, 0.20, 0.38, 0.0, 0.028),
    ]
    for i, (x0, x1, y0, y1, z0, z1) in enumerate(boards):
        bm = bmesh.new()
        box_bm(bm, x0, x1, y0, y1, z0, z1)
        for v in bm.verts:
            v.co.z += 0.002 * math.sin(v.co.x * 12 + i)
        parts.append(bm_to_object(f'_frame{i}', bm, oak if i % 2 == 0 else dark, smooth=False))

    # Nail heads / pegs at corners of opening
    iron = mat('_peg_iron', (0.32, 0.30, 0.26), 0.5, metallic=0.4)
    for i, (x, y) in enumerate((
        (-0.20, -0.18), (0.20, -0.18), (-0.20, 0.18), (0.20, 0.18),
        (-0.50, 0.0), (0.50, 0.0),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=0.008)
        for v in bm.verts:
            v.co.z *= 0.5
            v.co += Vector((x, y, 0.030))
        parts.append(bm_to_object(f'_nail{i}', bm, iron, smooth=True))

    return join_named('Mold_FloorFrame', parts)


def make_lifted_boards(oak, dark):
    """Two boards propped / slid aside — hidey-hole read."""
    parts = []
    # Board A: tilted up toward +Y / +Z (lifted)
    bm = bmesh.new()
    box_bm(bm, -0.20, 0.02, -0.18, 0.18, 0.0, 0.025)
    # Rotate around X near front edge
    pivot = Vector((0, -0.18, 0.012))
    ang = math.radians(28)
    for v in bm.verts:
        p = v.co - pivot
        y = p.y * math.cos(ang) - p.z * math.sin(ang)
        z = p.y * math.sin(ang) + p.z * math.cos(ang)
        v.co = Vector((v.co.x, pivot.y + y, pivot.z + z))
        # warp grain
        v.co.z += 0.003 * math.sin(v.co.x * 20)
    parts.append(bm_to_object('Mold_BoardLift', bm, oak, smooth=False))

    # Board B: slid aside to +X, slightly askew on floor
    bm = bmesh.new()
    box_bm(bm, 0.05, 0.28, -0.16, 0.20, 0.028, 0.052)
    for v in bm.verts:
        # slight yaw
        x, y = v.co.x, v.co.y
        a = math.radians(8)
        v.co.x = 0.16 + (x - 0.16) * math.cos(a) - (y - 0.02) * math.sin(a)
        v.co.y = 0.02 + (x - 0.16) * math.sin(a) + (y - 0.02) * math.cos(a)
        v.co.z += 0.002 * math.cos(v.co.y * 15)
    parts.append(bm_to_object('Mold_BoardSlide', bm, dark, smooth=False))

    # Prop stick under lifted board
    bm = bmesh.new()
    path = [
        Vector((-0.08, -0.05, 0.01)),
        Vector((-0.10, 0.02, 0.10)),
        Vector((-0.12, 0.08, 0.18)),
    ]
    tube(bm, path, [0.012, 0.011, 0.010], segs=6)
    parts.append(bm_to_object('Mold_PropStick', bm, dark, smooth=True))

    return join_named('Mold_LiftedBoards', parts)


def make_cavity_box(earth, timber):
    """Dirt/earth cavity walls under the opening — hidey-hole, not magic."""
    parts = []
    # Floor of cavity
    bm = bmesh.new()
    box_bm(bm, -0.20, 0.20, -0.18, 0.18, -0.16, -0.13)
    for v in bm.verts:
        v.co.z += 0.008 * math.sin(v.co.x * 9 + v.co.y * 7)
    parts.append(bm_to_object('Mold_CavityFloor', bm, earth, smooth=False))

    # Four dirt walls (open top)
    walls = [
        (-0.22, -0.18, -0.18, 0.18, -0.16, 0.0),   # -X
        (0.18, 0.22, -0.18, 0.18, -0.16, 0.0),     # +X
        (-0.18, 0.18, -0.20, -0.16, -0.16, 0.0),   # -Y
        (-0.18, 0.18, 0.16, 0.20, -0.16, 0.0),     # +Y
    ]
    for i, (x0, x1, y0, y1, z0, z1) in enumerate(walls):
        bm = bmesh.new()
        box_bm(bm, x0, x1, y0, y1, z0, z1)
        for v in bm.verts:
            v.co.x += 0.004 * math.sin(v.co.z * 20 + i)
            v.co.y += 0.003 * math.cos(v.co.z * 18 + i)
        parts.append(bm_to_object(f'_cwall{i}', bm, earth, smooth=False))

    # Joist stubs visible at sides of hole
    for i, x in enumerate((-0.24, 0.24)):
        bm = bmesh.new()
        box_bm(bm, x - 0.04, x + 0.04, -0.22, 0.22, -0.08, 0.01)
        parts.append(bm_to_object(f'_joist{i}', bm, timber, smooth=False))

    return join_named('Mold_Cavity', parts)


def make_seal_die(lead, wood, wax):
    """Lead seal mold / die resting in cavity — readable as forged papal die."""
    parts = []
    # Wooden handle / stock of die
    bm = bmesh.new()
    box_bm(bm, -0.04, 0.04, -0.04, 0.04, -0.12, -0.05)
    for v in bm.verts:
        # slight octagon wear on top
        if v.co.z > -0.06:
            v.co.x *= 0.92
            v.co.y *= 0.92
    parts.append(bm_to_object('Mold_DieStock', bm, wood, smooth=False))

    # Lead face disk (impression side up for readability)
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=24, radius1=0.055, radius2=0.055, depth=0.022,
        matrix=Matrix.Translation((0, 0, -0.038)),
    )
    parts.append(bm_to_object('Mold_DieFace', bm, lead, smooth=True))

    # Raised rim ring on face
    bm = bmesh.new()
    segs = 24
    path = [Vector((0.048 * math.cos(a), 0.048 * math.sin(a), -0.025))
            for a in [(j / segs) * math.tau for j in range(segs + 1)]]
    tube(bm, path, [0.006] * (segs + 1), segs=6, close_caps=False)
    parts.append(bm_to_object('Mold_DieRim', bm, lead, smooth=True))

    # Crude cross / keys impression (raised on die)
    bm = bmesh.new()
    box_bm(bm, -0.008, 0.008, -0.028, 0.028, -0.027, -0.018)
    box_bm(bm, -0.028, 0.028, -0.008, 0.008, -0.027, -0.018)
    parts.append(bm_to_object('Mold_DieMark', bm, lead, smooth=False))

    # Small wax scrap / smear nearby (no glow)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.018)
    for v in bm.verts:
        v.co.z *= 0.35
        v.co.x *= 1.4
        v.co += Vector((0.10, -0.06, -0.125))
        if v.co.z < -0.145:
            v.co.z = -0.145
    parts.append(bm_to_object('Mold_WaxScrap', bm, wax, smooth=True))

    # Cloth wrap scrap under die
    cloth = mat('Mold_Cloth', (0.42, 0.36, 0.28), 0.92, specular=0.1)
    bm = bmesh.new()
    box_bm(bm, -0.08, 0.08, -0.07, 0.07, -0.135, -0.122)
    for v in bm.verts:
        v.co.z += 0.004 * math.sin(v.co.x * 25) * math.cos(v.co.y * 20)
    parts.append(bm_to_object('Mold_Cloth', bm, cloth, smooth=False))

    return join_named('Mold_Die', parts)


def make_debris(oak, earth, iron):
    parts = []
    # Wood chips / splinters
    for i, (x, y, z, a) in enumerate((
        (-0.14, 0.12, 0.01, 20),
        (0.12, -0.10, 0.015, -35),
        (-0.05, 0.22, 0.02, 55),
        (0.18, 0.08, -0.02, 10),
    )):
        bm = bmesh.new()
        box_bm(bm, -0.04, 0.04, -0.01, 0.01, -0.005, 0.005)
        for v in bm.verts:
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            rx = v.co.x * ca - v.co.y * sa
            ry = v.co.x * sa + v.co.y * ca
            v.co = Vector((rx + x, ry + y, v.co.z + z))
        parts.append(bm_to_object(f'_chip{i}', bm, oak, smooth=False))

    # Dirt clods
    for i, (x, y, z) in enumerate((
        (-0.16, -0.12, -0.10),
        (0.14, 0.10, -0.11),
        (0.0, -0.14, -0.08),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=0.025)
        for v in bm.verts:
            v.co.x *= 1.3; v.co.y *= 0.9; v.co.z *= 0.55
            v.co += Vector((x, y, z))
        parts.append(bm_to_object(f'_clod{i}', bm, earth, smooth=True))

    # Bent nail
    bm = bmesh.new()
    path = [
        Vector((0.08, 0.14, 0.01)),
        Vector((0.10, 0.14, 0.02)),
        Vector((0.12, 0.13, 0.04)),
    ]
    tube(bm, path, [0.004, 0.004, 0.003], segs=5)
    parts.append(bm_to_object('Mold_BentNail', bm, iron, smooth=True))

    return join_named('Mold_Debris', parts)


def build_mold_cavity():
    clear_scene()
    oak = mat('Mold_Oak', (0.40, 0.28, 0.15), 0.88, specular=0.16)
    dark = mat('Mold_DarkOak', (0.28, 0.18, 0.10), 0.90, specular=0.12)
    earth = mat('Mold_Earth', (0.34, 0.26, 0.16), 0.96, specular=0.06)
    timber = mat('Mold_Timber', (0.32, 0.22, 0.12), 0.88, specular=0.14)
    lead = mat('Mold_Lead', (0.42, 0.42, 0.40), 0.55, metallic=0.65, specular=0.35)
    wood = mat('Mold_DieWood', (0.36, 0.24, 0.12), 0.82, specular=0.18)
    wax = mat('Mold_Wax', (0.55, 0.22, 0.16), 0.65, specular=0.25)
    iron = mat('Mold_Iron', (0.30, 0.28, 0.24), 0.5, metallic=0.5)

    meshes = [
        make_floor_frame(oak, dark),
        make_lifted_boards(oak, dark),
        make_cavity_box(earth, timber),
        make_seal_die(lead, wood, wax),
        make_debris(oak, earth, iron),
    ]
    meshes = [m for m in meshes if m is not None]
    plant_and_center(meshes)

    b = world_bounds(meshes)
    tris = count_tris(meshes)
    print(f"Mold cavity size={tuple(round(x, 4) for x in b['size'])} "
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

    bpy.ops.object.light_add(type='AREA', location=(2.2, -2.5, 2.8))
    key = bpy.context.active_object
    key.name = 'PreviewKey'
    key.data.energy = 260
    key.data.size = 2.2
    key.rotation_euler = (math.radians(48), math.radians(10), math.radians(30))

    bpy.ops.object.light_add(type='AREA', location=(-2.0, 1.5, 1.8))
    fill = bpy.context.active_object
    fill.name = 'PreviewFill'
    fill.data.energy = 80
    fill.data.size = 2.8
    fill.data.color = (0.70, 0.76, 0.85)

    bpy.ops.object.light_add(type='SUN', location=(0, 0, 4))
    sun = bpy.context.active_object
    sun.name = 'PreviewSun'
    sun.data.energy = 1.1
    sun.rotation_euler = (math.radians(42), math.radians(5), math.radians(-20))

    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -0.17))
    ground = bpy.context.active_object
    ground.name = 'PreviewGround'
    ground.data.materials.append(mat('Ground', (0.32, 0.26, 0.18), 0.96))


def render_previews():
    setup_preview_world()
    bpy.ops.object.camera_add(location=(0, -2.4, 1.2))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam
    target = Vector((0, 0, 0.05))

    views = [
        ('front', (0.0, -2.5, 1.1)),
        ('threequarter', (2.0, -1.8, 1.4)),
    ]
    for name, loc in views:
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        out = os.path.join(PREV_DIR, f'mold_cavity_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)


def cleanup_preview_helpers():
    for name in ('PreviewGround', 'PreviewCam', 'PreviewKey', 'PreviewFill', 'PreviewSun'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def main():
    meshes = build_mold_cavity()
    glb_path = os.path.join(OUT_DIR, 'mold_cavity.glb')
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
    meta = os.path.join(PREV_DIR, 'mold_cavity_scale.txt')
    with open(meta, 'w') as f:
        f.write(
            f"height_m={b['size'][2]:.4f}\n"
            f"width_x_m={b['size'][0]:.4f}\n"
            f"depth_y_m={b['size'][1]:.4f}\n"
            f"tris={tris}\n"
            f"objects={','.join(names)}\n"
            f"origin=floor_plane_center_board_section\n"
            f"collision=tight_to_mesh\n"
            f"interact_latch_note=~1.2x generous RMB latch only (not collider shell)\n"
            f"reads=lifted_floorboards+earth_cavity+lead_seal_die\n"
            f"style=goldsmith_hidey_hole_occitan_1208\n"
        )
    print('Wrote', meta)
    print(f'Done. height={b["size"][2]:.4f} width={b["size"][0]:.4f} depth={b["size"][1]:.4f} tris={tris}')
    print('Objects:', names)


if __name__ == '__main__':
    main()
