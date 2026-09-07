"""Shared helpers for Broken Seal building-shell makers (Blender 4.x)."""
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


def bm_to_object(name, bm, material=None, smooth=False):
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
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    for f in faces:
        bm.faces.new([verts[i] for i in f])
    return verts


def wear_stone(bm, amp=0.012, seed=1.7):
    for v in bm.verts:
        n = (math.sin(v.co.x * 7.1 + seed) * math.cos(v.co.y * 5.3 + seed * 1.3)
             + 0.5 * math.sin(v.co.z * 9.2 + v.co.x * 3.1))
        v.co.x += amp * 0.6 * n
        v.co.y += amp * 0.5 * math.sin(v.co.x * 4.2 + seed)
        if v.co.z > 0.02:
            v.co.z += amp * 0.35 * math.cos(v.co.x * 6.1 + v.co.y * 4.8)


def pitch_roof_bm(bm, xmin, xmax, ymin, ymax, z_eave, z_ridge, ridge_along_x=True):
    """Simple gable roof solid (closed volume under eaves)."""
    if ridge_along_x:
        # ridge runs along X at y mid
        ymid = (ymin + ymax) * 0.5
        v = [
            bm.verts.new((xmin, ymin, z_eave)),
            bm.verts.new((xmax, ymin, z_eave)),
            bm.verts.new((xmax, ymax, z_eave)),
            bm.verts.new((xmin, ymax, z_eave)),
            bm.verts.new((xmin, ymid, z_ridge)),
            bm.verts.new((xmax, ymid, z_ridge)),
        ]
        bm.verts.ensure_lookup_table()
        bm.faces.new((v[0], v[1], v[2], v[3]))  # bottom
        bm.faces.new((v[0], v[1], v[5], v[4]))  # -Y slope
        bm.faces.new((v[3], v[2], v[5], v[4]))  # +Y slope
        bm.faces.new((v[0], v[4], v[3]))  # -X gable
        bm.faces.new((v[1], v[2], v[5]))  # +X gable
    else:
        xmid = (xmin + xmax) * 0.5
        v = [
            bm.verts.new((xmin, ymin, z_eave)),
            bm.verts.new((xmax, ymin, z_eave)),
            bm.verts.new((xmax, ymax, z_eave)),
            bm.verts.new((xmin, ymax, z_eave)),
            bm.verts.new((xmid, ymin, z_ridge)),
            bm.verts.new((xmid, ymax, z_ridge)),
        ]
        bm.verts.ensure_lookup_table()
        bm.faces.new((v[0], v[1], v[2], v[3]))
        bm.faces.new((v[0], v[1], v[4]))
        bm.faces.new((v[3], v[2], v[5]))
        bm.faces.new((v[0], v[4], v[5], v[3]))
        bm.faces.new((v[1], v[2], v[5], v[4]))
    return v


def arch_opening_ring(bm, cx, cy, cz_spring, r_inner, r_outer, depth_front, depth_back, segs=14):
    """Romanesque round arch ring in XZ, extruded in Y. Returns nothing; adds to bm."""
    y0, y1 = depth_front, depth_back
    fo, fi, bo, bi = [], [], [], []
    for i in range(segs + 1):
        a = math.pi * (1.0 - i / segs)
        co, si = math.cos(a), math.sin(a)
        fo.append(bm.verts.new((cx + r_outer * co, y0, cz_spring + r_outer * si)))
        fi.append(bm.verts.new((cx + r_inner * co, y0, cz_spring + r_inner * si)))
        bo.append(bm.verts.new((cx + r_outer * co, y1, cz_spring + r_outer * si)))
        bi.append(bm.verts.new((cx + r_inner * co, y1, cz_spring + r_inner * si)))
    bm.verts.ensure_lookup_table()
    for i in range(segs):
        bm.faces.new((fi[i], fi[i + 1], fo[i + 1], fo[i]))
        bm.faces.new((bo[i], bo[i + 1], bi[i + 1], bi[i]))
        bm.faces.new((fo[i], fo[i + 1], bo[i + 1], bo[i]))
        bm.faces.new((bi[i], bi[i + 1], fi[i + 1], fi[i]))
    for idx in (0, segs):
        bm.faces.new((fi[idx], fo[idx], bo[idx], bi[idx]))


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


def setup_preview_world(ground_color=(0.36, 0.32, 0.24)):
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

    bpy.ops.object.light_add(type='AREA', location=(4.5, -5.0, 5.5))
    key = bpy.context.active_object
    key.name = 'PreviewKey'
    key.data.energy = 420
    key.data.size = 4.0
    key.rotation_euler = (math.radians(55), math.radians(8), math.radians(35))

    bpy.ops.object.light_add(type='AREA', location=(-4.0, 3.0, 3.5))
    fill = bpy.context.active_object
    fill.name = 'PreviewFill'
    fill.data.energy = 130
    fill.data.size = 5.0
    fill.data.color = (0.75, 0.80, 0.90)

    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    sun = bpy.context.active_object
    sun.name = 'PreviewSun'
    sun.data.energy = 1.5
    sun.rotation_euler = (math.radians(42), math.radians(10), math.radians(-30))

    bpy.ops.mesh.primitive_plane_add(size=24, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = 'PreviewGround'
    ground.data.materials.append(mat('Ground', ground_color, 0.95))


def render_previews(stem, cam_target=(0, 0, 2.2), views=None, dist_scale=1.0):
    setup_preview_world()
    bpy.ops.object.camera_add(location=(0, -8, 3))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam
    target = Vector(cam_target)
    if views is None:
        views = [
            ('front', (0.0, -10.0 * dist_scale, 3.2 * dist_scale)),
            ('threequarter', (7.5 * dist_scale, -7.0 * dist_scale, 4.5 * dist_scale)),
        ]
    for name, loc in views:
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        out = os.path.join(PREV_DIR, f'{stem}_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)


def cleanup_preview_helpers():
    for name in ('PreviewGround', 'PreviewCam', 'PreviewKey', 'PreviewFill', 'PreviewSun'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def write_scale(stem, meshes, extra_lines=None):
    b = world_bounds(meshes)
    tris = count_tris(meshes)
    names = sorted(o.name for o in meshes)
    meta = os.path.join(PREV_DIR, f'{stem}_scale.txt')
    with open(meta, 'w') as f:
        f.write(
            f"height_m={b['size'][2]:.4f}\n"
            f"width_x_m={b['size'][0]:.4f}\n"
            f"depth_y_m={b['size'][1]:.4f}\n"
            f"tris={tris}\n"
            f"objects={','.join(names)}\n"
            f"origin=ground_center_footprint\n"
            f"collision=tight_to_mesh\n"
        )
        if extra_lines:
            for line in extra_lines:
                f.write(line.rstrip('\n') + '\n')
    print('Wrote', meta)
    print(f'Done. height={b["size"][2]:.4f} width={b["size"][0]:.4f} '
          f'depth={b["size"][1]:.4f} tris={tris}')
    print('Objects:', names)
    return b, tris


# Palette — Occitania 1208 winter dirt-and-mail
PALETTE = {
    'limestone': (0.60, 0.54, 0.42),
    'limestone_dark': (0.46, 0.42, 0.34),
    'limestone_warm': (0.64, 0.56, 0.44),
    'plaster': (0.58, 0.52, 0.42),
    'oak': (0.30, 0.20, 0.11),
    'oak_dark': (0.22, 0.14, 0.08),
    'tile': (0.38, 0.28, 0.20),
    'tile_dark': (0.30, 0.22, 0.16),
    'thatch': (0.48, 0.40, 0.24),
    'thatch_dark': (0.36, 0.30, 0.18),
    'mud': (0.30, 0.24, 0.15),
    'iron': (0.26, 0.24, 0.22),
    'rubble': (0.50, 0.46, 0.38),
}
