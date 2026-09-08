"""Blender: Limestone rubble / fallen masonry pile (Broken Seal).

Corbières densifier — off-lane roadside / ruin-yard clutter.
Dirt-and-mail Occitania 1208. Visual densifier; collision tight to pile mass.
Rebuild:
  /usr/bin/blender -b -P tools/make_ruin_debris_pile.py
"""
from __future__ import annotations
import math, os, sys
import bmesh
import bpy
from mathutils import Vector

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import building_shell_common as bc

STEM = 'ruin_debris_pile'


def make_pile(limestone, limestone_dark, rubble, mud):
    parts = []
    # Core mound
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.85)
    for v in bm.verts:
        v.co.x *= 1.35
        v.co.y *= 1.05
        v.co.z *= 0.55
        v.co.z += 0.25
        # flatten underside
        if v.co.z < 0.05:
            v.co.z = 0.02 + 0.02 * abs(math.sin(v.co.x * 5))
        # irregular crown
        v.co.z += 0.08 * math.sin(v.co.x * 4.2) * math.cos(v.co.y * 3.5)
    bc.wear_stone(bm, amp=0.04, seed=1.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Debris_Mound', bm, rubble, False))

    # Fallen ashlar blocks / voussoirs
    blocks = [
        (-0.55, -0.35, 0.0, 0.45, 0.22, 0.18, 0.15),
        (0.40, 0.25, 0.05, 0.38, 0.28, 0.20, 0.22),
        (0.10, -0.50, 0.08, 0.50, 0.18, 0.15, 0.12),
        (-0.20, 0.40, 0.12, 0.32, 0.25, 0.16, -0.2),
        (0.65, -0.10, 0.0, 0.28, 0.20, 0.14, 0.4),
        (-0.70, 0.15, 0.02, 0.35, 0.16, 0.20, -0.35),
        (0.0, 0.05, 0.35, 0.40, 0.22, 0.18, 0.1),
        (-0.35, -0.15, 0.42, 0.30, 0.18, 0.14, 0.5),
    ]
    for i, (cx, cy, cz, sx, sy, sz, rot) in enumerate(blocks):
        bm = bmesh.new()
        bc.box_bm(bm, -sx * 0.5, sx * 0.5, -sy * 0.5, sy * 0.5, 0.0, sz)
        # slight taper / break
        for v in bm.verts:
            if v.co.z > sz * 0.6:
                v.co.x *= 0.92
                v.co.y *= 0.95
            ang = rot
            x, y = v.co.x, v.co.y
            v.co.x = x * math.cos(ang) - y * math.sin(ang) + cx
            v.co.y = x * math.sin(ang) + y * math.cos(ang) + cy
            v.co.z += cz
        bc.wear_stone(bm, amp=0.015, seed=2.0 + i)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        mat = limestone if i % 2 == 0 else limestone_dark
        parts.append(bc.bm_to_object(f'_block{i}', bm, mat, False))

    # Smaller rubble stones
    for i, (mx, my, mr, mz) in enumerate((
        (-0.9, -0.55, 0.12, 0.08), (0.85, 0.45, 0.14, 0.09),
        (-0.15, 0.70, 0.10, 0.07), (0.55, -0.60, 0.11, 0.08),
        (-0.50, 0.55, 0.09, 0.06), (0.20, -0.75, 0.13, 0.07),
        (0.95, 0.05, 0.10, 0.06), (-0.80, -0.20, 0.11, 0.07),
        (0.30, 0.55, 0.08, 0.05), (-0.05, -0.30, 0.15, 0.10),
    )):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=mr)
        for v in bm.verts:
            v.co.x *= 1.2 + 0.15 * math.sin(i * 1.7)
            v.co.y *= 1.0
            v.co.z *= 0.65
            v.co += Vector((mx, my, mz))
            if v.co.z < 0:
                v.co.z = 0.01
        mat = rubble if i % 3 else limestone
        parts.append(bc.bm_to_object(f'_stone{i}', bm, mat, False))

    # Broken column drum fragment
    bm = bmesh.new()
    segs = 10
    r, h = 0.16, 0.22
    cx, cy, cz = -0.25, -0.55, 0.15
    bot, top = [], []
    for i in range(segs):
        a = (i / segs) * math.tau
        bot.append(bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), cz)))
        # broken top — uneven
        z1 = cz + h * (0.55 + 0.45 * abs(math.sin(a * 2)))
        top.append(bm.verts.new((cx + (r * 0.95) * math.cos(a), cy + (r * 0.95) * math.sin(a), z1)))
    bm.verts.ensure_lookup_table()
    for i in range(segs):
        i2 = (i + 1) % segs
        bm.faces.new((bot[i], bot[i2], top[i2], top[i]))
    bc_v = bm.verts.new((cx, cy, cz))
    for i in range(segs):
        i2 = (i + 1) % segs
        bm.faces.new((bc_v, bot[i2], bot[i]))
    # open broken top — fan to center approx
    tc = bm.verts.new((cx, cy, cz + h * 0.7))
    for i in range(segs):
        i2 = (i + 1) % segs
        bm.faces.new((tc, top[i], top[i2]))
    bc.wear_stone(bm, amp=0.01, seed=9.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Debris_Drum', bm, limestone_dark, True))

    # Mud skirts at pile edge
    for i, (mx, my, mr) in enumerate((
        (-1.0, -0.7, 0.28), (1.0, 0.5, 0.25), (0.0, -0.9, 0.22),
        (-0.6, 0.75, 0.20), (0.8, -0.7, 0.24),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=4, radius=mr)
        for v in bm.verts:
            v.co.z *= 0.28
            v.co.x *= 1.4
            v.co += Vector((mx, my, 0.015))
            if v.co.z < 0:
                v.co.z = 0.002
        parts.append(bc.bm_to_object(f'_mud{i}', bm, mud, True))

    return bc.join_named('Debris_Pile', parts)


def build():
    bc.clear_scene()
    limestone = bc.mat('Debris_Limestone', bc.PALETTE['limestone'], 0.92, specular=0.12)
    limestone_dark = bc.mat('Debris_LimestoneDark', bc.PALETTE['limestone_dark'], 0.94, specular=0.10)
    rubble = bc.mat('Debris_Rubble', bc.PALETTE['rubble'], 0.95, specular=0.08)
    mud = bc.mat('Debris_Mud', bc.PALETTE['mud'], 0.97, specular=0.05)
    meshes = [make_pile(limestone, limestone_dark, rubble, mud)]
    meshes = [m for m in meshes if m]
    bc.plant_and_center(meshes)
    return meshes


def main():
    meshes = build()
    glb = os.path.join(bc.OUT_DIR, f'{STEM}.glb')
    bc.export_glb(glb)
    print('Exported', glb)
    bc.render_previews(STEM, cam_target=(0, 0, 0.45),
                       views=[
                           ('front', (0.0, -3.8, 1.2)),
                           ('threequarter', (3.0, -2.8, 1.6)),
                       ])
    bc.cleanup_preview_helpers()
    bc.export_glb(glb)
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bc.write_scale(STEM, mesh_objs, [
        'footprint_target_m~=2.2x1.8',
        'reads=limestone_rubble_fallen_masonry_pile',
        'collision=tight_to_mesh',
        'visual_ok_for_scattered_pebbles=1',
        'style=corbieres_ruin_debris_occitan_1208',
        'off_lane=1',
        'road_clear_m=2.4',
        'road_crown_x=[-1.2,1.2]_no_colliders',
        'place_band=soft_shoulder_|x|_1.2-4_or_heavy_|x|>=4',
        'hub_anchor_hint=Corbieres_turnoff_(-4,-28)_or_priory_ruin_yards',
        'place=off_road_corbieres_densifier_ruin_yard',
    ])


if __name__ == '__main__':
    main()
