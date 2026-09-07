"""Blender: Sheep-gate exit prop (Broken Seal) — game-ready GLB + previews.

Wooden stock / hurdle gate in limestone posts — readable as hold_door escape
route (not locked burial gate). Dirt-and-mail Occitania 1208 — NO fantasy glow.
Rebuild:
  /usr/bin/blender -b -P tools/make_sheep_gate.py

Scale notes:
  - Origin at ground center between posts
  - Clear opening ~1.6 m; posts ~1.45 m; hurdle leaf ~1.2 m high (climbable/openable read)
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


def make_posts(limestone, mud):
    """Rougher rural limestone posts — sheep fold, not churchyard."""
    parts = []
    half = 0.85
    post_w = 0.28
    post_d = 0.30
    post_h = 1.42

    for side, sx in (('L', -1), ('R', 1)):
        bm = bmesh.new()
        x0 = sx * half
        x1 = sx * (half + post_w)
        box_bm(bm, min(x0, x1), max(x0, x1), -post_d / 2, post_d / 2, 0.0, post_h)
        wear_stone(bm, amp=0.015, seed=5.0 + sx)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Sheep_Post{side}', bm, limestone, smooth=False))

        # Simple flat cap (not fancy coping)
        bm = bmesh.new()
        box_bm(bm, min(x0, x1) - 0.03, max(x0, x1) + 0.03,
               -post_d / 2 - 0.03, post_d / 2 + 0.03, post_h - 0.02, post_h + 0.10)
        wear_stone(bm, amp=0.006, seed=8 + sx)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Sheep_Cap{side}', bm, limestone, smooth=False))

        # Wooden hinge pin stubs on left
        if sx < 0:
            oak_pin = mat('_pin_oak', (0.32, 0.22, 0.12), 0.85, specular=0.2)
            for i, z in enumerate((0.28, 0.95)):
                bm = bmesh.new()
                path = [Vector((x0 + 0.01, 0.0, z)), Vector((x0 - 0.06, 0.04, z))]
                tube(bm, path, [0.02, 0.018], segs=6)
                parts.append(bm_to_object(f'Sheep_Pin{i}', bm, oak_pin, smooth=True))

    for i, (mx, my) in enumerate((
        (-half - post_w * 0.5, 0.1),
        (half + post_w * 0.5, -0.08),
        (-half, -0.16),
        (half, 0.14),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=0.09)
        for v in bm.verts:
            v.co.z *= 0.4
            v.co.x *= 1.3
            v.co += Vector((mx, my, 0.025))
            if v.co.z < 0:
                v.co.z = 0.002
        parts.append(bm_to_object(f'_smud{i}', bm, mud, smooth=True))

    return join_named('Sheep_Posts', parts)


def make_hurdle_leaf(oak, dark):
    """Horizontal-rail stock / hurdle gate — openable escape read (ajar slightly)."""
    parts = []
    # Slightly ajar toward +Y (yard → exit hint)
    ajar_y = 0.08
    x0, x1 = -0.78, 0.78
    z_rails = [0.18, 0.42, 0.68, 0.92, 1.12]

    # Vertical stiles
    for i, x in enumerate((x0 + 0.04, x1 - 0.04)):
        bm = bmesh.new()
        box_bm(bm, x - 0.04, x + 0.04, ajar_y - 0.04, ajar_y + 0.04, 0.08, 1.22)
        # pointed / worn top
        for v in bm.verts:
            if v.co.z > 1.12:
                v.co.x = x + (v.co.x - x) * 0.6
                v.co.y = ajar_y + (v.co.y - ajar_y) * 0.6
        parts.append(bm_to_object(f'_stile{i}', bm, oak, smooth=False))

    # Horizontal rails (hurdle / stock look)
    for i, z in enumerate(z_rails):
        bm = bmesh.new()
        # rails slightly uneven thickness
        h = 0.04 + 0.008 * (i % 2)
        box_bm(bm, x0 + 0.06, x1 - 0.06, ajar_y - 0.035, ajar_y + 0.035, z - h, z + h)
        for v in bm.verts:
            v.co.z += 0.006 * math.sin(v.co.x * 7 + i)
        parts.append(bm_to_object(f'_rail{i}', bm, oak if i % 2 == 0 else dark, smooth=False))

    # Diagonal brace (farm gate authenticity)
    bm = bmesh.new()
    path = [
        Vector((x0 + 0.12, ajar_y, 0.22)),
        Vector((0.1, ajar_y, 0.65)),
        Vector((x1 - 0.14, ajar_y, 1.05)),
    ]
    tube(bm, path, [0.025, 0.028, 0.025], segs=6)
    parts.append(bm_to_object('Sheep_Brace', bm, dark, smooth=True))

    # Mid vertical pickets between rails (sparse — sheep barrier, not solid door)
    for i, x in enumerate((-0.4, 0.0, 0.4)):
        bm = bmesh.new()
        box_bm(bm, x - 0.025, x + 0.025, ajar_y - 0.025, ajar_y + 0.025, 0.2, 1.08)
        parts.append(bm_to_object(f'_pick{i}', bm, oak, smooth=False))

    return join_named('Sheep_Leaf', parts)


def make_latch(oak, iron):
    """Simple wooden drop-latch — soft latch (Convers can lift) — NOT padlocked."""
    parts = []
    # Drop bar on right side (reads openable)
    bm = bmesh.new()
    box_bm(bm, 0.55, 0.95, 0.02, 0.10, 0.72, 0.82)
    parts.append(bm_to_object('Sheep_DropBar', bm, oak, smooth=False))

    # Keeper on right post
    bm = bmesh.new()
    box_bm(bm, 0.82, 0.98, -0.06, 0.12, 0.68, 0.86)
    # U slot
    box_bm(bm, 0.84, 0.96, 0.10, 0.14, 0.70, 0.74)
    box_bm(bm, 0.84, 0.96, 0.10, 0.14, 0.80, 0.84)
    parts.append(bm_to_object('Sheep_Keeper', bm, oak, smooth=False))

    # Iron staple (small)
    bm = bmesh.new()
    path = [Vector((0.70, 0.06, 0.77)), Vector((0.78, 0.06, 0.77))]
    tube(bm, path, [0.012, 0.012], segs=6)
    parts.append(bm_to_object('Sheep_Staple', bm, iron, smooth=True))

    # Rope loop alternate latch (yard / fold feel)
    hemp = mat('Sheep_Hemp', (0.50, 0.40, 0.26), 0.9, specular=0.12)
    bm = bmesh.new()
    path, radii = [], []
    for i in range(14):
        t = i / 13
        ang = t * math.tau * 1.5
        x = 0.72 + 0.06 * math.cos(ang)
        y = 0.08 + 0.05 * math.sin(ang)
        z = 0.77 + 0.04 * math.sin(ang * 0.5)
        path.append(Vector((x, y, z)))
        radii.append(0.012)
    tube(bm, path, radii, segs=6)
    parts.append(bm_to_object('Sheep_RopeLoop', bm, hemp, smooth=True))

    return join_named('Sheep_Latch', parts)


def make_low_hurdle_wings(oak, limestone):
    """Short wattle / rail wings — fold continuity, exit corridor read."""
    parts = []
    half = 0.85
    post_w = 0.28
    for side, sx in (('L', -1), ('R', 1)):
        # stone stub
        bm = bmesh.new()
        x_start = sx * (half + post_w)
        x_end = sx * (half + post_w + 0.45)
        box_bm(bm, min(x_start, x_end), max(x_start, x_end), -0.12, 0.12, 0.0, 0.75)
        wear_stone(bm, amp=0.01, seed=11 + sx)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Sheep_WingStone{side}', bm, limestone, smooth=False))

        # low rail on wing
        bm = bmesh.new()
        box_bm(bm, min(x_start, x_end) + 0.05 * sx, max(x_start, x_end) - 0.05 * sx,
               -0.03, 0.03, 0.45, 0.52)
        parts.append(bm_to_object(f'Sheep_WingRail{side}', bm, oak, smooth=False))

    return join_named('Sheep_Wings', parts)


def build_sheep_gate():
    clear_scene()
    limestone = mat('Sheep_Limestone', (0.58, 0.53, 0.41), 0.90, specular=0.15)
    oak = mat('Sheep_Oak', (0.38, 0.28, 0.15), 0.86, specular=0.18)
    dark = mat('Sheep_DarkOak', (0.26, 0.18, 0.10), 0.90, specular=0.14)
    mud = mat('Sheep_Mud', (0.28, 0.22, 0.14), 0.96, specular=0.08)
    iron = mat('Sheep_Iron', (0.28, 0.26, 0.22), 0.55, metallic=0.55, specular=0.4)

    meshes = [
        make_posts(limestone, mud),
        make_hurdle_leaf(oak, dark),
        make_latch(oak, iron),
        make_low_hurdle_wings(oak, limestone),
    ]
    meshes = [m for m in meshes if m is not None]
    plant_and_center(meshes)

    b = world_bounds(meshes)
    tris = count_tris(meshes)
    print(f"Sheep gate size={tuple(round(x, 4) for x in b['size'])} "
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
    key.data.energy = 300
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
    ground.data.materials.append(mat('Ground', (0.36, 0.32, 0.24), 0.95))


def render_previews():
    setup_preview_world()
    bpy.ops.object.camera_add(location=(0, -4.5, 1.3))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam
    target = Vector((0, 0, 0.8))

    views = [
        ('front', (0.0, -4.6, 1.25)),
        ('threequarter', (3.5, -3.4, 1.9)),
    ]
    for name, loc in views:
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        out = os.path.join(PREV_DIR, f'sheep_gate_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)


def cleanup_preview_helpers():
    for name in ('PreviewGround', 'PreviewCam', 'PreviewKey', 'PreviewFill', 'PreviewSun'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def build_sheep_gate_main():
    return build_sheep_gate()


def main():
    meshes = build_sheep_gate()
    glb_path = os.path.join(OUT_DIR, 'sheep_gate.glb')
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
    meta = os.path.join(PREV_DIR, 'sheep_gate_scale.txt')
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
            f"opening_m~=1.70 latch=drop_bar+rope_loop (NOT padlocked)\n"
            f"reads=sheep_fold_hurdle_exit_gate\n"
            f"style=priory_sheep_gate_occitan_1208\n"
        )
    print('Wrote', meta)
    print(f'Done. height={b["size"][2]:.4f} width={b["size"][0]:.4f} depth={b["size"][1]:.4f} tris={tris}')
    print('Objects:', names)


if __name__ == '__main__':
    main()
