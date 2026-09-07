"""Blender: Collapsed priory loft section (Broken Seal) — game-ready GLB + previews.

Broken loft / collapsed timber floor with beams and debris — static damaged state
for Guide loft fight set dressing. Dirt-and-mail Occitania 1208 — NO fantasy glow.
Rebuild:
  /usr/bin/blender -b -P tools/make_collapsing_loft.py

Scale notes:
  - Origin at ground center under debris footprint
  - Section ~3.2 × 2.4 m footprint; broken deck height ~2.0–2.4 m; debris to ground
  - Collision shell tight to mesh (static set dressing)
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


def add_oriented_beam(parts, name, p0, p1, half_w, half_h, material, idx):
    """Rectangular beam from p0 to p1."""
    bm = bmesh.new()
    d = (p1 - p0)
    length = d.length
    if length < 1e-4:
        bm.free()
        return
    tang = d.normalized()
    up = Vector((0, 0, 1))
    if abs(tang.dot(up)) > 0.9:
        up = Vector((1, 0, 0))
    binormal = tang.cross(up).normalized()
    normal = binormal.cross(tang).normalized()
    # 8 corners
    corners0 = []
    corners1 = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        off = binormal * (sx * half_w) + normal * (sy * half_h)
        corners0.append(bm.verts.new(p0 + off))
        corners1.append(bm.verts.new(p1 + off))
    bm.verts.ensure_lookup_table()
    # end caps
    bm.faces.new(corners0)
    bm.faces.new(list(reversed(corners1)))
    for i in range(4):
        i2 = (i + 1) % 4
        bm.faces.new((corners0[i], corners0[i2], corners1[i2], corners1[i]))
    # splinter tip jitter on broken end
    for v in corners1:
        v.co += tang * (0.02 * math.sin(v.co.x * 20 + idx))
        v.co += binormal * (0.015 * math.cos(v.co.z * 15 + idx))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object(f'{name}{idx}', bm, material, smooth=False))


def make_remaining_joists(oak, dark):
    """Partial loft floor still hanging — broken joists + remaining planks."""
    parts = []
    deck_z = 2.15
    # Wall-side ledger still attached (-Y)
    add_oriented_beam(
        parts, 'Loft_Ledger',
        Vector((-1.5, -1.05, deck_z)), Vector((1.5, -1.05, deck_z)),
        0.08, 0.07, oak, 0,
    )
    # Surviving joists (short stubs from ledger, broken mid-span)
    joist_data = [
        (-1.1, 0.55, 0.04),
        (-0.45, 0.35, -0.08),
        (0.15, 0.70, 0.12),
        (0.85, 0.40, -0.15),
        (1.25, 0.25, 0.05),
    ]
    for i, (x, reach, tip_dz) in enumerate(joist_data):
        p0 = Vector((x, -1.0, deck_z))
        p1 = Vector((x + 0.08 * math.sin(i), -1.0 + reach, deck_z + tip_dz - 0.15 * reach))
        add_oriented_beam(parts, 'Loft_Joist', p0, p1, 0.05, 0.06, oak if i % 2 == 0 else dark, i)

    # Remaining floor planks on joists (partial, broken)
    plank_specs = [
        (-1.3, -0.9, -0.7, -0.55, deck_z + 0.06),
        (-0.55, -0.95, 0.05, -0.45, deck_z + 0.05),
        (0.2, -0.9, 0.7, -0.35, deck_z + 0.04),
        (0.9, -0.95, 1.35, -0.70, deck_z + 0.055),
    ]
    for i, (x0, y0, x1, y1, z) in enumerate(plank_specs):
        bm = bmesh.new()
        box_bm(bm, x0, x1, y0, y1, z - 0.025, z + 0.025)
        # broken jagged far edge
        for v in bm.verts:
            if v.co.y > (y0 + y1) * 0.5:
                v.co.y -= 0.04 * abs(math.sin(v.co.x * 14 + i))
                v.co.z += 0.02 * math.sin(v.co.x * 9)
        parts.append(bm_to_object(f'_plank{i}', bm, oak if i % 2 else dark, smooth=False))

    return join_named('Loft_Remaining', parts)


def make_fallen_beams(oak, dark):
    """Collapsed beams angled from loft height to ground / mid debris."""
    parts = []
    beams = [
        # big diagonal main fall
        (Vector((-0.8, -0.9, 2.0)), Vector((0.4, 0.6, 0.35)), 0.07, 0.08, oak),
        (Vector((0.9, -0.85, 2.05)), Vector((0.2, 0.9, 0.25)), 0.06, 0.07, dark),
        (Vector((-1.2, -0.5, 1.6)), Vector((-0.3, 0.4, 0.15)), 0.05, 0.055, oak),
        (Vector((1.1, 0.2, 1.2)), Vector((0.5, -0.3, 0.4)), 0.045, 0.05, dark),
        # snapped mid piece
        (Vector((-0.2, 0.1, 0.9)), Vector((0.8, 0.7, 0.55)), 0.05, 0.05, oak),
    ]
    for i, (p0, p1, hw, hh, matl) in enumerate(beams):
        add_oriented_beam(parts, 'Loft_Fallen', p0, p1, hw, hh, matl, i)
    return join_named('Loft_FallenBeams', parts)


def make_debris(oak, dark, limestone, mud):
    """Floor boards, rubble, shattered planks on ground."""
    parts = []
    # Scattered broken planks
    debris_planks = [
        (-0.9, 0.3, 0.35, 0.12, 0.08, 0.35),
        (0.5, 0.6, -0.2, 0.08, 0.45, 0.18),
        (-0.2, 0.8, 0.55, 0.15, 0.1, 0.08),
        (1.0, -0.2, 0.1, 0.1, 0.4, 0.25),
        (-1.1, 0.5, -0.4, 0.12, 0.3, 0.05),
        (0.1, 0.2, 0.0, 0.5, 0.08, 0.12),
    ]
    for i, (cx, cy, yaw, lx, ly, lz) in enumerate(debris_planks):
        bm = bmesh.new()
        box_bm(bm, -lx / 2, lx / 2, -ly / 2, ly / 2, 0.0, 0.04)
        # rotate around Z via vertex transform
        ca, sa = math.cos(yaw), math.sin(yaw)
        for v in bm.verts:
            x, y = v.co.x, v.co.y
            v.co.x = cx + x * ca - y * sa
            v.co.y = cy + x * sa + y * ca
            v.co.z = lz + v.co.z + 0.01 * math.sin(x * 20)
        parts.append(bm_to_object(f'_debris{i}', bm, oak if i % 2 == 0 else dark, smooth=False))

    # Stone chunks fallen with loft (limestone wall bits)
    for i, (mx, my, mz, mr) in enumerate((
        (-0.6, 0.55, 0.12, 0.11),
        (0.7, 0.35, 0.1, 0.09),
        (0.0, 0.95, 0.08, 0.08),
        (1.2, 0.5, 0.09, 0.07),
    )):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=mr)
        for v in bm.verts:
            v.co.x *= 1.3 + 0.2 * math.sin(v.co.y * 8)
            v.co.y *= 1.1
            v.co.z *= 0.7
            v.co += Vector((mx, my, mz))
            if v.co.z < 0:
                v.co.z = 0.01
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'_rubble{i}', bm, limestone, smooth=False))

    # Dust / mud piles
    for i, (mx, my, mr) in enumerate((
        (0.2, 0.4, 0.14), (-0.5, 0.7, 0.11), (0.9, 0.8, 0.1),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=mr)
        for v in bm.verts:
            v.co.z *= 0.35
            v.co.x *= 1.4
            v.co += Vector((mx, my, 0.02))
            if v.co.z < 0:
                v.co.z = 0.002
        parts.append(bm_to_object(f'_dust{i}', bm, mud, smooth=True))

    return join_named('Loft_Debris', parts)


def make_wall_stubs(limestone):
    """Short limestone wall stubs the loft once sat on."""
    parts = []
    # Back wall ledge (-Y)
    bm = bmesh.new()
    box_bm(bm, -1.6, 1.6, -1.25, -0.95, 0.0, 2.35)
    # corbel / beam pocket recess suggestion
    box_bm(bm, -1.55, 1.55, -0.95, -0.88, 2.0, 2.25)
    for v in bm.verts:
        n = math.sin(v.co.x * 5) * math.cos(v.co.z * 4)
        v.co.y += 0.012 * n
        if v.co.z > 0.1:
            v.co.z += 0.008 * math.cos(v.co.x * 6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bm_to_object('Loft_WallBack', bm, limestone, smooth=False))

    # Side pier stubs
    for sx, name in ((-1, 'L'), (1, 'R')):
        bm = bmesh.new()
        x0 = sx * 1.45
        box_bm(bm, x0 - 0.18, x0 + 0.18, -1.1, -0.4, 0.0, 1.8)
        for v in bm.verts:
            if v.co.z > 1.5:
                v.co.z -= 0.15 * abs(math.sin(v.co.y * 8))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bm_to_object(f'Loft_Pier{name}', bm, limestone, smooth=False))

    return join_named('Loft_Stone', parts)


def build_collapsing_loft():
    clear_scene()
    oak = mat('Loft_Oak', (0.36, 0.26, 0.14), 0.86, specular=0.18)
    dark = mat('Loft_DarkOak', (0.24, 0.16, 0.09), 0.90, specular=0.14)
    limestone = mat('Loft_Limestone', (0.56, 0.51, 0.40), 0.91, specular=0.14)
    mud = mat('Loft_Dust', (0.32, 0.27, 0.18), 0.96, specular=0.06)

    meshes = [
        make_wall_stubs(limestone),
        make_remaining_joists(oak, dark),
        make_fallen_beams(oak, dark),
        make_debris(oak, dark, limestone, mud),
    ]
    meshes = [m for m in meshes if m is not None]
    plant_and_center(meshes)

    b = world_bounds(meshes)
    tris = count_tris(meshes)
    print(f"Collapsing loft size={tuple(round(x, 4) for x in b['size'])} "
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

    bpy.ops.object.light_add(type='AREA', location=(3.5, -3.5, 4.0))
    key = bpy.context.active_object
    key.name = 'PreviewKey'
    key.data.energy = 340
    key.data.size = 3.5
    key.rotation_euler = (math.radians(52), math.radians(8), math.radians(30))

    bpy.ops.object.light_add(type='AREA', location=(-3.0, 2.5, 2.8))
    fill = bpy.context.active_object
    fill.name = 'PreviewFill'
    fill.data.energy = 110
    fill.data.size = 4.0
    fill.data.color = (0.72, 0.78, 0.88)

    bpy.ops.object.light_add(type='SUN', location=(0, 0, 7))
    sun = bpy.context.active_object
    sun.name = 'PreviewSun'
    sun.data.energy = 1.3
    sun.rotation_euler = (math.radians(40), math.radians(8), math.radians(-28))

    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = 'PreviewGround'
    ground.data.materials.append(mat('Ground', (0.34, 0.30, 0.22), 0.95))


def render_previews():
    setup_preview_world()
    bpy.ops.object.camera_add(location=(0, -6.0, 2.2))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam
    target = Vector((0, 0, 1.1))

    views = [
        ('front', (0.0, -6.2, 2.0)),
        ('threequarter', (4.5, -4.5, 2.8)),
    ]
    for name, loc in views:
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        out = os.path.join(PREV_DIR, f'collapsing_loft_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)


def cleanup_preview_helpers():
    for name in ('PreviewGround', 'PreviewCam', 'PreviewKey', 'PreviewFill', 'PreviewSun'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def main():
    meshes = build_collapsing_loft()
    glb_path = os.path.join(OUT_DIR, 'collapsing_loft.glb')
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
    meta = os.path.join(PREV_DIR, 'collapsing_loft_scale.txt')
    with open(meta, 'w') as f:
        f.write(
            f"height_m={b['size'][2]:.4f}\n"
            f"width_x_m={b['size'][0]:.4f}\n"
            f"depth_y_m={b['size'][1]:.4f}\n"
            f"tris={tris}\n"
            f"objects={','.join(names)}\n"
            f"origin=ground_center_debris_footprint\n"
            f"collision=tight_to_mesh\n"
            f"state=static_damaged_collapsed\n"
            f"style=priory_loft_collapse_occitan_1208\n"
        )
    print('Wrote', meta)
    print(f'Done. height={b["size"][2]:.4f} width={b["size"][0]:.4f} depth={b["size"][1]:.4f} tris={tris}')
    print('Objects:', names)


if __name__ == '__main__':
    main()
