"""Blender: Corbières ruined priory wall section (Broken Seal).

Broken limestone wall with empty window arches and rubble footing.
Modular section for Engineering. Dirt-and-mail Occitania 1208.
Rebuild:
  /usr/bin/blender -b -P tools/make_priory_ruin_wall.py
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

STEM = 'priory_ruin_wall'
# Wall section ~6.5 x 1.4 m footprint; broken top ~3.2–4.0 m
W, D = 6.5, 1.2
TW = 0.55


def jagged_top(bm, base_amp=0.35, seed=3.0):
    for v in bm.verts:
        if v.co.z > 2.2:
            jagged = abs(math.sin(v.co.x * 2.7 + seed)) * base_amp
            jagged += 0.15 * abs(math.sin(v.co.x * 7.1 + seed * 2))
            # pull down more on right half to read as collapse
            if v.co.x > 0.5:
                jagged += 0.25 * ((v.co.x - 0.5) / 3.0)
            v.co.z -= jagged
            v.co.y += 0.02 * math.sin(v.co.x * 4)


def make_wall(limestone, limestone_dark, rubble):
    parts = []
    hx = W * 0.5

    # Main wall body with two empty arched windows
    win = [(-1.8, 0.55), (1.1, 0.50)]  # (cx, half_width)
    bm = bmesh.new()
    # left solid
    bc.box_bm(bm, -hx, win[0][0] - win[0][1], -TW * 0.5, TW * 0.5, 0.25, 3.8)
    # between windows
    bc.box_bm(bm, win[0][0] + win[0][1], win[1][0] - win[1][1], -TW * 0.5, TW * 0.5, 0.25, 3.6)
    # right solid (lower ruin)
    bc.box_bm(bm, win[1][0] + win[1][1], hx, -TW * 0.5, TW * 0.5, 0.25, 3.1)
    # under / over each window
    for cx, hw in win:
        bc.box_bm(bm, cx - hw, cx + hw, -TW * 0.5, TW * 0.5, 0.25, 1.35)
        bc.box_bm(bm, cx - hw, cx + hw, -TW * 0.5, TW * 0.5, 2.55, 3.5)
    jagged_top(bm, 0.4, 2.5)
    bc.wear_stone(bm, 0.018, 1.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Ruin_Wall', bm, limestone, False))

    # Arch rings (empty — no fill)
    for cx, hw in win:
        bm = bmesh.new()
        bc.arch_opening_ring(bm, cx, 0.0, 1.95, hw - 0.05, hw + 0.12,
                             -TW * 0.55, TW * 0.55, segs=14)
        bc.wear_stone(bm, 0.01, 4.0)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bc.bm_to_object(f'Ruin_Arch{cx}', bm, limestone_dark, True))

    # Broken pier / buttress remnant on left
    bm = bmesh.new()
    bc.box_bm(bm, -hx - 0.35, -hx + 0.15, -0.45, 0.45, 0.0, 2.8)
    for v in bm.verts:
        if v.co.z > 2.0:
            v.co.z -= 0.4 * abs(math.sin(v.co.y * 5))
            v.co.x += 0.05
    bc.wear_stone(bm, 0.015, 6.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Ruin_Buttress', bm, limestone_dark, False))

    # Collapsed end stub on right (lower)
    bm = bmesh.new()
    bc.box_bm(bm, hx - 0.3, hx + 0.4, -0.5, 0.35, 0.0, 1.6)
    for v in bm.verts:
        if v.co.z > 1.0:
            v.co.z -= 0.35 * (v.co.x - (hx - 0.3)) / 0.7
            v.co.y += 0.08 * math.sin(v.co.z * 3)
    bc.wear_stone(bm, 0.02, 7.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Ruin_EndStub', bm, limestone, False))

    return bc.join_named('Ruin_Stone', parts)


def make_rubble(rubble, mud, limestone):
    parts = []
    # Footing rubble along base
    spots = [
        (-2.8, -0.55, 0.22, 0.18), (-1.5, 0.6, 0.28, 0.2), (-0.3, -0.7, 0.2, 0.15),
        (0.9, 0.55, 0.25, 0.18), (2.2, -0.5, 0.32, 0.22), (3.0, 0.4, 0.2, 0.16),
        (1.5, -0.8, 0.18, 0.12), (-2.0, 0.3, 0.15, 0.1), (0.2, 0.0, 0.35, 0.15),
    ]
    for i, (mx, my, mr, mz) in enumerate(spots):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=mr)
        for v in bm.verts:
            v.co.x *= 1.3 + 0.2 * math.sin(i)
            v.co.y *= 1.1
            v.co.z *= 0.7
            v.co += Vector((mx, my, mz * 0.5))
            if v.co.z < 0:
                v.co.z = 0.01
        mat = rubble if i % 3 else limestone
        parts.append(bc.bm_to_object(f'_rubble{i}', bm, mat, False))

    # Fallen voussoir chunks near arches
    for i, (mx, my, mz) in enumerate(((-1.6, 0.7, 0.25), (1.3, -0.65, 0.2), (1.0, 0.8, 0.15))):
        bm = bmesh.new()
        bc.box_bm(bm, mx - 0.25, mx + 0.2, my - 0.12, my + 0.15, 0.0, mz + 0.2)
        for v in bm.verts:
            v.co.z *= 0.9 + 0.1 * math.sin(v.co.x * 8)
            v.co.x += 0.03 * math.cos(v.co.y * 5)
        parts.append(bc.bm_to_object(f'_chunk{i}', bm, limestone, False))

    # Mud / earth banks
    for i, (mx, my, mr) in enumerate((
        (-2.5, -0.8, 0.35), (0.0, 0.75, 0.3), (2.8, -0.7, 0.28),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=mr)
        for v in bm.verts:
            v.co.z *= 0.3
            v.co.x *= 1.6
            v.co += Vector((mx, my, 0.02))
            if v.co.z < 0:
                v.co.z = 0.002
        parts.append(bc.bm_to_object(f'_mud{i}', bm, mud, True))

    return bc.join_named('Ruin_Debris', parts)


def build():
    bc.clear_scene()
    limestone = bc.mat('Ruin_Limestone', (0.55, 0.50, 0.40), 0.92, specular=0.12)
    limestone_dark = bc.mat('Ruin_LimestoneDark', (0.42, 0.38, 0.30), 0.94, specular=0.10)
    rubble = bc.mat('Ruin_Rubble', bc.PALETTE['rubble'], 0.95, specular=0.08)
    mud = bc.mat('Ruin_Mud', bc.PALETTE['mud'], 0.97, specular=0.05)
    meshes = [
        make_wall(limestone, limestone_dark, rubble),
        make_rubble(rubble, mud, limestone),
    ]
    meshes = [m for m in meshes if m]
    bc.plant_and_center(meshes)
    return meshes


def main():
    meshes = build()
    glb = os.path.join(bc.OUT_DIR, f'{STEM}.glb')
    bc.export_glb(glb)
    print('Exported', glb)
    bc.render_previews(STEM, cam_target=(0, 0, 2.0), dist_scale=0.95,
                       views=[
                           ('front', (0.0, -9.0, 2.8)),
                           ('threequarter', (7.0, -6.5, 3.8)),
                       ])
    bc.cleanup_preview_helpers()
    bc.export_glb(glb)
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bc.write_scale(STEM, mesh_objs, [
        'footprint_target_m~=6.5x1.4',
        'doorway_clear_w_m=none',
        'doorway=none_wall_section_only',
        'collision=tight_to_mesh',
        'tileable_wall_section=1',
        'style=corbieres_ruined_priory_occitan_1208',
    ])


if __name__ == '__main__':
    main()
