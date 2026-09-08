"""Blender: Small lean-to / village shed (Broken Seal).

Compact off-road lean-to: oak posts, limestone dwarf walls, thatch lean-to roof.
Open front ≥1.2 m clear. Dirt-and-mail Occitania 1208.
Rebuild:
  /usr/bin/blender -b -P tools/make_village_shed.py
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

STEM = 'village_shed'
# Compact footprint ~2.4 x 1.8 m; open front along -Y
W, D = 2.40, 1.80
HX, HY = W * 0.5, D * 0.5


def make_walls(limestone, limestone_dark, oak):
    parts = []
    # Rear wall (full)
    bm = bmesh.new()
    bc.box_bm(bm, -HX, HX, HY - 0.18, HY, 0.0, 1.65)
    bc.wear_stone(bm, amp=0.01, seed=1.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Shed_Rear', bm, limestone, False))

    # Side walls — leave front open (≥1.2 m clear)
    for name, x0, x1 in (('L', -HX, -HX + 0.16), ('R', HX - 0.16, HX)):
        bm = bmesh.new()
        bc.box_bm(bm, x0, x1, -HY + 0.15, HY, 0.0, 1.45)
        # step down toward front
        for v in bm.verts:
            if v.co.y < -0.2 and v.co.z > 1.0:
                v.co.z -= 0.15 * ((-0.2 - v.co.y) / (HY - 0.15))
        bc.wear_stone(bm, amp=0.008, seed=2.0)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bc.bm_to_object(f'Shed_Side{name}', bm, limestone_dark, False))

    # Front posts (oak) — clear opening ~1.9 m between posts
    for sx in (-0.95, 0.95):
        bm = bmesh.new()
        bc.box_bm(bm, sx - 0.07, sx + 0.07, -HY, -HY + 0.12, 0.0, 1.55)
        for v in bm.verts:
            v.co.x += 0.004 * math.sin(v.co.z * 8)
        parts.append(bc.bm_to_object(f'_post{sx}', bm, oak, False))

    # Front lintel beam
    bm = bmesh.new()
    bc.box_bm(bm, -1.05, 1.05, -HY - 0.02, -HY + 0.14, 1.48, 1.60)
    parts.append(bc.bm_to_object('Shed_Lintel', bm, oak, False))

    # Corner braces
    for sx in (-0.95, 0.95):
        bm = bmesh.new()
        bc.box_bm(bm, sx - 0.04, sx + 0.04, -HY + 0.08, -HY + 0.45, 1.15, 1.28)
        # slant by moving verts
        for v in bm.verts:
            if v.co.y > -HY + 0.25:
                v.co.z += 0.18
        parts.append(bc.bm_to_object(f'_brace{sx}', bm, oak, False))

    return bc.join_named('Shed_Structure', parts)


def make_roof(thatch, thatch_dark, oak):
    parts = []
    # Lean-to: high at rear, low at front
    z_rear, z_front = 2.05, 1.55
    bm = bmesh.new()
    # roof slab as thin prism
    verts = [
        bm.verts.new((-HX - 0.12, -HY - 0.15, z_front)),
        bm.verts.new((HX + 0.12, -HY - 0.15, z_front)),
        bm.verts.new((HX + 0.12, HY + 0.08, z_rear)),
        bm.verts.new((-HX - 0.12, HY + 0.08, z_rear)),
        bm.verts.new((-HX - 0.12, -HY - 0.15, z_front - 0.10)),
        bm.verts.new((HX + 0.12, -HY - 0.15, z_front - 0.10)),
        bm.verts.new((HX + 0.12, HY + 0.08, z_rear - 0.10)),
        bm.verts.new((-HX - 0.12, HY + 0.08, z_rear - 0.10)),
    ]
    bm.verts.ensure_lookup_table()
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    for f in faces:
        bm.faces.new([verts[i] for i in f])
    for v in bm.verts:
        v.co.z += 0.02 * math.sin(v.co.x * 6) * math.cos(v.co.y * 4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Shed_Thatch', bm, thatch, False))

    # Ridge / eaves poles
    for y, z in ((-HY - 0.05, z_front - 0.02), (HY - 0.05, z_rear - 0.02)):
        bm = bmesh.new()
        bc.box_bm(bm, -HX - 0.05, HX + 0.05, y - 0.04, y + 0.04, z - 0.04, z + 0.04)
        parts.append(bc.bm_to_object(f'_pole{y}', bm, oak, False))

    # Thatch overhang clumps
    for i, x in enumerate((-0.8, -0.2, 0.4, 0.9)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=0.12)
        for v in bm.verts:
            v.co.x *= 1.5
            v.co.y *= 0.6
            v.co.z *= 0.4
            v.co += Vector((x, -HY - 0.18, z_front - 0.05))
        parts.append(bc.bm_to_object(f'_thatchlip{i}', bm, thatch_dark, True))

    return bc.join_named('Shed_Roof', parts)


def make_floor_clutter(mud, oak, thatch_dark):
    parts = []
    # Packed earth floor
    bm = bmesh.new()
    bc.box_bm(bm, -HX + 0.05, HX - 0.05, -HY + 0.05, HY - 0.15, 0.0, 0.04)
    for v in bm.verts:
        if v.co.z > 0.02:
            v.co.z += 0.005 * math.sin(v.co.x * 5 + v.co.y * 3)
    parts.append(bc.bm_to_object('Shed_Floor', bm, mud, False))

    # Tool shelf / plank against rear
    bm = bmesh.new()
    bc.box_bm(bm, -0.6, 0.6, HY - 0.35, HY - 0.22, 0.55, 0.62)
    parts.append(bc.bm_to_object('Shed_Shelf', bm, oak, False))

    # Stacked firewood
    for i, (x, y, z) in enumerate(((-0.7, 0.4, 0.08), (-0.55, 0.5, 0.08), (-0.62, 0.45, 0.20))):
        bm = bmesh.new()
        bc.box_bm(bm, x - 0.18, x + 0.18, y - 0.06, y + 0.06, z, z + 0.08)
        parts.append(bc.bm_to_object(f'_wood{i}', bm, oak, False))

    # Straw scatter near front (visual-only clutter)
    for i, (x, y) in enumerate(((-0.4, -0.5), (0.3, -0.6), (0.0, -0.35))):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=5, v_segments=3, radius=0.08)
        for v in bm.verts:
            v.co.z *= 0.25
            v.co.x *= 1.6
            v.co += Vector((x, y, 0.03))
            if v.co.z < 0:
                v.co.z = 0.005
        parts.append(bc.bm_to_object(f'_straw{i}', bm, thatch_dark, True))

    return bc.join_named('Shed_Interior', parts)


def build():
    bc.clear_scene()
    limestone = bc.mat('Shed_Limestone', bc.PALETTE['limestone'], 0.92, specular=0.12)
    limestone_dark = bc.mat('Shed_LimestoneDark', bc.PALETTE['limestone_dark'], 0.94, specular=0.10)
    oak = bc.mat('Shed_Oak', bc.PALETTE['oak'], 0.88, specular=0.18)
    thatch = bc.mat('Shed_Thatch', bc.PALETTE['thatch'], 0.95, specular=0.06)
    thatch_dark = bc.mat('Shed_ThatchDark', bc.PALETTE['thatch_dark'], 0.96, specular=0.05)
    mud = bc.mat('Shed_Mud', bc.PALETTE['mud'], 0.97, specular=0.05)
    meshes = [
        make_walls(limestone, limestone_dark, oak),
        make_roof(thatch, thatch_dark, oak),
        make_floor_clutter(mud, oak, thatch_dark),
    ]
    meshes = [m for m in meshes if m]
    bc.plant_and_center(meshes)
    return meshes


def main():
    meshes = build()
    glb = os.path.join(bc.OUT_DIR, f'{STEM}.glb')
    bc.export_glb(glb)
    print('Exported', glb)
    bc.render_previews(STEM, cam_target=(0, 0, 1.0),
                       views=[
                           ('front', (0.0, -5.0, 1.6)),
                           ('threequarter', (4.0, -3.8, 2.2)),
                       ])
    bc.cleanup_preview_helpers()
    bc.export_glb(glb)
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bc.write_scale(STEM, mesh_objs, [
        'footprint_target_m~=2.4x1.8',
        'doorway_clear_w_m~=1.90',
        'doorway=open_front_lean_to',
        'collision=tight_to_mesh',
        'style=occitan_village_lean_to_1208',
        'off_lane=1',
        'road_clear_m=2.4',
        'road_crown_x=[-1.2,1.2]_no_colliders',
        'place_band=heavy_shell_|x|>=4',
        'hub_anchor_hint=parish_(+7,-2)_or_goldsmith_(-7,-14)_or_Narbonne_(+5,-44)',
        'soft_shoulder_|x|_1.2-4=too_heavy_keep_out',
        'place=off_road_village_edge_compact_shed',
    ])


if __name__ == '__main__':
    main()
