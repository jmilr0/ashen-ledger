"""Blender: smooth low-poly fantasy humanoids (not voxel). Exports GLB."""
import math
import os
import bpy
from mathutils import Vector

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'models', 'characters')
os.makedirs(OUT_DIR, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes):
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials):
        if block.users == 0:
            bpy.data.materials.remove(block)


def mat(name, color, roughness=0.65, metallic=0.0):
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


def cone(name, radius1, depth, vertices, material, loc=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(radius1=radius1, depth=depth, vertices=vertices, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


def ico_sphere(name, radius, subdivisions, material, loc=(0, 0, 0)):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=radius, subdivisions=subdivisions, location=loc)
    obj = bpy.context.active_object
    obj.name = name
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
    min_z = min((joined.matrix_world @ Vector(c)).z for c in joined.bound_box)
    joined.location.z -= min_z
    bpy.ops.object.transform_apply(location=True)
    return joined


def export_glb(path):
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_yup=True,
    )


def build_humanoid(style):
    clear_scene()
    skin = mat('Skin', style['skin'], 0.55)
    cloth = mat('Cloth', style['cloth'], 0.75)
    accent = mat('Accent', style['accent'], 0.55, metallic=style.get('accent_metal', 0.05))
    hair_m = mat('Hair', style['hair'], 0.7)
    leather = mat('Leather', style.get('leather', (0.25, 0.16, 0.1)), 0.8)
    dark = mat('Dark', (0.08, 0.07, 0.09), 0.85)

    cylinder('Torso', 0.22, 0.55, 12, cloth, loc=(0, 0, 1.05), scale=(1.05, 0.85, 1))
    uv_sphere('Pelvis', 0.2, 12, 8, cloth, loc=(0, 0, 0.72), scale=(1.1, 0.85, 0.7))
    uv_sphere('Head', 0.16, 14, 10, skin, loc=(0, 0, 1.55))
    cylinder('Neck', 0.06, 0.1, 8, skin, loc=(0, 0, 1.38))

    if style.get('hood'):
        uv_sphere('Hood', 0.19, 12, 8, cloth, loc=(0, -0.02, 1.58), scale=(1.15, 1.25, 1.05))
    else:
        ico_sphere('Hair', 0.17, 2, hair_m, loc=(0, -0.02, 1.62))
        if style.get('long_hair'):
            cone('HairTail', 0.1, 0.35, 8, hair_m, loc=(0, -0.12, 1.4))

    if style.get('hat'):
        cylinder('HatBrim', 0.22, 0.03, 12, dark, loc=(0, 0, 1.72))
        cone('HatCrown', 0.12, 0.22, 10, dark, loc=(0, 0, 1.84))

    for side, sx in (('L', 0.32), ('R', -0.32)):
        cylinder(f'UpperArm{side}', 0.055, 0.32, 8, cloth, loc=(sx, 0, 1.15), rot=(0, math.radians(12 if sx > 0 else -12), 0))
        cylinder(f'ForeArm{side}', 0.045, 0.28, 8, skin, loc=(sx * 1.15, 0.02, 0.88), rot=(0, math.radians(8 if sx > 0 else -8), 0))
        uv_sphere(f'Hand{side}', 0.05, 8, 6, skin, loc=(sx * 1.25, 0.04, 0.7))

    for side, sx in (('L', 0.1), ('R', -0.1)):
        leg_mat = cloth if style.get('skirt') else leather
        cylinder(f'Thigh{side}', 0.075, 0.38, 8, leg_mat, loc=(sx, 0, 0.48))
        cylinder(f'Calf{side}', 0.055, 0.34, 8, leather, loc=(sx, 0.02, 0.18))
        uv_sphere(f'Boot{side}', 0.07, 10, 6, dark, loc=(sx, 0.06, 0.04), scale=(1.1, 1.6, 0.7))

    if style.get('cloak'):
        cylinder('Cloak', 0.28, 0.7, 10, accent, loc=(0, -0.08, 1.0), scale=(1.15, 0.55, 1))

    cylinder('Belt', 0.23, 0.05, 12, leather, loc=(0, 0, 0.78))
    if style.get('pouch'):
        uv_sphere('Pouch', 0.06, 8, 6, leather, loc=(0.18, 0.12, 0.75), scale=(1, 0.8, 1.2))

    if style.get('role') == 'investigator':
        cylinder('Sheath', 0.03, 0.18, 6, dark, loc=(-0.2, 0.14, 0.78), rot=(math.radians(90), 0, math.radians(20)))
        cylinder('Strap', 0.02, 0.55, 6, leather, loc=(0.12, 0.05, 1.05), rot=(0, math.radians(35), 0))
    elif style.get('role') == 'clerk':
        soft_box('Book', 0.12, accent, loc=(0.28, 0.1, 0.95), scale=(0.6, 0.15, 0.9))
        cylinder('Quill', 0.012, 0.22, 6, hair_m, loc=(-0.12, 0.14, 1.55), rot=(math.radians(70), 0, 0))
    elif style.get('role') == 'dockhand':
        bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.02, location=(0.28, 0.1, 0.85))
        torus = bpy.context.active_object
        torus.name = 'Rope'
        torus.data.materials.append(leather)
        bpy.ops.object.shade_smooth()

    if style.get('skirt'):
        cone('Skirt', 0.32, 0.4, 12, cloth, loc=(0, 0, 0.55))

    join_all(style['name'])
    out = os.path.join(OUT_DIR, f"{style['file']}.glb")
    export_glb(out)
    print('Exported', out)


def main():
    styles = [
        {
            'name': 'Rowan', 'file': 'rowan',
            'skin': (0.86, 0.72, 0.58), 'cloth': (0.35, 0.28, 0.22),
            'accent': (0.45, 0.22, 0.12), 'hair': (0.22, 0.14, 0.1),
            'leather': (0.28, 0.18, 0.1), 'cloak': True, 'pouch': True,
            'role': 'investigator',
        },
        {
            'name': 'Mirelle', 'file': 'mirelle',
            'skin': (0.9, 0.78, 0.7), 'cloth': (0.28, 0.18, 0.38),
            'accent': (0.55, 0.35, 0.7), 'hair': (0.15, 0.1, 0.18),
            'leather': (0.2, 0.12, 0.18), 'cloak': True, 'hood': True,
            'long_hair': True, 'skirt': True, 'pouch': True,
            'role': 'clerk', 'accent_metal': 0.15,
        },
        {
            'name': 'Brin', 'file': 'brin',
            'skin': (0.7, 0.55, 0.42), 'cloth': (0.22, 0.32, 0.28),
            'accent': (0.4, 0.35, 0.2), 'hair': (0.35, 0.28, 0.18),
            'leather': (0.3, 0.22, 0.12), 'hat': True, 'role': 'dockhand',
        },
    ]
    for s in styles:
        build_humanoid(s)
    print('Done.')


if __name__ == '__main__':
    main()
