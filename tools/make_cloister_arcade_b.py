"""Blender: Fontfroide cloister arcade bay B (Broken Seal) — second modular variant.

Tiles with cloister_arcade at the same column-center pitch (3.20 m).
Variant: twin half-columns / pier cluster, low stone bench, slightly flatter arch.
Dirt-and-mail Occitania 1208 — Cistercian, not ornate Gothic.
Rebuild:
  /usr/bin/blender -b -P tools/make_cloister_arcade_b.py
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

STEM = 'cloister_arcade_b'
# Same tile pitch as cloister_arcade so Engineering can alternate bays
BAY_HALF = 1.60  # tile_pitch_m = 3.20
SPRING_Z = 2.00
COL_R = 0.12
WALL_Y = 0.95
WALK_Y_COURTYARD = -1.15
WALK_Y_WALL = WALL_Y + 0.05


def cylinder_bm(bm, cx, cy, z0, z1, r, segs=12):
    bot, top = [], []
    for i in range(segs):
        a = (i / segs) * math.tau
        bot.append(bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z0)))
        top.append(bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z1)))
    bm.verts.ensure_lookup_table()
    for i in range(segs):
        i2 = (i + 1) % segs
        bm.faces.new((bot[i], bot[i2], top[i2], top[i]))
    bc_v = bm.verts.new((cx, cy, z0))
    tc = bm.verts.new((cx, cy, z1))
    for i in range(segs):
        i2 = (i + 1) % segs
        bm.faces.new((bc_v, bot[i2], bot[i]))
        bm.faces.new((tc, top[i], top[i2]))


def make_walk(gravel, mud):
    parts = []
    bm = bmesh.new()
    bc.box_bm(bm, -BAY_HALF - 0.05, BAY_HALF + 0.05, WALK_Y_COURTYARD - 0.05, WALK_Y_WALL, 0.0, 0.04)
    for v in bm.verts:
        if v.co.z > 0.02:
            mid = 1.0 - abs(v.co.x) / (BAY_HALF + 0.2)
            v.co.z += 0.007 * mid + 0.003 * math.sin(v.co.x * 4.1 + v.co.y * 2.4)
    bc.wear_stone(bm, amp=0.005, seed=3.1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('ArcadeB_Walk', bm, gravel, False))

    for i, (x, y, sx) in enumerate((
        (-1.0, WALK_Y_COURTYARD - 0.14, 0.32),
        (0.5, WALK_Y_COURTYARD - 0.11, 0.26),
        (1.15, WALK_Y_COURTYARD - 0.09, 0.20),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=9, v_segments=5, radius=sx)
        for v in bm.verts:
            v.co.x *= 1.3
            v.co.y *= 0.65
            v.co.z *= 0.26
            v.co += Vector((x, y, 0.014))
            if v.co.z < 0:
                v.co.z = 0.002
        parts.append(bc.bm_to_object(f'_mud{i}', bm, mud, True))
    return bc.join_named('ArcadeB_Ground', parts)


def make_rear_wall(limestone, limestone_dark):
    parts = []
    bm = bmesh.new()
    bc.box_bm(bm, -BAY_HALF - 0.18, BAY_HALF + 0.18, WALL_Y, WALL_Y + 0.42, 0.0, SPRING_Z + 1.10)
    bc.wear_stone(bm, amp=0.01, seed=4.2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('ArcadeB_Wall', bm, limestone, False))

    # Blind niche — visual difference from arcade A
    bm = bmesh.new()
    bc.box_bm(bm, -0.35, 0.35, WALL_Y - 0.06, WALL_Y + 0.02, 0.55, 1.55)
    bc.wear_stone(bm, amp=0.006, seed=4.8)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('ArcadeB_Niche', bm, limestone_dark, False))

    bm = bmesh.new()
    bc.box_bm(bm, -BAY_HALF - 0.12, BAY_HALF + 0.12, WALL_Y - 0.28, WALL_Y + 0.08, 0.0, 0.28)
    bc.wear_stone(bm, amp=0.007, seed=5.1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('ArcadeB_Plinth', bm, limestone, False))
    return bc.join_named('ArcadeB_Rear', parts)


def make_twin_column(cx, cy, limestone, limestone_dark, label):
    """Paired shafts on one plinth — Fontfroide-style pier cluster variant."""
    parts = []
    bm = bmesh.new()
    bc.box_bm(bm, cx - 0.32, cx + 0.32, cy - 0.24, cy + 0.24, 0.0, 0.14)
    bc.wear_stone(bm, amp=0.006, seed=6.0 + cx)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object(f'_base{label}', bm, limestone, False))

    for j, ox in enumerate((-0.11, 0.11)):
        bm = bmesh.new()
        cylinder_bm(bm, cx + ox, cy, 0.12, 0.20, COL_R + 0.03, segs=12)
        parts.append(bc.bm_to_object(f'_torus{label}{j}', bm, limestone_dark, True))

        bm = bmesh.new()
        cylinder_bm(bm, cx + ox, cy, 0.18, SPRING_Z - 0.06, COL_R - 0.01, segs=12)
        for v in bm.verts:
            if 0.3 < v.co.z < SPRING_Z - 0.2:
                v.co.x += 0.004 * math.sin(v.co.z * 4.2 + ox)
        bc.wear_stone(bm, amp=0.005, seed=8.0 + ox)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bc.bm_to_object(f'_shaft{label}{j}', bm, limestone, True))

        bm = bmesh.new()
        cylinder_bm(bm, cx + ox, cy, SPRING_Z - 0.08, SPRING_Z + 0.10, COL_R + 0.04, segs=10)
        parts.append(bc.bm_to_object(f'_cap{label}{j}', bm, limestone, True))

    # Shared abacus across twins
    bm = bmesh.new()
    bc.box_bm(bm, cx - 0.30, cx + 0.30, cy - 0.20, cy + 0.20, SPRING_Z + 0.08, SPRING_Z + 0.16)
    bc.wear_stone(bm, amp=0.004, seed=10.0 + cx)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object(f'_abacus{label}', bm, limestone, False))
    return parts


def make_columns(limestone, limestone_dark):
    parts = []
    cy = WALL_Y - 0.38
    for side, sx in (('L', -1), ('R', 1)):
        parts.extend(make_twin_column(sx * BAY_HALF, cy, limestone, limestone_dark, side))
    return bc.join_named('ArcadeB_Columns', parts)


def make_arch(limestone):
    parts = []
    cy0 = WALL_Y - 0.55
    cy1 = WALL_Y - 0.18
    half_span = BAY_HALF - 0.28
    rise = 0.82  # slightly flatter than arcade A
    r_inner = (half_span * half_span + rise * rise) / (2.0 * rise)
    r_outer = r_inner + 0.18
    z_c = SPRING_Z + 0.12
    z_center = z_c - (r_inner - rise)
    segs = 14

    bm = bmesh.new()
    front_o, front_i, back_o, back_i = [], [], [], []
    ang_l = math.atan2(z_c - z_center, -half_span)
    ang_r = math.atan2(z_c - z_center, half_span)
    for i in range(segs + 1):
        t = i / segs
        ang = ang_l + t * (ang_r - ang_l)
        co, si = math.cos(ang), math.sin(ang)
        front_o.append(bm.verts.new((r_outer * co, cy0, z_center + r_outer * si)))
        front_i.append(bm.verts.new((r_inner * co, cy0, z_center + r_inner * si)))
        back_o.append(bm.verts.new((r_outer * co, cy1, z_center + r_outer * si)))
        back_i.append(bm.verts.new((r_inner * co, cy1, z_center + r_inner * si)))
    bm.verts.ensure_lookup_table()
    for i in range(segs):
        bm.faces.new((front_i[i], front_i[i + 1], front_o[i + 1], front_o[i]))
        bm.faces.new((back_o[i], back_o[i + 1], back_i[i + 1], back_i[i]))
        bm.faces.new((front_o[i], front_o[i + 1], back_o[i + 1], back_o[i]))
        bm.faces.new((back_i[i], back_i[i + 1], front_i[i + 1], front_i[i]))
    for idx in (0, segs):
        bm.faces.new((front_i[idx], front_o[idx], back_o[idx], back_i[idx]))
    bc.wear_stone(bm, amp=0.006, seed=14.2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('ArcadeB_Archivolt', bm, limestone, True))

    crown = z_center + r_outer
    bm = bmesh.new()
    bc.box_bm(bm, -BAY_HALF - 0.12, BAY_HALF + 0.12, cy0 - 0.05, WALL_Y + 0.35,
              crown - 0.08, crown + 0.30)
    for v in bm.verts:
        if v.co.z > crown + 0.12:
            v.co.z += 0.035 * max(0.0, (WALL_Y + 0.35 - v.co.y) / 1.0)
    bc.wear_stone(bm, amp=0.008, seed=15.2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('ArcadeB_Entablature', bm, limestone, False))

    oak = bc.mat('ArcadeB_Oak', bc.PALETTE['oak'], 0.85, specular=0.2)
    soffit_z = z_center + r_inner - 0.04
    bm = bmesh.new()
    bc.box_bm(bm, -half_span + 0.1, half_span - 0.1, cy0 + 0.04, cy1 - 0.04,
              soffit_z - 0.05, soffit_z)
    parts.append(bc.bm_to_object('ArcadeB_Beam', bm, oak, False))
    return bc.join_named('ArcadeB_Arch', parts)


def make_bench(limestone):
    """Low stone bench against rear wall — variant dressing."""
    parts = []
    bm = bmesh.new()
    bc.box_bm(bm, -0.85, 0.85, WALL_Y - 0.55, WALL_Y - 0.22, 0.28, 0.42)
    bc.wear_stone(bm, amp=0.006, seed=20.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('ArcadeB_BenchTop', bm, limestone, False))
    for sx in (-0.7, 0.7):
        bm = bmesh.new()
        bc.box_bm(bm, sx - 0.10, sx + 0.10, WALL_Y - 0.52, WALL_Y - 0.25, 0.0, 0.30)
        parts.append(bc.bm_to_object(f'_bleg{sx}', bm, limestone, False))
    return bc.join_named('ArcadeB_Bench', parts)


def build():
    bc.clear_scene()
    limestone = bc.mat('ArcadeB_Limestone', (0.62, 0.56, 0.45), 0.90, specular=0.14)
    limestone_dark = bc.mat('ArcadeB_LimestoneDark', (0.48, 0.44, 0.36), 0.93, specular=0.12)
    gravel = bc.mat('ArcadeB_Gravel', (0.40, 0.36, 0.28), 0.97, specular=0.06)
    mud = bc.mat('ArcadeB_Mud', bc.PALETTE['mud'], 0.97, specular=0.05)
    meshes = [
        make_walk(gravel, mud),
        make_rear_wall(limestone, limestone_dark),
        make_columns(limestone, limestone_dark),
        make_arch(limestone),
        make_bench(limestone),
    ]
    meshes = [m for m in meshes if m]
    bc.plant_and_center(meshes)
    return meshes


def main():
    meshes = build()
    glb = os.path.join(bc.OUT_DIR, f'{STEM}.glb')
    bc.export_glb(glb)
    print('Exported', glb)
    bc.render_previews(STEM, cam_target=(0, -0.1, 1.5),
                       views=[
                           ('front', (0.0, -7.5, 2.0)),
                           ('threequarter', (5.8, -5.5, 3.0)),
                       ])
    bc.cleanup_preview_helpers()
    bc.export_glb(glb)
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bc.write_scale(STEM, mesh_objs, [
        'origin=ground_center_bay_footprint',
        'bay_width_m~=3.20 column_centers_at_pm1.60',
        'tile_pitch_m=3.20',
        'tiles_with=cloister_arcade',
        'variant=twin_columns_bench_blind_niche',
        'collision=tight_to_mesh',
        'style=cistercian_fontfroide_cloister_bay_b_occitan_1208',
        'off_lane=1',
        'road_clear_m=2.4',
        'road_crown_x=[-1.2,1.2]_no_colliders',
        'place_band=heavy_shell_|x|>=4_or_hub_pocket',
        'hub_anchor_hint=Fontfroide_cloister_(-6,+38)',
        'soft_shoulder_|x|_1.2-4=light_only_not_this_shell',
        'place=cloister_gallery_hub_pocket_not_road_crown',
    ])


if __name__ == '__main__':
    main()
