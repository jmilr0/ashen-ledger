"""Blender: The Clerk (Broken Seal) — lean dirt-and-mail humanoid GLB + previews.

Scale (Game Design):
  - Collision capsule ~0.6 m diameter → keep silhouette lean (shoulder/cloak under ~0.55 m).
  - Height ~1.7–1.8 m adult male (authored at ~1.75 m).
  - Formation spacing ~0.9 m c-c is context only (not modeled into mesh).
  - Characters stay tight; props later may be 1.2× mesh vs collision.
"""
import math
import os
import bpy
from mathutils import Vector, Matrix

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT_DIR = os.path.join(ROOT, 'public', 'models', 'characters')
PREV_DIR = os.path.join(OUT_DIR, 'previews')
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PREV_DIR, exist_ok=True)

# Target authored height (meters). Engineering should fitToHeight ≈ this.
TARGET_HEIGHT = 1.75
# Soft max half-width for torso/cloak bulk (diameter 0.6 → radius 0.3; leave margin for arms).
MAX_BODY_HALF_WIDTH = 0.26


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes):
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials):
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in list(bpy.data.cameras):
        if block.users == 0:
            bpy.data.cameras.remove(block)
    for block in list(bpy.data.lights):
        if block.users == 0:
            bpy.data.lights.remove(block)


def mat(name, color, roughness=0.7, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    if 'Metallic' in bsdf.inputs:
        bsdf.inputs['Metallic'].default_value = metallic
    return m


def uv_sphere(name, radius, segments, rings, material, loc=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=segments, ring_count=rings, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


def cylinder(name, radius, depth, vertices, material, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, vertices=vertices, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler = rot
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


def soft_box(name, size, material, loc=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.modifier_add(type='SUBSURF')
    obj.modifiers['Subdivision'].levels = 1
    obj.modifiers['Subdivision'].render_levels = 1
    bpy.ops.object.modifier_apply(modifier='Subdivision')
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


def ico_sphere(name, radius, subdivisions, material, loc=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=radius, subdivisions=subdivisions, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


def join_all(root_name):
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not objs:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = root_name
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    # Plant feet on Z=0
    min_z = min((joined.matrix_world @ Vector(c)).z for c in joined.bound_box)
    joined.location.z -= min_z
    bpy.ops.object.transform_apply(location=True)
    return joined


def mesh_bounds(obj):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs = [c.x for c in corners]
    ys = [c.y for c in corners]
    zs = [c.z for c in corners]
    return {
        'min': (min(xs), min(ys), min(zs)),
        'max': (max(xs), max(ys), max(zs)),
        'size': (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)),
    }


def export_glb(path):
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_yup=True,
    )


def build_clerk():
    clear_scene()

    # Dirt-and-mail palette (muted Occitan winter road)
    skin = mat('Skin', (0.76, 0.60, 0.48), 0.58)
    tunic = mat('Tunic', (0.34, 0.30, 0.26), 0.82)
    cloak = mat('Cloak', (0.26, 0.24, 0.22), 0.88)
    leather = mat('Leather', (0.22, 0.15, 0.10), 0.8)
    hair_m = mat('Hair', (0.18, 0.14, 0.11), 0.72)
    wood = mat('Wood', (0.38, 0.26, 0.14), 0.78)
    mail = mat('Mail', (0.42, 0.42, 0.40), 0.45, metallic=0.55)
    dark = mat('Dark', (0.09, 0.08, 0.07), 0.9)
    parchment = mat('Parchment', (0.72, 0.64, 0.48), 0.85)

    # Lean torso — shoulder half-width ~0.20–0.22 (under 0.6 m capsule)
    cylinder('Torso', 0.175, 0.52, 12, tunic, loc=(0, 0, 1.12), scale=(1.0, 0.78, 1))
    uv_sphere('Pelvis', 0.16, 12, 8, tunic, loc=(0, 0, 0.78), scale=(1.05, 0.8, 0.65))
    # Thin mail collar / coif rim (dirt-and-mail, not plate)
    cylinder('MailCollar', 0.11, 0.06, 12, mail, loc=(0, 0, 1.36), scale=(1.05, 0.9, 1))
    cylinder('Neck', 0.05, 0.09, 8, skin, loc=(0, 0, 1.42))
    uv_sphere('Head', 0.135, 14, 10, skin, loc=(0, 0, 1.58))
    ico_sphere('Hair', 0.14, 2, hair_m, loc=(0, -0.015, 1.64), scale=(1.05, 1.1, 0.95))

    # Arms close to body (alleys / two-abreast)
    for side, sx in (('L', 0.22), ('R', -0.22)):
        cylinder(
            f'UpperArm{side}', 0.045, 0.30, 8, tunic,
            loc=(sx, 0.0, 1.18),
            rot=(0, math.radians(8 if sx > 0 else -8), 0),
        )
        cylinder(
            f'ForeArm{side}', 0.038, 0.26, 8, skin,
            loc=(sx * 1.05, 0.02, 0.92),
            rot=(0, math.radians(5 if sx > 0 else -5), 0),
        )
        uv_sphere(f'Hand{side}', 0.042, 8, 6, skin, loc=(sx * 1.1, 0.04, 0.76))

    # Legs / boots
    for side, sx in (('L', 0.085), ('R', -0.085)):
        cylinder(f'Thigh{side}', 0.062, 0.36, 8, tunic, loc=(sx, 0, 0.52))
        cylinder(f'Calf{side}', 0.048, 0.32, 8, leather, loc=(sx, 0.015, 0.20))
        uv_sphere(f'Boot{side}', 0.055, 10, 6, dark, loc=(sx, 0.05, 0.04), scale=(1.05, 1.55, 0.65))

    # Slim travel cloak (rear half — do not oversize beyond capsule)
    # Rear cloak drape (lean; does not inflate capsule)
    uv_sphere('CloakShoulder', 0.19, 12, 8, cloak, loc=(0, -0.05, 1.28), scale=(1.0, 0.55, 0.55))
    cylinder('CloakBody', 0.18, 0.55, 12, cloak, loc=(0, -0.08, 0.95), scale=(0.95, 0.35, 1))

    cylinder('Belt', 0.185, 0.04, 12, leather, loc=(0, 0, 0.84))

    # Charter satchel (hip) — readable prop, still lean
    soft_box('Satchel', 0.11, leather, loc=(0.175, 0.07, 0.88), scale=(0.5, 0.24, 0.8))
    soft_box('CharterEdge', 0.07, parchment, loc=(0.175, 0.095, 0.92), scale=(0.4, 0.07, 0.65))
    cylinder('SatchelStrap', 0.011, 0.40, 6, leather, loc=(0.10, 0.03, 1.12), rot=(0, math.radians(26), 0))

    # Walking staff (right hand side) — thin, may exceed capsule slightly
    cylinder('Staff', 0.016, 1.32, 8, wood, loc=(-0.22, 0.05, 0.76), rot=(math.radians(6), 0, math.radians(-4)))
    uv_sphere('StaffKnob', 0.024, 8, 6, wood, loc=(-0.23, 0.06, 1.42))

    # Quill tucked in belt (job read)
    cylinder('Quill', 0.008, 0.16, 6, hair_m, loc=(0.05, 0.12, 0.95), rot=(math.radians(55), 0, math.radians(20)))

    joined = join_all('Clerk')
    b = mesh_bounds(joined)
    height = b['size'][2]
    if abs(height - TARGET_HEIGHT) > 0.01 and height > 0:
        s = TARGET_HEIGHT / height
        joined.scale = (s, s, s)
        bpy.ops.object.transform_apply(scale=True)
        # Re-plant
        min_z = min((joined.matrix_world @ Vector(c)).z for c in joined.bound_box)
        joined.location.z -= min_z
        bpy.ops.object.transform_apply(location=True)

    b = mesh_bounds(joined)
    half_x = b['size'][0] * 0.5
    half_y = b['size'][1] * 0.5
    print(f"Clerk bounds size={b['size']} halfXY=({half_x:.3f},{half_y:.3f}) height={b['size'][2]:.3f}")
    if half_x > 0.38 or half_y > 0.38:
        print('WARN: silhouette wider than preferred for 0.6 m capsule (staff/satchel may stick out).')
    return joined


def setup_preview_world():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE'
    # Fallback if EEVEE_NEXT name differs
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

    # Cold winter fill
    bpy.ops.object.light_add(type='AREA', location=(2.2, -2.5, 3.2))
    key = bpy.context.active_object
    key.data.energy = 250
    key.data.size = 2.5
    key.rotation_euler = (math.radians(50), math.radians(15), math.radians(35))

    bpy.ops.object.light_add(type='AREA', location=(-2.0, 1.5, 2.4))
    fill = bpy.context.active_object
    fill.data.energy = 80
    fill.data.size = 3.0
    fill.data.color = (0.75, 0.82, 0.9)

    bpy.ops.object.light_add(type='SUN', location=(0, 0, 5))
    sun = bpy.context.active_object
    sun.data.energy = 1.2
    sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(-20))

    # Ground plane (shadow catcher-ish muted dirt)
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = 'PreviewGround'
    gm = mat('Ground', (0.45, 0.40, 0.34), 0.95)
    ground.data.materials.append(gm)


def add_capsule_guide():
    """Non-exported reference cylinder for preview only (0.6 m diameter × 1.75 m)."""
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.75, vertices=24, location=(0, 0, 0.875))
    guide = bpy.context.active_object
    guide.name = 'CapsuleGuide'
    m = mat('CapsuleGuide', (0.2, 0.55, 0.85), 0.4)
    m.blend_method = 'BLEND'
    try:
        bsdf = m.node_tree.nodes.get('Principled BSDF')
        if 'Alpha' in bsdf.inputs:
            bsdf.inputs['Alpha'].default_value = 0.18
    except Exception:
        pass
    guide.data.materials.append(m)
    guide.hide_render = False
    return guide


def render_previews(clerk_obj):
    setup_preview_world()
    guide = add_capsule_guide()

    bpy.ops.object.camera_add(location=(0, -3.2, 1.15))
    cam = bpy.context.active_object
    cam.name = 'PreviewCam'
    bpy.context.scene.camera = cam

    views = [
        # Character faces +Y (satchel/face); shoot from +Y
        ('front', (0, 3.4, 1.15), None, False),
        ('threequarter', (2.5, 2.7, 1.35), None, False),
        ('side', (3.4, 0.15, 1.15), None, False),
        ('front_with_capsule', (0, 3.4, 1.15), None, True),
    ]

    # Aim camera at mid-chest
    target = Vector((0, 0, 0.95))

    for name, loc, _rot, show_guide in views:
        guide.hide_render = not show_guide
        guide.hide_viewport = not show_guide
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

        out = os.path.join(PREV_DIR, f'clerk_{name}.png')
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print('Preview', out)

    # Remove guide + ground + lights + camera before final GLB? Caller exports before previews.
    return


def main():
    clerk = build_clerk()
    glb_path = os.path.join(OUT_DIR, 'clerk.glb')
    export_glb(glb_path)
    print('Exported', glb_path)

    # Re-import path: scene currently has joined mesh only — render previews from same scene
    # Add lights/camera/ground/guide for stills (guide not in prior export)
    render_previews(clerk)

    # Re-export clean GLB without preview helpers
    for name in ('PreviewGround', 'CapsuleGuide', 'PreviewCam'):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
    for obj in list(bpy.data.objects):
        if obj.type in {'LIGHT', 'CAMERA'}:
            bpy.data.objects.remove(obj, do_unlink=True)

    # Ensure only Clerk mesh remains and re-export
    if bpy.data.objects.get('Clerk'):
        export_glb(glb_path)
        print('Re-exported clean', glb_path)

    b = mesh_bounds(bpy.data.objects['Clerk'])
    meta = os.path.join(PREV_DIR, 'clerk_scale.txt')
    with open(meta, 'w') as f:
        f.write(
            f"height_m={b['size'][2]:.4f}\n"
            f"width_x_m={b['size'][0]:.4f}\n"
            f"depth_y_m={b['size'][1]:.4f}\n"
            f"capsule_diameter_m=0.60\n"
            f"formation_spacing_m=0.90 (context only)\n"
            f"target_height_m={TARGET_HEIGHT}\n"
        )
    print('Wrote', meta)
    print('Done.')


if __name__ == '__main__':
    main()
